#!/usr/bin/env python3
"""Frozen routing comparison with identical persistent branch states."""
from copy import deepcopy
from collections import Counter
from functools import partial
from pathlib import Path
from unittest.mock import patch
import random,sqlite3,subprocess,sys,tempfile,time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_cofactor_handoff as previous
from experiments import cnf_targeted_backbone as targeted
from experiments.cnf_ranked_binary_targets import discover
from experiments.cnf_binary_routing import priority_expand
from experiments.cnf_bipolar_routing import bipolar_expand
from experiments import cnf_residual_dag as native
from experiments.cnf_cofactor_handoff import CofactorHandoffSolver,handoff_expand,handoff_propagate
from experiments.cnf_probed_partition import run as probed
from experiments.cnf_partition_preparation import run as prepared_run
from experiments.cnf_residual_dag import normalize,token
base=previous.base;binding=previous.binding;bound=previous.bound
TABLES=previous.TABLES;read_zip=previous.read_zip;write_zip=previous.write_zip;restore=previous.restore;tables=previous.tables
PARENT=Path('experiments/results/cnf-cofactor-handoff');MODES=('binary1','binary-prepared','handoff','handoff-prepared')
harness=previous.harness

def native_split(split):return split.startswith('polarity-')
FILES=('experiments/cnf_partition_preparation.py','experiments/compare_cnf_partition_preparation.py','solver/test_cnf_partition_preparation.py')


def branch_seed(spec):
    report=bound(spec['trial_report']);delta=read_zip(report['delta']);prefix=read_zip(spec['prefix'])
    keys=set(spec['extra_ids']);extra={t:[[k,v] for k,v in delta[t] if t==TABLES[0] and k in keys] for t in TABLES}
    assert len(extra[TABLES[0]])==spec['extra_count']
    return {t:prefix[t]+extra[t] for t in TABLES}


def prepare(out):
    assert out.is_dir() and not (out/'protocol.json').exists();began=time.perf_counter()
    parent=base.load(PARENT/'checkpoint.json');old=base.load(PARENT/'protocol.json');oldcases=bound(old['cases'])
    for f,h in parent['source_fingerprints'].items():assert base.sha(f)==h,f
    cases=[dict(deepcopy(c),split='controls') for c in oldcases if c['split']=='novel']
    prefixes={i:deepcopy(old['prefixes'][i]) for i in ('25','31','61')}
    with tempfile.TemporaryDirectory() as td:
        path=Path(td)/'union';base.restore_archive(parent['reference_union'],path);con=sqlite3.connect(path)
        try:known={k for t in TABLES for k, in con.execute(f'SELECT id FROM {t}')}
        finally:con.close()
    for index in (25,31,61):
        original=next(c for c in oldcases if (c['split'],c['case'],c['variant'])==('novel',index,'delete'))
        rng=random.Random(202611230132+index);deleted=rng.sample(range(len(original['source'])),2)
        for i,cid in enumerate(deleted):
            source=[c for j,c in enumerate(original['source']) if j!=cid];added=None
            if i:
                added=sorted(v*(1 if rng.randrange(2) else -1) for v in rng.sample(original['candidate']['target_names'],3))
                assert added not in source;source.append(added)
            cnf,names=normalize(source);root=token(cnf,Counter());assert root not in known
            candidate=deepcopy(original['candidate']);candidate.update(target=[list(c) for c in cnf],target_names=list(names))
            cases.append(dict(split='novel',case=index,variant='delete' if not i else 'replace',source=harness.target_source(candidate),
                candidate=candidate,root=root,deleted_clause=original['source'][cid],added_clause=added))
    assert len(cases)==12 and len({c['root'] for c in cases})==12
    for c in cases:
        prefix=prefixes[c['split'] if native_split(c['split']) else str(c['case'])]
        assert all(c['root'] not in dict(read_zip(prefix['archive'])[t]) for t in TABLES)
    base.write(out/'cases.json',cases)
    base.write(out/'protocol.json',dict(parent=binding(PARENT/'checkpoint.json'),parent_manifest=binding(PARENT/'manifest.json'),
        cases=binding(out/'cases.json'),prefixes=prefixes,node_limit=256,handoff_bytes=256*1024,
        orders=[list(MODES),list(reversed(MODES))],source_fingerprints={**parent['source_fingerprints'],**{f:base.sha(f) for f in FILES}},
        preparation_seconds=time.perf_counter()-began,limitations=[
        'Frozen paired ablations: binary-frequency routing with/without shared partition preparation; cofactor-handoff routing with/without the same preparation. Two opposite serial orders. Native search, probe budgets, branch order and independent proof/sidecar checkers remain unchanged.',
        'The optional acquisition path prepares one immutable source, ordered missing-clause list and six-or-fewer first-false branches. Prefix tuples share immutable clauses. Premise publication consumes validated clause data without constructing unused branches; sidecar creation reuses the prepared model-lifting data.',
        'The unchanged independent sidecar checker reconstructs the partition and rechecks exact source, premise, child roots, status and models. Preparation grants no authority, is never persisted, and this acquisition path supports no guard chain.',
        'Preparation snapshots, validation, construction, conservative sizing and disposal are charged. The optional descriptor has no fixed byte cap: its retained graph grows with source and branch output sizes. Its graph audit excludes transient preparation and whole-process memory. Existing cofactor offers retain their256KiB cap.',
        'Six preceding novel edits are controls; six fixed-seed nearby edits are absent from the preceding union. Identical appropriate cold prefixes are restored. Candidates/maps and prior acquisition remain supplied/sunk. This is not a broad external holdout or new whole-source coverage.',
        'A shared256 ordinary-expansion budget excludes direct probes, checking and publication. Exact native payloads, models, decisions, partitions and expansions must match each prepared arm to its unprepared parent.',
        'Serial timing precedes profiles, tests and cumulative audits. Complete worker time includes restore, checking, warm reuse, persistence and cold reconstruction; it is not production query latency.',
        'Retain regressions and all raw observations. Sharing exact preparation adds no tractable category, general efficiency guarantee or Lean refinement theorem.']))




