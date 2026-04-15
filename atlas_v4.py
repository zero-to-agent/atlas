"""atlas_v4.py — Structured output with validated classification and extraction."""

import json
import sys
import logging
from enum import Enum
from typing import Optional

import anthropic
from pydantic import BaseModel, Field, ValidationError

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

client = anthropic.Anthropic()
MODEL = "claude-sonnet-4-6"
MAX_RETRIES = 3


# --- Pydantic models ---

class Category(str, Enum):
    BugReport = "BugReport"
    FeatureRequest = "FeatureRequest"
    BillingQuestion = "BillingQuestion"
    AccountIssue = "AccountIssue"
    GeneralInquiry = "GeneralInquiry"


class Priority(str, Enum):
    Low = "Low"
    Medium = "Medium"
    High = "High"


class SupportTicketDecision(BaseModel):
    category: Category = Field(description="The type of support request")
    priority: Priority = Field(description="Urgency level")
    summary: str = Field(
        min_length=1,
        description="Brief one-sentence summary of the request"
    )


# --- Helpers ---

def extract_json(text: str) -> dict:
    """Extract JSON from model output, handling markdown fences."""
    cleaned = text.strip()
    if cleaned.startswith("```"):
        lines = cleaned.split("\n")
        lines = [l for l in lines if not l.strip().startswith("```")]
        cleaned = "\n".join(lines).strip()
    return json.loads(cleaned)


CLASSIFIER_SYSTEM_PROMPT = """You are a support ticket classifier.
Respond with ONLY a JSON object matching this exact schema:
{
  "category": one of "BugReport", "FeatureRequest", "BillingQuestion", "AccountIssue", "GeneralInquiry",
  "priority": one of "Low", "Medium", "High",
  "summary": a brief one-sentence summary of the request
}
You MUST set all three fields. Do not include any text outside the JSON object."""


def classify_with_retry(user_input: str) -> SupportTicketDecision:
    """Classify a support request with bounded retry on validation failure."""
    messages = [{"role": "user", "content": user_input}]

    for attempt in range(MAX_RETRIES):
        message = client.messages.create(
            model=MODEL,
            max_tokens=256,
            system=CLASSIFIER_SYSTEM_PROMPT,
            messages=messages,
        )
        raw_text = message.content[0].text
        logger.info(f"Attempt {attempt + 1}: {raw_text[:120]}")

        # Step 1: Parse JSON
        try:
            data = extract_json(raw_text)
        except json.JSONDecodeError as e:
            error_msg = f"Invalid JSON: {e}"
            logger.warning(error_msg)
            messages = [
                {"role": "user", "content": user_input},
                {"role": "assistant", "content": raw_text},
                {"role": "user", "content": f"Your response was not valid JSON. Error: {error_msg}\nPlease respond with ONLY a valid JSON object."},
            ]
            continue

        # Step 2: Validate with Pydantic
        try:
            return SupportTicketDecision.model_validate(data)
        except ValidationError as e:
            error_msg = str(e)
            logger.warning(f"Validation failed: {error_msg}")
            messages = [
                {"role": "user", "content": user_input},
                {"role": "assistant", "content": raw_text},
                {"role": "user", "content": f"Your JSON did not pass validation:\n{error_msg}\nPlease fix the errors and respond with ONLY a valid JSON object."},
            ]
            continue

    raise RuntimeError(f"Classification failed after {MAX_RETRIES} attempts")


# --- Routing stubs ---

def handle_bug_report(decision: SupportTicketDecision):
    print(f"Escalating bug report: {decision.summary}")

def handle_feature_request(decision: SupportTicketDecision):
    print(f"Logging feature request: {decision.summary}")

def handle_billing(decision: SupportTicketDecision):
    print(f"Routing to billing: {decision.summary}")

def handle_account(decision: SupportTicketDecision):
    print(f"Routing to account team: {decision.summary}")

def handle_general(decision: SupportTicketDecision):
    print(f"General inquiry: {decision.summary}")


HANDLERS = {
    Category.BugReport: handle_bug_report,
    Category.FeatureRequest: handle_feature_request,
    Category.BillingQuestion: handle_billing,
    Category.AccountIssue: handle_account,
    Category.GeneralInquiry: handle_general,
}


def route_request(user_input: str):
    """Classify and route a support request."""
    decision = classify_with_retry(user_input)
    print(f"\nDecision: category={decision.category.value}, "
          f"priority={decision.priority.value}")
    print(f"Summary: {decision.summary}\n")
    handler = HANDLERS[decision.category]
    handler(decision)
    return decision


if __name__ == "__main__":
    test_input = "my thing broke and I need help asap"
    if len(sys.argv) > 1:
        test_input = " ".join(sys.argv[1:])
    route_request(test_input)
