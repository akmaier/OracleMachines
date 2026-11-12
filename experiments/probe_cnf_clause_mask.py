#!/usr/bin/env python3
"""Matched cold-source pilot for clause-mask reconstruction, preserving counters."""
import gzip
import json
from pathlib import Path
import shutil
import sys
import tempfile
from collections import Counter

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments.cnf_prepared_probes import PreparedProbeInventory
from experiments.cnf_clause_mask import ClauseMaskInventory
from experiments.cnf_pattern_inventory import encode
from experiments.compare_cnf_retained_plans import sha


def main(output):
    if output.exists():raise FileExistsError(output)
    source=Path('experiments/results/cnf-prepared-probes-full/report.json');r=json.loads(source.read_text());rows=[];ref={}
    with tempfile.TemporaryDirectory() as tmp:
        seed=Path(tmp)/'seed.db'
        with gzip.open(r['seed']['path'],'rb') as src,seed.open('wb') as dst:shutil.copyfileobj(src,dst)
        assert sha(seed)==r['seed']['database_sha256']
        for i in (1194,1441,1471):
            for cls in (PreparedProbeInventory,ClauseMaskInventory):
                path=Path(tmp)/(str(i)+cls.__name__);shutil.copyfile(seed,path);h=cls(path,**r['options'])
                found=h.inspect(r['cases'][i]['source']);signature=encode([found['root'],found['profile'],found['summary']])
                if i not in ref:ref[i]=signature
                assert ref[i]==signature
                metrics=Counter(found['metrics'])+Counter(found['prepared_metrics'])
                rows.append(dict(case=i,mode=cls.__name__,seconds=found['seconds'],metrics=dict(metrics),
                                 summary=found['summary'],state=h.reconstruction_state() if cls is ClauseMaskInventory else None))
                h.close()
    data=dict(input_report_sha256=sha(source),script_sha256=sha(Path(__file__)),rows=rows,
        fingerprints={p:sha(p) for p in ['experiments/cnf_clause_mask.py','experiments/cnf_single_pass_inventory.py']},
        limitations=['Three isolated sources from prepared history, fixed scan-then-mask order; not a full timing or memory comparison',
                     'Same roots, profiles and summaries; all discovery and checking costs inside inspect are timed'])
    output.write_text(json.dumps(data,indent=2)+'\n')
    print(json.dumps([{k:v for k,v in row.items() if k not in ('metrics','state')} for row in rows]))


if __name__=='__main__':main(Path(sys.argv[1]))
