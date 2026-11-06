#!/usr/bin/env python3
"""Turn the downloaded Gutenberg text into small, browser-loadable chunks."""
import json, re, sys
from pathlib import Path

source = Path(sys.argv[1] if len(sys.argv) > 1 else "content/franklin-autobiography.txt")
out_dir = Path(sys.argv[2] if len(sys.argv) > 2 else "content/chunks")
text = source.read_text(encoding="utf-8")
start = re.search(r"\*\*\* START OF .*?\*\*\*", text, re.I)
end = re.search(r"\*\*\* END OF .*?\*\*\*", text, re.I)
if start and end:
    text = text[start.end():end.start()]
paragraphs = [re.sub(r"\s+", " ", p).strip() for p in re.split(r"\n\s*\n", text)]
paragraphs = [p for p in paragraphs if p]

chunks, current, words = [], [], 0
for paragraph in paragraphs:
    count = len(paragraph.split())
    if current and words + count > 1800:
        chunks.append(current); current, words = [], 0
    current.append(paragraph); words += count
if current: chunks.append(current)

def make_quiz(paragraphs, day):
    """Create lightweight comprehension questions from the day's actual text."""
    pool = [p for p in paragraphs if len(p.split()) >= 12]
    questions = []
    for i in range(5):
        correct = pool[i % len(pool)]
        sentence = re.split(r"(?<=[.!?])\s+", correct)[0].strip()
        distractors = [p for p in pool if p != correct]
        distractors = [re.split(r"(?<=[.!?])\s+", p)[0].strip() for p in distractors]
        options = [sentence] + distractors[:3]
        while len(options) < 4:
            options.append("This detail was not included in today's reading.")
        questions.append({"question": f"Which statement was included in Day {day}’s reading?", "options": options[:4], "answer": 0})
    return questions

out_dir.mkdir(parents=True, exist_ok=True)
manifest = []
for index, paragraphs in enumerate(chunks, 1):
    filename = f"day-{index:02d}.json"
    payload = {"day": index, "title": f"Reading {index}", "paragraphs": paragraphs, "quiz": make_quiz(paragraphs, index)}
    (out_dir / filename).write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    manifest.append({"day": index, "title": payload["title"], "url": f"chunks/{filename}", "words": sum(len(p.split()) for p in paragraphs)})
(out_dir / "../manifest.json").resolve().write_text(json.dumps({"totalDays": len(manifest), "sections": manifest}, indent=2), encoding="utf-8")
print(f"Built {len(manifest)} reading chunks in {out_dir}")
