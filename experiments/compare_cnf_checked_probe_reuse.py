#!/usr/bin/env python3
"""Matched exact-proof replay cache, with unchanged persistent SAT evidence."""
import argparse
from collections import Counter
import gc
import gzip
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import time

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments.cnf_checked_probe_reuse import CheckedProbeReuseInventory
from experiments.cnf_implied_subsumption import ImpliedSubsumptionInventory
from experiments.cnf_residual_dag import ResidualSolver, holds
from experiments.cnf_pattern_inventory import encode
from experiments.compare_cnf_implied_subsumption import node_summary, root_lift
from experiments.compare_cnf_pattern_inventory import memory_profile

OPTIONS=dict(max_depth=2,probe_limit=4,learn_limit=4)
MODES=dict(baseline=(ImpliedSubsumptionInventory,OPTIONS),
           cached=(CheckedProbeReuseInventory,dict(OPTIONS,checked_probe_bytes=1024*1024)))
PILOT_INDICES=[858,875,907,970,1042,1194,1185,1467]


def digest(raw):return hashlib.sha256(raw).hexdigest()


def cache_state(h):
    return h.probe_cache_state() if isinstance(h,CheckedProbeReuseInventory) else None


def cold_audit(path,raw,cls,options):
    path.write_bytes(raw);started=time.perf_counter();h=cls(path,**options)
    assert cache_state(h) is None or cache_state(h)['entries']==0
    nodes=sources=0
    for key, in h.db.execute('SELECT id FROM cnf_patterns_v1'):
        h._load(key);nodes+=1
    counts=dict(h.counts);state=cache_state(h)
    for key,payload in h.db.execute('SELECT id,payload FROM cnf_pattern_sources_v1'):
        saved=json.loads(payload);result=h.inspect(saved['source'])
        assert result['source_id']==key and result['root']==saved['root']
        assert result['metrics'].get('inserted_nodes',0)==0 and result['metrics']['inserted_sources']==0
        sources+=1
    h.close();solver=ResidualSolver(path);residuals=0
    for key, in solver.db.execute('SELECT id FROM cnf_residual_v1'):
        assert solver._read(key) is not None;residuals+=1
    assert solver.counts.get('expanded_nodes',0)==0
    assert solver.db.execute('PRAGMA integrity_check').fetchone()[0]=='ok';solver.close()
    assert path.read_bytes()==raw
    return dict(seconds=time.perf_counter()-started,nodes=nodes,sources=sources,residuals=residuals,
                node_check_metrics=counts,cache=state,bytes_unchanged=True)


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--pilot',action='store_true');args=parser.parse_args();out=args.output
    out.mkdir(parents=True,exist_ok=False)
    prior_dir=Path('experiments/results/cnf-implied-subsumption');input_path=prior_dir/'report.json'
    prior=json.loads(input_path.read_text());reference={r['case']:r for r in prior['records'] if r['mode']=='implied'}
    indices=PILOT_INDICES if args.pilot else list(range(len(prior['cases'])))
    cases=[dict(prior['cases'][i],original_case=i) for i in indices]
    modes=MODES if not args.pilot else dict(baseline=MODES['baseline'],**{
        f'cache_{b}':(CheckedProbeReuseInventory,dict(OPTIONS,checked_probe_bytes=b))
        for b in (32768,262144,1048576,8388608)})
    prior_entry=next(a for a in prior['archives'] if a['mode']=='implied')
    records=[];archives=[];expected_database=None
    for mode,(cls,options) in modes.items():
        gc.collect()
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'history.db';started=time.perf_counter();solver=ResidualSolver(path);h=cls(path,**options)
            initialization=time.perf_counter()-started
            for j,(i,case) in enumerate(zip(indices,cases)):
                if j%200==0:print(mode,'case',j,flush=True)
                started=time.perf_counter();discovery=h.inspect(case['source']);solved=solver.solve(case['source'])
                if solved['answer']:root_lift(h,discovery,solved['model'])
                elapsed=time.perf_counter()-started;operation_metrics=dict(h.counts)
                expected=reference[i]
                assert solved['answer']==expected['answer']
                assert discovery['summary']==expected['discovery']['summary']
                assert encode(discovery['profile'])==encode(expected['discovery']['profile'])
                assert digest(discovery['root']['key'].encode())==expected['discovery']['root_hash']
                if solved['answer']:assert holds(case['source'],solved['model'])
                discovery['dag']=node_summary(h,discovery['root']['key'])
                assert discovery['dag']==expected['discovery']['dag']
                discovery['root_hash']=digest(discovery['root']['key'].encode())
                del discovery['root'],discovery['source_id']
                records.append(dict(mode=mode,case=j,original_case=i,total_seconds=elapsed,discovery=discovery,
                    solver_seconds=solved['seconds'],answer=solved['answer'],operation_metrics=operation_metrics,
                    cache=cache_state(h)))
            storage=h.storage();state=cache_state(h);started=time.perf_counter()
            for case in cases:
                result=h.inspect(case['source'])
                assert result['metrics'].get('inserted_nodes',0)==0 and result['metrics']['inserted_sources']==0
            warm=time.perf_counter()-started;assert storage==h.storage();h.close();solver.close()
            raw=path.read_bytes();database_hash=digest(raw)
            if expected_database is None:expected_database=database_hash
            assert database_hash==expected_database
            if args.pilot:
                name='archive.sqlite3.gz'
                if not (out/name).exists():(out/name).write_bytes(gzip.compress(raw,mtime=0))
                archive_path=str(out/name)
            else:
                assert database_hash==prior_entry['database_sha256']
                archive_path=str(prior_dir/prior_entry['path'])
            checked=cold_audit(Path(tmp)/'cold.db',raw,cls,options)
            archives.append(dict(mode=mode,path=archive_path,database_sha256=database_hash,database_bytes=len(raw),
                initialization_seconds=initialization,warm_inventory_seconds=warm,storage=storage,cache=state,audit=checked))
        print(mode,'checked',flush=True)
    allocation_indices=[] if args.pilot else [858,875,907,970,1042,1061]
    profiles=[dict(mode=mode,**memory_profile([prior['cases'][i] for i in allocation_indices],options,cls))
              for mode,(cls,options) in modes.items()] if allocation_indices else []
    files=list(dict.fromkeys([str(Path(__file__)), 'experiments/cnf_checked_probe_reuse.py',
          'solver/test_cnf_checked_probe_reuse.py']+list(prior['fingerprints'])))
    report=dict(source_commit=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
        input_report_sha256=digest(input_path.read_bytes()),fingerprints={p:digest(Path(p).read_bytes()) for p in files},
        cases=cases,records=records,archives=archives,pilot=args.pilot,
        allocation_case_indices=allocation_indices,allocation_profiles=profiles,
        modes={m:dict(inventory=c.__name__,options=o) for m,(c,o) in modes.items()},
        limitations=['No discovery policy, budget, proof, source identity or persistent record changes',
          'Lookup serializes complete source/proof/config; results admitted only after successful existing checks',
          'LRU budget is retained serialized key/result bytes, not RSS or peak temporary memory',
          'All modes generate the same database bytes; full study also matches the previous retained archive',
          'Operation time includes discovery, checking, full-key cache lookup, decoding, persistence, solving and root lifts',
          'No extra pointwise model-lift checks between timed queries: tests and previous identical archives cover small fibers without warming this cache',
          'Generation, summaries, hashing, compression, initialization and audits excluded or timed separately',
          'Cold audit starts with an empty cache and verifies every alternative, source binding and solver certificate',
          'Same 1497 inputs as prior study; this is a resource optimization, not broader structural coverage',
          'Single sequential synthetic-corpus timing; six-case traced allocation excludes native SQLite, RSS and full peak'])
    (out/'report.json').write_text(json.dumps(report,separators=(',',':'))+'\n')
    summary=[]
    for mode in modes:
        rows=[r for r in records if r['mode']==mode]
        summary.append(dict(mode=mode,total_seconds=sum(r['total_seconds'] for r in rows),
            discovery_seconds=sum(r['discovery']['seconds'] for r in rows),
            solver_seconds=sum(r['solver_seconds'] for r in rows),
            closed=sum(r['discovery']['summary']['closed'] for r in rows),
            operation_metrics=dict(sum((Counter(r['operation_metrics']) for r in rows),Counter())),
            archive=next(a for a in archives if a['mode']==mode)))
    (out/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    print(json.dumps({r['mode']:dict(total=r['total_seconds'],discovery=r['discovery_seconds']) for r in summary}),flush=True)


if __name__=='__main__':main()
