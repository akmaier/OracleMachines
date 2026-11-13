#!/usr/bin/env python3
"""Read only: bind the remaining selected target leaves and probe opportunities."""
from collections import Counter
import json
from pathlib import Path
import sys
import tempfile
import time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments.compare_cnf_trace_learning import restore_checkpoint
from experiments.compare_cnf_trace_reuse import read_archive
from experiments.compare_cnf_probe_continuation import sha,sha_key
from experiments.cnf_coupled_pivots import BudgetedInventory,FrontierIndex
from experiments.cnf_failed_literal import probe_choices


def inspect(out):
    started=time.perf_counter()
    with tempfile.TemporaryDirectory() as td:
        tmp=Path(td);path=tmp/'history';r,_,records=restore_checkpoint(out/'report.json',path,tmp)
        restoration=time.perf_counter()-started;before=sha(path)
        h=BudgetedInventory(path,**r['options']);h.set_admission_budget(0);index=FrontierIndex(h);counts=Counter();rows=[]
        diagnostics=read_archive(r['diagnostics']);cases={records[x['learning_index']]['source']:x['cases']
            for x in diagnostics if x['learning_index'] is not None}
        phase=time.perf_counter()
        for record in records:
            if record['edge'] is None:continue
            source=h._load(record['source']);target=h._load(record['edge']['key']);leaves=[]
            if target is not None:
                for key,multiplicity in sorted(index.frontier(record['edge']['key']).items()):
                    node=h._load(key);cnf=node['cnf'];tried={a['variable'] for a in node['profile']['probing'].get('attempts',[])}
                    ranked=probe_choices(cnf,64,counts)
                    leaves.append(dict(key=key,sha256=sha_key(key),multiplicity=multiplicity,variables=len({abs(l) for c in cnf for l in c}),
                        clauses=len(cnf),literals=sum(map(len,cnf)),minimum_width=min(map(len,cnf)),depth=node['depth'],
                        original_probe_status=node['profile']['probing']['status'],original_source_probe_variables=sorted(tried),
                        remaining_ranked_variables=[v for v in ranked if v not in tried]))
            rows.append(dict(source_sha256=sha_key(record['source']),cases=cases[record['source']],kind=record['probing']['status'],
                source_variables=len({abs(l) for c in source['cnf'] for l in c}),target_variables=None if target is None else len({abs(l) for c in target['cnf'] for l in c}),
                pending=target is None,selected_leaves=leaves))
        diagnosis=time.perf_counter()-phase;assert not h.admitted;h.close();assert sha(path)==before
    result=dict(report_sha256=sha(out/'report.json'),script_sha256=sha(Path(__file__)),rows=rows,counts=dict(counts),frontier_counts=dict(index.counts),
        restore_seconds=restoration,diagnosis_seconds=diagnosis,total_seconds=time.perf_counter()-started,history_bytes_unchanged=True,
        scope='Selected old-plan leaves below the three learned rewrite targets only, not all alternatives or a new probe pass.')
    (out/'remaining-targets.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
    print(json.dumps([dict(cases=x['cases'],source=x['source_variables'],target=x['target_variables'],
        leaves=[(y['variables'],len(y['remaining_ranked_variables'])) for y in x['selected_leaves']]) for x in rows]),flush=True)


if __name__=='__main__':inspect(Path(sys.argv[1]))
