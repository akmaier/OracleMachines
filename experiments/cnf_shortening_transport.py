"""Transport checked guards after satisfaction, then absent-coordinate checks.

A satisfied support clause can contain variables absent from the residual. Its
whole clause must be restricted before looking up surviving coordinates.
"""
from experiments import cnf_residual_dag as native
from experiments.cnf_conditional_unit_support import check_template
from experiments.cnf_guard_context_solver import check_bound_rup


def transport_state(context, template, missing, counts):
    inverse=context.inverse;fixed=context.fixed;positions=context.positions
    if any(v not in inverse for v,_ in missing):
        counts['absent_guard_variables']+=1
        return None
    translated=[]
    for clause in template['clauses']:
        raw=native.restrict_scan((clause,),fixed,counts)
        if not raw:
            translated.append(None)
            continue
        if any(abs(l) not in inverse for l in raw[0]):
            counts['local_support_misses']+=1
            return None
        reduced=tuple(sorted(inverse[abs(l)]*(1 if l>0 else -1) for l in raw[0]))
        counts['local_containment_clauses']+=1
        if reduced not in positions:
            counts['local_support_misses']+=1
            return None
        translated.append(reduced)
    clauses=sorted({cl for cl in translated if cl is not None});ids={cl:i for i,cl in enumerate(clauses)}
    trace=[];conflict=None
    for lit,cid in template['trace']:
        counts['trace_transport_steps']+=1
        if abs(lit) in fixed:
            if fixed[abs(lit)]==(lit>0):continue
            conflict=ids[translated[cid]]
            break
        if translated[cid] is None or abs(lit) not in inverse:
            raise ValueError('Unbound surviving trace')
        trace.append([inverse[abs(lit)]*(1 if lit>0 else -1),ids[translated[cid]]])
    if conflict is None:conflict=ids[translated[template['conflict']]]
    assumptions=sorted([[inverse[v],b] for v,b in missing])
    lifted=dict(clauses=[list(cl) for cl in clauses],assumptions=assumptions,trace=trace,conflict=conflict)
    check_template(lifted,counts)
    clause=sorted(-v if b else v for v,b in assumptions)
    proof=dict(units=[[l,positions[clauses[cid]]] for l,cid in trace],conflict=positions[clauses[conflict]])
    check_bound_rup(context,clause,proof,counts)
    return dict(clause=clause,template=lifted,proof=proof)
