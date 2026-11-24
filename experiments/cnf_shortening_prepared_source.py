"""Own validated immutable inputs across one shortening discovery call.

The original source and templates are checked once. Every cofactor, transported
trace and current clause position is still checked. Native compilation and
portable proof validation remain the frozen independent implementations.
"""
from collections import deque
from copy import deepcopy
from dataclasses import dataclass
from types import MappingProxyType
from experiments.cnf_shortening_clause_filters import NoPathFilter
from experiments.cnf_shortening_priority import priority_roots
from experiments.cnf_shortening_reach_bfs import NegativeReachCache,frozen,native
from experiments.cnf_conditional_unit_support import check_template,fixed_pairs
from experiments.cnf_guard_context_solver import LocalContext
from experiments.cnf_shortening_transport import transport_state
compile_program=frozen.compile_program
validate=frozen.validate


@dataclass(frozen=True, slots=True)
class PreparedSource:
    """Private preparation, never certificate authority or a cross-source cache.

    Construct through prepare. All reachable input containers are immutable and
    detached from the caller. A changed source/template set requires prepare.
    No caller-supplied prepared object is accepted by discover or the compiler.
    """
    source: tuple
    variables: frozenset
    templates: tuple
    guards: tuple
    literals: int

    @classmethod
    def prepare(cls, source, templates, counts):
        source=tuple(map(tuple,source))
        if native.normalize(source,counts)[0]!=source:
            raise ValueError('Canonical source required')
        members=set(source);owned=[];guards=[];slots=0
        for supplied in templates:
            # Validate our own copy; later caller edits cannot invalidate checks.
            template=deepcopy(supplied)
            if not check_template(template,counts)<=members:
                raise ValueError('Missing template support')
            guard=tuple(fixed_pairs(template['assumptions']).items())
            frozen_template={key:(tuple(tuple(row) for row in value)
                                 if key!='conflict' else value)
                             for key,value in template.items()}
            owned.append(MappingProxyType(frozen_template));guards.append(guard)
            slots+=sum(map(len,template['clauses']))+2*len(template['trace'])+4*len(guard)+1
        literals=sum(map(len,source));variables=frozenset(abs(l) for cl in source for l in cl)
        counts['source_preparations']+=1
        counts['prepared_templates']+=len(owned)
        counts['prepared_input_slots']=max(counts['prepared_input_slots'],literals+len(variables)+slots)
        return cls(source,variables,tuple(owned),tuple(guards),literals)

    def state(self, fixed, counts):
        fixed=fixed_pairs([[v,b] for v,b in fixed.items()])
        if not fixed.keys()<=self.variables:
            raise ValueError('Assignment names an absent source variable')
        raw=native.restrict_scan(self.source,fixed,counts)
        local,names=native.normalize(raw,counts)
        counts['conditioned_source_literals']+=self.literals
        parent=dict(cnf=local,mapping=dict(enumerate(names,1)),fixed=fixed)
        context=None;hints=[];inverse={v:i+1 for i,v in enumerate(names)}
        for index,(template,guard) in enumerate(zip(self.templates,self.guards)):
            counts['template_candidates']+=1
            if any(v in fixed and fixed[v]!=bit for v,bit in guard):
                counts['incompatible_guards']+=1
                continue
            missing=[(v,bit) for v,bit in guard if v not in fixed]
            counts['compatible_width_'+str(len(missing))]+=1
            if any(v not in inverse for v,bit in missing):
                counts['absent_guard_variables']+=1
                continue
            if context is None:context=LocalContext.prepare(local,parent,counts)
            hint=transport_state(context,template,missing,counts)
            if hint is None:continue
            hints.append(dict(origin_template=index,**hint))
            counts['accepted_width_'+str(len(hint['clause']))]+=1
        graph=sorted({cl for cl in local if 1<=len(cl)<=2} |
                     {tuple(h['clause']) for h in hints if 1<=len(h['clause'])<=2})
        return dict(local=local,names=names,hints=hints,graph=graph)


