#!/usr/bin/env python3
"""Matched persistent-prestate diagnostic; every exploratory proof is retained."""
from collections import Counter
from functools import partial
from pathlib import Path
from unittest.mock import patch
import sys,tempfile
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_ranked_binary_targets as previous
from experiments import cnf_targeted_backbone as targeted
from experiments.cnf_ranked_binary_targets import discover
from experiments.cnf_probed_partition import acquire
from experiments.cnf_affine_probe_safe import InputSafeAffineProbeSolver
from experiments.cnf_canonical_verify import CanonicalVerifySnapshot
from experiments.cnf_residual_dag import token
base=previous.base


def inspect(out):
    out.mkdir();spec=base.load(previous.PARENT.parent/'cnf-ranked-binary-targets/next-target.json')
    report=previous.bound(spec['trial_report']);delta=previous.read_zip(report['delta']);prefix=previous.read_zip(spec['prefix'])
    extra={t:[[k,v] for k,v in delta[t] if t==previous.TABLES[0] and k in set(spec['extra_ids'])] for t in previous.TABLES}
    seed={t:prefix[t]+extra[t] for t in previous.TABLES};assert len(extra[previous.TABLES[0]])==35
    seed_entry=previous.write_zip(out/'prefix.json.gz',seed);records=[];original=targeted.inspect_targeted_backbone
    for mode in ('baseline','total4','binary1'):
        fn=original if mode=='baseline' else partial(discover,policy=mode);trace=[]
        def wrapped(cnf,counts):
            result=fn(cnf,counts)
            trace.append(dict(root=token(cnf,Counter()),clauses=len(cnf),literals=sum(map(len,cnf)),
                proof_kind=None if result[0] is None else result[0]['kind'],cover=result[1],partials=result[2]))
            return result
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/'db';previous.restore(seed,path);s=InputSafeAffineProbeSolver(path)
            try:
                cnf,_,root=s._canonical(spec['source']);assert root==spec['root'] and s._read(root,cnf) is None
                with patch.object(targeted,'inspect_targeted_backbone',wrapped):answer=acquire(s,spec['source'],256)
                final=previous.tables(s);new={t:final[t][len(seed[t]):] for t in previous.TABLES}
            finally:s.close()
            s=CanonicalVerifySnapshot(path)
            try:
                for k,v in new[previous.TABLES[0]]:assert s._read(k) is not None
                assert s._read(root)['answer'] is False
            finally:s.close()
        base.write(out/f'{mode}-trace.json',trace)
        records.append(dict(mode=mode,result=answer,trace=previous.binding(out/f'{mode}-trace.json'),delta=previous.write_zip(out/f'{mode}-delta.json.gz',new)))
        print(mode,answer['metrics'].get('expanded_nodes'),flush=True)
    assert [r['result']['metrics']['expanded_nodes'] for r in records]==[10,35,33]
    base.write(out/'report.json',dict(source=spec['source'],root=spec['root'],prefix=seed_entry,
        predecessor=previous.binding(Path('experiments/results/cnf-ranked-binary-targets/next-target.json')),records=records,
        script_sha256=base.sha(__file__),limitations=[
        'Exposed posthoc diagnostic from identical persistent prestate and empty transient caches/pools. Instrumented times are not a performance comparison.',
        'Each arm starts without the target root and independently checks every new native record. All exploratory proofs remain in the deltas.',
        'The reproducible 10/35/33 expansion difference establishes a policy effect under this prestate, not universal optimality.']))


if __name__=='__main__':inspect(Path(sys.argv[1]))
