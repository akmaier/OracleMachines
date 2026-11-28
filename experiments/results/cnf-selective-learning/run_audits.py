"""Run independent audits after matched timing, retaining separate reproduction."""
from pathlib import Path
import subprocess,sys
out=Path('experiments/results/cnf-selective-learning');temporary=out/'semantic-reproduction';temporary.mkdir()
subprocess.run([sys.executable,'experiments/audit_cnf_selective_learning.py','semantics',str(temporary)],check=True)
(out/'semantic-audit-reproduced.json').write_bytes((temporary/'semantic-audit.json').read_bytes())
for action in ('transports','references'):
    subprocess.run([sys.executable,'experiments/audit_cnf_selective_learning.py',action,str(out)],check=True)
print('Independent audits completed',flush=True)
