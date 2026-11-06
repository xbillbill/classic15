#!/usr/bin/env python3
"""Fetch and chunk the additional Harvard Classics titles for static hosting."""
import json, re, urllib.request
from pathlib import Path

books = {
    "republic": ("The Republic", "Plato", "1497"),
    "meditations": ("Meditations", "Marcus Aurelius", "2680"),
    "utopia": ("Utopia", "Thomas More", "2130"),
    "prince": ("The Prince", "Niccolò Machiavelli", "1232"),
    "essays-montaigne": ("Essays", "Michel de Montaigne", "3600"),
    "confessions": ("The Confessions", "Saint Augustine", "3296"),
    "odyssey": ("The Odyssey", "Homer", "1727"),
    "aeneid": ("The Aeneid", "Virgil", "228"),
    "poetics": ("Poetics", "Aristotle", "1974"),
    "walden": ("Walden", "Henry David Thoreau", "205"),
}

for book_id, (title, author, ebook) in books.items():
    raw = urllib.request.urlopen(f"https://www.gutenberg.org/cache/epub/{ebook}/pg{ebook}.txt", timeout=60).read().decode("utf-8", "replace").replace("\r", "")
    start = re.search(r"\*\*\* START OF .*?\*\*\*", raw, re.I)
    end = re.search(r"\*\*\* END OF .*?\*\*\*", raw, re.I)
    if start and end: raw = raw[start.end():end.start()]
    paragraphs = [re.sub(r"\s+", " ", p).strip() for p in re.split(r"\n\s*\n", raw)]
    paragraphs = [p for p in paragraphs if p]
    chunks, current, words = [], [], 0
    for paragraph in paragraphs:
        count = len(paragraph.split())
        if current and words + count > 1800: chunks.append(current); current, words = [], 0
        current.append(paragraph); words += count
    if current: chunks.append(current)
    out = Path("content/books") / book_id / "chunks"
    out.mkdir(parents=True, exist_ok=True)
    sections = []
    for i, chunk in enumerate(chunks, 1):
        filename = f"day-{i:02d}.json"
        (out / filename).write_text(json.dumps({"day": i, "title": f"Reading {i}", "paragraphs": chunk, "quiz": []}, ensure_ascii=False), encoding="utf-8")
        sections.append({"day": i, "title": f"Reading {i}", "url": f"chunks/{filename}", "words": sum(len(p.split()) for p in chunk)})
    (out.parent / "manifest.json").write_text(json.dumps({"book": book_id, "title": title, "author": author, "totalDays": len(sections), "sections": sections}, indent=2), encoding="utf-8")
    print(f"{book_id}: {len(sections)} chunks", flush=True)
