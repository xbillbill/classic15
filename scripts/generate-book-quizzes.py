#!/usr/bin/env python3
"""Generate one validated five-question comprehension quiz per added book."""
import json, re, time, urllib.request
from pathlib import Path

models = ["gemma4:e2b-nvfp4", "llama3:8b", "qwen2.5-coder:7b-instruct-q4_K_M"]
for manifest_path in sorted(Path("content/books").glob("*/manifest.json")):
    manifest = json.loads(manifest_path.read_text())
    book_dir = manifest_path.parent
    samples = []
    for chunk_path in sorted((book_dir / "chunks").glob("day-*.json"))[:3] + sorted((book_dir / "chunks").glob("day-*.json"))[-2:]:
        samples.extend(json.loads(chunk_path.read_text())["paragraphs"])
    passage = "\n\n".join(samples)[:12000]
    prompt = f'''Create exactly five engaging, intellectually serious comprehension questions about {manifest["title"]} by {manifest["author"]}. Test central idea, motivation, cause/effect, sequence, inference, and evidence. Return only a JSON array. Each object must contain question, options (exactly four strings), answer (integer 0-3), and explanation. Use only the passage below.\n\n{passage}'''
    quiz = None
    started = time.monotonic()
    for model in models:
        try:
            body = json.dumps({"model": model, "prompt": prompt, "stream": False, "format": "json", "options": {"temperature": .1, "num_predict": 2200}}).encode()
            req = urllib.request.Request("http://127.0.0.1:11434/api/generate", data=body, headers={"Content-Type":"application/json"})
            with urllib.request.urlopen(req, timeout=240) as response: raw = json.loads(response.read()).get("response", "")
            match = re.search(r"\[[\s\S]*\]", raw)
            candidate = json.loads(match.group(0)) if match else None
            if isinstance(candidate, list) and len(candidate) == 5 and all(len(q.get("options", [])) == 4 and q.get("answer") in range(4) for q in candidate): quiz = candidate; break
        except Exception: continue
    if quiz is None: raise RuntimeError(f"Could not generate {manifest['book']}")
    payload = {"book": manifest["book"], "title": manifest["title"], "author": manifest["author"], "model": model, "seconds": round(time.monotonic()-started, 1), "quiz": quiz}
    (book_dir / "quiz.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2))
    print(f"{manifest['book']}: {payload['seconds']}s via {model}", flush=True)
