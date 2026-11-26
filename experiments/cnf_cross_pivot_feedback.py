"""Join independently checked failed branches without retaining open siblings.

Every retained lemma proves seed => -assumption. No sibling verdict is needed
for that implication; a parent refutation still requires a checked joint proof.
"""
from copy import deepcopy
from experiments import cnf_conditioned_saturation as conditioned
from experiments.cnf_probe_support import slice_trace
k=conditioned.kernel
FORMAT='cnf-cross-pivot-feedback-v1'


def bank(seed,lemmas):return tuple(sorted(set(seed)|{(-row['assumption'],) for row in lemmas}))


def validate(source,result,counts,*,order_source=None):
    result=deepcopy(result);seed,order=k._seed(source,order_source,counts)
    if type(result) is not dict or set(result)!={'format','seed','order_source','lemmas','status','proof','closure'} or result['format']!=FORMAT:
        raise ValueError('Invalid cross-pivot summary')
    if result['seed']!=list(map(list,seed)) or result['order_source']!=list(map(list,order)) or type(result['lemmas']) is not list:
        raise ValueError('Changed summary seed or ordering')
    seen=set();variables={abs(l) for cl in seed for l in cl}
    for row in result['lemmas']:
        if type(row) is not dict or set(row)!={'assumption','saturation'}:raise ValueError('Invalid branch lemma')
        lit=row['assumption']
        if type(lit) is not int or abs(lit) not in variables or lit in seen:raise ValueError('Invalid or repeated assumption')
        seen.add(lit);k.validate((*seed,(lit,)),row['saturation'],counts,order_source=order)
        if row['saturation']['status']!='refuted':raise ValueError('Only refuted branches imply units')
        counts['cross_checked_lemmas']+=1
    clauses=bank(seed,result['lemmas'])
    if result['status']=='refuted' and result['closure'] is None:
        k.frozen.check_trace(seed,clauses,None,result['proof'],counts,max(1,len(variables)))
    elif result['status']=='unresolved' and result['proof'] is None:
        k.closure_check.check_closure(clauses,result['closure'],counts)
    else:raise ValueError('Invalid cross-pivot outcome')
    return seed,order,clauses


def collect(source,partitions,counts,*,order_source=None):
    seed,order=k._seed(source,order_source,counts);lemmas={}
    for partition in partitions:
        conditioned.validate(seed,partition,counts,order_source=order)
        for field,lit in (('low',-partition['pivot']),('high',partition['pivot'])):
            if partition[field]['status']=='refuted':
                lemmas.setdefault(lit,dict(assumption=lit,saturation=deepcopy(partition[field])))
    rows=[lemmas[lit] for lit in sorted(lemmas)];clauses=bank(seed,rows);closure,proof=k._close(clauses,counts)
    counts['cross_collected_lemmas']+=len(rows)
    return dict(format=FORMAT,seed=list(map(list,seed)),order_source=list(map(list,order)),lemmas=rows,
        status='refuted' if proof is not None else 'unresolved',proof=proof,closure=closure)


def compact(source,result,counts,*,order_source=None):
    seed,_,clauses=validate(source,result,counts,order_source=order_source);result=deepcopy(result)
    if result['status']!='refuted':return result
    proof,_=slice_trace(clauses,result['proof'],None,counts)
    used={clauses[i] for i in {proof['conflict']}|{i for _,i in proof['units']}}
    rows=[row for row in result['lemmas'] if (-row['assumption'],) in used and (-row['assumption'],) not in seed]
    smaller=bank(seed,rows);positions={cl:i for i,cl in enumerate(smaller)}
    counts['cross_dropped_lemmas']+=len(result['lemmas'])-len(rows)
    result.update(lemmas=rows,proof=dict(units=[[lit,positions[clauses[i]]] for lit,i in proof['units']],conflict=positions[clauses[proof['conflict']]]))
    validate(seed,result,counts,order_source=order_source)
    return result
