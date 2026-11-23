"""Try the bounded existing proof/model pools before conditional recovery.

No SAT search occurs here. A negative hit must pass the existing native subset
checker; a positive vector is checked against every target clause and checked
again on native publication. Misses are not cached or treated as answers.
"""
from experiments.cnf_residual_dag import FORMAT


def witness_candidate(solver,cnf):
    if not solver.witness_pool or not cnf or () in cnf:return None
    c=solver.counts;c['witness_probes']+=1;c['witness_shape_literals']+=sum(map(len,cnf))
    variables=max(abs(l) for cl in cnf for l in cl);tried=0
    for (n,packed) in reversed(solver.witness_pool):
        c['witness_index_entries']+=1
        if n!=variables:continue
        tried+=1;c['witness_candidates']+=1;valid=True
        for clause in cnf:
            c['witness_checked_clauses']+=1;satisfied=False
            for literal in clause:
                c['witness_literal_tests']+=1;i=abs(literal)-1
                if bool(packed[i//8] & (1<<(i%8)))==(literal>0):satisfied=True;break
            if not satisfied:valid=False;break
        if valid:
            c['witness_hits']+=1;c['witness_model_variables']+=n
            return [bool(packed[i//8] & (1<<(i%8))) for i in range(n)]
        if tried==solver.candidate_limit:break
    c['witness_misses']+=1;return None


def try_pools(solver,cnf,key):
    """Publish a hit for an already canonicalized target on an owned idle DB.

    Causal discovery/materialization inside the existing negative pool retains
    its own caps and costs. It is not a constant-time lookup. A following native
    fallback may repeat unsuccessful checks; no miss cache is introduced.
    """
    solver.counts['pool_priority_calls']+=1;solver.db.start();route=None
    try:
        proof=solver._negative_reuse(cnf)
        node=dict(format=FORMAT,cnf=[list(cl) for cl in cnf],answer=False)
        if proof is not None:
            node['proof']=proof;route='negative-pool'
        else:
            model=witness_candidate(solver,cnf)
            if model is not None:node.update(answer=True,model=model);route='witness-pool'
        if route is not None:solver._store(key,node)
        solver.db.finish()
    except BaseException:
        solver.db.abort();raise
    finally:solver.db.active=False
    if route is None:
        solver.counts['pool_priority_misses']+=1;return None
    if route=='negative-pool':solver._admit_negative(dict(root=key,answer=False,authority='native'))
    solver._peak();solver.counts['pool_priority_'+route.replace('-','_')+'_hits']+=1
    return route