def discover(source,templates,counts,*,round_limit=32,root_limit=64,
             edge_limit=16384,path_limit=256,cache_vertex_limit=16384,
             order="priority", filters="weak"):
    if order not in ("priority","numeric") or filters not in ("endpoint","weak"):
        raise ValueError("Unknown root order or filter")
    reuse=True
    if any(type(v) is not int or v<1 for v in (round_limit,root_limit,edge_limit,path_limit)):
        raise ValueError('Positive discovery bounds required')
    prepared=PreparedSource.prepare(source,templates,counts);fixed={};steps=[]
    cache=NegativeReachCache(cache_vertex_limit)
    initial_roots=counts['reach_roots'];initial_edges=counts['reach_edge_visits']+counts['reuse_invalidation_checks']+counts['cache_admission_edge_checks']
    def remaining():return edge_limit-(counts['reach_edge_visits']+counts['reuse_invalidation_checks']+counts['cache_admission_edge_checks']-initial_edges)
    def result(status,reason,terminal=None):
        return dict(status=status,reason=reason,steps=steps,terminal=terminal,path_limit=path_limit)
    for iteration in range(round_limit+1):
        state=prepared.state(fixed,counts);counts['rounds']+=1
        if () in state['local']:return result('refuted','empty',dict(kind='empty'))
        empty=next((h for h in state['hints'] if not h['clause']),None)
        if empty is not None:return result('refuted','guard',dict(kind='guard',template=empty['origin_template']))
        model,proof=native.two_cnf(state['graph'],counts)
        if proof is not None:
            if max(len(proof['forward']),len(proof['backward']))>path_limit:return result('unresolved','path_limit')
            return result('refuted','binary',dict(kind='binary',variable=state['names'][proof['variable']-1],
                forward=frozen._external_path(proof['forward'],state),backward=frozen._external_path(proof['backward'],state)))
        if iteration==round_limit:return result('unresolved','round_limit')
        def external(l):return state['names'][abs(l)-1]*(1 if l>0 else -1)
        adjacency={};edges=set()
        for cid,cl in enumerate(state['graph']):
            a,b=cl[0],cl[-1];adjacency.setdefault(-a,[]).append((b,cid));edges.add((external(-a),external(b)))
            if a!=b:adjacency.setdefault(-b,[]).append((a,cid));edges.add((external(-b),external(a)))
        if reuse and not cache.update(edges,counts,remaining()):return result('unresolved','edge_limit')
        roots=(priority_roots(state['local'],model,counts) if order=='priority' else
               sorted({l for cl in state['local'] if len(cl)>2 for l in cl
                       if abs(l) in model and model[abs(l)]!=(l>0)}))
        reach_filter=None
        chosen=None
        for root in roots:
            counts['candidate_attempts']+=1
            rawroot=external(root)
            if reuse and cache.contains(rawroot,counts):continue
            if reach_filter is None:reach_filter=NoPathFilter(adjacency,counts,weak=filters=='weak')
            if reach_filter.excludes(root):continue
            if counts['reach_roots']-initial_roots>=root_limit:return result('unresolved','root_limit')
            counts['reach_roots']+=1;parents={root:None};queue=deque([root])
            while queue and -root not in parents:
                current=queue.popleft()
                for nxt,cid in adjacency.get(current,()):
                    if remaining()<=0:return result('unresolved','edge_limit')
                    counts['reach_edge_visits']+=1
                    if nxt not in parents:parents[nxt]=(current,cid);queue.append(nxt)
            counts['peak_reach_vertices']=max(counts['peak_reach_vertices'],len(parents))
            if -root not in parents:
                # The queue is exhausted and every outgoing edge of every
                # reached vertex was just inspected. The graph has not changed:
                # closure is established by this BFS, with its edge cost paid.
                if queue:raise AssertionError('Incomplete negative traversal')
                if reuse:cache._insert_complete(rawroot,(external(v) for v in parents),counts)
                continue
            path=[];current=-root
            while current!=root:
                prev,cid=parents[current];path.append([current,cid]);current=prev
            path.reverse()
            if len(path)>path_limit:return result('unresolved','path_limit')
            forced=-rawroot;chosen=dict(forced=forced,path=frozen._external_path(path,state));break
        if chosen is None:return result('unresolved','no_useful_forced_literal')
        steps.append(chosen);fixed[abs(chosen['forced'])]=chosen['forced']>0;counts['forced_steps']+=1
    raise AssertionError('Unreachable')
