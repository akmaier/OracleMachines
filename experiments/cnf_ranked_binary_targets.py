"""Optional bounded target rankings after the frozen binary-cover discovery.

The preceding whole-cover phase is copied unchanged to share its graph and path
cache without mutating fingerprinted historical source. Only the final target
ranking changes. Evidence still uses the original native checker/compiler.
Callers scope replacement of the experimental recognizer to one serial worker;
this module does not alter any solver default or install a global patch.
"""
from collections import Counter,deque
from experiments.cnf_residual_dag import two_cnf


def discover(cnf, counts, *, policy, root_limit=8, width_limit=4):
    if policy not in ('total4', 'binary1'):raise ValueError('Invalid target ranking')
    if type(root_limit) is not int or root_limit < 0 or type(width_limit) is not int or width_limit < 3:
        raise ValueError('Invalid binary-cover limits')
    # Preserve the preceding negative-subset gate and accounting exactly.
    counts['binary_subset_calls'] += 1
    ids=[];wide=positive=negative=False
    for cid, clause in enumerate(cnf):
        counts['binary_subset_width_checks'] += 1
        if len(clause)<2:
            counts['binary_subset_unit_skips'] += 1;return None, None, None
        if len(clause)==2:
            ids.append(cid);counts['binary_subset_sign_literals'] += 2
            positive |= clause[0]>0 and clause[1]>0
            negative |= clause[0]<0 and clause[1]<0
        else:wide=True
    if not wide or not ids:
        counts['binary_subset_shape_skips'] += 1;return None, None, None
    if not (positive and negative):
        counts['binary_subset_uniform_skips'] += 1
        model={abs(l):bool(positive) for i in ids for l in cnf[i]}
        counts['binary_cover_uniform_models'] += 1
        counts['binary_cover_uniform_model_literals'] += 2*len(ids)
    else:
        local=Counter();model,proof=two_cnf(tuple(cnf[i] for i in ids),local)
        counts.update({'binary_subset_'+k:v for k,v in local.items()});counts['binary_subset_scc_calls'] += 1
        if proof is not None:
            counts['binary_subset_refutations'] += 1
            for name in ('forward','backward'):
                proof[name]=[[lit,ids[cid]] for lit,cid in proof[name]]
                counts['binary_subset_path_steps'] += len(proof[name])
            return proof, None, None
        counts['binary_subset_satisfiable_misses'] += 1
    # A clause entailed false by the binary subset must be false in its model,
    # and every clause variable must occur in that subset.
    candidates=[]
    for cid,clause in enumerate(cnf):
        counts['binary_cover_clause_checks'] += 1
        if not 3<=len(clause)<=width_limit:continue
        counts['binary_cover_model_literals'] += len(clause)
        if all(abs(l) in model and model[abs(l)] != (l>0) for l in clause):candidates.append(cid)
    if not candidates:
        counts['binary_cover_no_candidates'] += 1
    graph=None
    paths={}
    # Memoize completed reachability searches by literal. A budget stop is
    # inconclusive and is never cached as absence of a path.
    def path(root, *, targeted=False):
        prefix = 'binary_target_' if targeted else 'binary_cover_'
        if root in paths:
            counts[prefix+'reach_hits'] += 1;return paths[root]
        if not targeted and len(paths)>=root_limit:
            counts['binary_cover_budget_skips'] += 1;return None
        nonlocal graph
        if graph is None:
            graph={}
            for cid in ids:
                a,b=cnf[cid];graph.setdefault(-a,[]).append((b,cid));graph.setdefault(-b,[]).append((a,cid))
                counts['binary_cover_graph_edges'] += 2
        counts[prefix+'reach_roots'] += 1
        parents={root:None};queue=deque([root])
        while queue and -root not in parents:
            current=queue.popleft()
            for target,cid in graph.get(current,()):
                counts[prefix+'edge_visits'] += 1
                if target not in parents:parents[target]=(current,cid);queue.append(target)
        counts[prefix+'reached_entries'] += len(parents)
        result=None
        if -root in parents:
            result=[];current=-root
            while current!=root:
                previous,cid=parents[current];result.append([current,cid]);current=previous
            result.reverse();counts[prefix+'path_steps'] += len(result)
        paths[root]=result;return result
    for cid in candidates:
        evidence=[]
        for literal in cnf[cid]:
            got=path(literal)
            if got is None:break
            evidence.append(got)
        else:
            counts['binary_cover_found'] += 1
            return None, dict(clause_index=cid,paths=evidence), None
    if candidates:counts['binary_cover_unresolved'] += 1
    # Use the binary model to exclude one polarity. A completed cover search
    # is reusable; a budget skip is not a completed negative reachability result.
    counts['ranked_target_calls'] += 1
    frequencies=Counter(abs(l) for c in cnf if policy=='total4' or len(c)==2 for l in c)
    counts['ranked_target_ranking_literals'] += sum(map(len,cnf))
    # Sorting is charged separately: unlike the old single minimum, this costs
    # O(V log V) in the comparison model. At most four extra BFS roots are tried.
    counts['ranked_target_sort_variables'] += len(frequencies)
    choices=sorted(frequencies,key=lambda v:(-frequencies[v],v))[:4 if policy=='total4' else 1]
    for variable in choices:
        counts['ranked_target_candidates'] += 1
        if variable not in model:
            counts['ranked_target_absent_variables'] += 1
            continue
        literal=-variable if model[variable] else variable
        got=path(literal,targeted=True)
        if got is not None:
            counts['ranked_target_found'] += 1
            return None,None,[dict(literal=literal,path=got)]
    counts['ranked_target_misses'] += 1
    return None,None,None
