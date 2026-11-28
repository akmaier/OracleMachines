"""Reproduce truth/trace audit, then independently rerun measured policies."""
from pathlib import Path
import subprocess,sys
out=Path('experiments/results/cnf-watched-learning');dest=out/'semantic-reproduction';dest.mkdir()
subprocess.run([sys.executable,'experiments/audit_cnf_watched_learning.py',str(dest)],check=True)
(out/'semantic-audit-reproduced.json').write_bytes((dest/'semantic-audit.json').read_bytes())
subprocess.run([sys.executable,'experiments/validate_cnf_watched_learning.py','validate',str(out)],check=True)
