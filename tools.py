"""
tools.py
--------
Mock tool implementations the agent can call.

There are three tools:
  1. get_weather             -> safe, read-only
  2. search_knowledge_base   -> safe, read-only
  3. delete_user_account     -> DESTRUCTIVE (irreversible), requires human approval

Each tool raises ToolError for "expected" failure cases (bad input, simulated
downstream failure, etc.) so the agent can distinguish handled tool errors
from unexpected bugs.
"""

import time


class ToolError(Exception):
    """Raised for expected/handled failures inside a tool."""
    pass


def get_weather(city: str) -> dict:
    """Mock weather lookup. Safe, read-only tool."""
    if not city or not isinstance(city, str):
        raise ToolError("Parameter 'city' must be a non-empty string.")

    mock_db = {
        "new york": {"temp_c": 22, "condition": "Cloudy"},
        "london": {"temp_c": 17, "condition": "Rainy"},
        "lahore": {"temp_c": 38, "condition": "Sunny"},
        "tokyo": {"temp_c": 27, "condition": "Clear"},
        "karachi": {"temp_c": 34, "condition": "Humid"},
    }
    key = city.strip().lower()
    if key not in mock_db:
        return {
            "city": city,
            "found": False,
            "message": "No weather data for this city in the mock database.",
        }
    data = mock_db[key]
    return {"city": city, "found": True, **data}


def search_knowledge_base(query: str) -> dict:
    """Mock internal knowledge-base search. Safe, read-only tool."""
    if not query or not isinstance(query, str):
        raise ToolError("Parameter 'query' must be a non-empty string.")

    mock_articles = [
        {"id": 1, "title": "How to reset your password", "tags": ["password", "account", "login"]},
        {"id": 2, "title": "Billing cycle explained", "tags": ["billing", "payment", "invoice"]},
        {"id": 3, "title": "Setting up two-factor authentication", "tags": ["security", "2fa", "account"]},
        {"id": 4, "title": "Exporting your data", "tags": ["export", "data", "backup"]},
    ]
    q = query.strip().lower()
    matches = [
        a for a in mock_articles
        if q in a["title"].lower() or any(q in t for t in a["tags"])
    ]
    return {"query": query, "results": matches, "count": len(matches)}


def delete_user_account(user_id: str) -> dict:
    """
    Mock DESTRUCTIVE action: permanently deletes a user account.
    This tool is irreversible in a real system, so the executor always
    routes it through the human-approval gate before calling it.

    Pass user_id="ERROR" to simulate a downstream failure for testing the
    error-handling path.
    """
    if not user_id or not isinstance(user_id, str):
        raise ToolError("Parameter 'user_id' must be a non-empty string.")

    if user_id.upper() == "ERROR":
        raise ToolError("Simulated downstream failure: user service unreachable.")

    time.sleep(0.2)  # pretend this takes a moment
    return {
        "user_id": user_id,
        "status": "deleted",
        "deleted_at": time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime()),
    }


# Registry the rest of the app uses to look tools up by name.
TOOL_REGISTRY = {
    "get_weather": get_weather,
    "search_knowledge_base": search_knowledge_base,
    "delete_user_account": delete_user_account,
}

# Tools listed here are always gated behind human approval before execution.
DESTRUCTIVE_TOOLS = {"delete_user_account"}
