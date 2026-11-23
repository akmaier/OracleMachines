"""Carry minimum original-clause representatives through a checked proof.

The root is an immutable canonical CNF read through the native verifier. A
source-variable index selects live representatives touched by each new path
assignment. Equal residuals stay equal under later restrictions, so their
smallest original index is sufficient. Component edges retain the global map.
"""
from collections import Counter
from contextlib import contextmanager
from dataclasses import dataclass
from unittest.mock import patch

from experiments import cnf_learned_conditional as learned
from experiments.cnf_conditional_unit_support import FORMAT_HINT, ExtractionBudget, check_template
from experiments.cnf_residual_dag import restrict


@dataclass(frozen=True, slots=True)
class OriginState:
    # Private call-local maps; advance never mutates a preceding state.
    by_clause: dict
    by_id: dict


class OriginIndex:
    """Internal checked-canonical-source precondition, as in fused preimages."""
    def __init__(self, root, counts):
        self.counts = counts
        self.postings = {}
        by_clause = {}
        for cid, clause in enumerate(root):
            by_clause.setdefault(clause, cid)
            for lit in clause:
                self.postings.setdefault(abs(lit), []).append(cid)
                counts['origin_index_literals'] += 1
        self.initial = OriginState(by_clause, {cid: cl for cl, cid in by_clause.items()})
        counts['origin_index_variables'] += len(self.postings)
        counts['origin_initial_representatives'] += len(by_clause)
        self.live_slots = 2 * len(by_clause)
        counts['origin_peak_live_map_slots'] = self.live_slots

    def advance(self, state, assignment):
        c = self.counts
        c['origin_transition_calls'] += 1
        if not assignment:
            c['origin_identity_reuses'] += 1
            return state
        touched = set()
        for v in assignment:
            ids = self.postings.get(v, ())
            c['origin_posting_visits'] += len(ids)
            touched.update(ids)
        affected = sorted(cid for cid in touched if cid in state.by_id)
        c['origin_live_affected_representatives'] += len(affected)
        c['origin_peak_affected_ids'] = max(c['origin_peak_affected_ids'], len(touched))
        if not affected:
            c['origin_identity_reuses'] += 1
            return state
        # Copy map containers, retaining immutable clause tuples. Account for
        # both copies before deletions/merges; this is not constant-space work.
        by_clause, by_id = dict(state.by_clause), dict(state.by_id)
        c['origin_copied_map_slots'] += len(by_clause) + len(by_id)
        c['origin_peak_live_map_slots'] = max(c['origin_peak_live_map_slots'], self.live_slots + len(by_clause) + len(by_id))
        pending = []
        for cid in affected:
            clause = state.by_id[cid]
            kept = None
            satisfied = False
            for index, lit in enumerate(clause):
                c['origin_scanned_literals'] += 1
                variable = abs(lit)
                if variable in assignment:
                    if assignment[variable] == (lit > 0):
                        satisfied = True
                        break
                    if kept is None:
                        kept = list(clause[:index])
                elif kept is not None:
                    kept.append(lit)
            if not satisfied and kept is None:
                c['origin_unchanged_affected_clauses'] += 1
                continue
            del by_clause[clause]
            del by_id[cid]
            if satisfied:
                c['origin_satisfied_clauses'] += 1
            else:
                reduced = tuple(kept)
                pending.append((cid, reduced))
                c['origin_shortened_clauses'] += 1
                c['origin_new_tuple_literals'] += len(reduced)
        c['origin_peak_pending_changes'] = max(c['origin_peak_pending_changes'], len(pending))
        # Remove all changed old images first: a new image may equal another
        # old image. The minimum original id, not map iteration order, wins.
        for cid, reduced in pending:
            old = by_clause.get(reduced)
            if old is not None:
                c['origin_duplicate_merges'] += 1
                if old < cid:
                    continue
                del by_id[old]
            by_clause[reduced] = cid
            by_id[cid] = reduced
        c['origin_untouched_representatives'] += len(state.by_id) - len(affected)
        result = OriginState(by_clause, by_id)
        self.live_slots += len(by_clause) + len(by_id)
        return result

    def release(self, parent, child):
        if child is not parent:
            self.live_slots -= len(child.by_clause) + len(child.by_id)


