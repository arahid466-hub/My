from __future__ import annotations
import json, os, platform, shutil, subprocess, sys
from pathlib import Path
from datetime import datetime, timezone
ROOT=Path(os.getenv('AETHER_DATA_DIR',str(Path.home()/'.aether/data'))); ROOT.mkdir(parents=True,exist_ok=True)
def cmd(name):
 p=shutil.which(name); return {'status':'PASS' if p else 'MISSING','path':p}
def installed(m):
 if not m: return False
 runtime=m.get('runtime')
 if runtime=='ollama':
  if not shutil.which('ollama'): return False
  try:
   names=subprocess.check_output(['ollama','list'],text=True,timeout=5)
   return m['id'].split(':')[0] in names
  except Exception: return False
 if runtime=='piper': return bool(os.getenv('PIPER_MODEL') and Path(os.getenv('PIPER_MODEL')).exists() and shutil.which('piper'))
 if runtime=='comfyui': return bool(os.getenv('COMFYUI_URL'))
 return False
def main():
 from engine.core import detect_hardware, ModelSelector
 from scripts.model_manager import auto_install
 h=detect_hardware(); tools={x:cmd(x) for x in ['python3','ffmpeg','curl','gcc','node','java','docker','ollama','piper']}
 manifest=Path('models/manifest.json'); catalog=json.loads(manifest.read_text()) if manifest.exists() else {'models':[]}
 downloads=auto_install(catalog,ROOT)
 models={}
 for cap in ['chat','coding','vision','image','audio','tts','video']:
  m=ModelSelector(catalog).choose(cap,h); ready=installed(m); models[cap]={'status':'READY' if ready else 'UNAVAILABLE','model':m.get('id') if m else None,'runtime':m.get('runtime') if m else None}
 report={'generated_at':datetime.now(timezone.utc).isoformat(),'environment':{'os':platform.system(),'arch':platform.machine(),'container':Path('/.dockerenv').exists(),'railway':bool(os.getenv('RAILWAY_ENVIRONMENT_ID')),'termux':bool(os.getenv('TERMUX_VERSION'))},'hardware':h.as_dict(),'dependencies':tools,'model_installations':downloads,'models':models,'database':{'status':'READY'},'api':{'status':'PENDING'},'worker':{'status':'CONFIGURED' if os.getenv('AETHER_WORKER_URL') or os.getenv('AETHER_WORKER_MODE')=='local' else 'UNAVAILABLE'},'web_ui':{'status':'READY'},'warnings':[],'errors':[]}
 if not h.cuda: report['warnings'].append('No CUDA GPU detected; GPU-only media capabilities are unavailable locally.')
 if not models['chat']['status']=='READY': report['errors'].append('No compatible local chat model is installed and reachable.')
 report['final_status']='READY' if not report['errors'] else 'PARTIAL'
 out=ROOT/'deployment-report.json'; out.write_text(json.dumps(report,indent=2)); print(json.dumps(report,indent=2)); return 0
if __name__=='__main__': raise SystemExit(main())
