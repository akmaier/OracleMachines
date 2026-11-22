#!/usr/bin/env python3
"""Frozen routing comparison with identical persistent branch states."""
from copy import deepcopy
from collections import Counter
from functools import partial
from pathlib import Path
from unittest.mock import patch
import random,sqlite3,subprocess,sys,tempfile,time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_ranked_binary_targets as previous
from experiments import cnf_targeted_backbone as targeted
from experiments.cnf_ranked_binary_targets import discover
from experiments.cnf_binary_routing import priority_expand
from experiments.cnf_probed_partition import run as probed
from experiments.cnf_residual_dag import normalize,token
base=previous.base;binding=previous.binding;bound=previous.bound
TABLES=previous.TABLES;read_zip=previous.read_zip;write_zip=previous.write_zip;restore=previous.restore;tables=previous.tables
PARENT=Path('experiments/results/cnf-ranked-binary-targets');MODES=('baseline','binary1','priority')
FILES=('experiments/inspect_cnf_binary_routing.py','experiments/cnf_binary_routing.py','experiments/compare_cnf_binary_routing.py','solver/test_cnf_binary_routing.py')


def branch_seed(spec):
    report=bound(spec['trial_report']);delta=read_zip(report['delta']);prefix=read_zip(spec['prefix'])
    keys=set(spec['extra_ids']);extra={t:[[k,v] for k,v in delta[t] if t==TABLES[0] and k in keys] for t in TABLES}
    assert len(extra[TABLES[0]])==spec['extra_count']
    return {t:prefix[t]+extra[t] for t in TABLES}


def prepare(out):
    assert out.is_dir() and not (out/'protocol.json').exists();began=time.perf_counter()
    parent=base.load(PARENT/'checkpoint.json');old=base.load(PARENT/'protocol.json');oldcases=bound(old['cases'])
    for f,h in parent['source_fingerprints'].items():assert base.sha(f)==h,f
    cases=[dict(deepcopy(c),split='controls') for c in oldcases if c['split']=='fresh']
    prefixes={i:deepcopy(old['prefixes'][i]) for i in ('25','31','61')}
    for split,file in (('good','experiments/results/cnf-probed-partition/next-branch.json'),('regression',str(PARENT/'next-target.json'))):
        spec=base.load(file);seed=branch_seed(spec)
        prefixes[split]=dict(archive=write_zip(out/f'{split}-prefix.json.gz',seed),spec=binding(Path(file)))
        assert all(spec['root'] not in dict(seed[t]) for t in TABLES)
        cases.append(dict(split=split,case=31,variant='isolated',source=spec['source'],root=spec['root']))
    with tempfile.TemporaryDirectory() as td:
        path=Path(td)/'union';base.restore_archive(parent['reference_union'],path);con=sqlite3.connect(path)
        try:known={k for t in TABLES for k, in con.execute(f'SELECT id FROM {t}')}
        finally:con.close()
    for index in (25,31,61):
        original=next(c for c in oldcases if (c['split'],c['case'],c['variant'])==('novel',index,'delete'))
        rng=random.Random(202611222128+index);deleted=rng.sample(range(len(original['source'])),2)
        for i,cid in enumerate(deleted):
            source=[c for j,c in enumerate(original['source']) if j!=cid];added=None
            if i:
                added=sorted(v*(1 if rng.randrange(2) else -1) for v in rng.sample(original['candidate']['target_names'],3))
                assert added not in source;source.append(added)
            cnf,names=normalize(source);root=token(cnf,Counter());assert root not in known
            candidate=deepcopy(original['candidate']);candidate.update(target=[list(c) for c in cnf],target_names=list(names))
            cases.append(dict(split='novel',case=index,variant='delete' if not i else 'replace',source=previous.previous.previous.target_source(candidate),
                candidate=candidate,root=root,deleted_clause=original['source'][cid],added_clause=added))
    assert len(cases)==14 and len({c['root'] for c in cases})==14
    for c in cases:
        prefix=prefixes[c['split'] if c['split'] in ('good','regression') else str(c['case'])]
        assert all(c['root'] not in dict(read_zip(prefix['archive'])[t]) for t in TABLES)
    base.write(out/'cases.json',cases)
    base.write(out/'protocol.json',dict(parent=binding(PARENT/'checkpoint.json'),parent_manifest=binding(PARENT/'manifest.json'),
        exploration=binding(out/'exploration/report.json'),cases=binding(out/'cases.json'),prefixes=prefixes,node_limit=256,
        orders=[list(MODES),list(reversed(MODES))],source_fingerprints={**parent['source_fingerprints'],**{f:base.sha(f) for f in FILES}},
        preparation_seconds=time.perf_counter()-began,limitations=[
        'The exposed identical-prestate diagnostic reproduces10/35/33 native expansions. The priority policy was selected after inspecting this branch; no outcome-based tuning occurs after this protocol.',
        'Priority uses binary1 discovery, then probes only the default frequency split\'s false cofactor when its variable differs from the binary-forced candidate. A checked cached negative or a unit-conflict certificate may preempt the candidate. A miss conveys no verdict.',
        'The extra probe is admitted only within256 variables,4096 clauses and16384 literals. It is not an extra native expansion. Ranking, canonicalization, lookup, propagation, checking and direct publication are separately charged; the shared256 ordinary-expansion cap does not bound time, memory or all published nodes.',
        'Six old controls, two exposed isolated branches and six fixed-seed new edits. Fresh roots are absent from the preceding union. Whole-query controls/edits use the unchanged probe6 wrapper; isolated branches use native acquisition. Donors/maps remain supplied.',
        'Each isolated branch restores exactly its prefix plus its bound pre-branch publications, with empty transient caches/pools. Other arms restore the preceding cold seeds. No final target answers are imported.',
        'Three separate serial policy processes in opposite orders. The expansion-method patch is scoped to a worker, not a thread-safe public API or solver-default change.',
        'Inherited workers charge publication, persistence, warm reuse, full cold replay and reconstruction. Complete time includes audit/measurement overhead; query time excludes some of those costs. Earlier acquisition and supplied-candidate selection remain sunk.',
        'Retain failed ideas and regressions. A local failed-literal certificate is established reasoning, not automatic broad SAT coverage, optimal routing, polynomial unrestricted expansion or a Lean refinement proof.']))


def worker(out,p,split,index,mode):
    harness=previous.previous.previous;query=harness.query
    def dispatch(s,c,unused,budget):
        return query(s,c,'native',budget) if split in ('good','regression') else probed(s,c['candidate'],'probe6',budget)
    p=deepcopy(p)
    if split in ('good','regression'):p['prefixes'][str(index)]=p['prefixes'][split]
    with patch.object(harness,'query',dispatch):
        if mode=='baseline':harness.worker(out,p,split,index,mode)
        elif mode=='binary1':
            with patch.object(targeted,'inspect_targeted_backbone',partial(discover,policy='binary1')):harness.worker(out,p,split,index,mode)
        else:
            with patch.object(targeted.TargetedBackboneMixin,'_expand',priority_expand):harness.worker(out,p,split,index,mode)


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
