#!/usr/bin/env python3
"""Matched exact-prefix pilot of a separately versioned negative proof backend."""
from collections import Counter
from pathlib import Path
from unittest.mock import patch
import shutil
import sys
import tempfile
import time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_affine_completion as prior
from experiments.cnf_affine_completion import select
from experiments.cnf_affine_negative import NegativeStore, compose, check_composed, TABLE, CHAIN
from experiments.cnf_clause_deletion_guard import check_guard
from experiments.cnf_snapshot_replay import SnapshotResidualSolver
from experiments.validate_cnf_partition_screen import check_composed as check_native

base=prior.base;bound=prior.bound;binding=prior.binding
PARENT=Path('experiments/results/cnf-affine-completion')
FILES=('experiments/cnf_affine_negative.py','experiments/compare_cnf_affine_negative.py',
       'experiments/validate_cnf_affine_negative.py','solver/test_cnf_affine_negative.py')
SAVED=(13,33,41,45,53,57)
RECENT=(4,12,16,29,41,47,57)


def rows(s):return prior.native.rows(s)

def extension_rows(s):return dict(s.db.execute(f'SELECT id,payload FROM {TABLE} ORDER BY id'))


def contexts(tmp):
    p=base.load(PARENT/'protocol.json')
    chosen=[c for c in prior.contexts(p,tmp) if c['cohort']=='affine-target' and c['case'] in SAVED]
    trial=base.load(PARENT/'affine-0/report.json')
    def read(entry,name):
        path=tmp/name;base.restore_archive(entry,path);s=prior.native.ResidualSolver(path)
        try:return rows(s)
        finally:s.close()
    before=read(bound(p['parent'])['reference_union'],'recent-initial')
    final=read(trial['archive'],'recent-final');by_hash={base.key_sha(k):k for k in final}
    for row in bound(trial['queries']):
        if row['case'] in RECENT:
            prefix=dict(before);ids=row['ordinary_ids']+row['near_ids']
            for h in ids:
                key=by_hash[h];assert key not in prefix;prefix[key]=final[key]
            chosen.append(dict(cohort='recent',case=row['case'],before=prefix,source=row['record']['source'],
                guards=row['record']['guards'],expected_answer=row['record']['answer'],preparation_ids=ids))
        for h in row['new_ids']:
            key=by_hash[h];assert key not in before;before[key]=final[key]
    assert before==final and len(chosen)==13
    return chosen


def evaluate(s,store,source,target,guards,mode):
    started=time.perf_counter();counts=Counter();s.counts=Counter()
    with patch.object(s,'_expand',side_effect=AssertionError('Discovery search')),patch.object(s,'_store',side_effect=AssertionError('Discovery publication')):
        choice,trace=select(s,target,4,counts)
    seconds=time.perf_counter()-started;metrics=dict(s.counts)
    e=trace.get('affine_bridge')
    if mode=='negative' and e and e['status'] in ('linear-conflict','space-exhausted'):
        tick=time.perf_counter()
        with patch.object(s,'_visit',side_effect=AssertionError('Negative acquisition')),patch.object(s,'_store',side_effect=AssertionError('Native publication')):
            child=store.publish(target,e)
            composition_started=time.perf_counter();before=Counter(s.counts)
            record=compose(store,source,guards,child)
        return dict(record=record,admission=trace,local_choice=choice,child=child,probe_counts=dict(counts),
            probe_metrics=metrics,selection_seconds=seconds,child_seconds=composition_started-tick,
            composition_seconds=time.perf_counter()-composition_started,composition_metrics=dict(s.counts-before),
            evaluation_seconds=time.perf_counter()-started,extension=True)
    # Use the unchanged prior path, injecting the already-paid exact selection.
    # Its timing starts after selection, so include the measured original pass.
    with patch.object(prior,'select',return_value=(choice,trace)):
        r=prior.evaluate(s,source,target,guards,'affine',True,4)
    r['probe_counts']=dict(counts);r['probe_metrics']=metrics
    r['selection_seconds']+=seconds;r['evaluation_seconds']+=seconds;r['extension']=False
    return r


