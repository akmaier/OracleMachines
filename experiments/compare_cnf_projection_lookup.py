#!/usr/bin/env python3
"""Matched target discovery over the preserved unresolved development frontier."""
from collections import Counter
import hashlib
import json
from pathlib import Path
import sqlite3
import statistics
import subprocess
import sys
import tempfile
import time
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))

from experiments.cnf_projection_lookup import KernelIndex, search, kernel
from experiments.cnf_projection_bridge import projection, verify, record_key, verify_positive
from experiments.compare_cnf_projection_bridge import (restore_checkpoint as restore_base,
    routes_for, read_archive, archive_json, sha, sha_key, digests, BudgetedInventory, full, expand)
from experiments.compare_cnf_probe_continuation import unpack

BASE=Path('experiments/results/cnf-projection-bridge/report.json')
FORMAT='projection-lookup-comparison-v1'
FILES=['experiments/cnf_projection_lookup.py','experiments/compare_cnf_projection_lookup.py',
       'solver/test_cnf_projection_lookup.py','experiments/cnf_projection_bridge.py',
       'experiments/cnf_anchored_subsets.py','experiments/cnf_implied_subsumption.py']


def restore_checkpoint(report_path,path,tmp):
    r=json.loads(Path(report_path).read_text())
    if r['format']!=FORMAT or Path(r['parent']['path'])!=BASE or sha(BASE)!=r['parent']['sha256']:
        raise ValueError('Changed projection lookup parent')
    for name,digest in r['fingerprints'].items():
        if sha(name)!=digest:raise ValueError('Changed lookup implementation')
    base,*evidence=restore_base(BASE,path,tmp)
    if digests(path)!=r['logical_table_digests']:raise ValueError('Changed lookup authority')
    h=BudgetedInventory(path,**r['options']);h.set_admission_budget(0)
    try:
        bridges=read_archive(r['bridges'])
        for record in bridges:verify(h,record,Counter())
        roots=[h._canonical(c['source'],h.config['max_depth'])[2]
               for c,b in zip(r['cases'],r['final_closed'],strict=True) if b]
        verify_positive(h,read_archive(r['expanded_certificate']),roots,evidence,bridges,Counter())
        assert not h.admitted
    finally:h.close()
    return r,*evidence


def diagnostics(h,key,index):
    node=h._load(key);cnf=node['cnf'];rows=[]
    for v in range(1,min(64,len({abs(l) for c in cnf for l in c}))+1):
        counts=Counter()
        try:projected,names=projection(cnf,v,counts,64)
        except ValueError:continue
        core=kernel(projected,counts)
        if len(core)>len(cnf)+2:continue
        target_key=h._canonical(core,node['depth'])[2]
        rows.append(dict(variable=v,projected_clauses=len(projected),minimal_clauses=len(core),
            projected_support=len(names),minimal_key=target_key,
            minimal_target_present=h.db.execute('SELECT 1 FROM cnf_patterns_v1 WHERE id=?',(target_key,)).fetchone() is not None,
            raw_growth_would_reject=len(projected)>len(cnf)+2,counts=dict(counts)))
    return rows


