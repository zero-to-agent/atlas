"""atlas_v6.py — Autonomous agent with planning, guardrails, and approval gates.

Builds on atlas_v5.py's tool infrastructure to add a while-loop agent
that takes a goal, plans, executes tools, and stops on completion or safety limits.

Requires: ANTHROPIC_API_KEY environment variable.
Optional: TAVILY_API_KEY for web search tool.
Usage: python atlas_v6.py "Research the top 3 Python HTTP libraries and write a comparison to comparison.md"
"""

import os
import sys
import time
import anthropic

# Import tool infrastructure from atlas_v5
from atlas_v5 import (
    get_tools_payload,
    execute_and_log,
    WORKSPACE_ROOT,
)

client = anthropic.Anthropic()

SYSTEM_PROMPT = """You are Atlas, a research assistant. You receive a goal and \
work toward it step by step. Use your tools to gather information and produce \
output. When the task is fully complete, say TASK_COMPLETE in your final message."""

PLANNING_PROMPT = """Before taking any action, create a numbered plan for completing \
this task. List each step on its own line. Then begin executing the plan."""

ALLOWED_TOOLS = {"web_search", "read_file", "write_file", "run_python"}
TOOLS_REQUIRING_APPROVAL = {"write_file", "run_python"}


def _estimate_cost(usage, model: str = "claude-sonnet-4-6") -> float:
    """Estimate USD cost from usage metadata."""
    pricing = {
        "claude-haiku-4-5-20251001": {"input": 1.0 / 1_000_000, "output": 5.0 / 1_000_000},
        "claude-sonnet-4-6": {"input": 3.0 / 1_000_000, "output": 15.0 / 1_000_000},
        "claude-opus-4-6": {"input": 5.0 / 1_000_000, "output": 25.0 / 1_000_000},
    }
    rates = pricing.get(model, pricing["claude-sonnet-4-6"])
    return usage.input_tokens * rates["input"] + usage.output_tokens * rates["output"]


def _extract_text(message) -> str:
    """Extract all text content from a model response."""
    return "".join(block.text for block in message.content if hasattr(block, "text"))


def _check_completion(final_text: str, required_files: list[str] = None) -> bool:
    """Check if the task is complete: TASK_COMPLETE signal and required files exist."""
    if "TASK_COMPLETE" not in final_text:
        return False
    if required_files:
        for path in required_files:
            full_path = WORKSPACE_ROOT / path
            if not full_path.exists():
                print(f"  Completion check: {path} not found yet")
                return False
    return True


def _extract_plan(message):
    """Parse numbered plan steps from the model's first response."""
    plan_steps = []
    step_status = {}
    for block in message.content:
        if hasattr(block, "text"):
            for line in block.text.split("\n"):
                stripped = line.strip()
                if stripped and len(stripped) > 2 and stripped[0].isdigit() and stripped[1] in ".):":
                    plan_steps.append(stripped)
    for i, step in enumerate(plan_steps):
        step_status[i] = "pending"
        print(f"  Plan step {i + 1}: {step}")
    return plan_steps, step_status


def _approval_gate(tool_name: str, tool_input: dict, require_approval: bool) -> bool:
    """Prompt for human approval before executing sensitive tools."""
    if not require_approval:
        return True
    if tool_name not in TOOLS_REQUIRING_APPROVAL:
        return True
    print(f"\n  APPROVAL REQUIRED")
    print(f"  Tool: {tool_name}")
    print(f"  Input: {tool_input}")
    response = input("  Approve? (y/n): ").strip().lower()
    return response == "y"


def run(goal: str,
        max_iterations: int = 15,
        max_runtime_seconds: int = 120,
        max_cost_usd: float = 0.50,
        require_approval: bool = False,
        required_files: list[str] = None,
        model: str = "claude-sonnet-4-6") -> str:
    """Execute the agent loop until completion or a stop condition is hit."""
    planning_goal = f"{goal}\n\n{PLANNING_PROMPT}"
    messages = [{"role": "user", "content": planning_goal}]
    tools = get_tools_payload()
    plan_steps = []
    step_status = {}
    iteration = 0
    cumulative_cost = 0.0
    start_time = time.monotonic()

    while iteration < max_iterations:
        iteration += 1
        elapsed = time.monotonic() - start_time
        print(f"\n--- Iteration {iteration}/{max_iterations} ---")

        # Stop condition: timeout
        if elapsed > max_runtime_seconds:
            return f"Stopped: timeout after {elapsed:.0f}s (limit: {max_runtime_seconds}s)."

        # Stop condition: budget (check before making the call)
        if cumulative_cost >= max_cost_usd:
            return f"Stopped: budget exceeded (${cumulative_cost:.4f} >= ${max_cost_usd})."

        message = client.messages.create(
            model=model, max_tokens=4096,
            system=SYSTEM_PROMPT, tools=tools, messages=messages,
        )

        cumulative_cost += _estimate_cost(message.usage, model)
        print(f"  Cost: ${cumulative_cost:.4f} | Elapsed: {elapsed:.1f}s")

        messages.append({"role": "assistant", "content": message.content})

        # Extract plan from first iteration
        if iteration == 1:
            plan_steps, step_status = _extract_plan(message)

        # Handle end_turn: check for completion
        if message.stop_reason == "end_turn":
            final_text = _extract_text(message)
            if _check_completion(final_text, required_files):
                print(f"\nTask completed in {iteration} iterations.")
                print(f"Final cost: ${cumulative_cost:.4f} | Time: {elapsed:.1f}s")
                return final_text
            # Not done yet — ask model to continue
            messages.append({"role": "user", "content": "Continue working on the task."})
            continue

        # Handle tool_use: execute tools and feed results back
        if message.stop_reason == "tool_use":
            # Print any intermediate text
            for block in message.content:
                if block.type == "text" and block.text.strip():
                    print(f"  Atlas: {block.text[:200]}")

            tool_results = []
            for block in message.content:
                if block.type != "tool_use":
                    continue

                # Guardrail: allowlist
                if block.name not in ALLOWED_TOOLS:
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": f"Error: tool '{block.name}' is not in the allowlist.",
                        "is_error": True,
                    })
                    continue

                # Guardrail: approval gate
                if not _approval_gate(block.name, block.input, require_approval):
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": "Error: action was not approved by the user.",
                        "is_error": True,
                    })
                    continue

                print(f"  Tool: {block.name}({list(block.input.keys())})")
                result = execute_and_log(block.name, block.input)
                is_error = result.startswith("Error:")
                entry = {"type": "tool_result", "tool_use_id": block.id, "content": result}
                if is_error:
                    entry["is_error"] = True
                tool_results.append(entry)

            messages.append({"role": "user", "content": tool_results})

    return f"Stopped: reached max iterations ({max_iterations})."


def main():
    print("Atlas v6 — Autonomous Agent\n")

    goal = "Research the top 3 Python HTTP libraries and write a comparison to comparison.md"
    if len(sys.argv) > 1:
        goal = " ".join(sys.argv[1:])

    print(f"Goal: {goal}\n")
    result = run(
        goal=goal,
        require_approval=False,
        required_files=["comparison.md"],
    )
    print(f"\n{'=' * 60}")
    print(result)


if __name__ == "__main__":
    main()
