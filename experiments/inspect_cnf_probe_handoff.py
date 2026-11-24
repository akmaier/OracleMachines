#!/usr/bin/env python3
"""Check exact producer/consumer reuse on the earlier largest unresolved prefix."""
from pathlib import Path
import json,sqlite3,sys,tempfile,time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_whole_pool_priority as previous
from experiments.cnf_probe_handoff import ProbeHandoffSolver
from experiments.cnf_fresh_mixtures import attempt
base=previous.base
PARENT=Path('experiments/results/cnf-whole-pool-priority')


def inspect(out,capacity=256*1024):
    p=base.load(PARENT/'protocol.json');cases=previous.bound(p['cases']['holdout'])[:41]
    expected=base.load(PARENT/'holdout-priority-0/queries.json')[:41];records=[]
    with tempfile.TemporaryDirectory() as td:
        path=Path(td)/'db';s=ProbeHandoffSolver(path,node_limit=256,handoff_bytes=capacity)
        try:
            for c,old in zip(cases,expected):
                r=attempt(s,c['source'])
                assert r['status']==old['status'] and r['metrics'].get('expanded_nodes',0)==old['metrics'].get('expanded_nodes',0)
                if r['result'] is not None:
                    for k in ('answer','model','root','authority'):assert json.loads(base.encode(r['result'][k]))==old['result'][k],(c['case'],k,r['result'][k],old['result'][k])
                records.append(dict(case=c['case'],**r))
            present={n for n, in s.db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
            captured={t:dict(s.db.execute(f'SELECT id,payload FROM {t}')) if t in present else {} for t in previous.ALL_TABLES}
        finally:s.close()
        full=Path(td)/'full';base.restore_archive(base.load(PARENT/'holdout-priority-0/report.json')['archive'],full)
        con=sqlite3.connect(full)
        try:
            present={n for n, in con.execute("SELECT name FROM sqlite_master WHERE type='table'")}
            for t,entries in captured.items():
                original=dict(con.execute(f'SELECT id,payload FROM {t}')) if t in present else {}
                assert entries.items()<=original.items()
        finally:con.close()
        out.mkdir(parents=True,exist_ok=True);archive=base.archive(path,out)
    base.write(out/'queries.json',records)
    base.write(out/'inspection.json',dict(parent=previous.binding(PARENT/'checkpoint.json'),
        capacity=capacity,cases=cases,queries=previous.binding(out/'queries.json'),archive=archive,
        prefix_payloads_equal=True,target=records[-1],
        limitations=['Exposed diagnostic, with only the exact prior chronological prefix and no future answers.',
            'Every retained payload equals one already preserved in the preceding matched archive.',
            'Timings are exploratory and do not enter prospective matched means.']))
    print(base.encode(dict(status=records[-1]['status'],metrics={k:v for k,v in records[-1]['metrics'].items() if 'handoff' in k})),flush=True)


if __name__=='__main__':inspect(Path(sys.argv[1]),int(sys.argv[2]) if len(sys.argv)>2 else 256*1024)
