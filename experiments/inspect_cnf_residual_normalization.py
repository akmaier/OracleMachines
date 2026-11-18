#!/usr/bin/env python3
"""Untimed exact-raw census and clause-invariant diagnosis before optimization."""
from collections import Counter
from pathlib import Path
import json,sys,tempfile
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_publication_batches as prior
from experiments.cnf_publication_batches import BatchedPublicationSolver
base=prior.base
PARENT=Path('experiments/results/cnf-publication-batches')


def inspect(out):
    out.mkdir(exist_ok=True);parent=base.load(PARENT/'checkpoint.json')
    for f,h in parent['source_fingerprints'].items():assert base.sha(f)==h,f
    cases=base.load(PARENT/'cases.json');expected=base.load(PARENT/'batch32-0/queries.json')
    class Census(BatchedPublicationSolver):
        def __init__(self,*a,**k):self.seen={};self.sites={};self.edges=Counter();super().__init__(*a,**k)
        def _canonical(self,cnf):
            raw=tuple(tuple(c) for c in cnf);site=sys._getframe(1).f_code.co_name
            counts=self.sites.setdefault(site,Counter());counts['calls']+=1
            pending=self._verification_canonical
            if pending is not None and cnf is pending[0]:
                counts['direct_verifier_transports']+=1;return super()._canonical(cnf)
            counts['normalizations']+=1;length=sum(map(len,raw));counts['literal_units']+=length
            ordered=all(all(a<b for a,b in zip(c,c[1:])) for c in raw)
            clean=all(not any(-v in set(c) for v in c) for c in raw)
            if ordered and clean:
                counts['ordered_clean_calls']+=1;counts['ordered_clean_literal_units']+=length
            if len(set(raw))<len(raw):counts['duplicate_clause_inputs']+=1
            earlier=self.seen.get(raw)
            if earlier is not None:
                counts['exact_repeats']+=1;counts['repeat_literal_units']+=length;self.edges[earlier[0]+' -> '+site]+=1
            result=super()._canonical(cnf)
            if earlier is not None:assert earlier[1]==result
            self.seen[raw]=(site,result)
            return result
    with tempfile.TemporaryDirectory() as td:
        s=Census(Path(td)/'db')
        try:
            for c,e in zip(cases,expected):
                s.seen={};got=s.solve(c['source'])
                for f in ('answer','model','root','authority','metrics','quotient_choice'):
                    assert json.loads(base.encode(got[f]))==e['result'][f]
            summary=base.load(PARENT/'report.json')['summary']['batch32']
            for name,rows in (('native',prior.native_rows(s)),('extension',prior.extension_rows(s))):
                assert base.key_sha(base.encode(sorted(rows.items())))==summary[name+'_digest']
            result=dict(parent=prior.binding(PARENT/'checkpoint.json'),source=dict(path=str(Path(__file__).relative_to(Path(__file__).resolve().parents[1])),sha256=base.sha(__file__)),queries=len(cases),outputs_counters_and_payloads_identical=True,
                sites={k:dict(v) for k,v in s.sites.items()},repeat_edges=dict(s.edges),
                limits=['Untimed diagnostic with retained raw inputs; no production cache or saved work is implemented.',
                    'Strict ordered, distinct, tautology-free literals survive deletion/restriction, but global clause order, uniqueness and compact variable names need not survive.'])
        finally:s.close()
    base.write(out/'diagnosis.json',result);print(base.encode(result['sites']),flush=True)


if __name__=='__main__':inspect(Path(sys.argv[1]))
