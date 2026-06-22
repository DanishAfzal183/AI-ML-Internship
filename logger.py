"""
logger.py
---------
Logs every tool call (input, output, status, approval decision) and other
agent events to a JSON-lines file so the full action history can be audited.
"""

import json
import os
from datetime import datetime, timezone

LOG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
LOG_FILE = os.path.join(LOG_DIR, "actions.log")


class ActionLogger:
    def __init__(self, log_file: str = LOG_FILE):
        self.log_file = log_file
        os.makedirs(os.path.dirname(self.log_file), exist_ok=True)

    def log(self, event: dict) -> dict:
        event = dict(event)
        event["timestamp"] = datetime.now(timezone.utc).isoformat()
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(event, default=str) + "\n")
        return event

    def log_tool_call(self, tool_name, tool_input, status, output=None, error=None, approved=None) -> dict:
        """status is one of: 'success', 'tool_error', 'error', 'rejected'."""
        return self.log({
            "type": "tool_call",
            "tool": tool_name,
            "input": tool_input,
            "status": status,
            "output": output,
            "error": error,
            "approved": approved,
        })

    def log_event(self, event_type: str, **kwargs) -> dict:
        return self.log({"type": event_type, **kwargs})

    def tail(self, n: int = 10):
        """Return the last n logged events, newest last."""
        if not os.path.exists(self.log_file):
            return []
        with open(self.log_file, "r", encoding="utf-8") as f:
            lines = f.readlines()
        out = []
        for line in lines[-n:]:
            line = line.strip()
            if line:
                out.append(json.loads(line))
        return out
