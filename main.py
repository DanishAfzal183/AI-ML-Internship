"""
main.py
-------
Interactive CLI demo entrypoint.

Run:
    python main.py

If GEMINI_API_KEY is configured (see .env.example), this drives the full
Gemini-powered Agent: type plain-English requests and the model decides
which tool(s) to call. If no API key is found, it automatically falls back
to manual_mode.py so you can still see the approval-gate/logging/error
pipeline working.
"""

from logger import ActionLogger
import config

BANNER = """
==============================================
 Tool-Calling Agent Demo (Gemini-powered)
==============================================
Type a request in plain English. The agent may
call tools to help answer it. The destructive
tool (delete_user_account) will pause and ask
for your approval before running.

Try things like:
  - What's the weather in Lahore?
  - Search the knowledge base for password reset
  - Delete user account U123
  - Delete user account ERROR        (simulates a tool failure)

Commands:
  /logs     show the last 10 logged actions
  /quit     exit
==============================================
"""


def run_llm_demo():
    from agent import Agent

    logger = ActionLogger()
    agent = Agent(logger=logger)
    print(BANNER)

    while True:
        try:
            user_input = input("\nYou: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye.")
            break

        if not user_input:
            continue
        if user_input.lower() in ("/quit", "/exit"):
            print("Goodbye.")
            break
        if user_input.lower() == "/logs":
            entries = logger.tail(10)
            if not entries:
                print("(no log entries yet)")
            for entry in entries:
                print(entry)
            continue

        answer = agent.run(user_input)
        print(f"\nAgent: {answer}")


def main():
    try:
        config.require_api_key()
    except RuntimeError as e:
        print(f"[Config notice] {e}\n")
        print("Falling back to manual tool-picker mode so you can still try")
        print("the approval gate, logging, and error handling without an API key.")
        from manual_mode import run_manual_loop
        run_manual_loop()
        return

    run_llm_demo()


if __name__ == "__main__":
    main()
