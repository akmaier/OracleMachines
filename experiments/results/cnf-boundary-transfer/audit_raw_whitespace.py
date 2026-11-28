"""Preserve downloaded bytes; audit Git whitespace diagnostics as raw-only."""
from pathlib import Path
import re,subprocess,sys
sys.path.insert(0,str(Path(__file__).resolve().parents[3]))
from experiments import compare_cnf_boundary_transfer as s
out=Path(__file__).parent
result=subprocess.run(['git','diff','--cached','--check'],capture_output=True,text=True)
assert result.returncode==2 and not result.stderr
warnings=[line for line in result.stdout.splitlines() if re.match(r'.+:\d+: (trailing whitespace|new blank line at EOF)\.$',line)]
paths={line.split(':',1)[0] for line in warnings}
expected={r['raw']['path'] for r in s.load(out/'acquisition.json')['records']}
assert paths==expected and len(paths)==24
for row in s.load(out/'acquisition.json')['records']:assert s.sha(row['raw']['path'])==row['raw']['sha256']
rest=subprocess.run(['git','diff','--cached','--check','--','.',':(exclude)experiments/results/cnf-boundary-transfer/raw/*.cnf'],capture_output=True,text=True)
assert rest.returncode==0 and not rest.stdout and not rest.stderr
s.write(out/'whitespace-audit.json',dict(passed=True,raw_files=sorted(paths),diagnostics=len(warnings),non_raw_check_clean=True,original_hashes_unchanged=True,scope='Git reports only publisher trailing whitespace and EOF blank lines in the 24 preserved originals. Raw bytes are intentionally not rewritten; code, documents and generated artifacts pass the separate check.'))
print(s.encode(dict(passed=True,raw_files=len(paths),diagnostics=len(warnings))))