def extract(solver,source,*,node_limit=64,literal_limit=65536):
    if any(type(v) is not int or v<1 for v in (node_limit,literal_limit)):raise ValueError('Invalid extraction limits')
    source=tuple(tuple(cl) for cl in source)
    counts=Counter();root,names,key=solver._canonical(source);start=solver._read(key,root,purpose='conditional_origin')
    if start is None or start['answer'] is not False:raise ValueError('Checked negative origin required')
    entries=[]
    index = None
    def external(l):return (1 if l>0 else -1)*names[abs(l)-1]
    def leaf(conflict,trace,guards,path,origin):
        needed={abs(l) for l in root[conflict]};kept=[]
        for lit,cid in reversed(trace):
            counts['conditional_slice_steps']+=1
            if abs(lit) not in needed:continue
            needed.remove(abs(lit));needed.update(abs(l) for l in root[cid] if l!=lit);kept.append((lit,cid))
        if not needed<=guards.keys():raise ValueError('Unclosed conditional dependency')
        kept.reverse();selected=sorted({conflict}|{cid for _,cid in kept})
        clauses=sorted(tuple(sorted(external(l) for l in root[cid])) for cid in selected);positions={cl:i for i,cl in enumerate(clauses)}
        local={cid:positions[tuple(sorted(external(l) for l in root[cid]))] for cid in selected}
        template=dict(clauses=[list(cl) for cl in clauses],assumptions=[[names[v-1],guards[v]] for v in sorted(needed)],
            trace=[[external(l),local[cid]] for l,cid in kept],conflict=local[conflict])
        check_template(template,counts);index=len(entries)
        entries.append(dict(template=template,leaf=origin,origin_canonical_indices=selected,path_assignment=[[names[v-1],b] for v,b in sorted(path.items())]))
        return dict(leaf=index)
    def walk(nodekey,mapping,fixed,guards,trace,state):
        nonlocal index
        if counts['conditional_node_visits']>=node_limit:raise ExtractionBudget('Node occurrence budget')
        node=solver._read(nodekey,purpose='conditional_path')
        if node is None or node['answer'] is not False:raise ValueError('Missing negative path node')
        cnf=tuple(map(tuple,node['cnf']));size=sum(map(len,cnf))
        if counts['conditional_node_literals']+size>literal_limit:raise ExtractionBudget('Path literal budget')
        counts['conditional_node_visits']+=1;counts['conditional_node_literals']+=size
        proof=node['proof'];kind=proof['kind']
        if kind not in ('empty','units','split','component'):
            counts['conditional_unsupported_endpoints']+=1;return dict(unresolved=nodekey,kind=kind)
        if state is None:
            index = OriginIndex(root, counts)
            state = index.initial
        # This global map includes clauses outside a selected component.
        # It has exactly the old full-source scan's minimum original indices.
        origins = state.by_clause
        def literal(l):return (1 if l>0 else -1)*mapping[abs(l)]
        root_ids=[origins[tuple(sorted(literal(l) for l in cl))] for cl in cnf]
        def descend(child,assignment,newguards,newtrace,subset=None):
            raw=restrict(cnf if subset is None else subset,assignment,counts)
            normalized,oldnames,actual=solver._canonical(raw)
            if actual!=child:raise ValueError('Wrong conditioned child')
            mapped={i+1:mapping[v] for i,v in enumerate(oldnames)}
            updated={**fixed,**{mapping[v]:b for v,b in assignment.items()}}
            delta = {mapping[v]: bit for v, bit in assignment.items()}
            child_state = index.advance(state, delta)
            try:
                return walk(child,mapped,updated,newguards,newtrace,child_state)
            finally:
                index.release(state, child_state)
        if kind=='empty':return leaf(root_ids[cnf.index(())],trace,guards,guards,nodekey)
        if kind=='units':
            more=trace+[(literal(l),root_ids[cid]) for l,cid in proof['trace']]
            if proof.get('conflict') is not None:return leaf(root_ids[proof['conflict']],more,guards,guards,nodekey)
            return descend(proof['child'],{abs(l):l>0 for l,_ in proof['trace']},guards,more)
        if kind=='component':return descend(proof['child'],{},guards,trace,tuple(cnf[i] for i in proof['clauses']))
        variable=proof['variable'];rawvar=mapping[variable]
        if rawvar in fixed:raise ValueError('Repeated path variable')
        children={}
        for bit,field in ((False,'low'),(True,'high')):
            children[field]=descend(proof[field],{variable:bit},{**guards,rawvar:bit},trace)
        return dict(variable=names[rawvar-1],**children)
    tree=walk(key,dict(enumerate(range(1,len(names)+1),1)),{}, {},[], None)
    return dict(format=FORMAT_HINT,source=[list(cl) for cl in source],origin=key,entries=entries,tree=tree),dict(counts)


@contextmanager
def carried_origins():
    """Scoped serial experiment; do not overlap threads within one process."""
    with patch.object(learned, 'extract', extract):
        yield
