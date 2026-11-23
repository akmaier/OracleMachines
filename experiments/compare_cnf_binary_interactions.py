#!/usr/bin/env python3
"""Freeze a second-target recognition ablation with exact persistent seeds."""
from collections import Counter
from copy import deepcopy
from functools import partial
from pathlib import Path
from unittest.mock import patch
import random,sqlite3,subprocess,sys,tempfile,time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_partition_preparation as previous
from experiments import cnf_targeted_backbone as targeted
from experiments.cnf_ranked_binary_targets import discover as first
from experiments.cnf_binary_target_fallback import discover as second
from experiments.cnf_partition_preparation import run as prepared_run
from experiments.probe_cnf_binary_interactions import branch_seed
from experiments.cnf_residual_dag import normalize,token
base=previous.base;binding=previous.binding;bound=previous.bound;TABLES=previous.TABLES
read_zip=previous.read_zip;write_zip=previous.write_zip;restore=previous.restore;tables=previous.tables;harness=previous.harness
PARENT=Path('experiments/results/cnf-partition-preparation');MODES=('binary1','binary2')
FILES=('experiments/probe_cnf_binary_interactions.py','experiments/cnf_binary_target_fallback.py','experiments/compare_cnf_binary_interactions.py','solver/test_cnf_binary_target_fallback.py')

def native_split(split):return split.startswith('branch-')

def prepare(out):
    assert not (out/'protocol.json').exists();tick=time.perf_counter()
    parent=base.load(PARENT/'checkpoint.json');old=base.load(PARENT/'protocol.json');oldcases=bound(old['cases'])
    for f,h in parent['source_fingerprints'].items():assert base.sha(f)==h,f
    cases=[dict(deepcopy(c),split='controls') for c in oldcases if c['split']=='novel'];prefixes=deepcopy(old['prefixes'])
    spec=base.load(PARENT/'next-target.json')['branch_candidate'];base.write(out/'branch-spec.json',spec)
    seed=write_zip(out/'branch-prefix.json.gz',branch_seed(spec));cnf,names=normalize(spec['source'])
    frequencies=Counter(abs(l) for c in cnf if len(c)==2 for l in c);variable=min(frequencies,key=lambda v:(-frequencies[v],v));raw_variable=names[variable-1]
    for label,flips in (('original',set()),('flip', {raw_variable}),('complement',{abs(l) for c in spec['source'] for l in c})):
        split='branch-'+label;source=[[-l if abs(l) in flips else l for l in c] for c in spec['source']]
        normalized,_=normalize(source);root=token(normalized,Counter())
        cases.append(dict(split=split,case=31,variant=label,source=source,root=root,flipped_variables=sorted(flips)))
        prefixes[split]=dict(archive=seed)
    with tempfile.TemporaryDirectory() as td:
        path=Path(td)/'union';base.restore_archive(parent['reference_union'],path);con=sqlite3.connect(path)
        try:known={k for t in TABLES for k, in con.execute(f'SELECT id FROM {t}')}
        finally:con.close()
    for index in (25,31,61):
        original=next(c for c in oldcases if (c['split'],c['case'],c['variant'])==('novel',index,'delete'))
        rng=random.Random(202611230229+index)
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
        branch_spec=binding(out/'branch-spec.json'),flipped_raw_variable=raw_variable,cases=binding(out/'cases.json'),prefixes=prefixes,node_limit=256,
        exploration=binding(out/'verified-exploration/exploration.json'),orders=[list(MODES),list(reversed(MODES))],
        source_fingerprints={**parent['source_fingerprints'],**{f:base.sha(f) for f in FILES}},preparation_seconds=time.perf_counter()-tick,
        limitations=[
        'One added binary-frequency target, only after the first misses. Whole-cover priority, shared implication graph, completed reachability cache and native proof compilation remain unchanged. At most two extra targeted roots follow the existing eight cover-root budget.',
        'Exploration compared existing policies on the exposed saved branch before freezing this candidate. It found a forced second-ranked target missed by the first, but no exposed expansion-count gain. Exploration is not held-out performance evidence.',
        'Six old edits are controls, three exposed signed branch inputs use the exact pre-branch seed, and six new fixed-seed edits are absent from the prior union. Donors/maps remain supplied. All whole-query arms use shared partition preparation.',
        'Each trial starts from its exact cold prefix; no future root is seeded. Native sign-branch budgets are256, versus247 remaining at the original captured call; all tested exposed policies use fewer. Warm parent-query transient pools are absent.',
        'Two opposite serial orders precede profiles, tests and cumulative audits. Recognition, failed searches, checking, publication, persistence and cold replay remain charged. Complete worker time includes audits and is not production latency.',
        'Search paths and payloads may change; decisions must agree and every new certificate is independently checked. Retain all alternatives and regressions. Extra reachability can change the continuation unfavourably.',
        'No new native proof rule, default change, broad external holdout, unrestricted polynomial bound or Lean refinement theorem is claimed.']))


def worker(out,p,split,index,mode):
    original_query=harness.query
    def dispatch(s,c,unused,budget):
        return original_query(s,c,'native',budget) if native_split(split) else prepared_run(s,c['candidate'],'probe6',budget)
    p=deepcopy(p)
    if native_split(split):p['prefixes'][str(index)]=p['prefixes'][split]
    fn=partial(first,policy='binary1') if mode=='binary1' else partial(second,policy='binary2')
    with patch.object(harness,'query',dispatch),patch.object(targeted,'inspect_targeted_backbone',fn):harness.worker(out,p,split,index,mode)


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
