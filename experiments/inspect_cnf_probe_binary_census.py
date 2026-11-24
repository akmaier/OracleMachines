#!/usr/bin/env python3
"""Census three exposed hard attempts without changing their chronological search."""
from collections import Counter
from pathlib import Path
import json,sqlite3,sys,tempfile,time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_probe_lifetime as prior
from experiments.cnf_probe_binary_census import BinaryCensusSolver
from experiments.cnf_fresh_mixtures import attempt
from experiments.cnf_residual_dag import ResidualSolver
base=prior.base
PARENT=Path('experiments/results/cnf-probe-lifetime')
FILES=('experiments/cnf_probe_binary_census.py','experiments/inspect_cnf_probe_binary_census.py',
    'solver/test_cnf_probe_binary_census.py')
TARGETS=(37,61,67)


def inspect(out):
    started=time.perf_counter();out.mkdir(parents=True,exist_ok=False)
    cp=base.load(PARENT/'checkpoint.json');p=base.load(PARENT/'protocol.json')
    for f,h in cp['source_fingerprints'].items():assert base.sha(f)==h,f
    sources={**cp['source_fingerprints'],**{f:base.sha(f) for f in FILES}}
    cases=prior.bound(p['cases']['holdout'])[:max(TARGETS)+1]
    expected=base.load(PARENT/'holdout-transfer-0/queries.json')[:len(cases)]
    base.write(out/'protocol.json',dict(parent=prior.binding(PARENT/'checkpoint.json'),
        cases=cases,targets=TARGETS,source_fingerprints=sources,node_limit=256,
        limitations=['Exposed diagnostic targets fixed from the preceding gap record; no untouched holdout or runtime speedup claim.',
            'Run the exact chronological empty-start prefix. Observe only prepared, nonconflicting whole probes; no new result enters search.',
            'Use the existing forced assignment, then binary SCC discovery with original source indices. Binary SAT is inconclusive for the full cofactor.',
            'Census timing excludes record serialization/checking; complete elapsed, raw records and separate checked proof archive are preserved.']))
    records=[];events=[]
    with tempfile.TemporaryDirectory() as td:
        path=Path(td)/'search';s=BinaryCensusSolver(path,node_limit=256,handoff_bytes=2*1024*1024)
        check_path=Path(td)/'proofs';checker=ResidualSolver(check_path)
        try:
            for c,old in zip(cases,expected):
                s.observe=c['case'] in TARGETS;s.events=[];r=attempt(s,c['source'])
                assert (r['status'],r['metrics'])==(old['status'],old['metrics']),(c['case'],'changed search')
                if r['result'] is not None:
                    for k in ('answer','model','root','authority','whole_plan','whole_pool'):
                        assert json.loads(base.encode(r['result'].get(k)))==old['result'].get(k),(c['case'],k)
                records.append(dict(case=c['case'],**r))
                for e in s.events:
                    for item in e['discovery']['nodes']:checker._store(item['key'],item['node'])
                    e['case']=c['case'];events.append(e)
                if s.observe:print('observed',c['case'],dict(Counter(e['discovery']['status'] for e in s.events)),flush=True)
            present={n for n, in s.db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
            captured={t:dict(s.db.execute(f'SELECT id,payload FROM {t}')) if t in present else {} for t in prior.ALL_TABLES}
            check_counts=dict(checker.counts)
        finally:s.close();checker.close()
        full=Path(td)/'expected';base.restore_archive(base.load(PARENT/'holdout-transfer-0/report.json')['archive'],full)
        con=sqlite3.connect(full)
        try:
            present={n for n, in con.execute("SELECT name FROM sqlite_master WHERE type='table'")}
            for t,rows in captured.items():
                old=dict(con.execute(f'SELECT id,payload FROM {t}')) if t in present else {}
                assert rows.items()<=old.items(),t
        finally:con.close()
        (out/'search').mkdir();(out/'proofs').mkdir()
        archive=base.archive(path,out/'search');proof_archive=base.archive(check_path,out/'proofs')
    base.write(out/'queries.json',records);base.write(out/'events.json',events)
    summary={str(i):dict(events=sum(e['case']==i for e in events),
        statuses=dict(Counter(e['discovery']['status'] for e in events if e['case']==i)),
        seconds=sum(e['seconds'] for e in events if e['case']==i)) for i in TARGETS}
    base.write(out/'report.json',dict(protocol=prior.binding(out/'protocol.json'),
        queries=prior.binding(out/'queries.json'),events=prior.binding(out/'events.json'),
        search_archive=archive,proof_archive=proof_archive,summary=summary,
        native_checker_counts=check_counts,exact_prefix_payloads=True,seconds=time.perf_counter()-started))
    print(base.encode(summary),flush=True)


if __name__=='__main__':inspect(Path(sys.argv[1]))
