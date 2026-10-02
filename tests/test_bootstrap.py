import json, os, subprocess, sys
from pathlib import Path
def test_bootstrap_report(tmp_path):
 env={**os.environ,'AETHER_DATA_DIR':str(tmp_path)}
 p=subprocess.run([sys.executable,'scripts/bootstrap.py'],env=env,capture_output=True,text=True,check=True)
 report=json.loads((tmp_path/'deployment-report.json').read_text())
 assert report['final_status'] in ('READY','PARTIAL')
 assert 'hardware' in report and 'models' in report
