from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass, asdict
from pathlib import Path
import os, platform, shutil, subprocess
@dataclass
class Hardware:
    os: str; arch: str; cpu_cores: int; ram_bytes: int; gpu: str; vram_bytes: int; disk_free_bytes: int; cuda: bool
    def as_dict(self): return asdict(self)
def detect_hardware() -> Hardware:
    ram=0
    try:
        for line in Path('/proc/meminfo').read_text().splitlines():
            if line.startswith('MemTotal:'): ram=int(line.split()[1])*1024
    except OSError: pass
    gpu='none'; vram=0; cuda=bool(shutil.which('nvidia-smi'))
    if cuda:
        try:
            gpu=subprocess.check_output(['nvidia-smi','--query-gpu=name','--format=csv,noheader'],text=True,timeout=3).splitlines()[0]
            vram=int(float(subprocess.check_output(['nvidia-smi','--query-gpu=memory.total','--format=csv,noheader,nounits'],text=True,timeout=3).splitlines()[0])*1024*1024)
        except Exception: gpu='nvidia-unknown'
    return Hardware(platform.system(),platform.machine(),os.cpu_count() or 1,ram,gpu,vram,shutil.disk_usage('/').free,cuda)
class AetherModel(ABC):
    name='base'; capability='unknown'
    @abstractmethod
    def health(self)->dict: ...
    @abstractmethod
    def load(self)->None: ...
    @abstractmethod
    def unload(self)->None: ...
    @abstractmethod
    def generate(self, payload:dict): ...
    def stream(self,payload): yield self.generate(payload)
    def cancel(self,job_id): return False
class ModelSelector:
    def __init__(self, manifest:dict): self.manifest=manifest
    def choose(self, capability:str, hw:Hardware):
        choices=[m for m in self.manifest.get('models',[]) if capability in m.get('capabilities',[])]
        compatible=[m for m in choices if m.get('min_vram_gb',0)*1024**3 <= hw.vram_bytes and m.get('min_ram_gb',0)*1024**3 <= hw.ram_bytes]
        return sorted(compatible,key=lambda x:x.get('quality_rank',0),reverse=True)[0] if compatible else None
