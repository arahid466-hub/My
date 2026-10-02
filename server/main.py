from __future__ import annotations
import asyncio, json, os, shutil, subprocess, threading, uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any
import httpx
from fastapi import FastAPI, HTTPException, UploadFile, File, WebSocket, WebSocketDisconnect, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel, Field

ROOT = Path(os.getenv('AETHER_DATA_DIR', '/data/aether'))
if not Path('/data').exists() or not os.access('/data', os.W_OK): ROOT = Path(os.getenv('AETHER_DATA_DIR', str(Path(__file__).parents[1] / 'data')))
DIRS = {k: ROOT / k for k in ['models','generated/images','generated/audio','generated/videos','uploads','jobs']}
for p in DIRS.values(): p.mkdir(parents=True, exist_ok=True)
app = FastAPI(title='Aether AI Engine', version='1.0.0')
app.add_middleware(CORSMiddleware, allow_origins=['*'], allow_methods=['*'], allow_headers=['*'])
DB = ROOT / 'aether.sqlite3'
import sqlite3

def conn():
    c=sqlite3.connect(DB, check_same_thread=False); c.row_factory=sqlite3.Row; return c
with conn() as c:
    c.executescript('''CREATE TABLE IF NOT EXISTS jobs(id TEXT PRIMARY KEY, kind TEXT, status TEXT, progress INTEGER, input TEXT, output TEXT, error TEXT, created TEXT, updated TEXT); CREATE TABLE IF NOT EXISTS users(id TEXT PRIMARY KEY, username TEXT UNIQUE, password TEXT, admin INTEGER DEFAULT 0); CREATE TABLE IF NOT EXISTS settings(k TEXT PRIMARY KEY, v TEXT);''')
    if not c.execute('SELECT 1 FROM users LIMIT 1').fetchone(): c.execute('INSERT INTO users VALUES(?,?,?,1)', ('admin','admin-change-me','admin')); c.commit()

class ChatReq(BaseModel):
    message: str = Field(min_length=1)
    history: list[dict[str, str]] = []
    system: str = 'You are Aether, a precise helpful assistant.'
class GenReq(BaseModel):
    prompt: str = Field(min_length=1)
    settings: dict[str, Any] = {}
class LoginReq(BaseModel): username: str; password: str

async def local_chat(req: ChatReq):
    base=os.getenv('OLLAMA_URL','http://localhost:11434'); model=os.getenv('OLLAMA_MODEL','llama3.2')
    messages=[{'role':'system','content':req.system}, *req.history, {'role':'user','content':req.message}]
    try:
        async with httpx.AsyncClient(timeout=180) as x:
            r=await x.post(f'{base}/api/chat',json={'model':model,'messages':messages,'stream':False}); r.raise_for_status(); d=r.json()
            return d.get('message',{}).get('content','')
    except Exception as e:
        raise HTTPException(503, f'Local chat unavailable. Start Ollama at {base} and install model {model}. Detail: {e}')

@app.get('/')
def index(): return FileResponse(Path(__file__).parents[1] / 'static' / 'index.html')
@app.get('/frontend/index.html')
def frontend_index():
    return FileResponse(Path(__file__).parents[1] / 'frontend' / 'index.html')

@app.get('/api/health')
def health():
    tools={x: shutil.which(x) is not None for x in ['ffmpeg','ollama','piper']}
    return {'ok':True,'engine':'aether','data_dir':str(ROOT),'tools':tools,'gpu':os.getenv('NVIDIA_VISIBLE_DEVICES','none') not in ('','none','void')}
@app.get('/api/deployment-report')
def deployment_report():
    p=ROOT/'deployment-report.json'
    if not p.exists(): raise HTTPException(404,'Deployment report not generated yet')
    return json.loads(p.read_text())
@app.post('/api/auth/login')
def login(req: LoginReq):
    with conn() as c: u=c.execute('SELECT * FROM users WHERE username=? AND password=?',(req.username,req.password)).fetchone()
    if not u: raise HTTPException(401,'Invalid credentials')
    return {'token':'local-admin-token','username':u['username'],'admin':bool(u['admin'])}
@app.post('/api/chat')
async def chat(req: ChatReq): return {'message':await local_chat(req),'model':os.getenv('OLLAMA_MODEL','llama3.2'),'provider':'local-ollama'}

def new_job(kind,payload):
    jid=str(uuid.uuid4()); now=datetime.utcnow().isoformat();
    with conn() as c: c.execute('INSERT INTO jobs VALUES(?,?,?,?,?,?,?,?,?)',(jid,kind,'QUEUED',0,json.dumps(payload),None,None,now,now)); c.commit()
    threading.Thread(target=run_job,args=(jid,kind,payload),daemon=True).start(); return jid

def set_job(jid,**kw):
    kw['updated']=datetime.utcnow().isoformat(); fields=','.join(f'{k}=?' for k in kw); vals=list(kw.values())+[jid]
    with conn() as c: c.execute(f'UPDATE jobs SET {fields} WHERE id=?',vals); c.commit()

