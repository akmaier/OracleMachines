#!/usr/bin/env python3
"""Freeze consequence arbitration against ordinary and joint binary discovery."""
from collections import Counter
from copy import deepcopy
from functools import partial
from pathlib import Path
from unittest.mock import patch
import random,sqlite3,subprocess,sys,tempfile,time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_joint_backbone as previous
from experiments.cnf_consequence_priority import ConsequencePrioritySolver
from experiments.cnf_joint_backbone import JointBackboneSolver
from experiments.cnf_affine_probe_safe import InputSafeAffineProbeSolver
base=previous.base;binding=previous.binding;bound=previous.bound;TABLES=previous.TABLES
read_zip=previous.read_zip;write_zip=previous.write_zip;restore=previous.restore;tables=previous.tables;harness=previous.harness
normalize=previous.normalize;token=previous.token;native_split=previous.native_split
PARENT=Path('experiments/results/cnf-joint-backbone');MODES=('binary1','joint','priority')
FILES=('experiments/probe_cnf_consequence_priority.py','experiments/cnf_consequence_priority.py','experiments/compare_cnf_consequence_priority.py','solver/test_cnf_consequence_priority.py')


def prepare(out):
    assert not (out/'protocol.json').exists();began=time.perf_counter()
    parent=base.load(PARENT/'checkpoint.json');old=base.load(PARENT/'protocol.json');oldcases=bound(old['cases'])
    for f,h in parent['source_fingerprints'].items():assert base.sha(f)==h,f
    cases=[dict(deepcopy(c),split='controls') for c in oldcases if c['split']=='novel']
    cases.extend(deepcopy(c) for c in oldcases if native_split(c['split']));prefixes=deepcopy(old['prefixes'])
    with tempfile.TemporaryDirectory() as td:
        path=Path(td)/'union';base.restore_archive(parent['reference_union'],path);con=sqlite3.connect(path)
        try:known={k for t in TABLES for k, in con.execute(f'SELECT id FROM {t}')}
        finally:con.close()
    for index in (25,31,61):
        original=next(c for c in oldcases if (c['split'],c['case'],c['variant'])==('novel',index,'delete'))
        rng=random.Random(202611230533+index)
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
        cases=binding(out/'cases.json'),prefixes=prefixes,node_limit=256,branch_limit=247,
        exploration=binding(out/'exploration.json'),orders=[list(MODES),list(reversed(MODES))],
        source_fingerprints={**parent['source_fingerprints'],**{f:base.sha(f) for f in FILES}},preparation_seconds=time.perf_counter()-began,
        limitations=[
        'Priority arbitration runs only for one selected binary consequence whose variable differs from the first binary-frequency candidate and the ordinary full-frequency split. Two consequences and first-ranked single consequences keep the preceding policy.',
        'At most two ordinary cofactors are probed, false then true, stopping at the first independently checked negative. Existing size guards are256 variables,4096 clauses,16384 literals. A miss conveys no verdict. This is a heuristic arbitration rule, not optimal expansion.',
        'Existing cached-negative and unit-proof rules certify the preferred cofactor. Compiled publications are outside ordinary expansion counts but remain charged in payload, checking, persistence and replay.',
        'All arms use shared partition preparation with restart. Six preceding edits are controls, three exposed sign variants are retained, and six fixed-seed nearby edits are absent from the prior union. Donors/maps and acquisition are supplied/sunk.',
        'Fifteen targets, three modes and two opposite serial orders give90 attempts in54 workers. Timing precedes CPU-heavy profiles/audits/tests. Instrumentation, complete-worker overhead and endpoint-space limitations remain explicit.',
        'The diagnostic case61 single-selected ablation is exposed and separately replayed/merged; it does not identify a general optimal choice or establish independent held-out performance.',
        'No default change, new inference rule, external benchmark, Lean refinement theorem or uniform arbitrary-SAT guarantee.']))


def worker(out,p,split,index,mode):
    original=harness.query;kernel=previous.previous.previous
    def dispatch(s,c,unused,budget):
        return original(s,c,'native',min(budget,p['branch_limit'])) if native_split(split) else kernel.prepared_run(s,c['candidate'],'probe6',budget)
    p=deepcopy(p)
    if native_split(split):p['prefixes'][str(index)]=p['prefixes'][split]
    cls={'binary1':InputSafeAffineProbeSolver,'joint':JointBackboneSolver,'priority':ConsequencePrioritySolver}[mode]
    with patch.object(harness,'query',dispatch),patch.object(harness,'InputSafeAffineProbeSolver',cls),patch.object(kernel.targeted,'inspect_targeted_backbone',partial(kernel.first,policy='binary1')):
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
