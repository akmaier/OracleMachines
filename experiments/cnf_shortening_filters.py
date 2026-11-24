"""Reject structurally impossible implication paths before spending BFS slots.

Filters are rebuilt from the exact current graph, in its local coordinates.
They only skip candidates; native replay still authorizes every refutation.
"""
from collections import deque
from experiments.cnf_shortening_priority import priority_roots
from experiments.cnf_shortening_reach_bfs import NegativeReachCache,frozen,native
compile_program=frozen.compile_program
validate=frozen.validate


class NoPathFilter:
    def __init__(self,adjacency,counts,*,weak=True):
        self.adjacency=adjacency;self.counts=counts;self.weak=weak
        self.incoming=set();self.parents=None;self.sizes={}
        counts['filter_preparations']+=1
        for start,edges in adjacency.items():
            counts['filter_adjacency_vertices']+=1
            for end,cid in edges:
                counts['filter_incoming_edges']+=1;self.incoming.add(end)

    def _find(self,v):
        c=self.counts;c['filter_find_calls']+=1
        if v not in self.parents:self.parents[v]=v;self.sizes[v]=1
        while self.parents[v]!=v:
            c['filter_parent_hops']+=1
            self.parents[v]=self.parents[self.parents[v]];v=self.parents[v]
        return v

    def _components(self):
        self.parents={};c=self.counts;c['filter_component_builds']+=1
        for start,edges in self.adjacency.items():
            for end,cid in edges:
                c['filter_component_edges']+=1;a,b=self._find(start),self._find(end)
                if a!=b:
                    if self.sizes[a]<self.sizes[b]:a,b=b,a
                    self.parents[b]=a;self.sizes[a]+=self.sizes[b];c['filter_unions']+=1
        c['filter_peak_vertices']=max(c['filter_peak_vertices'],len(self.parents))

    def excludes(self,root):
        c=self.counts;c['filter_candidates']+=1
        if not self.adjacency.get(root):c['filter_empty_outgoing']+=1;return True
        if -root not in self.incoming:c['filter_empty_target_incoming']+=1;return True
        if self.weak:
            if self.parents is None:self._components()
            if self._find(root)!=self._find(-root):c['filter_disconnected']+=1;return True
        c['filter_survivors']+=1;return False


def discover(source,templates,counts,*,round_limit=32,root_limit=64,
             edge_limit=16384,path_limit=256,cache_vertex_limit=16384,
             order="priority", filters="weak"):
    if order not in ("priority","numeric") or filters not in ("endpoint","weak"):
        raise ValueError("Unknown root order or filter")
    reuse=True
    if any(type(v) is not int or v<1 for v in (round_limit,root_limit,edge_limit,path_limit)):
        raise ValueError('Positive discovery bounds required')
    source=frozen._source(source,templates,counts);fixed={};steps=[]
    cache=NegativeReachCache(cache_vertex_limit)
    initial_roots=counts['reach_roots'];initial_edges=counts['reach_edge_visits']+counts['reuse_invalidation_checks']+counts['cache_admission_edge_checks']
    def remaining():return edge_limit-(counts['reach_edge_visits']+counts['reuse_invalidation_checks']+counts['cache_admission_edge_checks']-initial_edges)
    def result(status,reason,terminal=None):
        return dict(status=status,reason=reason,steps=steps,terminal=terminal,path_limit=path_limit)
    for iteration in range(round_limit+1):
        state=frozen._state(source,templates,fixed,counts);counts['rounds']+=1
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
