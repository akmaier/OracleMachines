"""One targeted binary implication search after the unchanged whole-cover budget.

The chosen variable maximizes total frequency, ties by smallest identifier.
Whole covers retain priority. A source-indexed path is checked before using the
existing direct excluded-child compiler and native split proof format.
"""
from collections import Counter,deque
from experiments.cnf_accounted_residuals import AccountedResidualSolver
from experiments.cnf_residual_dag import ResidualSolver,two_cnf,restrict
from experiments.cnf_binary_clause_cover import compile_cover
from experiments.cnf_binary_backbone import check_path,excluded_child


def inspect_targeted_backbone(cnf, counts, *, root_limit=8, width_limit=4):
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
    # The model excludes one polarity from being forced false. Query only its
    # opposite for the frequency-selected variable. A completed cover search
    # (including a negative result) is reusable; a budget stop is not cached.
    counts['binary_target_calls'] += 1
    frequencies=Counter(abs(l) for c in cnf for l in c)
    counts['binary_target_ranking_literals'] += sum(map(len,cnf))
    variable=min(frequencies,key=lambda v:(-frequencies[v],v))
    if variable not in model:
        counts['binary_target_absent_variables'] += 1
        return None,None,None
    literal=-variable if model[variable] else variable
    got=path(literal,targeted=True)
    if got is None:
        counts['binary_target_misses'] += 1
        return None,None,None
    counts['binary_target_found'] += 1
    return None,None,[dict(literal=literal,path=got)]


class TargetedBackboneMixin:
    def _expand(self,cnf):
        if self.leaves:
            proof,cover,partials=inspect_targeted_backbone(cnf,self.counts)
            if proof is not None:return None,proof
            if cover is not None:return None,compile_cover(self,cnf,cover)
            evidence=partials[0] if partials else None
            if evidence is not None:
                check_path(cnf,evidence,self.counts)
                literal=evidence['literal'];variable=abs(literal)
                self.counts['binary_backbone_selections'] += 1
                model,live=self._visit(restrict(cnf,{variable:literal<0},self.counts))
                if model is not None:
                    self.counts['binary_backbone_positive_lifts'] += 1
                    return {variable:literal<0,**model},None
                excluded=excluded_child(self,cnf,evidence)
                self.counts['binary_backbone_negative_splits'] += 1
                return None,dict(kind='split',variable=variable,low=live if literal>0 else excluded,high=excluded if literal>0 else live)
        return super()._expand(cnf)

class TargetedBackboneSolver(TargetedBackboneMixin,ResidualSolver):pass
class AccountedTargetedBackboneSolver(TargetedBackboneMixin,AccountedResidualSolver):pass
