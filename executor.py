"""
executor.py
-----------
ToolExecutor is the layer that actually runs a tool. It is used by the
Gemini-powered Agent, but it also works completely standalone (see
manual_mode.py), which makes it easy to demo / test the approval +
logging + error-handling behavior without needing an API key at all.

Responsibilities:
  1. Look the tool up by name (graceful error if unknown).
  2. If the tool is destructive, pause and call the approval function.
  3. Call the tool, catching and logging any error so the caller always
     gets back a structured result instead of an exception.
  4. Log every call: input, output (or error), status, approval decision.
"""

from tools import TOOL_REGISTRY, DESTRUCTIVE_TOOLS, ToolError
from approval import ask_human_approval


class ToolExecutor:
    def __init__(self, logger, approval_fn=None, tools=None, destructive_tools=None):
        self.logger = logger
        self.approval_fn = approval_fn or ask_human_approval
        self.tools = tools if tools is not None else TOOL_REGISTRY
        self.destructive_tools = destructive_tools if destructive_tools is not None else DESTRUCTIVE_TOOLS

    def execute(self, tool_name: str, tool_input: dict) -> dict:
        """
        Always returns a dict shaped like:
          {"ok": True,  "result": <tool return value>, "approved": True/None}
          {"ok": False, "error": <message>, "approved": True/False/None}
        Never raises.
        """
        tool_input = tool_input or {}

        if tool_name not in self.tools:
            error = f"Unknown tool '{tool_name}'. Available tools: {list(self.tools)}"
            self.logger.log_tool_call(tool_name, tool_input, status="error", error=error)
            return {"ok": False, "error": error, "approved": None}

        approved = None
        if tool_name in self.destructive_tools:
            approved = self.approval_fn(tool_name, tool_input)
            if not approved:
                self.logger.log_tool_call(
                    tool_name, tool_input, status="rejected", approved=False
                )
                return {
                    "ok": False,
                    "error": "Action rejected by human approver. Tool was not executed.",
                    "approved": False,
                }

        try:
            result = self.tools[tool_name](**tool_input)
        except ToolError as e:
            # Expected, "handled" failure raised deliberately by a tool.
            self.logger.log_tool_call(
                tool_name, tool_input, status="tool_error", error=str(e), approved=approved
            )
            return {"ok": False, "error": str(e), "approved": approved}
        except TypeError as e:
            # Usually means the caller (LLM or human) passed wrong/missing args.
            error = f"Invalid arguments for '{tool_name}': {e}"
            self.logger.log_tool_call(
                tool_name, tool_input, status="error", error=error, approved=approved
            )
            return {"ok": False, "error": error, "approved": approved}
        except Exception as e:
            # Anything else unexpected - still caught so the agent never crashes.
            error = f"Unexpected error while running '{tool_name}': {e}"
            self.logger.log_tool_call(
                tool_name, tool_input, status="error", error=error, approved=approved
            )
            return {"ok": False, "error": error, "approved": approved}

        self.logger.log_tool_call(
            tool_name, tool_input, status="success", output=result, approved=approved
        )
        return {"ok": True, "result": result, "approved": approved}
