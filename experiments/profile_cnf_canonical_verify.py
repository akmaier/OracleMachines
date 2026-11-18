#!/usr/bin/env python3
"""Posthoc direct-verification profiles and an exact canonical-output reuse census."""
from pathlib import Path
import cProfile,json,pstats,sys,tempfile
from collections import Counter
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_canonical_verify as study
from experiments.cnf_known_quotient import KnownQuotientSolver
from experiments.cnf_query_canonical_cache import QueryCanonicalSolver
from experiments.cnf_canonical_verify import CanonicalVerifySolver
base=study.base


def profile(out):
    p=base.load(out/'protocol.json');cases=study.bound(p['cases'])
    for f,h in p['source_fingerprints'].items():assert base.sha(f)==h,f
    profiles={};root=Path(__file__).resolve().parents[1]
    def location(filename,line,name):
        try:filename=str(Path(filename).relative_to(root))
        except ValueError:pass
        return dict(file=filename,line=line,function=name)
    for mode in ('known','cached','linear'):
        expected=base.load(out/f'{mode}-0/queries.json');summary=base.load(out/'report.json')['summary'][mode]
        with tempfile.TemporaryDirectory() as td:
            s={'known':KnownQuotientSolver,'cached':QueryCanonicalSolver,'linear':CanonicalVerifySolver}[mode](Path(td)/'db')
            prof=cProfile.Profile()
            try:
                prof.enable();results=[s.solve(c['source']) for c in cases];prof.disable()
                for case,(a,b) in enumerate(zip(results,expected)):
                    for key in ('answer','model','root','authority','metrics','quotient_choice'):
                        assert json.loads(base.encode(a[key]))==b['result'][key],(mode,case,key)
                for name,rows in (('native',study.native_rows(s)),('extension',study.extension_rows(s))):
                    assert base.key_sha(base.encode(sorted(rows.items())))==summary[name+'_digest']
            finally:s.close()
        stats=pstats.Stats(prof);entries=[];callers=[]
        for (filename,line,name),(primitive,total,own,cumulative,parents) in stats.stats.items():
            entries.append(dict(**location(filename,line,name),primitive_calls=primitive,total_calls=total,self_seconds=own,cumulative_seconds=cumulative))
            if name=='_canonical':
                for (f,l,n),counts in parents.items():
                    callers.append(dict(callee=location(filename,line,name),caller=location(f,l,n),counts=list(counts)))
        profiles[mode]=dict(outputs_and_counters_identical=True,total_profiled_seconds=stats.total_tt,total_calls=stats.total_calls,
            functions=sorted(entries,key=lambda r:-r['self_seconds']),canonical_callers=callers)
    class CensusSolver(CanonicalVerifySolver):
        def __init__(self,*args,**kwargs):
            self.earlier={};self.census={};super().__init__(*args,**kwargs)
        def _canonical(self,cnf):
            frozen=tuple(tuple(c) for c in cnf);caller=sys._getframe(1).f_code.co_name
            counts=self.census.setdefault(caller,Counter());counts['calls']+=1;counts['literal_units']+=sum(map(len,frozen))
            earlier=self.earlier.get(frozen)
            if earlier is not None:
                counts['earlier_normalized_output_hits']+=1;counts['hit_literal_units']+=sum(map(len,frozen))
            result=super()._canonical(cnf)
            if earlier is not None:
                assert result[0]==frozen and result[1]==tuple(range(1,len(result[1])+1)) and result[2]==earlier
            self.earlier[result[0]]=result[2]
            return result
    with tempfile.TemporaryDirectory() as td:
        s=CensusSolver(Path(td)/'db');expected=base.load(out/'linear-0/queries.json')
        try:
            for case,b in zip(cases,expected):
                s.earlier={};a=s.solve(case['source'])
                for key in ('answer','model','root','authority','metrics','quotient_choice'):
                    assert json.loads(base.encode(a[key]))==b['result'][key]
            census={k:dict(v) for k,v in s.census.items()}
        finally:s.close()
    result=dict(protocol=study.binding(out/'protocol.json'),profile_source=dict(path=str(Path(__file__).relative_to(root)),sha256=base.sha(__file__)),queries=len(cases),profiles=profiles,canonical_output_census=census,
        limitations=['One instrumented solve-only replay per arm; imports/setup, metadata, warm/cold replay and compression excluded.',
            'Inclusive times overlap and instrumentation affects methods unequally. Use matched report.json workers for runtime comparisons.',
            'The separate census recognizes exact earlier normalized outputs within one query; it retains diagnostic state and is not a production transport mechanism or measured saving. All original input-name maps must remain bound.'])
    base.write(out/'profile.json',result)
    print(base.encode({m:p['functions'][:7] for m,p in profiles.items()}),flush=True)


if __name__=='__main__':profile(Path(sys.argv[1]))
