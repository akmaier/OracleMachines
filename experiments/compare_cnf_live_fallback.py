#!/usr/bin/env python3
"""Freeze matched restart/resume streams before timing the live handoff."""
from collections import Counter
from copy import deepcopy
from functools import partial
from pathlib import Path
from unittest.mock import patch
import random,sqlite3,subprocess,sys,tempfile,time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_binary_interactions as previous
from experiments import cnf_live_fallback as live
base=previous.base;binding=previous.binding;bound=previous.bound;TABLES=previous.TABLES
read_zip=previous.read_zip;write_zip=previous.write_zip;restore=previous.restore;tables=previous.tables;harness=previous.harness
PARENT=Path('experiments/results/cnf-binary-interactions');MODES=('restart','resume')
FILES=('experiments/cnf_live_fallback.py','experiments/compare_cnf_live_fallback.py','solver/test_cnf_live_fallback.py')


def prepare(out):
    assert not (out/'protocol.json').exists();began=time.perf_counter()
    parent=base.load(PARENT/'checkpoint.json');old=base.load(PARENT/'protocol.json');oldcases=bound(old['cases'])
    for f,h in parent['source_fingerprints'].items():assert base.sha(f)==h,f
    cases=[dict(deepcopy(c),split='controls') for c in oldcases if c['split']=='novel']
    prefixes={str(i):old['prefixes'][str(i)] for i in (25,31,61)}
    with tempfile.TemporaryDirectory() as td:
        path=Path(td)/'union';base.restore_archive(parent['reference_union'],path);con=sqlite3.connect(path)
        try:known={k for t in TABLES for k, in con.execute(f'SELECT id FROM {t}')}
        finally:con.close()
    for index in (25,31,61):
        original=next(c for c in oldcases if (c['split'],c['case'],c['variant'])==('novel',index,'delete'))
        rng=random.Random(202611230333+index)
        for i,cid in enumerate(rng.sample(range(len(original['source'])),2)):
            source=[c for j,c in enumerate(original['source']) if j!=cid];added=None
            if i:
                added=sorted(v*(1 if rng.randrange(2) else -1) for v in rng.sample(original['candidate']['target_names'],3));assert added not in source;source.append(added)
            cnf,names=previous.normalize(source);root=previous.token(cnf,Counter());assert root not in known
            candidate=deepcopy(original['candidate']);candidate.update(target=[list(c) for c in cnf],target_names=list(names))
            cases.append(dict(split='novel',case=index,variant='delete' if not i else 'replace',source=harness.target_source(candidate),candidate=candidate,root=root,deleted_clause=original['source'][cid],added_clause=added))
    assert len(cases)==12 and len({c['root'] for c in cases})==12
    for c in cases:assert all(c['root'] not in dict(read_zip(prefixes[str(c['case'])]['archive'])[t]) for t in TABLES)
    base.write(out/'cases.json',cases)
    base.write(out/'protocol.json',dict(parent=binding(PARENT/'checkpoint.json'),parent_manifest=binding(PARENT/'manifest.json'),
        cases=binding(out/'cases.json'),prefixes=prefixes,node_limit=256,orders=[list(MODES),list(reversed(MODES))],
        source_fingerprints={**parent['source_fingerprints'],**{f:base.sha(f) for f in FILES}},preparation_seconds=time.perf_counter()-began,
        limitations=[
        'Both arms use the same binary1 recognizer and supplied support candidate. The new arm makes the existing routing decision before unwinding the stack. Only native fallback resumes; partition routing discards frames.',
        'The new kernel keeps the native visitor and proof rules except a synchronous callback at the existing expansion-budget guard. No threads, frame serialization or asynchronous user-visible continuation is introduced. Exclusive solver ownership is required.',
        'The eight-expansion probe and later work share256 expansions. Preparation is charged while frames remain live. Both selected-child counts and full source models remain checked. A completed pause prefix persists; unfinished frames carry no answer authority.',
        'Six preceding new edits become controls; six fixed-seed edits are generated before timing and absent from the prior cumulative union. This is a local supplied-candidate comparison, not a representative external SAT benchmark.',
        'Two opposite serial orders finish before profiling and tests. Complete worker time includes restoration, full cold audits and measurement overhead. Query-time changes are not complete-worker speedups.',
        'The live acquisition preserves its existing search-control flags, whereas restart resets them. Changes can include different subsequent search, not merely identical skipped frames. Retain all alternate proofs and regressions.',
        'A later total-budget stop under the resumed initial probe retains completed checked prefix nodes. Process loss discards live frames. Cold replay reuses finished proofs and begins incomplete queries again.',
        'No default change, new whole-source coverage class, unrestricted polynomial expansion bound or Lean refinement theorem is claimed.']))


def worker(out,p,split,index,mode):
    def dispatch(s,c,unused,budget):
        return (live.run if mode=='resume' else previous.prepared_run)(s,c['candidate'],'probe6',budget)
    with patch.object(harness,'query',dispatch),patch.object(harness,'InputSafeAffineProbeSolver',live.ContinuationSolver if mode=='resume' else previous.harness.InputSafeAffineProbeSolver),patch.object(previous.targeted,'inspect_targeted_backbone',partial(previous.first,policy='binary1')):
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
