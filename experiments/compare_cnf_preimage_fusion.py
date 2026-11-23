#!/usr/bin/env python3
"""Freeze fused causal preimages against the unchanged consequence-priority route."""
from collections import Counter
from contextlib import nullcontext
from copy import deepcopy
from pathlib import Path
from unittest.mock import patch
import random,sqlite3,subprocess,sys,tempfile,time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_consequence_priority as previous
from experiments.cnf_consequence_priority import ConsequencePrioritySolver
from experiments.cnf_preimage_fusion import fused_preimages
from experiments.cnf_partition_preparation import run as prepared_run
base=previous.base;binding=previous.binding;bound=previous.bound;TABLES=previous.TABLES
read_zip=previous.read_zip;write_zip=previous.write_zip;restore=previous.restore;tables=previous.tables;harness=previous.harness
normalize=previous.normalize;token=previous.token;native_split=previous.native_split
PARENT=Path('experiments/results/cnf-consequence-priority');MODES=('priority','fused')
FILES=('experiments/probe_cnf_preimage_fusion.py','experiments/cnf_preimage_fusion.py','experiments/compare_cnf_preimage_fusion.py','solver/test_cnf_preimage_fusion.py')


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
    spec=dict(observation['acquisitions'][4],trial=observation['trial']);branch=write_zip(out/'branch-prefix.json.gz',branch_seed(spec))
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
        rng=random.Random(202611230632+index)
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
        'Only causal parent-clause reconstruction changes. The input is the immutable canonical CNF of an already checked parent. Restriction preserves within-clause order; monotone variable compaction preserves signed and clause order. Exact full child keys and every emitted native proof remain checked.',
        'Unchanged parent tuples are reused, the first residual representative is preserved, and selected child indices map directly through the shared sorted residual description. No new memo, alternative support selection or proof format.',
        'Six preceding edits become controls; three sign variants expose the saved six-expansion source with its exact earlier native IDs and remaining242 budget. Warm hint pools are not serialized. Six fixed-seed nearby edits have roots absent from the preceding union.',
        'Fifteen targets, two modes and two opposite serial orders give60 attempts in36 workers. Serial timing precedes profiles/tests/audits. The scoped mode installation/removal is charged to complete-worker time; scope is process-local and must not overlap threads.',
        'All modes retain consequence-priority routing and shared partition preparation with restart. Recognition, serialization, checking, persistence, cold/warm replay and unsuccessful paths remain charged. Supplied donors/maps and historical acquisition remain sunk.',
        'The exposed preimage census adds no proof; all native bytes match the prior trial. Diagnostic sources and later profiles are not an independent external benchmark.',
        'No global default change, increased decision coverage, Lean implementation-refinement theorem or uniformly polynomial arbitrary-SAT claim.']))


def worker(out,p,split,index,mode):
    original=harness.query
    def dispatch(s,c,unused,budget):
        return original(s,c,'native',min(budget,p['branch_limit'])) if native_split(split) else prepared_run(s,c['candidate'],'probe6',budget)
    p=deepcopy(p)
    if native_split(split):p['prefixes'][str(index)]=p['prefixes'][split]
    with patch.object(harness,'query',dispatch),patch.object(harness,'InputSafeAffineProbeSolver',ConsequencePrioritySolver):
        tick=time.perf_counter()
        with fused_preimages() if mode=='fused' else nullcontext():
            setup=time.perf_counter()-tick;harness.worker(out,p,split,index,mode);tick=time.perf_counter()
        teardown=time.perf_counter()-tick
    report=base.load(out/'report.json');report['summary']['preimage_mode_setup_seconds']=setup+teardown
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
