#!/usr/bin/env python3
import concurrent.futures, glob, json, re, time, urllib.request
from pathlib import Path

MODELS=['qwen2.5vl:3b','gemma4:e2b-nvfp4','llama3:8b']
files=sorted(glob.glob('content/chunks/day-*.json')+glob.glob('content/books/*/chunks/day-*.json'))
files=[f for f in files if len(json.load(open(f)).get('quiz',[]))!=5]

def generate(path):
    d=json.load(open(path)); passage='\n\n'.join(d.get('paragraphs',[])); passage=passage[:3600]
    prompt=f'''Write exactly five engaging comprehension questions about this reading chunk. Test main idea, motivation, cause/effect, sequence, inference, or evidence. Do not ask whether a sentence appeared. Every option must be plausible and only one correct. Return only a JSON array. Each object must have question, options (4 strings), answer (0-3), explanation.\n\n{passage}'''
    for model in MODELS:
        for attempt in range(2):
            try:
                body=json.dumps({'model':model,'prompt':prompt,'stream':False,'format':'json','options':{'temperature':.1,'num_predict':1400}}).encode()
                req=urllib.request.Request('http://127.0.0.1:11434/api/generate',data=body,headers={'Content-Type':'application/json'})
                with urllib.request.urlopen(req,timeout=180) as r: raw=json.loads(r.read()).get('response','')
                m=re.search(r'\[[\s\S]*\]',raw); quiz=json.loads(m.group(0)) if m else None
                if isinstance(quiz,list) and len(quiz)==5 and all(len(q.get('options',[]))==4 and isinstance(q.get('answer'),int) and 0<=q['answer']<4 and q.get('explanation') for q in quiz):
                    d['quiz']=quiz; d['quizModel']=model; d['quizSeconds']=round(time.time()-started,1); Path(path).write_text(json.dumps(d,ensure_ascii=False),encoding='utf-8'); return path,model,d['quizSeconds'],None
            except Exception as e: error=e
    return path,None,round(time.time()-started,1),str(error)

def work(path):
    global started
    started=time.time()
    return generate(path)

with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
    for path,model,seconds,error in pool.map(work,files): print(f'{path}: {model or "FAILED"} {seconds}s {error or ""}',flush=True)
