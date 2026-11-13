#!/usr/bin/env python3
"""Count possible later windows from the validated, exact source-bound records."""
from collections import Counter
import gzip
import json
from pathlib import Path
import sqlite3
import sys
import tempfile
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments.cnf_failed_literal import probe_choices
from experiments.cnf_probe_window import TABLE,record_key
from experiments.compare_cnf_growth_escape import sha,sha_key


def main(out):
    report=json.loads((out/'report.json').read_text());validation=json.loads((out/'validation.json').read_text())
    assert validation['report_sha256']==sha(out/'report.json')
    d=report['delta'];assert sha(d['path'])==d['sha256'];rows=[]
    with tempfile.TemporaryDirectory() as tmp:
        path=Path(tmp)/'delta';path.write_bytes(gzip.decompress(Path(d['path']).read_bytes()))
        assert sha(path)==d['database_sha256'];db=sqlite3.connect(path)
        for key,payload in db.execute(f'SELECT id,payload FROM {TABLE}'):
            record=json.loads(payload);assert record_key(record)==key
            _,config,_,cnf=json.loads(record['source'])
            original=probe_choices(cnf,config['probe_limit'],Counter())
            ranked=probe_choices(cnf,64,Counter());selected=[v for v in ranked if v not in original][:record['width']]
            attempted={a['variable'] for a in record['probing']['attempts']}
            if record['probing']['status']=='clear':assert attempted==set(selected)
            rows.append(dict(window_sha256=sha_key(key),status=record['probing']['status'],
                original_candidates=original,attempted_variables=sorted(attempted),
                remaining_ranked_variables=[v for v in ranked if v not in set(original)|attempted]))
        db.close()
    clear=[r for r in rows if r['status']=='clear']
    result=dict(script_sha256=sha(Path(__file__)),report_sha256=sha(out/'report.json'),
        validation_sha256=sha(out/'validation.json'),rows=rows,
        clear_windows=len(clear),clear_with_later_candidates=sum(bool(r['remaining_ranked_variables']) for r in clear),
        clear_remaining_candidate_counts=dict(Counter(len(r['remaining_ranked_variables']) for r in clear)),
        limitations=['Post-hoc availability diagnostic, not a new probe or coverage result.',
            'A following window must reuse these checked prefixes explicitly; repeating the current width-four key does not advance it.'])
    (out/'continuation-opportunity.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ('rows','limitations')}))


if __name__=='__main__':main(Path(sys.argv[1]))
