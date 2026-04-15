"""atlas_v2.py — Atlas with persona, templates, and reasoning comparison.

Requires: ANTHROPIC_API_KEY environment variable.
Usage: python atlas_v2.py
"""

import sys
import time
import anthropic

# --- Versioned system prompt ---
ATLAS_SYSTEM_PROMPT_V2 = """You are Atlas, an AI development assistant created \
to help software developers write, debug, and review code.

<instructions>
- Be concise and practical. Prefer code examples over lengthy explanations.
- When asked to review code, use the Bugs/Style/Suggestion format.
- If you are uncertain about a specific API, library version, or behavior, \
say so rather than guessing.
- Focus on Python and general software engineering unless the user specifies \
another language.
- When the user provides code without a specific question, default to a code review.
</instructions>

<constraints>
- Do not fabricate library names, function signatures, or API endpoints.
- Do not provide medical, legal, or financial advice.
- Keep responses under 300 words unless the user asks for more detail.
</constraints>"""

# --- Few-shot example blocks ---
FEW_SHOT_BLOCKS = {
    "code_review": """
<examples>
<example>
<input>
def add(a, b):
    return a + b
</input>
<output>
**Bugs:** None found.
**Style:** Function lacks a docstring and type hints.
**Suggestion:** Add type hints: `def add(a: int, b: int) -> int:`
</output>
</example>
</examples>
""",
    "summarization": """
<examples>
<example>
<input>The Python GIL prevents true parallel execution of threads in CPython.</input>
<output>The GIL serializes thread execution in CPython, limiting CPU-bound parallelism. Use multiprocessing or async I/O for concurrency.</output>
</example>
</examples>
""",
    "qa": """
<examples>
<example>
<input>What is a context manager in Python?</input>
<output>A context manager defines `__enter__` and `__exit__` methods, used with `with` to manage resources like file handles.</output>
</example>
</examples>
""",
}

MODEL = "claude-sonnet-4-6"
client = anthropic.Anthropic()


def build_prompt(task_type: str, context: str) -> list[dict]:
    """Build a messages list with task-specific few-shot examples."""
    examples = FEW_SHOT_BLOCKS.get(task_type, "")
    user_content = f"{examples}\n<task>\n{context}\n</task>" if examples else context
    return [{"role": "user", "content": user_content}]


def ask_atlas(user_input: str, task_type: str = "qa") -> str:
    """Send a request to Atlas and return the response text."""
    messages = build_prompt(task_type, user_input)
    message = client.messages.create(
        model=MODEL,
        max_tokens=1024,
        system=ATLAS_SYSTEM_PROMPT_V2,
        messages=messages,
    )
    return message.content[0].text


def reasoning_comparison(task: str) -> None:
    """Run one task in three reasoning modes and print results."""
    print(f"\nTask: {task}\n{'=' * 60}")

    # Mode 1: Plain
    start = time.time()
    msg = client.messages.create(
        model=MODEL, max_tokens=512,
        system=ATLAS_SYSTEM_PROMPT_V2,
        messages=[{"role": "user", "content": task}],
    )
    plain_time = time.time() - start
    plain_answer = msg.content[0].text.strip()
    print(f"Plain    | {plain_time:.1f}s | {msg.usage.output_tokens} out tokens")
    print(f"  Answer: {plain_answer[:200]}")

    # Mode 2: Explicit CoT
    start = time.time()
    msg = client.messages.create(
        model=MODEL, max_tokens=2048,
        system=ATLAS_SYSTEM_PROMPT_V2,
        messages=[{"role": "user", "content": task + "\nThink step by step."}],
    )
    cot_time = time.time() - start
    cot_answer = msg.content[0].text.strip()
    print(f"CoT      | {cot_time:.1f}s | {msg.usage.output_tokens} out tokens")
    print(f"  Answer: {cot_answer[:200]}")

    # Mode 3: Extended thinking
    start = time.time()
    msg = client.messages.create(
        model=MODEL, max_tokens=4096,
        thinking={"type": "enabled", "budget_tokens": 2000},
        messages=[{"role": "user", "content": task}],
    )
    think_time = time.time() - start
    think_answer = next(b.text for b in msg.content if b.type == "text").strip()
    print(f"Thinking | {think_time:.1f}s | {msg.usage.output_tokens} out tokens")
    print(f"  Answer: {think_answer[:200]}")


def main():
    # --- Persona consistency: 5-run stability test ---
    test_query = "What's the difference between a list and a tuple in Python?"
    print("--- Atlas v2: Persona consistency test (5 runs) ---")
    print(f"Query: {test_query}\n")
    for i in range(5):
        response = ask_atlas(test_query)
        print(f"Run {i + 1} ({len(response)} chars): {response[:150]}...")
        print()

    print("Check: Do all 5 runs use a concise, code-oriented style?")
    print("Check: Does Atlas stay within the Python/software engineering scope?")
    print("Compare this against 5 runs with no system prompt (Exercise 1).\n")

    # --- Task-specific templates ---
    print("--- Task-specific template: code_review ---")
    code = "def greet(name):\n    print('hello' + name)"
    print(ask_atlas(code, task_type="code_review"))

    # --- Reasoning comparison ---
    reasoning_comparison(
        "A farmer has 17 sheep. All but 9 die. How many are left? Give only the number."
    )


if __name__ == "__main__":
    main()