def worker(out,p,split,index,mode):
    def dispatch(s,c,unused,budget):
        fn=prepared_run if mode.endswith('-prepared') else probed
        if not mode.startswith('handoff'):return fn(s,c['candidate'],'probe6',budget)
        began=time.perf_counter()
        with s.handoff_session():r=fn(s,c['candidate'],'probe6',budget)
        r['cofactor_handoff']=dict(s.handoff_summary,capacity=s.handoff_bytes)
        r['seconds']=time.perf_counter()-began
        return r
    with patch.object(harness,'query',dispatch):
        if mode.startswith('binary'):
            with patch.object(targeted,'inspect_targeted_backbone',partial(discover,policy='binary1')):harness.worker(out,p,split,index,mode)
        else:
            with patch.object(targeted.TargetedBackboneMixin,'_expand',handoff_expand),patch.object(native,'propagate',handoff_propagate),patch.object(harness,'InputSafeAffineProbeSolver',CofactorHandoffSolver):
                harness.worker(out,p,split,index,mode)



def run(out):
    p=base.load(out/'protocol.json');samples=[]
    for split,index in dict.fromkeys((c['split'],c['case']) for c in bound(p['cases'])):
        for repeat,order in enumerate(p['orders']):
            for mode in order:
                dest=out/f'{split}-{index}-{mode}-{repeat}'
                subprocess.run([sys.executable,__file__,'worker',str(dest),str(out/'protocol.json'),split,str(index),mode],check=True)
                samples.append(dict(split=split,case=index,mode=mode,repeat=repeat,**binding(dest/'report.json')))
            print('finished',split,index,repeat,flush=True)
    base.write(out/'report.json',dict(protocol=binding(out/'protocol.json'),samples=samples))


if __name__=='__main__':
    if sys.argv[1]=='prepare':prepare(Path(sys.argv[2]))
    elif sys.argv[1]=='worker':worker(Path(sys.argv[2]),base.load(sys.argv[3]),sys.argv[4],int(sys.argv[5]),sys.argv[6])
    else:run(Path(sys.argv[1]))
