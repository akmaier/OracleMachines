"""Fresh-worker target-only certificate replay; supplemental, not benchmark cost."""
from collections import Counter
from pathlib import Path
from unittest.mock import patch
import subprocess,sys
sys.path.insert(0,str(Path(__file__).resolve().parents[3]))
from experiments import compare_cnf_watched_learning as s
out=Path(__file__).resolve().parent
if len(sys.argv)>1:
 mode=sys.argv[1];p=s.load(out/'protocol.json');report=s.load(out/(mode+'-0')/'report.json');counts=Counter();answers=[]
 with patch.object(s.e,'search',side_effect=AssertionError),patch.object(s.e,'expand',side_effect=AssertionError),patch.object(s.e.selective,'transport',side_effect=AssertionError),patch.object(s.e.baseline,'search',side_effect=AssertionError):
  for row in s.source_rows(p):
   if row['expansion_case']:
    answer=s.check(row['source'],s.load(out/(mode+'-0')/(row['id']+'.json')),counts);answers.append(dict(id=row['id'],result=answer))
 assert dict(counts)==report['warm_counts']
 assert s.encode(answers)==s.encode([dict(id=r['id'],result=r['result']) for r in report['cases']])
 print(s.encode(dict(mode=mode,passed=True,counts=dict(counts),cases=len(answers))))
else:
 results=[]
 for mode in s.MODES:
  import json
  results.append(json.loads(subprocess.check_output([sys.executable,__file__,mode],text=True)))
 s.write(out/'fresh-process-replay.json',dict(passed=True,records=results,scope='One new Python process per policy, loading only target inputs and stored target certificates. Search, expansion and parent transport are disabled. Counts and answers equal the measured replay. This is additional correctness validation, excluded from benchmark timings; OS caches are not flushed.'))
 print('Both fresh-process target replays passed')
