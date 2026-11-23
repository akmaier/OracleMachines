#!/usr/bin/env python3
"""Freeze direct joint-prefix reuse against the preceding fused-preimage policy."""
from collections import Counter
from contextlib import nullcontext
from copy import deepcopy
from pathlib import Path
from unittest.mock import patch
import random,sqlite3,subprocess,sys,tempfile,time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_preimage_fusion as previous
from experiments.cnf_consequence_priority import ConsequencePrioritySolver
from experiments.cnf_preimage_fusion import fused_preimages
from experiments.cnf_joint_prefix import reused_joint_prefix
from experiments.cnf_partition_preparation import run as prepared_run
base=previous.base;binding=previous.binding;bound=previous.bound;TABLES=previous.TABLES
read_zip=previous.read_zip;write_zip=previous.write_zip;restore=previous.restore;tables=previous.tables;harness=previous.harness
normalize=previous.normalize;token=previous.token;native_split=previous.native_split
PARENT=Path('experiments/results/cnf-preimage-fusion');MODES=('fused','prefix')
FILES=('experiments/probe_cnf_joint_prefix.py','experiments/cnf_joint_prefix.py','experiments/compare_cnf_joint_prefix.py','solver/test_cnf_joint_prefix.py')


def branch_seed(spec):
    prefix=read_zip(spec['prefix']);delta=read_zip(bound(spec['trial'])['delta'])
    extra={t:[[k,v] for k,v in delta[t] if k in set(spec['extra_ids'][t])] for t in TABLES}
    for t in TABLES:assert len(extra[t])==len(spec['extra_ids'][t])
    return {t:prefix[t]+extra[t] for t in TABLES}


def prepare(out):
    assert not (out/'protocol.json').exists();began=time.perf_counter()
    parent=base.load(PARENT/'checkpoint.json');old=base.load(PARENT/'protocol.json');oldcases=bound(old['cases'])
    for f,h in parent['source_fingerprints'].items():assert base.sha(f)==h,f
    cases=[dict(deepcopy(c),split='controls') for c in oldcases if c['split']=='novel'];prefixes={i:deepcopy(old['prefixes'][i]) for i in ('25','31','61')}
    observation=next(o for o in base.load(PARENT/'next-target.json')['observations'] if o['split']=='novel')
    spec=dict(observation['acquisitions'][2],trial=observation['trial']);branch=write_zip(out/'branch-prefix.json.gz',branch_seed(spec))
    freq=Counter(abs(l) for c in spec['source'] for l in c);raw=min(freq,key=lambda v:(-freq[v],v))
    for label,flips in (('original',set()),('flip',{raw}),('complement',set(freq))):
        split='branch-'+label;source=[[-l if abs(l) in flips else l for l in c] for c in spec['source']];cnf,_=normalize(source)
        cases.append(dict(split=split,case=31,variant=label,source=source,root=token(cnf,Counter()),flipped_variables=sorted(flips)))
        prefixes[split]=dict(archive=branch)
    with tempfile.TemporaryDirectory() as td:
        path=Path(td)/'union';base.restore_archive(parent['reference_union'],path);con=sqlite3.connect(path)
        try:known={k for t in TABLES for k, in con.execute(f'SELECT id FROM {t}')}
        finally:con.close()
    for index in (25,31,61):
        original=next(c for c in oldcases if (c['split'],c['case'],c['variant'])==('novel',index,'delete'))
        rng=random.Random(202611230737+index)
        for i,cid in enumerate(rng.sample(range(len(original['source'])),2)):
            source=[c for j,c in enumerate(original['source']) if j!=cid];added=None
            if i:
                added=sorted(v*(1 if rng.randrange(2) else -1) for v in rng.sample(original['candidate']['target_names'],3));assert added not in source;source.append(added)
            cnf,names=normalize(source);root=token(cnf,Counter());assert root not in known
            candidate=deepcopy(original['candidate']);candidate.update(target=[list(c) for c in cnf],target_names=list(names))
            cases.append(dict(split='novel',case=index,variant='delete' if not i else 'replace',source=harness.target_source(candidate),candidate=candidate,root=root,deleted_clause=original['source'][cid],added_clause=added))
    assert len(cases)==15 and len({c['root'] for c in cases})==15
    for c in cases:
        prefix=prefixes[c['split'] if native_split(c['split']) else str(c['case'])]
        assert all(c['root'] not in dict(read_zip(prefix['archive'])[t]) for t in TABLES)
    base.write(out/'cases.json',cases)
    base.write(out/'protocol.json',dict(parent=binding(PARENT/'checkpoint.json'),parent_manifest=binding(PARENT/'manifest.json'),
        cases=binding(out/'cases.json'),prefixes=prefixes,node_limit=256,branch_limit=spec['budget'],branch_spec=spec,flipped_raw_variable=raw,
        exploration=binding(out/'exploration.json'),orders=[list(MODES),list(reversed(MODES))],
        source_fingerprints={**parent['source_fingerprints'],**{f:base.sha(f) for f in FILES}},preparation_seconds=time.perf_counter()-began,
        limitations=[
        'Only backward construction of the first surviving cofactor changes in a batch of exactly two checked consequences. Its immutable normalized CNF, original-name map and complete key are already live in the forward-lookup frame.',
        'No extra CNF, source-indexed memo, cross-call cache or proof authority is introduced. Cached-prefix priority, single paths, model lifting and every native check remain unchanged. The two-path bound is essential.',
        'Six preceding edits become controls; three sign variants expose the saved nine-expansion source with three earlier native IDs and remaining247 budget. Six fixed-seed nearby edits have roots absent from the preceding union. Warm pools require preceding-stream replay.',
        'Fifteen targets, two modes and two opposite serial orders give60 attempts in36 workers. Both arms use consequence-priority routing, fused preimages and shared partition preparation with restart. Mode setup/removal is charged.',
        'All native deltas and partition sidecars must remain identical between arms. Count savings do not prove wall-time attribution. Retain regressions, checking, persistence, cold replay and endpoint-space costs. Prior acquisition and supplied donors/maps remain sunk.',
        'The exact source/assignment census is exposed and produces no extra proof. No default change, external benchmark, new coverage cell, Lean refinement theorem or uniformly polynomial arbitrary-SAT claim.']))


def worker(out,p,split,index,mode):
    original=harness.query
    def dispatch(s,c,unused,budget):
        return original(s,c,'native',min(budget,p['branch_limit'])) if native_split(split) else prepared_run(s,c['candidate'],'probe6',budget)
    p=deepcopy(p)
    if native_split(split):p['prefixes'][str(index)]=p['prefixes'][split]
    with patch.object(harness,'query',dispatch),patch.object(harness,'InputSafeAffineProbeSolver',ConsequencePrioritySolver):
        tick=time.perf_counter()
        with fused_preimages(),reused_joint_prefix() if mode=='prefix' else nullcontext():
            setup=time.perf_counter()-tick;harness.worker(out,p,split,index,mode);tick=time.perf_counter()
        teardown=time.perf_counter()-tick
    report=base.load(out/'report.json');report['summary']['joint_prefix_mode_setup_seconds']=setup+teardown
    report['summary']['complete_worker_seconds']+=setup+teardown;base.write(out/'report.json',report)


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
