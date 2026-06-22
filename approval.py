"""
approval.py
-----------
The human-approval gate. Any tool marked as "destructive" gets routed through
ask_human_approval() before it is allowed to execute.

This default implementation asks via the terminal (input()), which is fine
for the CLI demo. To use the agent in a non-interactive context (tests,
web backend, etc.) pass a different `approval_fn` into Agent(...) /
ToolExecutor(...) with the same signature: (tool_name: str, tool_input: dict) -> bool
"""


def ask_human_approval(tool_name: str, tool_input: dict) -> bool:
    print("\n" + "=" * 60)
    print("APPROVAL REQUIRED - destructive action requested")
    print("=" * 60)
    print(f"Tool : {tool_name}")
    print(f"Input: {tool_input}")
    print("-" * 60)
    while True:
        choice = input("Approve this action? [y/N]: ").strip().lower()
        if choice in ("y", "yes"):
            print(">> Approved.\n")
            return True
        if choice in ("", "n", "no"):
            print(">> Rejected.\n")
            return False
        print("Please enter 'y' or 'n'.")


def auto_approve(tool_name: str, tool_input: dict) -> bool:
    """Convenience approval function that always says yes. Useful for
    scripted/non-interactive testing only - do NOT use this in production."""
    print(f"[auto_approve] Approving '{tool_name}' with input {tool_input} (no human asked).")
    return True


def auto_reject(tool_name: str, tool_input: dict) -> bool:
    """Convenience approval function that always says no. Useful for testing
    the rejection path without typing anything."""
    print(f"[auto_reject] Rejecting '{tool_name}' with input {tool_input} (no human asked).")
    return False
