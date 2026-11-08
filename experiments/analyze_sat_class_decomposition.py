#!/usr/bin/env python3
"""Small exhaustive diagnostics for class decomposition of arbitrary CNF.

No production solver changes or timing claims. Checks a reduction into two easy
but interacting classes, and searches bounded heterogeneous strong backdoors.
The subset search is deliberately explicit and combinatorial, not an FPT claim.
"""
import argparse
import hashlib
import itertools
import json
from pathlib import Path
import random
import subprocess


def variables(cnf):
    return sorted({abs(lit) for clause in cnf for lit in clause})


def assignments(names):
    for bits in itertools.product((False,True),repeat=len(names)):
        yield dict(zip(names,bits))


def holds(cnf,assignment):
    return all(any(assignment[abs(lit)]==(lit>0) for lit in clause) for clause in cnf)


def classes(cnf):
    result=[]
    if all(sum(lit>0 for lit in c)<=1 for c in cnf):result.append('Horn')
    if all(sum(lit<0 for lit in c)<=1 for c in cnf):result.append('dual-Horn')
    if all(len(c)<=2 for c in cnf):result.append('2-CNF')
    return result


def restrict(cnf,assignment):
    return [[lit for lit in c if abs(lit) not in assignment] for c in cnf
            if not any(abs(lit) in assignment and assignment[abs(lit)]==(lit>0) for lit in c)]


def split_easy(cnf):
    """Two indicators per old variable. Positive clauses plus negative pairs.
    Both parts separately have an immediate model unless input has an empty
    clause. Their conjunction is equisatisfiable with the arbitrary input.
    """
    names=variables(cnf);position={x:i for i,x in enumerate(names)}
    positive=[[2*position[abs(lit)]+(1 if lit>0 else 2) for lit in c] for c in cnf]
    positive += [[2*i+1,2*i+2] for i in range(len(names))]
    negative=[[-2*i-1,-2*i-2] for i in range(len(names))]
    return names,positive,negative


def check_split(cnf):
    names,positive,negative=split_easy(cnf)
    assert 'dual-Horn' in classes(positive)
    assert {'Horn','2-CNF'}<=set(classes(negative))
    models=0
    for a in assignments(list(range(1,2*len(names)+1))):
        paired=all(a[2*i+1]!=a[2*i+2] for i in range(len(names)))
        old={name:a[2*i+1] for i,name in enumerate(names)}
        expected=paired and holds(cnf,old)
        assert holds(positive+negative,a)==expected
        models+=int(expected)
    assert models==sum(holds(cnf,a) for a in assignments(names))
    if all(cnf):assert holds(positive,{i:True for i in range(1,2*len(names)+1)})
    assert holds(negative,{i:False for i in range(1,2*len(names)+1)})
    return models>0


def bounded_backdoor(cnf,allowed,max_size):
    candidates=branches=literal_visits=0
    for size in range(max_size+1):
        for chosen in itertools.combinations(variables(cnf),size):
            candidates+=1;leaves=[]
            for assignment in assignments(chosen):
                branches+=1;literal_visits+=sum(map(len,cnf))
                residual=restrict(cnf,assignment)
                tags=[c for c in classes(residual) if c in allowed]
                if not tags:break
                leaves.append(dict(assignment=assignment,classes=tags,residual=residual))
            else:
                return dict(found=True,variables=chosen,size=size,leaves=leaves,
                            candidates=candidates,branches=branches,source_literal_visits=literal_visits)
    return dict(found=False,searched_through_size=max_size,candidates=candidates,
                branches=branches,source_literal_visits=literal_visits)


def heterogeneous_example(n):
    # Gaspers et al. (AAAI 2014), introductory example, with integer variable names.
    x=1;a=list(range(2,n+2));b=list(range(n+2,2*n+2));c=list(range(2*n+2,3*n+2))
    return [[x,*[-v for v in a]]]+[[-x,y,z] for y,z in zip(b,c)]


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    if args.output.exists():raise ValueError('Do not overwrite previous evidence')
    clauses=[[sign*(i+1) for i,sign in enumerate(pattern) if sign]
             for pattern in itertools.product((-1,0,1),repeat=2) if any(pattern)]
    cases=[[c for i,c in enumerate(clauses) if mask>>i&1] for mask in range(1<<len(clauses))]
    cases += [[[]],[[1],[-1]],[],[[1,-1]]]
    rng=random.Random(20261108)
    for _ in range(200):
        cases.append([[sign*(i+1) for i,sign in enumerate([rng.choice((-1,0,1)) for _ in range(3)]) if sign]
                      for _ in range(rng.randrange(1,10))])
    answers=[check_split(cnf) for cnf in cases]
    examples=[]
    for n in (3,4):
        cnf=heterogeneous_example(n);assert not classes(cnf)
        results={name:bounded_backdoor(cnf,allowed,2) for name,allowed in
                 [('Horn',['Horn']),('2-CNF',['2-CNF']),('heterogeneous',['Horn','2-CNF'])]}
        mixed=results['heterogeneous'];assert mixed['found'] and mixed['variables']==(1,)
        # Exhaustively check conditioning, without relying on the class tags.
        whole=any(holds(cnf,a) for a in assignments(variables(cnf)))
        leaf_answers=[any(holds(leaf['residual'],a) for a in assignments(variables(leaf['residual'])))
                      for leaf in mixed['leaves']]
        assert whole==any(leaf_answers)
        examples.append(dict(n=n,cnf=cnf,backdoor_search=results,answer=whole,leaf_answers=leaf_answers))
    report=dict(source_commit=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
        script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),seed=20261108,
        reduction_checks=dict(formulas=len(cases),satisfiable=sum(answers),unsatisfiable=len(cases)-sum(answers),
            complete_two_variable_nonempty_clause_formulas=256,pointwise_model_bijection_checked=True),
        heterogeneous_examples=examples,
        example_source='https://www.cs.ox.ac.uk/standa.zivny/publications/gmosz14aaai-preprint.pdf',
        limitations=['Small diagnostic, not Lean verification, a new reduction claim or a production SAT path',
            'Bounded subset enumeration may take sum_i binomial(n,i)*2^i times polynomial scanning work',
            'Failure through size 2 is not a claim that no larger backdoor exists',
            'Class recognition does not remove shared-variable compatibility or the exponential branch count',
            'No measured runtime speedup or minimum-cost expansion guarantee'])
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(dict(reduction_checks=report['reduction_checks'],examples=[dict(n=e['n'],results={k:{x:v for x,v in r.items() if x!='leaves'} for k,r in e['backdoor_search'].items()}) for e in examples])))


if __name__=='__main__':main()
