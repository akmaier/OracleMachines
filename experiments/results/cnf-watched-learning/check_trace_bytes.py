"""Check byte-identical certificates and archives across all pairs and parent."""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[3]))
from experiments import compare_cnf_watched_learning as s
out=Path(__file__).resolve().parent;p=s.load(out/'protocol.json');records=[]
roots=[out/f'{mode}-{i}' for i in range(2) for mode in s.MODES]+[s.PARENT/'all-0']
for row in s.source_rows(p):
 if not row['expansion_case']:continue
 hashes=[s.sha(root/(row['id']+'.json')) for root in roots];assert len(set(hashes))==1
 records.append(dict(id=row['id'],sha256=hashes[0],bytes=(roots[0]/(row['id']+'.json')).stat().st_size))
archives={}
for name in ('certificates','discovery','combined'):
 hashes=[s.sha(root/(name+'.json.gz')) for root in roots];assert len(set(hashes))==1;archives[name]=hashes[0]
s.write(out/'trace-bytes.json',dict(passed=True,records=records,archives=archives,scope='All four measured runs and previous full-admission checkpoint have byte-identical certificates and deterministic gzip archives. Proof identity supplements independent source checking and exact diagnostic/counter comparisons.'))
print('All sixteen certificates and three archives are byte-identical across four runs and parent')
