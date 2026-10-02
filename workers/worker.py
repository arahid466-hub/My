from fastapi import FastAPI,Header,HTTPException
from pydantic import BaseModel
from engine.core import detect_hardware
import os
app=FastAPI(title='Aether GPU Worker')
TOKEN=os.getenv('AETHER_WORKER_TOKEN','')
class Task(BaseModel): job_id:str; kind:str; payload:dict
@app.get('/health')
def health(): return {'ok':True,'hardware':detect_hardware().as_dict()}
@app.post('/v1/jobs')
def submit(task:Task,x_aether_worker_token:str=Header(default='')):
 if not TOKEN or x_aether_worker_token!=TOKEN: raise HTTPException(401,'Invalid worker token')
 if task.kind in ('image','video') and not detect_hardware().cuda: raise HTTPException(503,'GPU runtime unavailable; refusing fake output')
 return {'accepted':True,'job_id':task.job_id,'status':'QUEUED'}
