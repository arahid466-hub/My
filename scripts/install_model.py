import argparse,hashlib,shutil,subprocess
from pathlib import Path
def sha256(p):
 h=hashlib.sha256()
 with open(p,'rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''): h.update(b)
 return h.hexdigest()
ap=argparse.ArgumentParser(); ap.add_argument('source'); ap.add_argument('dest'); ap.add_argument('--sha256',required=True); a=ap.parse_args()
s=Path(a.source); d=Path(a.dest); d.parent.mkdir(parents=True,exist_ok=True)
if not s.exists(): raise SystemExit('source model does not exist')
if sha256(s).lower()!=a.sha256.lower(): raise SystemExit('SHA256 mismatch; refusing install')
shutil.copy2(s,d); print(f'installed {d} ({sha256(d)})')
