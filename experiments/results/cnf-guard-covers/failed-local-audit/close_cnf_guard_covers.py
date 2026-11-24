#!/usr/bin/env python3
"""Independently bind and compile every distinct candidate local wide cover."""
from collections import Counter
from pathlib import Path
import sys
import tempfile
import time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_guard_covers as study
from experiments import cnf_residual_dag as native
from experiments.cnf_guard_clause_cover import discover,compile_cover
from experiments.cnf_guard_interactions import local_hints
from experiments.cnf_guard_probe_census import decode_key
from experiments.cnf_probe_binary_lazy_solver import LazyBinaryClosureSolver
from experiments.cnf_canonical_verify import CanonicalVerifySnapshot
from experiments.cnf_fresh_mixtures import attempt
from experiments.cnf_archive_parts import restore_archive
base=study.base;old=study.old


def run(out):
    p=base.load(out/'protocol.json');comparison=base.load(out/'comparisons.json');cases=old.bound(p['cases'])
    protocol=dict(comparisons=old.binding(out/'comparisons.json'),source=old.binding(Path(__file__)),
        selection='All candidate covers in repetition zero, including sites later closed by the old gate; deduplicate compilation only by exact local root after complete support checks.',
        limitations=['Full local CNFs, empty native stores and provisioned source templates. This offline follow-up changes neither query path nor whole-query verdict.',
            'One alternating cold pair per distinct supported local root; source binding/transport is timed separately. Earlier origin acquisition, census, serialization and final auditing remain additional.',
            'Ordinary comparison retains the 256-dispatch cap. Native compiled proof nodes are outside that cap. Do not infer equal total work budgets or whole-query speedups.',
            'Each proof and ordinary-search archive is preserved separately; earlier cumulative authority is unchanged. Root duplicates reuse the already checked local follow-up, not a general pattern match.'])
    base.write(out/'closures-protocol.json',protocol);records=[];seen={};census_counts=Counter();expanded=[];began=time.perf_counter()
    for sample in comparison['samples']:
        if sample['mode']!='census' or sample['repeat']!=0:continue
        report=old.bound(sample);events=old.bound(report['events'])['events'];target=sample['target']
        origin=old.bound(p['inputs'][p['targets'].index(target)]);templates=old.bound(origin['extraction'])['templates']
        source=native.normalize(cases[target]['source'])[0]
        tick=time.perf_counter();present={}
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/'query';restore_archive(report['archive'],path);reader=CanonicalVerifySnapshot(path)
            try:
                for event in events:
                    if event['cover'] is None or event['root'] in present:continue
                    node=reader._read(event['root'])
                    assert node is None or node['answer'] is False
                    present[event['root']]=node is not None
            finally:reader.close()
        query_presence_seconds=time.perf_counter()-tick
        for index,event in enumerate(events):
            local=decode_key(event['root']);counts=Counter()
            cover=discover(local,event['graph'],dict(event['model']),counts,**p['discovery'])
            assert cover==event['cover'] and dict(counts)==event['counts'];census_counts.update(counts)
            if cover is None:
                tick=time.perf_counter();ec=Counter();variables={abs(l) for cl in event['graph'] for l in cl}
                bounds={**p['discovery'],'root_limit':max(1,2*len(variables)),
                        'edge_limit':max(1,4*len(variables)*len(event['graph']))}
                candidate=discover(local,event['graph'],dict(event['model']),ec,**bounds)
                expanded.append(dict(target=target,event=index,cover=candidate,counts=dict(ec),
                    bounds=bounds,seconds=time.perf_counter()-tick))
                continue
            tick=time.perf_counter();checks=Counter()
            bound,hints,whole=local_hints(source,templates,event,checks);assert bound==local
            original={cl for cl in local if len(cl)<=2};bank={tuple(h['clause']):h for h in hints}
            used={tuple(event['graph'][cid]) for path in cover['paths'] for _,cid in path}
            missing=sorted(used-original-bank.keys())
            row=dict(target=target,event=index,root=event['root'],cover=cover,site_closed=event['site_closed'],
                whole_residual=whole,present_after_native_query=present[event['root']],
                query_presence_seconds=query_presence_seconds,missing_support=missing,support_counts=dict(checks),
                support_seconds=time.perf_counter()-tick,event_archive=report['events'])
            if missing:row['status']='unsupported';records.append(row);continue
            if event['root'] in seen:
                row.update(status='duplicate',reuses=seen[event['root']]);records.append(row);continue
            needed=[bank[cl] for cl in sorted(used-original)];arms={}
            for mode in ('fresh','cover') if len(seen)%2==0 else ('cover','fresh'):
                dest=out/f'closure-{target}-{index}-{mode}';dest.mkdir()
                with tempfile.TemporaryDirectory() as td:
                    path=Path(td)/'db';tick=time.perf_counter()
                    s=native.ResidualSolver(path) if mode=='cover' else LazyBinaryClosureSolver(path,node_limit=p['node_limit'])
                    setup=time.perf_counter()-tick;c=Counter()
                    try:
                        tick=time.perf_counter()
                        if mode=='cover':
                            root=compile_cover(s,local,needed,event['graph'],cover,c,**{k:p['discovery'][k] for k in ('width_limit','path_limit')});status='unsat'
                        else:
                            result=attempt(s,local);status=result['status'];root=None if result['result'] is None else result['result']['root']
                        elapsed=time.perf_counter()-tick;assert status in ('unsat','unresolved')
                        if root is not None:assert root==event['root'] and not s._read(root)['answer']
                        saved=list(s.db.execute('SELECT id,payload FROM cnf_residual_v1 ORDER BY id'))
                        nc=dict(s.counts);tick=time.perf_counter()
                        for key,_ in saved:assert s._read(key) is not None
                        warm=time.perf_counter()-tick
                    finally:s.close()
                    readers={}
                    for cls in (native.ResidualSolver,CanonicalVerifySnapshot):
                        tick=time.perf_counter();reader=cls(path)
                        try:
                            for key,_ in saved:assert reader._read(key) is not None
                        finally:reader.close()
                        readers[cls.__name__]=time.perf_counter()-tick
                    tick=time.perf_counter();archive=base.archive(path,dest);persistence=time.perf_counter()-tick
                result=dict(status=status,root=root,setup_seconds=setup,solve_seconds=elapsed,warm_seconds=warm,
                    native_counts=nc,composition_counts=dict(c),nodes=len(saved),
                    record_bytes=sum(len(k.encode())+len(v.encode()) for k,v in saved),
                    cold_readers_seconds=readers,persistence_seconds=persistence,archive=archive)
                base.write(dest/'report.json',result);arms[mode]=old.binding(dest/'report.json')
            row.update(status='compiled',arms=arms,selected_hints=len(needed))
            seen[event['root']]=dict(target=target,event=index);records.append(row)
        print('followed target',target,'candidate records',len(records),'compiled roots',len(seen),flush=True)
    base.write(out/'closures.json',dict(protocol=old.binding(out/'closures-protocol.json'),records=records,
        census_counts=dict(census_counts),expanded_discovery=expanded,
        expanded_discovery_limitation='Adaptive offline diagnostic on bounded misses: relax root/edge limits to cover all graph roots and traversals, retain width 8 and path length 256. Extra proposals are not support-checked or compiled here; no live policy or absence guarantee beyond the retained bounds.',complete_seconds=time.perf_counter()-began))


if __name__=='__main__':run(Path(sys.argv[1]))
