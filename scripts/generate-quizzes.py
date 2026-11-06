#!/usr/bin/env python3
"""Generate and validate comprehension quizzes with a local Ollama model."""
import json, re, urllib.request, time
from pathlib import Path

MODEL = "gemma4:e2b-nvfp4"

def ask(passage, day):
    prompt = f'''You are writing a serious but engaging reading quiz for Day {day} of Benjamin Franklin's autobiography. Create exactly five questions that test understanding, not sentence matching. Use a mix of: central idea, motivation, cause and effect, chronology, inference, and evidence. Every option must be plausible, only one answer may be correct, and the explanation must cite the passage's reasoning. Return ONLY a JSON array, with no markdown or commentary. Each object must have exactly these keys: question, options (4 strings), answer (integer 0-3), explanation.\n\nPASSAGE:\n{passage}'''
    for _ in range(3):
        body = json.dumps({"model": MODEL, "prompt": prompt, "stream": False, "format": "json", "options": {"temperature": 0.1, "num_predict": 2600}}).encode()
        request = urllib.request.Request("http://127.0.0.1:11434/api/generate", data=body, headers={"Content-Type":"application/json"})
        with urllib.request.urlopen(request, timeout=240) as response:
            raw = json.loads(response.read()).get("response", "")
        match = re.search(r"\[[\s\S]*\]", raw)
        try: quiz = json.loads(match.group(0)) if match else None
        except json.JSONDecodeError: quiz = None
        if isinstance(quiz, list) and len(quiz) == 5 and all(set(item) == {"question", "options", "answer", "explanation"} and len(item["options"]) == 4 and item["answer"] in range(4) for item in quiz):
            return quiz
    raise ValueError(f"Could not produce valid quiz for day {day}")

started = time.monotonic()
completed = 0
for path in sorted(Path("content/chunks").glob("day-*.json")):
    data = json.loads(path.read_text(encoding="utf-8"))
    if data["day"] <= 3 or data.get("quizSource") == "local-llm":
        continue
    full_passage = "\n\n".join(data["paragraphs"])
    passage = full_passage[:5200] + "\n[...]\n" + full_passage[-1200:]
    day_started = time.monotonic()
    data["quiz"] = ask(passage, data["day"])
    data["quizSource"] = "local-llm"
    path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    elapsed = time.monotonic() - day_started
    completed += 1
    print(f"generated {path} in {elapsed:.1f}s", flush=True)
print(f"completed {completed} quizzes in {time.monotonic() - started:.1f}s; average {((time.monotonic() - started) / completed):.1f}s each" if completed else "nothing to generate", flush=True)
