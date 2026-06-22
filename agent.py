"""
agent.py
--------
The Gemini-powered tool-calling agent. It:
  1. Sends the user's message to Gemini, with the 3 mock tools declared
     as available functions.
  2. If Gemini responds with a function call, runs it through ToolExecutor
     (which handles the approval gate, logging, and error handling).
  3. Sends the tool's result back to Gemini so it can either call another
     tool or produce a final natural-language answer.
  4. Repeats until Gemini stops calling tools (or a safety hop-limit hits).
"""

import json

import google.generativeai as genai

import config
from executor import ToolExecutor
from logger import ActionLogger


FUNCTION_DECLARATIONS = [
    {
        "name": "get_weather",
        "description": "Get mock current weather for a city. Safe, read-only tool.",
        "parameters": {
            "type": "object",
            "properties": {
                "city": {"type": "string", "description": "City name, e.g. 'London'"},
            },
            "required": ["city"],
        },
    },
    {
        "name": "search_knowledge_base",
        "description": "Search a mock internal knowledge base for help articles. Safe, read-only tool.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search keywords, e.g. 'password reset'"},
            },
            "required": ["query"],
        },
    },
    {
        "name": "delete_user_account",
        "description": (
            "Permanently delete a user account by ID. This is a DESTRUCTIVE, "
            "irreversible action. The system will always pause and ask a human "
            "to approve it before it actually runs."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "user_id": {"type": "string", "description": "The ID of the account to delete"},
            },
            "required": ["user_id"],
        },
    },
]

SYSTEM_INSTRUCTION = (
    "You are a helpful assistant with access to tools. Use a tool whenever it "
    "would help answer the user's request - don't guess at facts a tool could "
    "give you (weather, knowledge-base search results, etc.).\n\n"
    "The delete_user_account tool is destructive and irreversible. A human "
    "approval gate sits in front of it on the system side, so you do not need "
    "to ask the user 'are you sure?' yourself - just call the tool when the "
    "user has clearly asked to delete a specific account. If the tool result "
    "says the action was rejected by the human approver, or that an error "
    "occurred, explain that plainly to the user instead of claiming success."
)


class Agent:
    def __init__(self, logger: ActionLogger = None, approval_fn=None):
        config.require_api_key()
        genai.configure(api_key=config.GEMINI_API_KEY)

        self.logger = logger or ActionLogger()
        self.executor = ToolExecutor(self.logger, approval_fn=approval_fn)

        self.model = genai.GenerativeModel(
            model_name=config.GEMINI_MODEL,
            tools=[{"function_declarations": FUNCTION_DECLARATIONS}],
            system_instruction=SYSTEM_INSTRUCTION,
        )
        self.chat = self.model.start_chat()

    def execute_tool(self, name: str, args: dict) -> dict:
        """Exposed for the manual/offline demo mode too."""
        return self.executor.execute(name, args)

    def run(self, user_message: str, max_tool_hops: int = 5) -> str:
        """Send one user message through the agent loop and return the
        final natural-language reply."""
        self.logger.log_event("user_message", message=user_message)

        try:
            response = self.chat.send_message(user_message)
        except Exception as e:
            err = f"Gemini API request failed: {e}"
            self.logger.log_event("api_error", error=err)
            return f"[Error contacting Gemini API] {err}"

        hops = 0
        while hops < max_tool_hops:
            function_call = self._extract_function_call(response)
            if function_call is None:
                break
            hops += 1

            name = function_call.name
            try:
                args = dict(function_call.args) if function_call.args else {}
            except Exception:
                args = {}

            self.logger.log_event("model_requested_tool", tool=name, input=args)
            result = self.executor.execute(name, args)

            try:
                response = self.chat.send_message(
                    genai.protos.Content(
                        parts=[
                            genai.protos.Part(
                                function_response=genai.protos.FunctionResponse(
                                    name=name,
                                    response=self._jsonable(result),
                                )
                            )
                        ]
                    )
                )
            except Exception as e:
                err = f"Gemini API request failed while returning tool result: {e}"
                self.logger.log_event("api_error", error=err)
                return f"[Error contacting Gemini API] {err}"

        try:
            return response.text
        except Exception:
            return "[Agent finished but produced no readable text response]"

    @staticmethod
    def _extract_function_call(response):
        try:
            candidate = response.candidates[0]
        except (IndexError, AttributeError, TypeError):
            return None
        parts = getattr(candidate.content, "parts", []) or []
        for part in parts:
            fc = getattr(part, "function_call", None)
            if fc and getattr(fc, "name", None):
                return fc
        return None

    @staticmethod
    def _jsonable(obj):
        """Make sure the dict we hand back to Gemini is plain JSON-safe data."""
        return json.loads(json.dumps(obj, default=str))
