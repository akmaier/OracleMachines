#!/usr/bin/env python3
"""Freeze joint binary-consequence discovery against one/two target policies."""
from collections import Counter
from copy import deepcopy
from functools import partial
from pathlib import Path
from unittest.mock import patch
import random,sqlite3,subprocess,sys,tempfile,time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_live_fallback as previous
from experiments.cnf_joint_backbone import JointBackboneSolver
from experiments.probe_cnf_joint_backbone import seed
from experiments.cnf_residual_dag import normalize,token
from experiments.cnf_affine_probe_safe import InputSafeAffineProbeSolver
base=previous.base;binding=previous.binding;bound=previous.bound;TABLES=previous.TABLES
read_zip=previous.read_zip;write_zip=previous.write_zip;restore=previous.restore;tables=previous.tables;harness=previous.harness
PARENT=Path('experiments/results/cnf-live-fallback');MODES=('binary1','binary2','joint')
FILES=('experiments/probe_cnf_joint_backbone.py','experiments/cnf_joint_backbone.py','experiments/compare_cnf_joint_backbone.py','solver/test_cnf_joint_backbone.py')


def native_split(split):return split.startswith('branch-')


def prepare(out):
    assert not (out/'protocol.json').exists();began=time.perf_counter()
    parent=base.load(PARENT/'checkpoint.json');old=base.load(PARENT/'protocol.json');oldcases=bound(old['cases'])
    for f,h in parent['source_fingerprints'].items():assert base.sha(f)==h,f
    cases=[dict(deepcopy(c),split='controls') for c in oldcases if c['split']=='novel'];prefixes=deepcopy(old['prefixes'])
    exploration=base.load(out/'exploration.json');spec=exploration['spec'];branch=write_zip(out/'branch-prefix.json.gz',seed(spec))
    cnf,names=normalize(spec['source']);freq=Counter(abs(l) for c in cnf if len(c)==2 for l in c)
    raw=names[min(freq,key=lambda v:(-freq[v],v))-1]
    for label,flips in (('original',set()),('flip',{raw}),('complement',{abs(l) for c in spec['source'] for l in c})):
        split='branch-'+label;source=[[-l if abs(l) in flips else l for l in c] for c in spec['source']];cnf,_=normalize(source)
        cases.append(dict(split=split,case=31,variant=label,source=source,root=token(cnf,Counter()),flipped_variables=sorted(flips)))
        prefixes[split]=dict(archive=branch)
    with tempfile.TemporaryDirectory() as td:
        path=Path(td)/'union';base.restore_archive(parent['reference_union'],path);con=sqlite3.connect(path)
        try:known={k for t in TABLES for k, in con.execute(f'SELECT id FROM {t}')}
        finally:con.close()
    for index in (25,31,61):
        original=next(c for c in oldcases if (c['split'],c['case'],c['variant'])==('novel',index,'delete'))
        rng=random.Random(202611230432+index)
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
        cases=binding(out/'cases.json'),prefixes=prefixes,node_limit=256,branch_limit=247,flipped_raw_variable=raw,
        exploration=binding(out/'exploration.json'),orders=[list(MODES),list(reversed(MODES))],
        source_fingerprints={**parent['source_fingerprints'],**{f:base.sha(f) for f in FILES}},preparation_seconds=time.perf_counter()-began,
        limitations=[
        'The bounded joint policy shares the original graph/cover cache, searches at most eight ranked binary targets, skips values already implied by one selected survivor, and retains at most two consequences not implied by earlier selections. This directional filter does not compute a minimum independent basis; a later selection can imply an earlier one. This changes discovery breadth and batching together.',
        'Every source-indexed contradiction path is checked. Context-conditioned unit traces and native split parents use existing proof rules. An intermediate cached answer is inspected before fresh joint acquisition. Native compilation/publication is charged separately from ordinary expansions.',
        'Both older targeted policies and joint use the same shared partition preparation with restart, not the optional live-fallback wrapper. This isolates joint discovery from continuation changes.',
        'Six older fresh edits become controls; three signed variants expose the captured branch; six fixed-seed new edits are absent from the prior union. Donors/maps and earlier acquisition remain supplied/sunk.',
        'Each trial restores the exact historical prefix. Exposed branch budgets match the captured247 remaining expansions; whole queries use256 including the initial eight. No future queried root is seeded.',
        'Two opposite serial orders precede profiling and cumulative audits. Recognition, unsuccessful candidates, normalization, proof construction/checking, retained space, persistence, warm and cold replay remain charged.',
        'The complete exploratory census is exposed diagnostic work, not part of the bounded recognizer or a holdout result. A later single-selected-path ablation may isolate batching counts but is posthoc and separately audited.',
        'Complete worker time includes full-history audit and measurement overhead. No default change, broad external benchmark, uniformly polynomial arbitrary-SAT bound or Lean refinement theorem is claimed.']))


def worker(out,p,split,index,mode):
    original=harness.query
    def dispatch(s,c,unused,budget):
        return original(s,c,'native',min(budget,p['branch_limit'])) if native_split(split) else previous.previous.prepared_run(s,c['candidate'],'probe6',budget)
    p=deepcopy(p)
    if native_split(split):p['prefixes'][str(index)]=p['prefixes'][split]
    kernel=previous.previous
    fn=partial(kernel.second,policy='binary2') if mode=='binary2' else partial(kernel.first,policy='binary1')
    with patch.object(harness,'query',dispatch),patch.object(harness,'InputSafeAffineProbeSolver',JointBackboneSolver if mode=='joint' else InputSafeAffineProbeSolver),patch.object(kernel.targeted,'inspect_targeted_backbone',fn):
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
