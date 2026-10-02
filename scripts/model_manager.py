from __future__ import annotations
import hashlib, json, os, shutil, tempfile, urllib.request
from pathlib import Path

def sha256(path: Path) -> str:
    h=hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda:f.read(1024*1024),b''): h.update(block)
    return h.hexdigest()

def install_verified(model: dict, root: Path) -> dict:
    url=model.get('download_url'); expected=(model.get('sha256') or '').lower()
    if not url or not expected or expected in ('replace-me','null'):
        return {'status':'SKIPPED','reason':'No verified URL+SHA256 in manifest; refusing unverified download.'}
    dest=root/'models'/model['id'].replace('/','_')
    dest.parent.mkdir(parents=True,exist_ok=True)
    if dest.exists() and sha256(dest).lower()==expected:
        return {'status':'VERIFIED','path':str(dest),'sha256':expected}
    if dest.exists():
        backup=dest.with_suffix(dest.suffix+'.corrupt')
        shutil.move(dest,backup)
    fd,tmp=tempfile.mkstemp(prefix='aether-download-',dir=str(dest.parent)); os.close(fd)
    try:
        urllib.request.urlretrieve(url,tmp)
        actual=sha256(Path(tmp))
        if actual != expected:
            Path(tmp).unlink(missing_ok=True)
            return {'status':'FAILED','reason':f'SHA256 mismatch: expected {expected}, got {actual}'}
        os.replace(tmp,dest)
        return {'status':'INSTALLED','path':str(dest),'sha256':actual}
    finally:
        Path(tmp).unlink(missing_ok=True)

def auto_install(catalog: dict, root: Path) -> dict:
    if os.getenv('AETHER_AUTO_DOWNLOAD','1').lower() not in ('1','true','yes'):
        return {}
    out={}
    for model in catalog.get('models',[]):
        if model.get('download_url'):
            out[model['id']]=install_verified(model,root)
    return out
