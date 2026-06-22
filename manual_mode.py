"""
manual_mode.py
--------------
A no-API-key fallback / demo mode. Lets you pick a tool from a menu and type
its arguments directly, so you can see the approval-gate + logging +
error-handling pipeline working even before you've set up a Gemini API key.

Run directly with:  python manual_mode.py
"""

from executor import ToolExecutor
from logger import ActionLogger
from tools import TOOL_REGISTRY


def parse_kv_args(raw: str) -> dict:
    """Parse 'key=value, key2=value2' into a dict."""
    args = {}
    raw = raw.strip()
    if not raw:
        return args
    for pair in raw.split(","):
        pair = pair.strip()
        if not pair:
            continue
        if "=" not in pair:
            print(f"  (skipping '{pair}': expected key=value)")
            continue
        k, v = pair.split("=", 1)
        args[k.strip()] = v.strip()
    return args


def run_manual_loop(executor: ToolExecutor = None):
    executor = executor or ToolExecutor(ActionLogger())
    names = list(TOOL_REGISTRY.keys())

    print("\n=== Manual tool-picker mode (no LLM involved) ===")
    print("Use this to test the approval gate / logging / error handling directly.\n")

    while True:
        print("Available tools:")
        for i, n in enumerate(names, 1):
            tag = " (DESTRUCTIVE)" if n in executor.destructive_tools else ""
            print(f"  {i}. {n}{tag}")
        print("  0. quit")

        choice = input("\nPick a tool number: ").strip()
        if choice == "0":
            print("Goodbye.")
            break

        try:
            name = names[int(choice) - 1]
        except (ValueError, IndexError):
            print("Invalid choice, try again.\n")
            continue

        raw_args = input(
            f"Arguments for '{name}' as key=value pairs (comma-separated), or blank: "
        )
        args = parse_kv_args(raw_args)

        result = executor.execute(name, args)
        print("\nResult:")
        print(result)
        print()


if __name__ == "__main__":
    run_manual_loop()
