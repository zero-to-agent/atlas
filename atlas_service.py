"""atlas_service.py — Production FastAPI service for Atlas.

Includes structured logging, cost tracking, prompt caching, model routing,
rate limiting, circuit breaker, PII redaction, and safety filters.

Requires: ANTHROPIC_API_KEY environment variable.
Usage: uvicorn atlas_service:app --reload
"""

import os
import re
import time
import uuid
import json
import random
import hashlib
import logging
import sqlite3
from datetime import datetime, timezone
from collections import defaultdict

from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
import anthropic

# ============================================================================
# Configuration
# ============================================================================

MODEL = "claude-sonnet-4-6"
FALLBACK_MODEL = "claude-haiku-4-5-20251001"
DAILY_BUDGET_USD = float(os.environ.get("DAILY_BUDGET_USD", "10.0"))
BUDGET_ALERT_THRESHOLD = 0.80
DB_PATH = "atlas_costs.db"
MAX_CONCURRENT = 10
RATE_LIMIT_RPM = 30
MAX_MESSAGE_LENGTH = 50_000
CACHE_TTL_SECONDS = 300

SYSTEM_PROMPT = "You are Atlas, a helpful development assistant."

# ============================================================================
# Logging
# ============================================================================

logger = logging.getLogger("atlas")
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter("%(message)s"))
logger.addHandler(handler)

# ============================================================================
# Database
# ============================================================================

