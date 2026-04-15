import sys
import time
import argparse
import anthropic
from anthropic import AuthenticationError, RateLimitError, APIStatusError


def parse_args():
    parser = argparse.ArgumentParser(description="Atlas v1 — first Claude API call")
    parser.add_argument("prompt", nargs="?", default="Say hello and introduce yourself in two sentences.")
    parser.add_argument("--model", default="claude-sonnet-4-6",
                        help="Model to use (e.g. claude-haiku-4-5-20251001, claude-sonnet-4-6, claude-opus-4-6)")
    parser.add_argument("--max-tokens", type=int, default=1024)
    parser.add_argument("--daily-budget", type=float, default=5.00,
                        help="Daily budget in USD for cost warnings")
    parser.add_argument("--daily-runs", type=int, default=500,
                        help="Expected daily run count for budget projection")
    return parser.parse_args()


def format_usage(usage):
    return (
        f"  Input tokens:  {usage.input_tokens}\n"
        f"  Output tokens: {usage.output_tokens}"
    )


def estimate_cost(usage, model="claude-sonnet-4-6"):
    """Estimate USD cost from a usage object.
    WARNING: Prices below are hardcoded and may be outdated.
    Always verify current rates at https://www.anthropic.com/pricing"""
    pricing = {
        "claude-haiku-4-5-20251001":  {"input": 1.00 / 1_000_000, "output": 5.00 / 1_000_000},
        "claude-sonnet-4-6":   {"input": 3.00 / 1_000_000, "output": 15.00 / 1_000_000},
        "claude-opus-4-6":     {"input": 5.00 / 1_000_000, "output": 25.00 / 1_000_000},
    }
    rates = pricing.get(model, pricing["claude-sonnet-4-6"])
    input_cost = usage.input_tokens * rates["input"]
    output_cost = usage.output_tokens * rates["output"]
    return input_cost + output_cost


def check_daily_budget(cost_per_call, daily_runs, budget_usd):
    """Raise if projected daily cost exceeds budget."""
    projected = cost_per_call * daily_runs
    if projected > budget_usd:
        raise RuntimeError(
            f"Projected daily cost ${projected:.2f} exceeds budget ${budget_usd:.2f} "
            f"({daily_runs} runs × ${cost_per_call:.4f}/call)"
        )
    return projected


def stream_response(client, model, max_tokens, prompt):
    """Send a streaming request and print chunks as they arrive."""
    with client.messages.stream(
        model=model,
        max_tokens=max_tokens,
        messages=[{"role": "user", "content": prompt}],
    ) as stream:
        for text in stream.text_stream:
            print(text, end="", flush=True)

    response = stream.get_final_message()
    print()  # newline after streamed text
    return response


def call_with_retry(client, model, max_tokens, prompt, max_retries=3):
    """Stream a response with bounded exponential backoff on transient errors."""
    for attempt in range(max_retries):
        try:
            return stream_response(client, model, max_tokens, prompt)
        except RateLimitError as e:
            if attempt == max_retries - 1:
                raise
            wait = 2 ** attempt
            print(f"\nRate limited. Retrying in {wait}s (attempt {attempt + 1}/{max_retries})...",
                  file=sys.stderr)
            time.sleep(wait)
        except APIStatusError as e:
            if e.status_code == 529 and attempt < max_retries - 1:
                wait = 2 ** attempt
                print(f"\nAPI overloaded. Retrying in {wait}s...", file=sys.stderr)
                time.sleep(wait)
            else:
                raise


def main():
    args = parse_args()
    client = anthropic.Anthropic()

    print(f"Model: {args.model}")
    print(f"Prompt: {args.prompt}\n")

    try:
        message = call_with_retry(client, args.model, args.max_tokens, args.prompt)
    except AuthenticationError:
        print("ERROR: Authentication failed.", file=sys.stderr)
        print("Check that ANTHROPIC_API_KEY is set and valid.", file=sys.stderr)
        print("  export ANTHROPIC_API_KEY='sk-ant-...'", file=sys.stderr)
        sys.exit(1)
    except RateLimitError:
        print("ERROR: Rate limit exceeded after retries. Try again later.", file=sys.stderr)
        sys.exit(1)
    except APIStatusError as e:
        if e.status_code in (400, 413):
            print(f"ERROR: Request too large (HTTP {e.status_code}).", file=sys.stderr)
            print("Reduce your input text, lower --max-tokens, or use a model with a larger context window.",
                  file=sys.stderr)
            sys.exit(1)
        raise

    # Usage and cost reporting
    print(f"\n--- Usage ---")
    print(format_usage(message.usage))
    print(f"Stop reason: {message.stop_reason}")

    cost = estimate_cost(message.usage, args.model)
    print(f"  Estimated cost: ${cost:.6f}")

    try:
        projected = check_daily_budget(cost, args.daily_runs, args.daily_budget)
        print(f"  Projected daily cost ({args.daily_runs} runs): ${projected:.2f}")
    except RuntimeError as e:
        print(f"  BUDGET WARNING: {e}", file=sys.stderr)


if __name__ == "__main__":
    main()
