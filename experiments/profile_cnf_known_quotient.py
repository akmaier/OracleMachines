#!/usr/bin/env python3
"""Posthoc solve-only profile; never mix instrumented times with matched workers."""
from pathlib import Path
from collections import Counter
import cProfile,json,pstats,sys,tempfile
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_known_quotient as study
from experiments.cnf_known_quotient import KnownQuotientSolver
base=study.base


def profile(out):
    p=base.load(out/'protocol.json');cases=study.bound(p['cases'])
    for f,h in p['source_fingerprints'].items():assert base.sha(f)==h,f
    expected=base.load(out/'known-0/queries.json');summary=base.load(out/'report.json')['summary']['known']
    with tempfile.TemporaryDirectory() as td:
        s=KnownQuotientSolver(Path(td)/'db');prof=cProfile.Profile()
        try:
            prof.enable();results=[s.solve(c['source']) for c in cases];prof.disable()
            for case,(a,b) in enumerate(zip(results,expected)):
                for key in ('answer','model','root','authority','metrics','quotient_choice'):assert json.loads(base.encode(a[key]))==b['result'][key],(case,key)
            native=study.native_rows(s);ext=study.extension_rows(s)
            assert base.key_sha(base.encode(sorted(native.items())))==summary['native_digest']
            assert base.key_sha(base.encode(sorted(ext.items())))==summary['extension_digest']
        finally:s.close()
    class CensusSolver(KnownQuotientSolver):
        def __init__(self,*args,**kwargs):
            self.inputs=Counter();self.local=Counter();self.outputs={};super().__init__(*args,**kwargs)
        def _canonical(self,cnf):
            frozen=tuple(tuple(c) for c in cnf);result=super()._canonical(frozen)
            self.inputs[frozen]+=1;self.local[frozen]+=1
            if frozen in self.outputs:assert self.outputs[frozen]==result
            else:self.outputs[frozen]=result
            return result
    with tempfile.TemporaryDirectory() as td:
        s=CensusSolver(Path(td)/'db');local_stats=[]
        try:
            for c,b in zip(cases,expected):
                s.local=Counter();a=s.solve(c['source'])
                local_stats.append(dict(calls=sum(s.local.values()),distinct=len(s.local),repeats=sum(n-1 for n in s.local.values()),
                    repeated_literal_units=sum(sum(map(len,k))*(n-1) for k,n in s.local.items()),
                    encoded_state=sum(len(base.encode(k).encode())+len(base.encode(s.outputs[k]).encode()) for k in s.local)))
                for key in ('answer','model','root','authority','metrics','quotient_choice'):
                    assert json.loads(base.encode(a[key]))==b['result'][key]
            census=dict(within_query_repeats=sum(r['repeats'] for r in local_stats),
                within_query_repeated_literal_units=sum(r['repeated_literal_units'] for r in local_stats),
                max_query_distinct=max(r['distinct'] for r in local_stats),max_query_encoded_state=max(r['encoded_state'] for r in local_stats),
                calls=sum(s.inputs.values()),distinct=len(s.inputs),exact_repeats=sum(n-1 for n in s.inputs.values()),
                input_literal_units=sum(sum(map(len,k))*n for k,n in s.inputs.items()),
                repeated_literal_units=sum(sum(map(len,k))*(n-1) for k,n in s.inputs.items()),
                encoded_distinct_inputs=sum(len(base.encode(k).encode()) for k in s.inputs),
                encoded_distinct_outputs=sum(len(base.encode(v).encode()) for v in s.outputs.values()),
                limits=['Posthoc exact-input census; no cache implemented. Hashing, copying, lookup, retained objects and invalidation remain costs.',
                    'Result includes normalization, original-variable names and canonical full key; all three must be reused together.'])
            assert base.key_sha(base.encode(sorted(study.native_rows(s).items())))==summary['native_digest']
            assert base.key_sha(base.encode(sorted(study.extension_rows(s).items())))==summary['extension_digest']
        finally:s.close()
    stats=pstats.Stats(prof);entries=[]
    root=Path(__file__).resolve().parents[1]
    for (filename,line,name),(primitive,total,own,cumulative,_) in stats.stats.items():
        try:filename=str(Path(filename).relative_to(root))
        except ValueError:pass
        entries.append(dict(file=filename,line=line,function=name,primitive_calls=primitive,total_calls=total,self_seconds=own,cumulative_seconds=cumulative))
    result=dict(protocol=study.binding(out/'protocol.json'),profile_source=dict(path=__file__,sha256=base.sha(__file__)),queries=len(cases),
        outputs_and_counters_identical=True,canonical_census=census,total_profiled_seconds=stats.total_tt,total_calls=stats.total_calls,
        functions=sorted(entries,key=lambda r:-r['self_seconds']),
        limitations=['One instrumented solve-only replay. Imports, setup, metadata scans, warm replay, cold verification and compression excluded.',
            'Cumulative function times overlap; do not sum them. Instrumented times are not comparator wall-time measurements.'])
    base.write(out/'profile.json',result);print(base.encode(result['functions'][:12]),flush=True)


if __name__=='__main__':profile(Path(sys.argv[1]))
