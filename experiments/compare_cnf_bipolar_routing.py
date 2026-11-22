#!/usr/bin/env python3
"""Frozen routing comparison with identical persistent branch states."""
from copy import deepcopy
from collections import Counter
from functools import partial
from pathlib import Path
from unittest.mock import patch
import random,sqlite3,subprocess,sys,tempfile,time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_binary_routing as previous
from experiments import cnf_targeted_backbone as targeted
from experiments.cnf_ranked_binary_targets import discover
from experiments.cnf_binary_routing import priority_expand
from experiments.cnf_bipolar_routing import bipolar_expand
from experiments.cnf_probed_partition import run as probed
from experiments.cnf_residual_dag import normalize,token
base=previous.base;binding=previous.binding;bound=previous.bound
TABLES=previous.TABLES;read_zip=previous.read_zip;write_zip=previous.write_zip;restore=previous.restore;tables=previous.tables
PARENT=Path('experiments/results/cnf-binary-routing');MODES=('baseline','binary1','priority','bipolar')
harness=previous.previous.previous.previous

def native_split(split):return split.startswith('polarity-')
FILES=('experiments/cnf_bipolar_routing.py','experiments/compare_cnf_bipolar_routing.py','solver/test_cnf_bipolar_routing.py')


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
    specfile=PARENT/'next-target.json';spec=base.load(specfile);seed=branch_seed(spec)
    prefix=dict(archive=write_zip(out/'polarity-prefix.json.gz',seed),spec=binding(specfile))
    for name,flips in (('original',[]),('flip76',[spec['baseline_variable']]),('complement',sorted({abs(l) for c in spec['source'] for l in c}))):
        split='polarity-'+name;prefixes[split]=deepcopy(prefix)
        source=[[-l if abs(l) in flips else l for l in c] for c in spec['source']]
        cnf,_=normalize(source);root=token(cnf,Counter())
        assert all(root not in dict(seed[t]) for t in TABLES)
        cases.append(dict(split=split,case=31,variant=name,source=source,root=root,flipped_variables=flips))
    with tempfile.TemporaryDirectory() as td:
        path=Path(td)/'union';base.restore_archive(parent['reference_union'],path);con=sqlite3.connect(path)
        try:known={k for t in TABLES for k, in con.execute(f'SELECT id FROM {t}')}
        finally:con.close()
    for index in (25,31,61):
        original=next(c for c in oldcases if (c['split'],c['case'],c['variant'])==('novel',index,'delete'))
        rng=random.Random(202611222231+index);deleted=rng.sample(range(len(original['source'])),2)
        for i,cid in enumerate(deleted):
            source=[c for j,c in enumerate(original['source']) if j!=cid];added=None
            if i:
                added=sorted(v*(1 if rng.randrange(2) else -1) for v in rng.sample(original['candidate']['target_names'],3))
                assert added not in source;source.append(added)
            cnf,names=normalize(source);root=token(cnf,Counter());assert root not in known
            candidate=deepcopy(original['candidate']);candidate.update(target=[list(c) for c in cnf],target_names=list(names))
            cases.append(dict(split='novel',case=index,variant='delete' if not i else 'replace',source=harness.target_source(candidate),
                candidate=candidate,root=root,deleted_clause=original['source'][cid],added_clause=added))
    assert len(cases)==15 and len({c['root'] for c in cases})==15
    for c in cases:
        prefix=prefixes[c['split'] if native_split(c['split']) else str(c['case'])]
        assert all(c['root'] not in dict(read_zip(prefix['archive'])[t]) for t in TABLES)
    base.write(out/'cases.json',cases)
    base.write(out/'protocol.json',dict(parent=binding(PARENT/'checkpoint.json'),parent_manifest=binding(PARENT/'manifest.json'),
        polarity_spec=binding(specfile),cases=binding(out/'cases.json'),prefixes=prefixes,node_limit=256,
        orders=[list(MODES),list(reversed(MODES))],source_fingerprints={**parent['source_fingerprints'],**{f:base.sha(f) for f in FILES}},
        preparation_seconds=time.perf_counter()-began,limitations=[
        'Two-polarity routing was chosen after the saved false-only counterexample. Four frozen policies, two opposite orders; no outcome-based tuning after protocol creation.',
        'After unchanged binary1 discovery, the optional policy checks false then true cofactors of the ordinary frequency variable only when it differs from the binary-forced variable, within256 variables,4096 clauses,16384 literals. A checked cached negative or unit contradiction can preempt the binary choice.',
        'Misses are inconclusive and are not saved as solved children; later acquisition may repeat their propagation. Checked negative cofactor nodes are retained through ordinary native publication. Probes are not ordinary expansions; all timing, native publication, counter and storage costs are charged.',
        'Six preceding new edits are now controls. Six fixed-seed additional edits have roots absent from the prior union. Their supplied donors/maps and probe6 wrapper remain unchanged.',
        'Three isolated variants of the exposed285-clause residual: original, variable76 sign-flip, global complement. Each restores the identical bound pre-target prefix independently, with empty transient caches. No signed proof transport is assumed; these are native-only acquisitions.',
        'The256 ordinary-expansion shared limit bounds neither total time, memory, propagation nor direct publication. Sign changes preserve satisfiability, but can change scan order, branch selection, canonicalization and reuse.',
        'Separate serial workers; no concurrent CPU diagnostics during measured trials. The scoped method patch is experimental, not a default solver or thread-safe API change.',
        'Inherited harness charges preparation, canonicalization, checking, publication, persistence, warm reuse, cold replay and reconstruction. Complete time includes measurement/audit overhead. Earlier acquisition and supplied candidate discovery remain sunk.',
        'Retain regressions. These small exposed and nearby residual cases establish neither representative SAT coverage, uniformly cheap expansion, optimal routing nor a Lean refinement theorem.']))



def worker(out,p,split,index,mode):
    query=harness.query
    def dispatch(s,c,unused,budget):
        return query(s,c,'native',budget) if native_split(split) else probed(s,c['candidate'],'probe6',budget)
    p=deepcopy(p)
    if native_split(split):p['prefixes'][str(index)]=p['prefixes'][split]
    with patch.object(harness,'query',dispatch):
        if mode=='baseline':harness.worker(out,p,split,index,mode)
        elif mode=='binary1':
            with patch.object(targeted,'inspect_targeted_backbone',partial(discover,policy='binary1')):harness.worker(out,p,split,index,mode)
        else:
            with patch.object(targeted.TargetedBackboneMixin,'_expand',priority_expand if mode=='priority' else bipolar_expand):harness.worker(out,p,split,index,mode)


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
