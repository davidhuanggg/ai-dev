# Mini Research Assistant Agent — Take-Home Exercise

Thanks for taking the time to work through this. It's a small, deliberately
straightforward exercise meant to mirror the kind of work this role does day to
day: turning a researcher's ad-hoc questions into a small, reliable, AI-powered
tool. There are no trick questions and no clever algorithms required. We're more
interested in how you structure things and the trade-offs you reason about than
in volume of code.

**Time budget: ~2 hours.** If you run short on time, prioritize a working agent
and a working eval over polish, and use the README notes (Task 5) to describe
what you'd have done next.

## The scenario

A researcher has a small dataset of community programs (`data/programs.csv`) and
keeps asking questions about it in plain English: *"How many programs are in the
education sector?"*, *"What's the total budget?"*, and so on. You're building a
small agent that answers those questions by querying the data, and you're making
it reliable enough to trust and easy to evaluate.

The dataset is synthetic. Each row is a program with these columns:

| column | type | notes |
|---|---|---|
| `program_id` | text | e.g. `P001` |
| `program_name` | text | |
| `region` | text | Northeast, Southeast, Midwest, West, Southwest |
| `sector` | text | `health`, `education`, or `energy` |
| `year` | integer | 2019–2023 |
| `budget_usd` | integer | |
| `people_served` | integer | |
| `status` | text | active, completed, planned, cancelled |

## What's in the repo

```
data/programs.csv      ~150 rows of synthetic data (provided)
eval/questions.jsonl   ~10 question/expected-answer pairs (provided)
llm.py                 provider-agnostic LLM interface + an offline FakeLLM (provided)
tools.py               the query_data tool  -> YOU IMPLEMENT
agent.py               the agent loop        -> YOU IMPLEMENT
evaluate.py            the eval harness      -> YOU IMPLEMENT (the scorer)
requirements.txt       optional extras; the offline path needs only stdlib
```

### No API keys needed

`llm.py` ships a deterministic `FakeLLM` so the whole thing runs offline with no
keys and no cost. The agent talks to the `LLM` interface, never to a provider
directly. `FakeLLM` already knows how to handle the questions in the eval set, so
you can focus on the agent, the tool, and the harness. You should not need to
edit `FakeLLM`.

## Your tasks

1. **Implement the agent loop** in `agent.py` (`Agent.answer`). Given a question,
   let the LLM decide whether to call the `query_data` tool, run it, feed the
   result back, and return a final natural-language answer. The expected
   request/response JSON protocol is documented at the top of `agent.py`.

2. **Implement the tool** in `tools.py` (`query_data`). It runs a read-only SQL
   query against the data. Make it safe (SELECT-only) and make sure a bad query
   can't crash the agent. The CSV-to-SQLite loading is already done for you.

3. **Implement the scorer** in `evaluate.py` (`score_answer`) and run the harness.
   It should report a pass rate over `eval/questions.jsonl`. Note there are two
   kinds of question: `value` (the answer should contain an expected value) and
   `refusal` (questions the data can't answer, which the agent should decline).

4. **Add basic reliability.** Validate inputs, handle tool/parse errors, and
   retry the model call once before giving up. Keep the eval harness running even
   when an individual question fails.

5. **Write a short "Production notes" section** at the bottom of this README (a
   few bullets each is fine):
   - How would you swap `FakeLLM` for a real provider, and how would you keep the
     code provider-agnostic? (`llm.py` has a stub to point at.)
   - How would you evaluate and monitor reliability if this ran in a regulated,
     research environment?
   - Where would cost and latency come from, and how would you keep them in check?
   - What would move this from CSV to PostgreSQL, and how would you deploy it?
   - When (if ever) would you add a second agent?

## Running it

```bash
python evaluate.py                                          # run the eval harness
python agent.py "What is the total budget across all programs?"   # ask a single question
```

To switch providers later: `LLM_PROVIDER=fake` (default) or `LLM_PROVIDER=real`
(stub — intentionally not implemented).

## What we're looking for

Clear structure, sensible boundaries between the agent / tool / provider, honest
error handling, a meaningful eval, and thoughtful production notes. Working and
simple beats clever and fragile.

## Deliverables

- Working `agent.py`, `tools.py`, and `evaluate.py` (eval harness runs and reports
  a pass rate).
- The "Production notes" section below, filled in.

---

## Production notes

### How would you swap FakeLLM for a real provider, and how would you keep the code provider-agnostic? (llm.py has a stub to point at.) 

- Implement RealLLM.complete with the vendor SDK select it via LLM_PROVIDER = real. Keep the same JSON protocol (`{"tool": "query_data", "sql": "..."}` / `{"answer": "..."}`).
- Do not change agent.py/evaluate.py
- Keep the API key and model name in environment variables (e.g. OPENAI_API_KEY, LLM_MODEL). Store them in a local .env that is gitignored .gitignore already lists .env. Commit only a .env.example with empty placeholders, never real keys.
- Leave fake as the default so eval still runs offline
- Do not put provider-specific retry/token logic in the agent. If a vendor needs extra headers or tool-calling APIs, adapt that inside `RealLLM` so the agent still sees a string of JSON.



### How would you evaluate and monitor reliability if this ran in a regulated, research environment?

- Keep the gold eval in CI. Don’t rely on FakeLLM alone once RealLLM is on.
- Monitor while it runs. Log question, SQL, tool result/error, answer, model + prompt hash, latency so an audit can replay “why this number.”
- Track pass rate, refusal rate, tool-error rate and latency not just uptime.
- On failure refuse. Don’t silently answer from the model’s memory.
- Pin model name + prompt hash in the logs so an audit can say which version produced a result.
- Separate “the SQL is correct” from “the wording is acceptable.” The current scorer checks values/refusals a human spot-check (or a second judge model) can review tone and over-refusal.


### Where would cost and latency come from, and how would you keep them in check?

- Cost = tokens × model calls; latency = those same calls.
- Bound calls with MAX_STEPS + one retry don’t send full tables back to the model.
- Keep fake for local/CI; use a small/cheap model if the question is a simple count.
- Cache identical asks.
- If a real model is slow, stream the final answer only after the tool returns do not stream guessed SQL.


### What would move this from CSV to PostgreSQL, and how would you deploy it?

- Swap the connection in query_data / load_programs_db.
- Postgres is the source of truth CSV is only how you first loaded it.
- Read-only DB role + existing SELECT gate.
- Deploy as a small API in front of the agent, scale the app the DB is the source of truth.
- Run the same `evaluate.py` gold set against a staging DB snapshot before promoting.

### When (if ever) would you add a second agent?

- Not now. One agent + one read-only tool is the right size for this dataset and question type.
- Prefer a second *tool* (schema lookup, plot, export) before a second agent.
- Add a reviewer agent only if a human/audit would otherwise have to check every number, and the extra call is worth the cost.