def run_job(jid,kind,payload):
    try:
        set_job(jid,status='DOWNLOADING_MODEL',progress=5)
        if kind=='tts': out=run_tts(jid,payload)
        elif kind=='audio': out=run_audio(jid,payload)
        elif kind=='image': out=run_image(jid,payload)
        elif kind=='video': out=run_video(jid,payload)
        else: raise RuntimeError('Unsupported job')
        set_job(jid,status='COMPLETED',progress=100,output=json.dumps(out))
    except Exception as e: set_job(jid,status='FAILED',progress=100,error=str(e))

def require_tool(name, message):
    if not shutil.which(name): raise RuntimeError(message)

def run_tts(jid,p):
    require_tool('piper','TTS unavailable: install Piper and set PIPER_MODEL to a local .onnx model.')
    model=os.getenv('PIPER_MODEL');
    if not model or not Path(model).exists(): raise RuntimeError('TTS unavailable: PIPER_MODEL must point to an installed local Piper model.')
    set_job(jid,status='GENERATING',progress=40); fn=DIRS['generated/audio']/f'{jid}.wav'; text=p['prompt']
    proc=subprocess.run(['piper','--model',model,'--output_file',str(fn)],input=text.encode(),capture_output=True)
    if proc.returncode: raise RuntimeError(proc.stderr.decode()[-500:])
    return {'file':f'/api/files/generated/audio/{fn.name}','type':'audio/wav'}

def run_audio(jid,p):
    require_tool('ffmpeg','Audio processing unavailable: ffmpeg is required.'); raise RuntimeError('Audio generation needs a local audio model adapter; no fake audio is returned. Configure an adapter in a future provider module.')
def run_image(jid,p):
    raise RuntimeError('Image generation unavailable: configure a local ComfyUI or diffusers adapter with a downloaded model. No fake image is returned.')
def run_video(jid,p):
    if not os.getenv('VIDEO_MODEL_DIR'): raise RuntimeError('Video generation unavailable: set VIDEO_MODEL_DIR to a local supported video model and provide GPU/runtime. Railway CPU instances cannot run large video models reliably.')
    raise RuntimeError('Video adapter is not enabled for this hardware/runtime. No fake video is returned.')

@app.post('/api/generate/{kind}')
def generate(kind: str, req: GenReq):
    if kind not in ('image','audio','tts','video'): raise HTTPException(404,'Unknown generation type')
    return {'job_id':new_job(kind,req.model_dump())}
@app.get('/api/jobs')
def jobs():
    with conn() as c: return [dict(x) for x in c.execute('SELECT * FROM jobs ORDER BY created DESC LIMIT 100')]
@app.get('/api/jobs/{jid}')
def job(jid:str):
    with conn() as c: x=c.execute('SELECT * FROM jobs WHERE id=?',(jid,)).fetchone()
    if not x: raise HTTPException(404,'Job not found')
    d=dict(x); d['output']=json.loads(d['output']) if d['output'] else None; return d
@app.get('/api/models')
def models():
    return [{'name':p.name,'size':p.stat().st_size,'path':str(p)} for p in DIRS['models'].glob('**/*') if p.is_file()]
@app.post('/api/upload')
async def upload(file: UploadFile=File(...)):
    safe=Path(file.filename or 'upload.bin').name; fid=f'{uuid.uuid4()}-{safe}'; dest=DIRS['uploads']/fid
    with dest.open('wb') as f: shutil.copyfileobj(file.file,f)
    return {'id':fid,'name':safe,'url':f'/api/files/uploads/{fid}'}
@app.get('/api/files/{folder}/{name}')
def get_file(folder:str,name:str):
    if folder not in ('uploads','generated'): raise HTTPException(404,'Invalid folder')
    p=ROOT/folder/name if folder=='uploads' else ROOT/'generated'/name
    if not p.exists() or not p.is_file(): raise HTTPException(404,'File not found')
    return FileResponse(p)
@app.get('/api/events/{jid}')
async def events(jid:str):
    async def stream():
        while True:
            with conn() as c: x=c.execute('SELECT status,progress,error FROM jobs WHERE id=?',(jid,)).fetchone()
            if not x: yield 'event: error\ndata: not found\n\n'; break
            yield f'data: {json.dumps(dict(x))}\n\n'
            if x['status'] in ('COMPLETED','FAILED'): break
            await asyncio.sleep(1)
    return StreamingResponse(stream(),media_type='text/event-stream')
@app.websocket('/ws/jobs/{jid}')
async def ws(websocket:WebSocket,jid:str):
    await websocket.accept()
    try:
        while True:
            d=job(jid); await websocket.send_json({'status':d['status'],'progress':d['progress'],'error':d['error']})
            if d['status'] in ('COMPLETED','FAILED'): break
            await asyncio.sleep(1)
    except WebSocketDisconnect: pass
