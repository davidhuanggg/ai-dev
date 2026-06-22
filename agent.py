"""
A minimal data-question agent.

The agent takes a natural-language question, lets the LLM decide whether to call
the `query_data` tool, runs the tool, feeds the result back to the LLM, and
returns a final natural-language answer.

The agent depends only on the `LLM` interface from llm.py -- it must not care
which provider is behind it.

Protocol (what the LLM is told to produce):
  - To query the data, the model replies with ONLY a JSON object:
        {"tool": "query_data", "sql": "SELECT ..."}
  - To answer, the model replies with ONLY:
        {"answer": "..."}

Your job is to implement the loop in `Agent.answer` (see TODOs).
"""

from __future__ import annotations

import json
from typing import List

from llm import LLM, Message, get_llm
from tools import load_programs_db, query_data

SYSTEM_PROMPT = """You are a data assistant. Answer questions about a SQLite table
named `programs` with columns:
  program_id (TEXT), program_name (TEXT), region (TEXT), sector (TEXT),
  year (INTEGER), budget_usd (INTEGER), people_served (INTEGER), status (TEXT).

sector is one of: health, education, energy.

To read the data, reply with ONLY a JSON object: {"tool": "query_data", "sql": "SELECT ..."}
When you can answer, reply with ONLY: {"answer": "..."}
If the data cannot answer the question, reply with {"answer": "..."} saying so.
Reply with JSON only -- no extra text.
"""

MAX_STEPS = 4


class Agent:
    def __init__(self, llm: LLM | None = None):
        self.llm = llm or get_llm()
        self.con = load_programs_db()

    def answer(self, question: str) -> str:
        """
        Run the question through the agent loop and return a final answer string.

        TODO(candidate):
          1. Validate `question` (non-empty string).
          2. Build the message list (system + user) and loop up to MAX_STEPS:
               - call self.llm.complete(messages)
               - parse the JSON reply
               - if it's a tool call, run query_data(...) and append the result
                 as a {"role": "tool", "content": <json>} message, then continue
               - if it's an answer, return it
          3. Add basic reliability: handle malformed JSON / tool errors, and
             retry the LLM call once before giving up.
        """
        raise NotImplementedError("Implement the agent loop (see TODOs).")


if __name__ == "__main__":
    import sys

    agent = Agent()
    q = " ".join(sys.argv[1:]) or "How many programs are in the education sector?"
    print(agent.answer(q))
