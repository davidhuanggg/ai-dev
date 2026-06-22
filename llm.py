"""
Provider-agnostic LLM interface for the exercise.

The whole point of this file is the `LLM` interface: the agent should depend on
`LLM`, not on any specific provider. The repo ships with `FakeLLM` so everything
runs offline with no API keys and no cost. A real provider can be dropped in
behind the same interface (see `RealLLM` and `get_llm`).

You generally should NOT need to edit `FakeLLM` to complete the exercise.
"""

from __future__ import annotations

import json
import os
import re
from typing import List, Dict, Protocol


# A "message" is a simple dict: {"role": "system"|"user"|"assistant"|"tool", "content": str}
Message = Dict[str, str]


class LLM(Protocol):
    """Minimal interface every provider must implement."""

    def complete(self, messages: List[Message]) -> str:
        """Return the model's next message content given the conversation so far."""
        ...


# ---------------------------------------------------------------------------
# Offline, deterministic fake provider (default).
# ---------------------------------------------------------------------------

class FakeLLM:
    """
    A deterministic stand-in for a real chat model.

    It follows the same protocol the agent expects:
      - If the conversation does not yet contain a tool result, it either emits a
        tool call as JSON  ->  {"tool": "query_data", "sql": "SELECT ..."}
        or, for questions the data cannot answer, a direct refusal answer.
      - Once a tool result is present, it emits a final answer as JSON
        ->  {"answer": "..."} that includes the value returned by the tool.

    This is intentionally simple keyword-matching. A real model would generalize;
    this fake only needs to handle the questions in eval/questions.jsonl so the
    exercise is fully runnable offline.
    """

    REFUSAL = "I don't have that information in the dataset."

    # Ordered (keyword-predicate -> SQL) rules. First match wins.
    def _sql_for(self, question: str) -> str | None:
        q = question.lower()

        # Questions the dataset cannot answer -> no SQL, caller will refuse.
        if "email" in q or "address" in q or "phone" in q:
            return None
        if "next year" in q or "will have" in q or "predict" in q or "forecast" in q:
            return None

        if "average" in q and "energy" in q:
            return "SELECT AVG(budget_usd) FROM programs WHERE sector = 'energy'"
        if "total budget" in q:
            return "SELECT SUM(budget_usd) FROM programs"
        if "people" in q and "health" in q:
            return "SELECT SUM(people_served) FROM programs WHERE sector = 'health'"
        if "education" in q:
            return "SELECT COUNT(*) FROM programs WHERE sector = 'education'"
        if "active" in q:
            return "SELECT COUNT(*) FROM programs WHERE status = 'active'"
        if "which sector" in q or "most programs" in q:
            return ("SELECT sector FROM programs GROUP BY sector "
                    "ORDER BY COUNT(*) DESC LIMIT 1")
        if "2021" in q:
            return "SELECT COUNT(*) FROM programs WHERE year = 2021"
        if "region" in q:
            return "SELECT COUNT(DISTINCT region) FROM programs"

        return None

    @staticmethod
    def _first_value(tool_content: str):
        """Pull the scalar out of a JSON-encoded list of rows, e.g. [[50]] -> 50."""
        try:
            rows = json.loads(tool_content)
            value = rows[0][0]
        except (ValueError, IndexError, TypeError):
            return tool_content
        if isinstance(value, float):
            value = round(value)
        return value

    def complete(self, messages: List[Message]) -> str:
        # Find the most recent tool result, if any.
        last_tool = next((m for m in reversed(messages) if m.get("role") == "tool"), None)
        if last_tool is not None:
            value = self._first_value(last_tool["content"])
            return json.dumps({"answer": f"Based on the data, the result is {value}."})

        # Otherwise this is the first turn: decide on a tool call or a refusal.
        question = next((m["content"] for m in reversed(messages)
                         if m.get("role") == "user"), "")
        sql = self._sql_for(question)
        if sql is None:
            return json.dumps({"answer": self.REFUSAL})
        return json.dumps({"tool": "query_data", "sql": sql})


# ---------------------------------------------------------------------------
# Real provider stub.
# ---------------------------------------------------------------------------

class RealLLM:
    """
    Placeholder for a real provider (OpenAI, Anthropic/Bedrock, Azure OpenAI, ...).

    This is intentionally NOT implemented. The exercise does not require real API
    calls. If you want to show how you'd wire one up, implement `complete` here
    using your provider's SDK and select it with LLM_PROVIDER=real. Keep the
    `LLM` interface unchanged so the agent and the eval harness don't care which
    provider is in use.
    """

    def __init__(self, model: str | None = None):
        self.model = model or os.environ.get("LLM_MODEL", "")

    def complete(self, messages: List[Message]) -> str:
        raise NotImplementedError(
            "RealLLM is not implemented. Set LLM_PROVIDER=fake (the default) to run "
            "offline, or implement this method against your provider's SDK."
        )


def get_llm() -> LLM:
    """Factory: pick a provider via the LLM_PROVIDER env var (defaults to 'fake')."""
    provider = os.environ.get("LLM_PROVIDER", "fake").lower()
    if provider == "fake":
        return FakeLLM()
    if provider == "real":
        return RealLLM()
    raise ValueError(f"Unknown LLM_PROVIDER: {provider!r} (expected 'fake' or 'real')")
