"""Diagnostic exact bounded-clause refactoring of saved active Boolean factors."""
from collections import Counter
from itertools import combinations,product
from pathlib import Path
import time
from experiments import cnf_semantic_buckets as b
from experiments.compare_cnf_verified_operators import base,old
out=Path(__file__).parent
PARENT=Path('experiments/results/cnf-selective-width-buckets/remaining.json')


def cover(f,width,c):
    scope=f['scope'];n=len(scope);full=(1<<(1<<n))-1;target=full^f['bits'];covered=0;clauses=[]
    masks=[sum(1<<row for row in range(1<<n) if row>>i&1) for i in range(n)]
    for size in range(1,min(width,n)+1):
        for slots in combinations(range(n),size):
            for signs in product((-1,1),repeat=size):
                clause=tuple(sorted(sign*scope[i] for i,sign in zip(slots,signs)))
                if any(set(prev)<=set(clause) for prev in clauses):continue
                mask=full
                for i,sign in zip(slots,signs):mask &= masks[i] if sign<0 else full^masks[i]
                c['candidate_clauses']+=1
                if mask & f['bits']:continue
                clauses.append(clause);covered |= mask
    if covered!=target:return None,dict(covered=covered.bit_count(),zeros=target.bit_count())
    # Independent row evaluation of the exact reconstructed relation.
    for row in range(1<<n):
        assignment={v:bool(row>>i&1) for i,v in enumerate(scope)}
        assert b.native.holds(clauses,assignment)==bool(f['bits']>>row&1);c['checked_rows']+=1
    return clauses,dict(covered=covered.bit_count(),zeros=target.bit_count())


def main():
    records=[]
    for width in (2,3,4):
        counts=Counter();start=time.perf_counter()
        for root in base.load(PARENT)['cases']:
            for leaf in root['unresolved_leaves']:
                active=[];splits=[]
                for factor in leaf['active_factors']:
                    f=dict(scope=factor['scope'],bits=factor['bits']);n=len(f['scope'])
                    if n<=3 or f['bits']==(1<<(1<<n))-1:active.append(f);continue
                    clauses,diag=cover(f,width,counts)
                    edges=set() if clauses is None else {tuple(sorted(x)) for clause in clauses for x in combinations(map(abs,clause),2)}
                    accepted=clauses is not None and len(edges)<n*(n-1)//2
                    splits.append(dict(factor=factor['index'],width=n,clauses=clauses,removed_edges=n*(n-1)//2-len(edges) if clauses is not None else None,accepted=accepted,diagnostic=diag))
                    active.extend(b.leaf(clause) for clause in clauses) if accepted else active.append(f)
                factors=active;active=set(range(len(factors)));steps=[];spent=leaf['spent']
                while True:
                    if any(factors[i]['bits']==0 for i in active):status='unsat';break
                    variables=sorted({v for i in active for v in factors[i]['scope']})
                    if not variables:status='sat';break
                    choices=[]
                    for v in variables:
                        ids=sorted(i for i in active if v in factors[i]['scope']);bag={x for i in ids for x in factors[i]['scope']};choices.append((len(bag),len(ids),v,ids))
                    size,_,pivot,ids=min(choices);cost=(1<<size)*len(ids)
                    if size>9 or spent+cost>262144:status='unresolved';break
                    spent+=cost;scope,bits,choice=b.project([factors[i] for i in ids],pivot,counts);scope,bits=b.reduce_support(scope,bits,counts);steps.append(dict(variable=pivot,inputs=ids,scope=scope,bits=bits,choices=choice));active.difference_update(ids);active.add(len(factors));factors.append(dict(scope=scope,bits=bits))
                records.append(dict(id=root['id'],node=leaf['node'],max_clause_width=width,refinements=splits,status=status,steps=steps,next_width=None if status!='unresolved' else size,spent=spent))
        print(width,counts,round(time.perf_counter()-start,4),[(r['id'],r['node'],r['status'],len(r['steps']),r['next_width'],sum(x['accepted'] for x in r['refinements'])) for r in records if r['max_clause_width']==width],flush=True)
    base.write(out/'factor-cover-screen.json',dict(parent=old.binding(PARENT),records=records,scope='Diagnostic local relation covers independently checked row by row; continuation is only a search screen until independently certified. No root coverage or matched cost claim.'))


if __name__=='__main__':main()
