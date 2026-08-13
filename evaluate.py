"""
Evaluation harness.

Runs every question in eval/questions.jsonl through the agent, scores the answer
against the expected result, and prints a pass rate. Loading the questions and
the run loop are provided. Your job is to implement `score_answer` (see TODO).

Run:  python evaluate.py
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import List, Dict

from agent import Agent
import re
QUESTIONS_PATH = Path(__file__).resolve().parent / "eval" / "questions.jsonl"


def load_questions(path: Path = QUESTIONS_PATH) -> List[Dict]:
    with open(path) as f:
        return [json.loads(line) for line in f if line.strip()]


def score_answer(answer: str, expected: str, kind: str) -> bool:
    """
    Return True if `answer` is correct for this question.

    There are two kinds of question:
      - kind == "value":   the answer should contain the `expected` value
                           (e.g. a count, sum, or sector name).
      - kind == "refusal": there is no `expected` value; the answer is correct
                           if it acknowledges the data can't answer the question.

    TODO(candidate): implement scoring for both kinds. Think about what counts as
    a match -- e.g. should "37,888,285" match "37888285"? How do you detect a
    refusal without being fooled by an answer that just happens to contain a word?
    """
    text = str(answer or "").strip()
    if kind == "value":
        if expected.isdigit():
            numbers = re.findall(r"\d+", text.replace(",",""))
            return expected in numbers
        return expected.lower() in text.lower()
    if kind == "refusal":
        lowered = text.lower()
        cues = (
        "don't have",
        "do not have",
        "can't answer",
        "cannot answer",
        "not in the dataset",
        "no information",
        "don't know",
        )
        return any(cue in lowered for cue in cues)
    return False


def main() -> None:
    agent = Agent()
    questions = load_questions()
    passed = 0

    for item in questions:
        try:
            answer = agent.answer(item["question"])
        except Exception as e:  # keep the harness running even if the agent fails
            answer = f"ERROR: {e}"

        try:
            ok = score_answer(answer, item.get("expected", ""), item.get("kind", "value"))
        except NotImplementedError:
            ok = False

        passed += int(ok)
        mark = "PASS" if ok else "FAIL"
        print(f"[{mark}] {item['id']}: {item['question']}")
        print(f"        expected={item.get('expected', '')!r} kind={item.get('kind')}")
        print(f"        answer={answer!r}")

    total = len(questions)
    print(f"\nScore: {passed}/{total} ({passed / total:.0%})" if total else "No questions.")


if __name__ == "__main__":
    main()