def run(out):
    out.mkdir(exist_ok=False)
    sources=dict(base.load(PARENT/'validation.json')['source_fingerprints'])
    for f,h in sources.items():assert base.sha(f)==h,f
    sources.update({f:base.sha(f) for f in FILES})
    protocol=dict(parent=binding(PARENT/'checkpoint.json'),sources=sources,
        parent_validation=binding(PARENT/'validation.json'),control_protocol=binding(PARENT/'protocol.json'),
        recent_trial=binding(PARENT/'affine-0/report.json'),saved_cases=list(SAVED),recent_cases=list(RECENT),
        orders=[['affine','negative'],['negative','affine']],free_limit=8,
        limitations=['Retrospectively selected exact-prefix pilot, not a new held-out coverage estimate.',
            'The native table and native acquisition reader are unchanged. New negative terminals require the explicit cnf-affine-negative-v1 table/checker and affine-negative-chain-v1 composition.',
            'Both arms pay previous discovery. The extension rechecks retained negative evidence before publication; no negative discovery is free.',
            'Matched per-target cold replay is timed. Full inherited-native replay is separately validated, not included in the arm timing.',
            'All previous decisions remain in the preserved checkpoint. New certificates are retained alternatives, not replacements of prior native payloads.'])
    base.write(out/'protocol.json',protocol);samples=[]
    with tempfile.TemporaryDirectory() as td:
        tmp=Path(td);tick=time.perf_counter();cases=contexts(tmp);context_seconds=time.perf_counter()-tick
        for case in cases:
            prefix=tmp/'prefix';prefix.unlink(missing_ok=True);s=prior.native.ResidualSolver(prefix)
            with s.db:s.db.executemany('INSERT INTO cnf_residual_v1 VALUES (?,?)',case['before'].items())
            s.close()
            digest=base.key_sha(base.encode(sorted(case['before'].items())))
            for repeat,order in enumerate(protocol['orders']):
                for mode in order:
                    dest=out/f"{case['cohort']}-{case['case']}-{mode}-{repeat}";dest.mkdir()
                    started=time.perf_counter();path=tmp/'arm';shutil.copyfile(prefix,path)
                    s=prior.prep.ordinary.AccountedResidualSolver(path)
                    store=NegativeStore(s,create=True) if mode=='negative' else None
                    open_seconds=time.perf_counter()-started
                    try:
                        tick=time.perf_counter();target=case['source']
                        for g in case['guards']:_,target=check_guard(s,target,g)
                        guard_seconds=time.perf_counter()-tick
                        r=evaluate(s,store,case['source'],target,case['guards'],mode)
                        assert r['record']['answer']==case['expected_answer']
                        tick=time.perf_counter()
                        with patch.object(s,'_expand',side_effect=AssertionError('Warm search')),patch.object(s,'_store',side_effect=AssertionError('Warm publication')):
                            (check_composed(store,r['record']) if r['extension'] else check_native(s,r['record']))
                        warm_seconds=time.perf_counter()-tick
                        after=rows(s);assert case['before'].items()<=after.items()
                        delta=[(k,v) for k,v in after.items() if k not in case['before']]
                        ext=extension_rows(s) if store else {}
                        storage=store.storage() if store else (0,0)
                    finally:s.close()
                    tick=time.perf_counter();s=SnapshotResidualSolver(path)
                    try:
                        coldstore=NegativeStore(s) if mode=='negative' else None
                        (check_composed(coldstore,r['record']) if r['extension'] else check_native(s,r['record']))
                        cold_metrics=dict(s.counts)
                    finally:s.close()
                    cold_seconds=time.perf_counter()-tick;tick=time.perf_counter()
                    base.write(dest/'native-delta.json',delta);base.write(dest/'extension-delta.json',ext)
                    base.write(dest/'records.json',[r['record']])
                    serialized_seconds=time.perf_counter()-tick
                    r.update(cohort=case['cohort'],case=case['case'],mode=mode,repeat=repeat,input_guards=case['guards'],input_target=target,
                        prefix_nodes=len(case['before']),prefix_digest=digest,preparation_ids=case['preparation_ids'],
                        native_delta=binding(dest/'native-delta.json'),extension_delta=binding(dest/'extension-delta.json'),
                        records=binding(dest/'records.json'),new_native_nodes=len(delta),new_native_bytes=sum(len(k)+len(v) for k,v in delta),
                        new_extension_nodes=storage[0],new_extension_bytes=storage[1],database_bytes=path.stat().st_size,
                        retained_bytes=sum((dest/f).stat().st_size for f in ('native-delta.json','extension-delta.json','records.json')),
                        open_seconds=open_seconds,guard_seconds=guard_seconds,warm_seconds=warm_seconds,
                        cold_seconds=cold_seconds,cold_metrics=cold_metrics,serialization_seconds=serialized_seconds,
                        complete_arm_seconds=time.perf_counter()-started)
                    base.write(dest/'report.json',r);samples.append(binding(dest/'report.json'))
            print(case['cohort'],case['case'],flush=True)
    base.write(out/'report.json',dict(protocol=binding(out/'protocol.json'),samples=samples,context_seconds=context_seconds))


if __name__=='__main__':run(Path(sys.argv[1]))
