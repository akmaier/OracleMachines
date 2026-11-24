#!/usr/bin/env python3
"""Census unfinished-origin supports, then compare two exposed cold edits."""
from collections import Counter
from pathlib import Path
from functools import partial
from unittest.mock import patch
import json, shutil, sqlite3, subprocess, sys, tempfile, time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_probe_binary_lazy as previous
from experiments.cnf_stopped_observer import StoppedObserver
from experiments.cnf_stopped_support import extract,make_open_plan
from experiments.cnf_partial_proof_plan import survival,recompose
from experiments.cnf_conditional_unit_support import materialize
from experiments.cnf_fresh_mixtures import attempt
from experiments.cnf_snapshot_replay import SnapshotResidualSolver
from experiments.cnf_canonical_verify import CanonicalVerifySnapshot
from experiments.cnf_archive_parts import restore_archive
from experiments import cnf_residual_dag as native
base,binding,bound=previous.base,previous.binding,previous.bound
PARENT=Path('experiments/results/cnf-probe-binary-lazy')
FILES=('experiments/cnf_stopped_observer.py','experiments/cnf_stopped_support.py',
       'solver/test_cnf_stopped_support.py','experiments/study_cnf_stopped_origins.py')
ORIGINS=(0,3,27,36,39,60,63,66)
TARGETS=(28,64)
MODES=('native','plan')
FACTORY=partial(previous.CLASSES['lazy'])