def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS cost_log (
            request_id TEXT PRIMARY KEY,
            timestamp TEXT NOT NULL,
            model TEXT NOT NULL,
            input_tokens INTEGER NOT NULL,
            output_tokens INTEGER NOT NULL,
            estimated_cost_usd REAL NOT NULL
        )
    """)
    conn.commit()
    conn.close()

init_db()

def persist_cost(request_id, model, input_tokens, output_tokens, cost):
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "INSERT OR REPLACE INTO cost_log VALUES (?, ?, ?, ?, ?, ?)",
        (request_id, datetime.now(timezone.utc).isoformat(), model,
         input_tokens, output_tokens, cost),
    )
    conn.commit()
    conn.close()

def get_today_cost() -> float:
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    conn = sqlite3.connect(DB_PATH)
    row = conn.execute(
        "SELECT COALESCE(SUM(estimated_cost_usd), 0) FROM cost_log WHERE timestamp LIKE ?",
        (f"{today}%",),
    ).fetchone()
    conn.close()
    return row[0]

# ============================================================================
# Pricing
# ============================================================================

PRICING = {
    "claude-sonnet-4-6": {"input": 3.00, "output": 15.00, "cache_read": 0.30, "cache_write": 3.75},
    "claude-haiku-4-5-20251001": {"input": 1.00, "output": 5.00, "cache_read": 0.10, "cache_write": 1.25},
    "claude-opus-4-6": {"input": 15.00, "output": 75.00, "cache_read": 1.50, "cache_write": 18.75},
}

def estimate_cost(model: str, usage) -> float:
    p = PRICING.get(model, PRICING["claude-sonnet-4-6"])
    input_cost = (usage.input_tokens / 1_000_000) * p["input"]
    output_cost = (usage.output_tokens / 1_000_000) * p["output"]
    cache_read = getattr(usage, "cache_read_input_tokens", 0) or 0
    cache_write = getattr(usage, "cache_creation_input_tokens", 0) or 0
    cache_cost = (cache_read / 1_000_000) * p["cache_read"] + (cache_write / 1_000_000) * p["cache_write"]
    return input_cost + output_cost + cache_cost

# ============================================================================
# Safety Filters
# ============================================================================

PII_PATTERNS = [
    (re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+"), "[EMAIL_REDACTED]"),
    (re.compile(r"\b\d{3}[-.]?\d{3}[-.]?\d{4}\b"), "[PHONE_REDACTED]"),
    (re.compile(r"(?:sk-|AKIA|ghp_|xox[bpsa]-)[A-Za-z0-9_\-]{20,}"), "[SECRET_REDACTED]"),
]

def redact_pii(text: str) -> str:
    for pattern, replacement in PII_PATTERNS:
        text = pattern.sub(replacement, text)
    return text

INJECTION_PATTERNS = [
    re.compile(r"ignore\s+(all\s+)?previous\s+instructions", re.IGNORECASE),
    re.compile(r"you\s+are\s+now\s+", re.IGNORECASE),
    re.compile(r"system\s*prompt", re.IGNORECASE),
]

def check_injection(text: str) -> bool:
    return any(p.search(text) for p in INJECTION_PATTERNS)

BLOCKED_OUTPUT_PATTERNS = [
    re.compile(r"(?:sk-|AKIA|ghp_)[A-Za-z0-9_\-]{20,}"),
    re.compile(r"DROP\s+TABLE|DELETE\s+FROM", re.IGNORECASE),
]

def guardrail_check(text: str) -> tuple[str, str]:
    redacted = redact_pii(text)
    pii_decision = "pii_redacted" if redacted != text else "pass"
    for pattern in BLOCKED_OUTPUT_PATTERNS:
        if pattern.search(redacted):
            return "I'm unable to provide that response. Please rephrase your request.", "blocked"
    return redacted, pii_decision if pii_decision != "pass" else "allow"

# ============================================================================
# Response Cache
# ============================================================================

_response_cache: dict[str, tuple[str, float]] = {}

def cache_key(message: str) -> str:
    return hashlib.sha256(message.strip().lower().encode()).hexdigest()

def get_cached_response(message: str) -> str | None:
    key = cache_key(message)
    if key in _response_cache:
        response, ts = _response_cache[key]
        if time.time() - ts < CACHE_TTL_SECONDS:
            return response
        del _response_cache[key]
    return None

def set_cached_response(message: str, response: str) -> None:
    _response_cache[cache_key(message)] = (response, time.time())

# ============================================================================
# Model Routing
# ============================================================================

def select_model(message: str) -> tuple[str, str]:
    if len(message) < 200 and "?" in message:
        return FALLBACK_MODEL, "short_simple_query"
    return MODEL, "default_complex"

# ============================================================================
# Rate Limiting
# ============================================================================

_request_log: dict[str, list[float]] = defaultdict(list)

def check_rate_limit(request: Request) -> None:
    client_ip = request.client.host if request.client else "unknown"
    now = time.time()
    _request_log[client_ip] = [t for t in _request_log[client_ip] if t > now - 60]
    if len(_request_log[client_ip]) >= RATE_LIMIT_RPM:
        raise HTTPException(status_code=429, detail="Rate limit exceeded.")
    _request_log[client_ip].append(now)

# ============================================================================
# Circuit Breaker
# ============================================================================

class CircuitBreaker:
    def __init__(self, failure_threshold=3, cooldown_seconds=60):
        self.failure_threshold = failure_threshold
        self.cooldown_seconds = cooldown_seconds
        self.failures = 0
        self.state = "closed"
        self.opened_at = 0.0

    def record_failure(self):
        self.failures += 1
        if self.failures >= self.failure_threshold:
            self.state = "open"
            self.opened_at = time.monotonic()

    def record_success(self):
        self.failures = 0
        self.state = "closed"

    def allow_request(self) -> bool:
        if self.state == "closed":
            return True
        if self.state == "open" and time.monotonic() - self.opened_at > self.cooldown_seconds:
            self.state = "half-open"
            return True
        return self.state == "half-open"

circuit = CircuitBreaker()

# ============================================================================
# Retry with Backoff
# ============================================================================

def call_with_retry(fn, request_id: str, max_retries=3):
    for attempt in range(max_retries):
        try:
            result = fn()
            circuit.record_success()
            return result
        except anthropic.RateLimitError:
            if attempt == max_retries - 1:
                circuit.record_failure()
                raise
            wait = (2 ** attempt) + random.uniform(0, 1)
            time.sleep(wait)
        except anthropic.APIStatusError as e:
            if e.status_code in (500, 502, 503) and attempt < max_retries - 1:
                time.sleep((2 ** attempt) + random.uniform(0, 1))
            else:
                circuit.record_failure()
                raise

# ============================================================================
# Budget
# ============================================================================

_alert_fired_today = None

def check_budget(request_id: str) -> str:
    global _alert_fired_today
    today_cost = get_today_cost()
    if today_cost >= DAILY_BUDGET_USD:
        raise HTTPException(status_code=429, detail="Daily budget exceeded.")
    if today_cost >= DAILY_BUDGET_USD * BUDGET_ALERT_THRESHOLD:
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        if _alert_fired_today != today:
            _alert_fired_today = today
            logger.warning(json.dumps({"event": "budget_alert", "cost_today": round(today_cost, 4)}))
        return "alert"
    return "allowed"

# ============================================================================
# FastAPI App
# ============================================================================

app = FastAPI(title="Atlas Service")
client = anthropic.Anthropic()

class ChatRequest(BaseModel):
    message: str
    session_id: str | None = None

class ChatResponse(BaseModel):
    reply: str
    request_id: str


@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest, request: Request):
    request_id = str(uuid.uuid4())
    start = time.perf_counter()

    check_rate_limit(request)

    if len(req.message) > MAX_MESSAGE_LENGTH:
        raise HTTPException(status_code=400, detail="Message too long.")
    if check_injection(req.message):
        raise HTTPException(status_code=400, detail="Request rejected by safety filter.")

    safe_message = redact_pii(req.message)
    input_policy = "pii_redacted" if safe_message != req.message else "pass"

    check_budget(request_id)

    cached = get_cached_response(safe_message)
    if cached is not None:
        return ChatResponse(reply=cached, request_id=request_id)

    selected_model, routing_reason = select_model(safe_message)

    if not circuit.allow_request():
        return ChatResponse(
            reply="Atlas is temporarily unavailable. Please try again shortly.",
            request_id=request_id,
        )

    def make_call():
        return client.messages.create(
            model=selected_model, max_tokens=1024,
            system=[{"type": "text", "text": SYSTEM_PROMPT, "cache_control": {"type": "ephemeral"}}],
            messages=[{"role": "user", "content": safe_message}],
        )

    try:
        message = call_with_retry(make_call, request_id)
    except Exception:
        return ChatResponse(
            reply="Atlas is temporarily unavailable. Please try again shortly.",
            request_id=request_id,
        )

    latency_ms = (time.perf_counter() - start) * 1000
    raw_reply = "".join(b.text for b in message.content if b.type == "text")
    filtered_reply, output_policy = guardrail_check(raw_reply)

    cost = estimate_cost(selected_model, message.usage)
    persist_cost(request_id, selected_model, message.usage.input_tokens,
                 message.usage.output_tokens, cost)

    if routing_reason == "short_simple_query":
        set_cached_response(safe_message, filtered_reply)

    logger.info(json.dumps({
        "event": "llm_call", "request_id": request_id,
        "model": selected_model, "routing_reason": routing_reason,
        "latency_ms": round(latency_ms, 1),
        "input_tokens": message.usage.input_tokens,
        "output_tokens": message.usage.output_tokens,
        "estimated_cost_usd": round(cost, 6),
        "policy_input": input_policy, "policy_output": output_policy,
        "circuit_state": circuit.state,
    }))

    return ChatResponse(reply=filtered_reply, request_id=request_id)


@app.get("/health")
def health():
    return {
        "status": "ok",
        "model": MODEL,
        "cost_today_usd": round(get_today_cost(), 4),
        "budget_limit_usd": DAILY_BUDGET_USD,
        "circuit_state": circuit.state,
    }


@app.get("/cost-today")
def cost_today():
    return {"cost_usd": round(get_today_cost(), 4), "budget_usd": DAILY_BUDGET_USD}
