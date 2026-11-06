#!/usr/bin/env python3
import json
from pathlib import Path
p=Path('content/quiz-generation-status.json')
if not p.exists(): print('No queue status yet. Start scripts/generate-all-chunk-quizzes.py'); raise SystemExit(1)
print(json.dumps(json.loads(p.read_text()),indent=2))