def run(out):
    start=time.perf_counter();out.mkdir(exist_ok=False)
    r=dict(format=FORMAT,parent=dict(path=str(BASE),sha256=sha(BASE)),
        source_commit=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
        fingerprints={p:sha(p) for p in FILES},arms=[],limitations=[
        'Twenty-three adaptively selected unresolved development frontier sources plus one previously successful control; not a fresh holdout.',
        'Index and scan use the same prepared minimal-clause signatures, exact bridge checker and current-policy authority. Only target lookup differs.',
        'Three serial reversed-order repetitions share OS caches. Preparation, persisted index and cold replay are reported separately from warm search.',
        'Search tries at most 64 variables, 64 opposing pairs per variable and 64 target proposals; arbitrary signed renaming and stronger semantic implication are outside its scope.',
        'The index is a proposal cache. Missing, stale or capped candidates are inconclusive; only full checked endpoints and projection/subsumption justify a bridge.',
        'No new solving or pattern acquisition is permitted. Disk bytes are not peak RAM, and indexed lookup savings are not whole-solver speedups.'])
    with tempfile.TemporaryDirectory() as td,patch.object(BudgetedInventory,'_discover',side_effect=AssertionError('fresh recognition')):
        tmp=Path(td);history=tmp/'history';tick=time.perf_counter()
        base,*evidence=restore_base(BASE,history,tmp)
        r.update(restore_seconds=time.perf_counter()-tick,options=base['options'],cases=base['cases'],
                 baseline_closed=base['final_closed'],logical_table_digests=digests(history))
        history_hash=sha(history);h=BudgetedInventory(history,**r['options']);h.set_admission_budget(0)
        index=None
        try:
            selected=read_archive(base['next_selection'])
            sources=[x['source'] for x in selected['navigation']['ranked_sources']]
            assert len(sources)==len(set(sources))==23
            control=read_archive(base['bridges'])[0]['source'];sources.append(control)
            r['sources']=archive_json(out/'sources.json.gz',sources)
            r['source_roles']=['unresolved_frontier']*23+['known_bridge_control']
            tick=time.perf_counter();counts=Counter();index=KernelIndex(tmp/'index',h.config)
            for key, in h.db.execute('SELECT id FROM cnf_patterns_v1 ORDER BY id'):
                counts['authority_keys_scanned']+=1;index.add(key,counts)
            index.db.commit()
            r['index_build']=dict(seconds=time.perf_counter()-tick,counts=dict(counts),bytes=(tmp/'index').stat().st_size,
                entries=index.db.execute('SELECT COUNT(*) FROM targets').fetchone()[0],
                signatures=index.db.execute('SELECT COUNT(DISTINCT kernel) FROM targets').fetchone()[0])
            print(json.dumps(dict(stage='index',**{k:v for k,v in r['index_build'].items() if k!='counts'})),flush=True)
            tick=time.perf_counter()
            for key in sources:assert h._load(key) is not None
            r['source_validation_seconds']=time.perf_counter()-tick
            all_records=None
            for repeat,order in enumerate((('scan','indexed'),('indexed','scan'),('scan','indexed'))):
                for mode in order:
                    rows=[];tick=time.perf_counter()
                    for key in sources:
                        counts=Counter();q=time.perf_counter();records=search(h,key,index,counts,mode=mode)
                        rows.append(dict(source_sha256=sha_key(key),seconds=time.perf_counter()-q,counts=dict(counts),records=records))
                    seconds=time.perf_counter()-tick
                    logical=[[record_key(x) for x in row['records']] for row in rows]
                    if all_records is None:all_records=logical
                    else:assert all_records==logical
                    bound=archive_json(out/f'{repeat}-{mode}.json.gz',rows)
                    r['arms'].append(dict(mode=mode,repeat=repeat,seconds=seconds,results=bound))
                    print(json.dumps(dict(stage='query',mode=mode,repeat=repeat,seconds=seconds,bridges=sum(map(len,logical)))),flush=True)
            index.db.commit();index.close();index=None
            # Persist exact compressed keys and signatures; no rowid dependency.
            import gzip
            with (tmp/'index').open('rb') as source,gzip.GzipFile(filename='',mode='wb',fileobj=(out/'index.sqlite3.gz').open('wb'),mtime=0) as target:
                while data:=source.read(1024*1024):target.write(data)
            r['index']=dict(path=str(out/'index.sqlite3.gz'),sha256=sha(out/'index.sqlite3.gz'),
                database_sha256=sha(tmp/'index'),database_bytes=(tmp/'index').stat().st_size,
                compressed_bytes=(out/'index.sqlite3.gz').stat().st_size)
            tick=time.perf_counter();unpack(r['index']['path'],tmp/'cold-index',r['index']['database_sha256'])
            cold_index=KernelIndex(tmp/'cold-index',h.config)
            try:
                cold=[[record_key(x) for x in search(h,key,cold_index,Counter())] for key in sources]
                assert cold==all_records
                r['selected_diagnostics']=archive_json(out/'selected-diagnostics.json.gz',diagnostics(h,selected['source'],cold_index))
            finally:cold_index.close()
            r['index_reopen_and_search_seconds']=time.perf_counter()-tick
            rows=read_archive(r['arms'][0]['results']);discovered={record_key(x):x for row in rows for x in row['records']}
            previous=read_archive(base['bridges']);merged={record_key(x):x for x in previous};novel=[x for ident,x in discovered.items() if ident not in merged]
            merged.update(discovered);bridges=list(merged.values())
            r['discovered_bridges']=archive_json(out/'discovered-bridges.json.gz',list(discovered.values()))
            r['bridges']=archive_json(out/'bridges.json.gz',bridges);r['novel_bridges']=len(novel)
            tick=time.perf_counter();routes=routes_for(h,evidence,bridges)
            roots=[h._canonical(c['source'],h.config['max_depth'])[2] for c in r['cases']]
            closed,plans,counts=full(h,roots,routes)
            r.update(global_coverage_seconds=time.perf_counter()-tick,final_closed=closed[0],without_growth_closed=closed[1],
                     global_counts=counts,evidence_counts=list(map(len,evidence)))
            assert not any(a and not b for a,b in zip(r['baseline_closed'],closed[0],strict=True))
            r['gains']=[i for i,(a,b) in enumerate(zip(r['baseline_closed'],closed[0],strict=True)) if b and not a]
            positive=expand(h,plans[0],plans[0]['roots'],routes,Counter())
            verify_positive(h,positive,plans[0]['roots'],evidence,bridges,Counter())
            r['expanded_certificate']=archive_json(out/'expanded-coverage.json.gz',positive)
            assert not h.admitted
        finally:
            if index is not None:index.close()
            h.close()
        assert sha(history)==history_hash and digests(history)==r['logical_table_digests']
        r.update(authority_unchanged=True,admitted=0,matching_modes_and_repeats=True)
    r['pipeline_seconds']=time.perf_counter()-start
    (out/'report.json').write_text(encode_json(r))
    print(json.dumps(dict(stage='done',covered=sum(r['final_closed']),novel_bridges=r['novel_bridges'],seconds=r['pipeline_seconds'])),flush=True)


def encode_json(value):return json.dumps(value,indent=2,sort_keys=True)+'\n'


if __name__=='__main__':run(Path(sys.argv[1]))
