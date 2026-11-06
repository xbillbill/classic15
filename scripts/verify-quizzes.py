#!/usr/bin/env python3
import glob, json, sys
files=sorted(glob.glob('content/chunks/day-*.json')+glob.glob('content/books/*/chunks/day-*.json'))
invalid=[]
questions={}
for path in files:
    try:
        d=json.load(open(path)); quiz=d.get('quiz'); reasons=[]
        if not isinstance(quiz,list) or len(quiz)!=5: reasons.append('quiz length')
        else:
            for i,q in enumerate(quiz):
                if len(q.get('options',[]))!=4: reasons.append(f'q{i} options')
                if not isinstance(q.get('answer'),int) or not 0<=q['answer']<4: reasons.append(f'q{i} answer')
                if not q.get('explanation'): reasons.append(f'q{i} explanation')
                if not q.get('question'): reasons.append(f'q{i} question')
                else: questions.setdefault(q['question'].strip().lower(), []).append(path)
        if reasons: invalid.append((path, reasons))
    except Exception as e: invalid.append((path,[str(e)]))
duplicates={k:v for k,v in questions.items() if len(v)>1}
print(json.dumps({'total_books':1+len(glob.glob('content/books/*/manifest.json')),'total_chunks':len(files),'valid_chunks':len(files)-len(invalid),'invalid_chunks':len(invalid),'duplicate_questions':len(duplicates),'invalid_examples':invalid[:20],'duplicate_examples':list(duplicates.items())[:10]},indent=2))
sys.exit(1 if invalid or duplicates else 0)
