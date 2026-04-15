import sys
import time
import anthropic
from anthropic import APIError, APIStatusError

client = anthropic.Anthropic()

system_prompt = """You are Atlas, a senior software engineer and code-review assistant.
You give concise, actionable feedback on code. You remember prior context
in this conversation and refer back to earlier decisions when relevant."""

model = "claude-sonnet-4-6"
messages: list[dict] = []
cumulative_cost = 0.0


def validate_messages(msgs: list[dict]) -> bool:
    """Validate that messages alternate roles and start with 'user'.
    Malformed ordering is a common cause of broken conversational memory
    and should fail fast rather than produce a confusing API error."""
    if not msgs:
        return True
    if msgs[0]["role"] != "user":
        print("  [Error: first message must have role 'user']", file=sys.stderr)
        return False
    for i in range(1, len(msgs)):
        if msgs[i]["role"] == msgs[i - 1]["role"]:
            print(f"  [Error: consecutive '{msgs[i]['role']}' messages at index {i-1},{i}]",
                  file=sys.stderr)
            return False
    return True


def estimate_cost(usage, input_price_per_m=3.00, output_price_per_m=15.00):
    """Estimate USD cost from a response usage object."""
    input_cost = (usage.input_tokens / 1_000_000) * input_price_per_m
    output_cost = (usage.output_tokens / 1_000_000) * output_price_per_m
    return input_cost + output_cost


def estimate_cost_with_cache(usage, input_price=3.00, cache_read_price=0.30,
                              cache_write_price=3.75, output_price=15.00):
    """Estimate USD cost from a response usage object with caching.
    Default prices are illustrative — check https://www.anthropic.com/pricing
    for current rates."""
    fresh = usage.input_tokens - getattr(usage, 'cache_read_input_tokens', 0)
    cached = getattr(usage, 'cache_read_input_tokens', 0)
    cache_write = getattr(usage, 'cache_creation_input_tokens', 0)
    input_cost = (fresh / 1_000_000) * input_price
    cache_read_cost = (cached / 1_000_000) * cache_read_price
    cache_write_cost = (cache_write / 1_000_000) * cache_write_price
    output_cost = (usage.output_tokens / 1_000_000) * output_price
    return input_cost + cache_read_cost + cache_write_cost + output_cost


def chat(user_input: str) -> str:
    """Send a message and return the assistant's reply."""
    global cumulative_cost
    messages.append({"role": "user", "content": user_input})

    if not validate_messages(messages):
        messages.pop()
        raise ValueError("Message history has invalid role ordering. Fix before sending.")

    # Retry with backoff for transient errors
    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = client.messages.create(
                model=model,
                max_tokens=2048,
                system=[
                    {
                        "type": "text",
                        "text": system_prompt,
                        "cache_control": {"type": "ephemeral"},
                    }
                ],
                messages=messages,
            )
            break
        except APIStatusError as e:
            if e.status_code in (429, 529) and attempt < max_retries - 1:
                wait = 2 ** attempt
                print(f"  [Retrying in {wait}s...]", file=sys.stderr)
                time.sleep(wait)
            else:
                # Remove the user message we just appended so history stays clean
                messages.pop()
                raise

    assistant_text = response.content[0].text
    messages.append({"role": "assistant", "content": assistant_text})

    # Print usage for cost awareness
    u = response.usage
    cached_in = getattr(u, 'cache_read_input_tokens', 0)
    cache_write = getattr(u, 'cache_creation_input_tokens', 0)
    turn_cost = estimate_cost_with_cache(u)
    cumulative_cost += turn_cost
    print(f"  [tokens: in={u.input_tokens}, out={u.output_tokens}, "
          f"cache_read={cached_in}, cache_write={cache_write}]", file=sys.stderr)
    print(f"  [cost: ${turn_cost:.6f} | total: ${cumulative_cost:.6f}]", file=sys.stderr)

    return assistant_text


def main():
    print("Atlas v3 — type :quit to exit\n")
    while True:
        try:
            user_input = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye.")
            break

        if not user_input:
            continue
        if user_input.lower() == ":quit":
            print("Goodbye.")
            break

        try:
            reply = chat(user_input)
            print(f"\nAtlas: {reply}\n")
        except APIError as e:
            print(f"  API error: {e}", file=sys.stderr)


if __name__ == "__main__":
    main()