def tables(con):
    present={n for n, in con.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    return {t:dict(con.execute(f'SELECT id,payload FROM {t}')) if t in present else {} for t in previous.ALL_TABLES}


def prepare(out):
    assert not (out/'protocol.json').exists()
    parent=base.load(PARENT/'checkpoint.json')
    for f,h in parent['source_fingerprints'].items():assert base.sha(f)==h,f
    p=bound(parent['probe_binary_lazy']['protocol'])
    base.write(out/'protocol.json',dict(parent=binding(PARENT/'checkpoint.json'),
        parent_manifest=binding(PARENT/'manifest.json'),cases=p['cases']['holdout'],
        expected=binding(PARENT/'holdout-lazy-0/queries.json'),origins=list(ORIGINS),targets=list(TARGETS),
        orders=[list(MODES),list(reversed(MODES))]*2,node_limit=256,plan_node_limit=129,
        source_fingerprints={**parent['source_fingerprints'],**{f:base.sha(f) for f in FILES}},
        limitations=[
            'All inputs are exposed 132/156 cases from the preceding study. No fresh performance or population claim; no outcome filtering of the eight selected origins.',
            'Capture observes the seven initially unfinished base queries and completed-origin control 27. Exact original search metrics and all final six-table payloads must remain unchanged.',
            'Only retained negative endpoints can support extraction. A budget stop may discard the final pending batch; such candidates are recorded as unretained and provide no authority.',
            'Independent full-source unit propagation under captured branch guards derives conditional templates. Unsupported coordinate transitions or non-unit consequences remain misses.',
            'A 129-node tree routes every assignment to a checked conditional leaf or an explicitly open leaf. Ordering is first-compatible-template, not a minimum cover.',
            'Capture limits bound candidates, serialized key bytes and pending literal/context slots. Active search frames, source size, Python overhead and construction transients are not a process-memory cap.',
            'Cold diagnostics provision origins 27 and 63 explicitly, then compare native search with the plan on edits 28 and 64. Automatic origin recognition and fresh generalization are not established.',
            'Both arms restore the identical causal prefix into a new solver; neither sees later repeat results. Source capture/extraction are recorded separately and charged explicitly in the total-cost comparison.',
            'Native budget 256 does not bound discovery, extraction, proof checking or publication. Conditional materialization is separately persisted and never seeded into the census search.']))


def census(out):
    p=base.load(out/'protocol.json');cases=bound(p['cases']);expected=bound(p['expected'])
    for f,h in p['source_fingerprints'].items():assert base.sha(f)==h,f
    began=time.perf_counter();rows=[];reports=[]
    with tempfile.TemporaryDirectory() as td:
        path=Path(td)/'search';bankpath=Path(td)/'conditional'
        s=StoppedObserver(path,node_limit=256,handoff_bytes=2*1024*1024)
        bank=native.ResidualSolver(bankpath)
        try:
            for c,old in zip(cases,expected):
                s.observe=c['case'] in p['origins'];tick=time.perf_counter();r=attempt(s,c['source'])
                elapsed=time.perf_counter()-tick
                assert (r['status'],r['metrics'])==(old['status'],old['metrics']),(c['case'],'changed search')
                rows.append(dict(case=c['case'],**r))
                if not s.observe:continue
                target=cases[c['case']+1];dest=out/f"origin-{c['case']}";dest.mkdir()
                capture=s.capture;s.capture=None
                source=tuple(map(tuple,capture['source']))
                left,names=native.normalize(c['source']);right,right_names=native.normalize(target['source'])
                assert left==source and names==right_names
                tick=time.perf_counter();reader=SnapshotResidualSolver(path);counts=Counter()
                try:extracted=extract(source,capture['candidates'],reader,counts)
                finally:reader.close()
                extraction_seconds=time.perf_counter()-tick
                tick=time.perf_counter();plan=make_open_plan(extracted['templates'],node_limit=p['plan_node_limit'],counts=counts)
                intact=survival(right,plan,counts);plan_seconds=time.perf_counter()-tick
                tick=time.perf_counter();materialized=[];members=set(right)
                with patch.object(bank,'_expand',side_effect=AssertionError('Materialization acquired a result')):
                    for i,t in enumerate(extracted['templates']):
                        if set(map(tuple,t['clauses']))<=members:
                            result=materialize(bank,right,t,counts=counts)
                            materialized.append(dict(template=i,**result))
                materialization_seconds=time.perf_counter()-tick
                tick=time.perf_counter()
                base.write(dest/'capture.json',capture);base.write(dest/'extraction.json',extracted)
                base.write(dest/'plan.json',plan);base.write(dest/'materialized.json',materialized)
                serialization_seconds=time.perf_counter()-tick
                archive=base.archive(path,dest)
                report=dict(origin=c['case'],target=target['case'],status=r['status'],
                    capture=binding(dest/'capture.json'),extraction=binding(dest/'extraction.json'),plan=binding(dest/'plan.json'),
                    materialized=binding(dest/'materialized.json'),prefix_archive=archive,counts=dict(counts),
                    origin_attempt_seconds=elapsed,extraction_seconds=extraction_seconds,plan_seconds=plan_seconds,
                    materialization_seconds=materialization_seconds,serialization_seconds=serialization_seconds,
                    template_count=len(extracted['templates']),plan_templates=len(plan['templates']),
                    surviving_plan_templates=sum(intact),open_plan_templates=sum(t.get('open') is True for t in plan['templates']),
                    endpoint_kinds=dict(Counter(x['kind'] for x in extracted['observations'])))
                base.write(dest/'report.json',report);reports.append(binding(dest/'report.json'))
                print('captured',c['case'],r['status'],len(capture['candidates']),len(extracted['templates']),sum(intact),flush=True)
            final=tables(s.db)
        finally:s.close();bank.close()
        reference=Path(td)/'reference';restore_archive(base.load(PARENT/'holdout-lazy-0/report.json')['archive'],reference)
        con=sqlite3.connect(reference)
        try:assert tables(con)==final
        finally:con.close()
        (out/'search').mkdir();search_archive=base.archive(path,out/'search')
        (out/'conditional').mkdir();conditional_archive=base.archive(bankpath,out/'conditional')
    base.write(out/'census-queries.json',rows)
    base.write(out/'census.json',dict(protocol=binding(out/'protocol.json'),origins=reports,
        queries=binding(out/'census-queries.json'),search_archive=search_archive,conditional_archive=conditional_archive,
        exact_original_payloads=True,seconds=time.perf_counter()-began))


def trial(out,root,target,mode):
    p=base.load(root/'protocol.json');cases=bound(p['cases']);origin=base.load(root/f'origin-{target-1}/report.json')
    for f,h in p['source_fingerprints'].items():assert base.sha(f)==h,f
    out.mkdir();began=time.perf_counter()
    with tempfile.TemporaryDirectory() as td:
        path=Path(td)/'db';tick=time.perf_counter();restore_archive(origin['prefix_archive'],path)
        restore_seconds=time.perf_counter()-tick
        tick=time.perf_counter();s=FACTORY(path,node_limit=256);setup_seconds=time.perf_counter()-tick
        initial=tables(s.db);source=cases[target]['source'];canonical,names=native.normalize(source)
        try:
            tick=time.perf_counter()
            if mode=='native':r=attempt(s,source);outcome=None
            else:
                counts=Counter();outcome=recompose(s,canonical,bound(origin['plan']),256,counts)
                node=None if outcome['stopped'] else s._read(outcome['root'])
                r=dict(status='unresolved' if node is None else ('sat' if node['answer'] else 'unsat'),
                    metrics=dict(s.counts),extra_counts=dict(counts),result=node)
                if node is not None and node['answer']:
                    assert native.holds(source,dict(zip(names,node['model'])))
            solve_seconds=time.perf_counter()-tick
            final=tables(s.db)
        finally:s.close()
        tick=time.perf_counter();reader=CanonicalVerifySnapshot(path)
        try:
            for key in final[previous.ALL_TABLES[0]]:assert reader._read(key) is not None
        finally:reader.close()
        cold_seconds=time.perf_counter()-tick
        base.write(out/'result.json',dict(result=r,outcome=outcome))
        archive=base.archive(path,out)
    base.write(out/'report.json',dict(protocol=binding(root/'protocol.json'),origin=target-1,target=target,mode=mode,
        restore_seconds=restore_seconds,setup_seconds=setup_seconds,solve_seconds=solve_seconds,
        cold_seconds=cold_seconds,complete_seconds=time.perf_counter()-began,
        added={t:len(final[t].keys()-initial[t].keys()) for t in previous.ALL_TABLES},
        digest={t:base.key_sha(base.encode(sorted(rows.items()))) for t,rows in final.items()},
        archive=archive,result=binding(out/'result.json')))


def run(out):
    p=base.load(out/'protocol.json');samples=[]
    for target in p['targets']:
        for repeat,order in enumerate(p['orders']):
            for mode in order:
                dest=out/f'target-{target}-{mode}-{repeat}'
                subprocess.run([sys.executable,__file__,'trial',str(dest),str(out),str(target),mode],check=True)
                samples.append(dict(target=target,mode=mode,repeat=repeat,**binding(dest/'report.json')))
                print('finished',target,repeat,mode,flush=True)
    base.write(out/'trials.json',dict(protocol=binding(out/'protocol.json'),samples=samples))


if __name__=='__main__':
    action=sys.argv[1];out=Path(sys.argv[2])
    if action=='prepare':prepare(out)
    elif action=='census':census(out)
    elif action=='trial':trial(out,Path(sys.argv[3]),int(sys.argv[4]),sys.argv[5])
    elif action=='run':run(out)
