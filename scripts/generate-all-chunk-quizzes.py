#!/usr/bin/env python3
import concurrent.futures, glob, json, re, time, urllib.request
from pathlib import Path
from datetime import datetime, timezone

MODELS=['gemma4:e2b-nvfp4','qwen2.5vl:3b']
files=sorted(glob.glob('content/chunks/day-*.json')+glob.glob('content/books/*/chunks/day-*.json'))
files=[f for f in files if len(json.load(open(f)).get('quiz',[]))!=5]
status_path=Path('content/quiz-generation-status.json')
all_files=sorted(glob.glob('content/chunks/day-*.json')+glob.glob('content/books/*/chunks/day-*.json'))
def write_status(current=None,last=None,failed=None):
    valid=sum(len(json.load(open(f)).get('quiz',[]))==5 for f in all_files)
    payload={'updated_at':datetime.now(timezone.utc).isoformat(),'total_chunks':len(all_files),'valid_chunks':valid,'remaining_chunks':len(all_files)-valid,'current_chunk':current,'last_result':last,'failed_chunk':failed}
    status_path.write_text(json.dumps(payload,indent=2),encoding='utf-8')
write_status()

def generate(path):
    started=time.time(); error='unknown failure'
    d=json.load(open(path)); passage='\n\n'.join(d.get('paragraphs',[])); passage=passage[:1800]
    prompt=f'''Return ONLY valid JSON in this exact shape: {{"questions":[five objects]}}. The questions array must contain exactly 5 engaging comprehension questions about this reading chunk. Test main idea, motivation, cause/effect, sequence, inference, or evidence. Do not ask whether a sentence appeared. Each object must have question, options (exactly 4 strings), answer (integer 0-3), explanation. Base every question on the passage.\n\n{passage}'''
    for model in MODELS:
        for attempt in range(2):
            try:
                body=json.dumps({'model':model,'prompt':prompt,'stream':False,'format':'json','options':{'temperature':.1,'num_predict':1200}}).encode()
                req=urllib.request.Request('http://127.0.0.1:11434/api/generate',data=body,headers={'Content-Type':'application/json'})
                with urllib.request.urlopen(req,timeout=90) as r: raw=json.loads(r.read()).get('response','')
                obj=json.loads(raw); quiz=obj.get('questions',obj) if isinstance(obj,dict) else obj
                if isinstance(quiz,list) and len(quiz)==5 and all(len(q.get('options',[]))==4 and isinstance(q.get('answer'),int) and 0<=q['answer']<4 and q.get('explanation') for q in quiz):
                    d['quiz']=quiz; d['quizModel']=model; d['quizSeconds']=round(time.time()-started,1); Path(path).write_text(json.dumps(d,ensure_ascii=False),encoding='utf-8'); return path,model,d['quizSeconds'],None
            except Exception as e: error=e
    return path,None,round(time.time()-started,1),str(error)

def work(path):
    return generate(path)

with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
    for path in files:
        write_status(current=path)
        path,model,seconds,error=work(path)
        write_status(last={'chunk':path,'model':model,'seconds':seconds,'ok':bool(model)},failed=None if model else path)
        print(f'{path}: {model or "FAILED"} {seconds}s {error or ""}',flush=True)
