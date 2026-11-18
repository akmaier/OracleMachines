"""Bounded binary reachability covers a wider source clause with refutations.

A path l -> -l entails not-l. If every literal in a source clause has such a
path, the full source is UNSAT even if its binary subset is satisfiable. Shared
reachability is local to one exact residual. The compiler emits only old native
split/unit proofs and the unchanged checker validates every published node.
"""
from collections import Counter, deque
from experiments.cnf_accounted_residuals import AccountedResidualSolver
from experiments.cnf_residual_dag import ResidualSolver, FORMAT, two_cnf, propagate, restrict


def inspect(cnf, counts, *, root_limit=8, width_limit=4):
    if type(root_limit) is not int or root_limit < 0 or type(width_limit) is not int or width_limit < 3:
        raise ValueError('Invalid binary-cover limits')
    # Preserve the preceding negative-subset gate and accounting exactly.
    counts['binary_subset_calls'] += 1
    ids=[];wide=positive=negative=False
    for cid, clause in enumerate(cnf):
        counts['binary_subset_width_checks'] += 1
        if len(clause)<2:
            counts['binary_subset_unit_skips'] += 1;return None, None
        if len(clause)==2:
            ids.append(cid);counts['binary_subset_sign_literals'] += 2
            positive |= clause[0]>0 and clause[1]>0
            negative |= clause[0]<0 and clause[1]<0
        else:wide=True
    if not wide or not ids:
        counts['binary_subset_shape_skips'] += 1;return None, None
    if not (positive and negative):
        counts['binary_subset_uniform_skips'] += 1
        if not root_limit:return None, None
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
            return proof, None
        counts['binary_subset_satisfiable_misses'] += 1
    if not root_limit:return None, None
    # A clause entailed false by the binary subset must be false in its model,
    # and every clause variable must occur in that subset.
    candidates=[]
    for cid,clause in enumerate(cnf):
        counts['binary_cover_clause_checks'] += 1
        if not 3<=len(clause)<=width_limit:continue
        counts['binary_cover_model_literals'] += len(clause)
        if all(abs(l) in model and model[abs(l)] != (l>0) for l in clause):candidates.append(cid)
    if not candidates:
        counts['binary_cover_no_candidates'] += 1;return None, None
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
            return None, dict(clause_index=cid,paths=evidence)
    counts['binary_cover_unresolved'] += 1
    return None, None


def compile_cover(solver, cnf, cover):
    """Return a root proof; publish checked children without recursive solving."""
    cid=cover['clause_index']
    if type(cid) is not int or not 0<=cid<len(cnf):raise ValueError('Invalid cover source index')
    clause=cnf[cid]
    if len(clause)<3 or len(cover['paths'])!=len(clause):raise ValueError('Incomplete cover')
    for literal,path in zip(clause,cover['paths']):
        current=literal
        for nxt,reason in path:
            if (type(nxt) is not int or not nxt or type(reason) is not int or not 0<=reason<len(cnf)
                    or len(cnf[reason])!=2 or cnf[reason]!=tuple(sorted((-current,nxt)))):
                raise ValueError('Invalid binary cover path')
            solver.counts['binary_cover_checked_edges'] += 1;current=nxt
        if current!=-literal:raise ValueError('Incomplete binary implication')
    def node(external,index,terminal=False,root=False):
        source=cnf if root else restrict(cnf,external,solver.counts)
        local,names,key=solver._canonical(source)
        if not root:
            old=solver._read(key,local,purpose='binary_cover_compile')
            if old is not None:
                if old['answer']:raise ValueError('Cover contradicts a known model')
                return key
        proof=None
        if () in local:proof=dict(kind='empty')
        elif not root:
            _,trace,conflict=propagate(local,solver.counts)
            if conflict is not None:proof=dict(kind='units',trace=trace,conflict=conflict)
        if proof is None and not terminal and index==len(clause)-2:
            # Reuse two retained one-way paths and the now-binary source clause:
            # y -> -y, and -y -> z -> -z -> y. No fresh SCC is necessary when
            # their variables survive the stronger assignment unchanged.
            y,z=clause[index:];pair=cover['paths'][index:]
            used={abs(l) for path in pair for _,reason in path for l in cnf[reason]}
            if not used.intersection(external):
                rename={v:i+1 for i,v in enumerate(names)};lookup={c:i for i,c in enumerate(local)}
                def lit(l):return (1 if l>0 else -1)*rename[abs(l)]
                def transport(path):
                    result=[]
                    for target,reason in path:
                        mapped=tuple(sorted(lit(l) for l in cnf[reason]))
                        result.append([lit(target),lookup[mapped]])
                        solver.counts['binary_cover_transported_edges'] += 1
                    return result
                edge=lookup[tuple(sorted((lit(y),lit(z))))]
                forward=transport(pair[0]);backward=[[lit(z),edge]]+transport(pair[1])+[[lit(y),edge]]
                if y<0:forward,backward=backward,forward
                proof=dict(kind='implications',variable=abs(lit(y)),forward=forward,backward=backward)
                solver.counts['binary_cover_pair_reuses'] += 1
            else:
                # Conservative recovery if a path vertex was fixed. The full
                # native checker remains the final authority in either case.
                ids=[i for i,c in enumerate(local) if len(c)<=2];extra=Counter()
                model,proof=two_cnf(tuple(local[i] for i in ids),extra)
                if model is not None:raise ValueError('Covered binary pair was satisfiable')
                for name in ('forward','backward'):proof[name]=[[l,ids[i]] for l,i in proof[name]]
                solver.counts['binary_cover_pair_scc_repairs'] += 1
                solver.counts.update({'binary_cover_repair_'+k:v for k,v in extra.items()})
        if proof is None:
            if terminal or index==len(clause)-1:raise ValueError('Covered condition did not unit-refute')
            literal=clause[index];variable=names.index(abs(literal))+1
            yes={**external,abs(literal):literal>0};no={**external,abs(literal):literal<0}
            yes_key=node(yes,index,terminal=True);no_key=node(no,index+1)
            proof=dict(kind='split',variable=variable,low=no_key if literal>0 else yes_key,high=yes_key if literal>0 else no_key)
        if root:return proof
        solver._store(key,dict(format=FORMAT,cnf=[list(c) for c in local],answer=False,proof=proof))
        solver.counts['binary_cover_compiled_children'] += 1
        return key
    return node({},0,root=True)


class BinaryClauseCoverMixin:
    def _expand(self,cnf):
        if self.leaves:
            proof,cover=inspect(cnf,self.counts)
            if proof is not None:return None,proof
            if cover is not None:return None,compile_cover(self,cnf,cover)
        return super()._expand(cnf)


class BinaryClauseCoverSolver(BinaryClauseCoverMixin,ResidualSolver):pass
class AccountedBinaryClauseCoverSolver(BinaryClauseCoverMixin,AccountedResidualSolver):pass
