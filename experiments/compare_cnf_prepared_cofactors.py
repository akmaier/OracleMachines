#!/usr/bin/env python3
"""Frozen routing comparison with identical persistent branch states."""
from copy import deepcopy
from collections import Counter
from functools import partial
from pathlib import Path
from unittest.mock import patch
import random,sqlite3,subprocess,sys,tempfile,time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_bipolar_routing as previous
from experiments import cnf_targeted_backbone as targeted
from experiments.cnf_ranked_binary_targets import discover
from experiments.cnf_binary_routing import priority_expand
from experiments.cnf_bipolar_routing import bipolar_expand
from experiments import cnf_bipolar_routing as bipolar
from experiments.cnf_prepared_cofactors import PreparedCofactorSolver,prepared_probe_child
from experiments.cnf_probed_partition import run as probed
from experiments.cnf_residual_dag import normalize,token
base=previous.base;binding=previous.binding;bound=previous.bound
TABLES=previous.TABLES;read_zip=previous.read_zip;write_zip=previous.write_zip;restore=previous.restore;tables=previous.tables
PARENT=Path('experiments/results/cnf-bipolar-routing');MODES=('binary1','bipolar','prepared')
harness=previous.harness

def native_split(split):return split.startswith('polarity-')
FILES=('experiments/cnf_prepared_cofactors.py','experiments/compare_cnf_prepared_cofactors.py','solver/test_cnf_prepared_cofactors.py')


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
    specfile=Path(old['polarity_spec']['path']);spec=bound(old['polarity_spec'])
    for c in oldcases:
        if native_split(c['split']):
            cases.append(deepcopy(c));prefixes[c['split']]=deepcopy(old['prefixes'][c['split']])
    sizing=PreparedCofactorSolver()
    try:
        from experiments.cnf_residual_dag import restrict
        charges=[sizing._cofactor_charge(raw,sizing._canonical(raw)) for raw in
                 (restrict(tuple(map(tuple,spec['source'])),{spec['baseline_variable']:v}) for v in (False,True))]
    finally:sizing.close()
    with tempfile.TemporaryDirectory() as td:
        path=Path(td)/'union';base.restore_archive(parent['reference_union'],path);con=sqlite3.connect(path)
        try:known={k for t in TABLES for k, in con.execute(f'SELECT id FROM {t}')}
        finally:con.close()
    for index in (25,31,61):
        original=next(c for c in oldcases if (c['split'],c['case'],c['variant'])==('novel',index,'delete'))
        rng=random.Random(202611222333+index);deleted=rng.sample(range(len(original['source'])),2)
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
        polarity_spec=binding(specfile),cases=binding(out/'cases.json'),prefixes=prefixes,node_limit=256,cofactor_bytes=256*1024,exposed_cofactor_charges=charges,
        orders=[list(MODES),list(reversed(MODES))],source_fingerprints={**parent['source_fingerprints'],**{f:base.sha(f) for f in FILES}},
        preparation_seconds=time.perf_counter()-began,limitations=[
        'Frozen binary1, two-polarity and prepared-cofactor arms in two opposite serial orders. The only new policy is pure normalization reuse; binary recognition, probing, branch choices and all proof rules remain unchanged.',
        'Only cofactor probes produce immutable raw-input/normalization triples. Only native visit and negative-child checks consume them, validating exact nonzero integer literals before equality lookup. A memo entry cannot authenticate a child answer, certificate or dependency.',
        'A256KiB retained-object cap admits both saved cofactor triples, whose individual conservative charges are recorded before solving. FIFO eviction, validation, snapshots, sizing, lookup, cleanup and all normalizer work are charged. Transient allocation, allocator overhead and whole-process memory are outside this cap.',
        'The memo lasts for one whole query, including the existing initial probe/partition branches, and clears on success, stop or exception. It is not persisted and does not retain propagation traces or unfinished search continuations.',
        'Six previous novel edits are controls, three previous sign variants retain identical cold pre-target states, and six new fixed-seed edits are absent from the prior union. Candidates/maps remain supplied. No new automatic pattern class or broad external holdout is claimed.',
        'Shared256 native expansion limits do not bound direct probes, time, memory or publication. Paired trial proofs, decisions, partitions, model lifts and expansions must match exactly between bipolar and prepared.',
        'Separate serial workers run before CPU-heavy audits/tests. Complete worker time includes restore, checking, warm reuse, persistence and cold reconstruction overhead. Preparation is recorded separately and earlier acquisition remains sunk.',
        'Retain all costs and regressions. This targeted application of previous normalization reuse is neither a polynomial arbitrary-SAT bound, new tractable category nor a Lean refinement proof.']))



def worker(out,p,split,index,mode):
    query=harness.query
    def dispatch(s,c,unused,budget):
        def work():return query(s,c,'native',budget) if native_split(split) else probed(s,c['candidate'],'probe6',budget)
        if mode!='prepared':return work()
        began=time.perf_counter()
        with s.cofactor_session():r=work()
        r['prepared_cofactors']=dict(s.cofactor_summary,capacity=s.cofactor_bytes)
        r['seconds']=time.perf_counter()-began
        return r
    p=deepcopy(p)
    if native_split(split):p['prefixes'][str(index)]=p['prefixes'][split]
    with patch.object(harness,'query',dispatch):
        if mode=='binary1':
            with patch.object(targeted,'inspect_targeted_backbone',partial(discover,policy='binary1')):harness.worker(out,p,split,index,mode)
        elif mode=='bipolar':
            with patch.object(targeted.TargetedBackboneMixin,'_expand',bipolar_expand):harness.worker(out,p,split,index,mode)
        else:
            with patch.object(targeted.TargetedBackboneMixin,'_expand',bipolar_expand),patch.object(bipolar,'probe_child',prepared_probe_child),patch.object(harness,'InputSafeAffineProbeSolver',PreparedCofactorSolver):
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
