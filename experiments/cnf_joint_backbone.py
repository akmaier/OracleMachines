"""Batch at most two checked binary consequences with native split/unit proofs.

Discovery shares its graph and skips consequences implied by a selected literal.
Compilation conditions original reason clauses; it never reuses raw indices in a
renamed cofactor. Intermediate cached answers retain priority over fresh solving.
"""
from collections import Counter,deque
from experiments.cnf_residual_dag import two_cnf,restrict,FORMAT
from experiments.cnf_binary_backbone import check_path,excluded_child
from experiments.cnf_binary_clause_cover import compile_cover
from experiments.cnf_targeted_backbone import TargetedBackboneMixin
from experiments.cnf_affine_probe_safe import InputSafeAffineProbeSolver


def discover(cnf, counts, *, root_limit=8, width_limit=4, target_limit=8):
    if type(target_limit) is not int or not 1<=target_limit<=8:raise ValueError('Invalid joint target limit')
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
    frequencies=Counter(abs(l) for c in cnf if len(c)==2 for l in c)
    counts['ranked_target_ranking_literals'] += sum(map(len,cnf))
    # At most eight targeted roots, sharing completed cover searches. Only two
    # consequences not yet implied by earlier selections are retained. The closure is a selection aid;
    # source-indexed contradiction paths remain the actual proof evidence.
    counts['joint_sort_variables']+=len(frequencies)
    choices=sorted(frequencies,key=lambda v:(-frequencies[v],v))[:target_limit]
    selected=[];covered=set()
    for variable in choices:
        literal=-variable if model[variable] else variable
        if -literal in covered:
            counts['joint_redundant_candidates']+=1;continue
        counts['joint_target_candidates']+=1
        got=path(literal,targeted=True)
        if got is None:continue
        selected.append(dict(literal=literal,path=got));counts['joint_paths_found']+=1
        if len(selected)==2:break
        queue=deque([-literal]);covered.add(-literal)
        counts['joint_closure_roots']+=1
        while queue:
            current=queue.popleft()
            for nxt,cid in graph.get(current,()):
                counts['joint_closure_edge_visits']+=1
                if nxt not in covered:covered.add(nxt);queue.append(nxt)
    counts['joint_selected_paths']+=len(selected)
    return None,None,selected or None


def excluded_context(solver,cnf,evidence,fixed):
    """Compile a checked original path under earlier surviving assignments."""
    check_path(cnf,evidence,solver.counts);literal=evidence['literal'];variable=abs(literal)
    if variable in fixed:raise ValueError('Repeated joint variable')
    external={**fixed,variable:literal>0}
    local,names,key=solver._canonical(restrict(cnf,external,solver.counts))
    old=solver._read(key,local,purpose='joint_excluded')
    if old is not None:
        if old['answer']:raise ValueError('Excluded joint branch has a model')
        solver.counts['joint_excluded_hits']+=1;return key
    proof=None
    if () in local:proof=dict(kind='empty')
    else:
        rename={v:i+1 for i,v in enumerate(names)};lookup={c:i for i,c in enumerate(local)};assigned={};trace=[]
        for _,cid in evidence['path']:
            reason=cnf[cid];solver.counts['joint_transport_literals']+=len(reason)
            if any(abs(l) in external and external[abs(l)]==(l>0) for l in reason):continue
            reduced=tuple(sorted((1 if l>0 else -1)*rename[abs(l)] for l in reason if abs(l) not in external))
            if reduced not in lookup:raise ValueError('Joint reason disappeared under conditioning')
            if any(abs(l) in assigned and assigned[abs(l)]==(l>0) for l in reduced):continue
            left=[l for l in reduced if abs(l) not in assigned]
            if not left:
                proof=dict(kind='units',trace=trace,conflict=lookup[reduced]);break
            if len(left)!=1:raise ValueError('Joint path did not supply a unit reason')
            forced=left[0];assigned[abs(forced)]=forced>0;trace.append([forced,lookup[reduced]])
            solver.counts['joint_transported_units']+=1
        if proof is None:raise ValueError('Joint path did not compile a contradiction')
    solver._store(key,dict(format=FORMAT,cnf=[list(c) for c in local],answer=False,proof=proof))
    solver.counts['joint_compiled_excluded']+=1
    return key


def force_all(solver,cnf,evidence):
    if not 1<=len(evidence)<=2:raise ValueError('One or two joint paths required')
    for e in evidence:check_path(cnf,e,solver.counts)
    if len({abs(e['literal']) for e in evidence})!=len(evidence):raise ValueError('Joint variables must differ')
    # Preserve the single-consequence implementation when no second additional
    # consequence was found; this also avoids a gratuitous prefix cache lookup.
    if len(evidence)==1:
        e=evidence[0];l=e['literal'];v=abs(l)
        model,live=solver._visit(restrict(cnf,{v:l<0},solver.counts))
        if model is not None:return {v:l<0,**model},None
        excluded=excluded_child(solver,cnf,e)
        return None,dict(kind='split',variable=v,low=live if l>0 else excluded,high=excluded if l>0 else live)
    fixed={};parents=[];model=None;live=None
    for index,e in enumerate(evidence):
        parents.append((dict(fixed),e));fixed[abs(e['literal'])]=e['literal']<0
        child=restrict(cnf,fixed,solver.counts)
        if index+1<len(evidence):
            local,names,key=solver._canonical(child);old=solver._read(key,local,purpose='joint_prefix')
            if old is not None:
                solver.counts['joint_prefix_hits']+=1;live=key
                if old['answer']:model={oldvar:old['model'][j] for j,oldvar in enumerate(names)}
                break
        else:model,live=solver._visit(child)
    if model is not None:
        solver.counts['joint_positive_lifts']+=1;return {**fixed,**model},None
    solver.counts['joint_negative_batches']+=1
    for index in range(len(parents)-1,-1,-1):
        context,e=parents[index];raw=restrict(cnf,context,solver.counts)
        local,names,key=solver._canonical(raw);v=abs(e['literal'])
        if v not in names:
            if live!=key:raise ValueError('Irrelevant joint variable changed residual')
            solver.counts['joint_irrelevant_variables']+=1;continue
        excluded=excluded_context(solver,cnf,e,context);variable=names.index(v)+1
        proof=dict(kind='split',variable=variable,low=live if e['literal']>0 else excluded,high=excluded if e['literal']>0 else live)
        if index==0:return None,proof
        solver._store(key,dict(format=FORMAT,cnf=[list(c) for c in local],answer=False,proof=proof))
        solver.counts['joint_compiled_parents']+=1;live=key
    raise ValueError('No joint root split')


class JointBackboneMixin(TargetedBackboneMixin):
    joint_single_only=False

    def _expand(self,cnf):
        if self.leaves:
            proof,cover,parts=discover(cnf,self.counts)
            if proof is not None:return None,proof
            if cover is not None:return None,compile_cover(self,cnf,cover)
            if parts:return force_all(self,cnf,parts[:1] if self.joint_single_only else parts)
        # Replace the frozen targeted recognizer while preserving the earlier
        # witness/negative reuse layers in the full solver's MRO.
        return super(TargetedBackboneMixin,self)._expand(cnf)


class JointBackboneSolver(InputSafeAffineProbeSolver,JointBackboneMixin):pass
class SingleFromJointSolver(JointBackboneSolver):joint_single_only=True
