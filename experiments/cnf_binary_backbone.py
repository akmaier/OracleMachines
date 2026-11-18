"""Reuse partial binary implication evidence to avoid one search branch.

Whole-clause covers retain priority. Successful paths from an unresolved cover
are checked and reused as forced-literal evidence. Only the surviving cofactor
is searched. A negative result compiles the excluded branch directly from the
path into the existing native unit proof format; SAT needs only a full model.
"""
from collections import Counter,deque
from experiments.cnf_accounted_residuals import AccountedResidualSolver
from experiments.cnf_residual_dag import ResidualSolver,FORMAT,two_cnf,restrict
from experiments.cnf_binary_clause_cover import compile_cover


def inspect_backbones(cnf, counts, *, root_limit=8, width_limit=4):
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
        if not root_limit:return None, None, None
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
    if not root_limit:return None, None, None
    # A clause entailed false by the binary subset must be false in its model,
    # and every clause variable must occur in that subset.
    candidates=[]
    for cid,clause in enumerate(cnf):
        counts['binary_cover_clause_checks'] += 1
        if not 3<=len(clause)<=width_limit:continue
        counts['binary_cover_model_literals'] += len(clause)
        if all(abs(l) in model and model[abs(l)] != (l>0) for l in clause):candidates.append(cid)
    if not candidates:
        counts['binary_cover_no_candidates'] += 1;return None, None, None
    graph={}
    for cid in ids:
        a,b=cnf[cid];graph.setdefault(-a,[]).append((b,cid));graph.setdefault(-b,[]).append((a,cid))
        counts['binary_cover_graph_edges'] += 2
    paths={}
    # Memoize completed reachability searches by literal. A budget stop is
    # inconclusive and is never cached as absence of a path.
    def path(root):
        if root in paths:
            counts['binary_cover_reach_hits'] += 1;return paths[root]
        if len(paths)>=root_limit:
            counts['binary_cover_budget_skips'] += 1;return None
        counts['binary_cover_reach_roots'] += 1
        parents={root:None};queue=deque([root])
        while queue and -root not in parents:
            current=queue.popleft()
            for target,cid in graph.get(current,()):
                counts['binary_cover_edge_visits'] += 1
                if target not in parents:parents[target]=(current,cid);queue.append(target)
        counts['binary_cover_reached_entries'] += len(parents)
        result=None
        if -root in parents:
            result=[];current=-root
            while current!=root:
                previous,cid=parents[current];result.append([current,cid]);current=previous
            result.reverse();counts['binary_cover_path_steps'] += len(result)
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
    counts['binary_cover_unresolved'] += 1
    partials=[dict(literal=literal,path=path) for literal,path in paths.items() if path is not None]
    counts['binary_backbone_candidates'] += len(partials)
    return None, None, partials



def check_path(cnf,evidence,counts):
    literal=evidence['literal'];path=evidence['path']
    if type(literal) is not int or not literal or not path:raise ValueError('Invalid binary backbone literal/path')
    current=literal
    for nxt,cid in path:
        if (type(nxt) is not int or not nxt or type(cid) is not int or not 0<=cid<len(cnf)
                or len(cnf[cid])!=2 or cnf[cid]!=tuple(sorted((-current,nxt)))):
            raise ValueError('Invalid binary backbone reason')
        counts['binary_backbone_checked_edges'] += 1;current=nxt
    if current!=-literal:raise ValueError('Binary backbone path does not refute its premise')


def excluded_child(solver,cnf,evidence):
    """Transport retained path reasons into a unit trace, without propagation."""
    check_path(cnf,evidence,solver.counts)
    literal=evidence['literal'];external={abs(literal):literal>0}
    local,names,key=solver._canonical(restrict(cnf,external,solver.counts))
    old=solver._read(key,local,purpose='binary_backbone_excluded')
    if old is not None:
        if old['answer']:raise ValueError('Excluded branch has a checked model')
        solver.counts['binary_backbone_excluded_hits'] += 1;return key
    proof=None
    if () in local:proof=dict(kind='empty')
    else:
        rename={v:i+1 for i,v in enumerate(names)};lookup={c:i for i,c in enumerate(local)}
        assigned={};trace=[]
        for _,cid in evidence['path']:
            reason=cnf[cid];solver.counts['binary_backbone_transport_literals'] += len(reason)
            if literal in reason:continue
            reduced=tuple(sorted((1 if l>0 else -1)*rename[abs(l)] for l in reason if l!=-literal))
            if reduced not in lookup:raise ValueError('Backbone reason disappeared under restriction')
            if any(abs(l) in assigned and assigned[abs(l)]==(l>0) for l in reduced):continue
            left=[l for l in reduced if abs(l) not in assigned]
            if not left:
                proof=dict(kind='units',trace=trace,conflict=lookup[reduced]);break
            if len(left)!=1:raise ValueError('Backbone path did not supply a unit reason')
            forced=left[0];assigned[abs(forced)]=forced>0;trace.append([forced,lookup[reduced]])
            solver.counts['binary_backbone_transported_units'] += 1
        if proof is None:raise ValueError('Backbone path did not compile a contradiction')
    solver._store(key,dict(format=FORMAT,cnf=[list(c) for c in local],answer=False,proof=proof))
    solver.counts['binary_backbone_compiled_children'] += 1
    return key


class BinaryBackboneMixin:
    backbone_policy='first'

    def _choose_backbone(self,cnf,partials):
        if not partials:return None
        if self.backbone_policy=='first':return partials[0]
        if self.backbone_policy!='frequency':raise ValueError('Invalid backbone policy')
        frequencies=Counter(abs(l) for c in cnf for l in c)
        self.counts['binary_backbone_ranking_literals'] += sum(map(len,cnf))
        variable=min(frequencies,key=lambda v:(-frequencies[v],v))
        chosen=next((p for p in partials if abs(p['literal'])==variable),None)
        self.counts['binary_backbone_frequency_hits' if chosen else 'binary_backbone_frequency_misses'] += 1
        return chosen

    def _expand(self,cnf):
        if self.leaves:
            proof,cover,partials=inspect_backbones(cnf,self.counts)
            if proof is not None:return None,proof
            if cover is not None:return None,compile_cover(self,cnf,cover)
            evidence=self._choose_backbone(cnf,partials)
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


class BinaryBackboneSolver(BinaryBackboneMixin,ResidualSolver):pass
class AccountedBinaryBackboneSolver(BinaryBackboneMixin,AccountedResidualSolver):pass

class FrequencyBinaryBackboneSolver(BinaryBackboneMixin,ResidualSolver):backbone_policy='frequency'
class AccountedFrequencyBinaryBackboneSolver(BinaryBackboneMixin,AccountedResidualSolver):backbone_policy='frequency'
