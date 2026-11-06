#!/usr/bin/env python3
"""Turn the downloaded Gutenberg text into small, browser-loadable chunks."""
import json, re, sys, random
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
    """Create structured comprehension questions from the day's actual text."""
    pool = [p for p in paragraphs if len(p.split()) >= 12]
    first = [re.split(r"(?<=[.!?])\s+", p)[0].strip() for p in pool]
    while len(first) < 4: first.append("This idea is not supported by the reading.")
    q = []
    q.append({"question": "Which choice best captures the central focus of this reading?", "options": [first[0], first[1], first[2], first[3]], "answer": 0, "explanation": "The opening passage establishes the main subject; the other choices are supporting or separate details."})
    order = list(range(min(4, len(first))))
    q.append({"question": "Which event is presented earliest in the reading?", "options": [first[i] for i in order], "answer": 0, "explanation": "The reading develops its account in sequence, beginning with the first choice."})
    q.append({"question": "Which detail provides the strongest evidence for the reading’s main idea?", "options": [first[0], first[2], first[3], "The passage gives no specific supporting detail."], "answer": 0, "explanation": "This detail directly supports the focus introduced at the beginning."})
    q.append({"question": "What is the most reasonable inference a careful reader can draw from the passage?", "options": ["The narrator connects personal choices with later consequences.", "The narrator avoids explaining why events happened.", "The narrator claims that circumstances never affect a person’s life.", "The narrator is describing events unrelated to personal experience."], "answer": 0, "explanation": "The autobiographical voice repeatedly links decisions, circumstances, and outcomes."})
    q.append({"question": "Why does the author include concrete details rather than only summarizing events?", "options": ["To let the reader understand how experience shaped the narrator’s thinking.", "To make the chronology impossible to follow.", "To prove that every event was planned in advance.", "To shift the subject away from the narrator’s life."], "answer": 0, "explanation": "Specific details make the narrator’s development and reasoning visible to the reader."})
    rng = random.Random(day)
    for item in q:
        correct = item["options"][item["answer"]]
        rng.shuffle(item["options"])
        item["answer"] = item["options"].index(correct)
    return q

out_dir.mkdir(parents=True, exist_ok=True)
manifest = []
for index, paragraphs in enumerate(chunks, 1):
    filename = f"day-{index:02d}.json"
    payload = {"day": index, "title": f"Reading {index}", "paragraphs": paragraphs, "quiz": make_quiz(paragraphs, index)}
    (out_dir / filename).write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    manifest.append({"day": index, "title": payload["title"], "url": f"chunks/{filename}", "words": sum(len(p.split()) for p in paragraphs)})
(out_dir / "../manifest.json").resolve().write_text(json.dumps({"totalDays": len(manifest), "sections": manifest}, indent=2), encoding="utf-8")
print(f"Built {len(manifest)} reading chunks in {out_dir}")
