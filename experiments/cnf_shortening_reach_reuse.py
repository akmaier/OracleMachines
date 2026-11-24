"""Reuse negative reachability certificates through checked graph changes.

A cached set contains its root, excludes the opposite literal, and is closed
under graph edges. Deletions preserve closure. Only an added edge leaving the
set invalidates it. Coordinates are original source literals, never round-local
indices. Certificates guide discovery; native proof replay remains authority.
"""
from collections import deque
from experiments import cnf_guard_shortening_context as frozen
native=frozen.native
compile_program=frozen.compile_program
validate=frozen.validate


class NegativeReachCache:
    def __init__(self, vertex_limit=16384):
        if type(vertex_limit) is not int or vertex_limit<1:
            raise ValueError('Positive cache vertex limit required')
        self.limit=vertex_limit;self.edges=set();self.sets={};self.users={};self.vertices=0

    def _drop(self,root,counts):
        reached=self.sets.pop(root);self.vertices-=len(reached)
        for vertex in reached:
            self.users[vertex].remove(root)
            if not self.users[vertex]:del self.users[vertex]
            counts['cache_index_removals']+=1

    def update(self,edges,counts,remaining_checks):
        """Return False on a checking-budget stop; no caller may use that state."""
        edges=set(edges);added=edges-self.edges
        counts['graph_delta_edges_scanned']+=len(edges)+len(self.edges)
        counts['graph_added_edges']+=len(added);counts['graph_removed_edges']+=len(self.edges-edges)
        checks=0
        for start,end in sorted(added):
            for root in sorted(self.users.get(start,())):
                if checks>=remaining_checks:
                    counts['invalidation_budget_stops']+=1
                    # A partially checked transition is not a valid cache state.
                    self.sets.clear();self.users.clear();self.vertices=0;self.edges=edges
                    return False
                checks+=1;counts['reuse_invalidation_checks']+=1
                if end not in self.sets[root]:
                    self._drop(root,counts);counts['cache_invalidations']+=1
        self.edges=edges
        return True

    def remember(self,root,reached,counts):
        reached=frozenset(reached)
        if root not in reached or -root in reached:raise ValueError('Invalid negative reach set')
        # Only complete BFS supplies certificates internally; this independent
        # closure check also makes the cache API safe for supplied sets.
        for start,end in self.edges:
            counts['cache_admission_edge_checks']+=1
            if start in reached and end not in reached:raise ValueError('Reach set is not closed')
        if root in self.sets:self._drop(root,counts)
        if self.vertices+len(reached)>self.limit:
            counts['cache_capacity_misses']+=1;return
        self.sets[root]=reached;self.vertices+=len(reached)
        for v in reached:self.users.setdefault(v,set()).add(root);counts['cache_index_insertions']+=1
        counts['cache_stores']+=1
        counts['cache_peak_roots']=max(counts['cache_peak_roots'],len(self.sets))
        counts['cache_peak_vertices']=max(counts['cache_peak_vertices'],self.vertices)

    def contains(self,root,counts):
        counts['cache_lookups']+=1
        if root in self.sets:counts['negative_reuses']+=1;return True
        return False


def discover(source,templates,counts,*,round_limit=32,root_limit=64,
             edge_limit=16384,path_limit=256,cache_vertex_limit=16384):
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
        if not cache.update(edges,counts,remaining()):return result('unresolved','edge_limit')
        roots=sorted({l for cl in state['local'] if len(cl)>2 for l in cl
                      if abs(l) in model and model[abs(l)]!=(l>0)})
        chosen=None
        for root in roots:
            counts['candidate_attempts']+=1
            rawroot=external(root)
            if cache.contains(rawroot,counts):continue
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
                if len(cache.edges)>remaining():
                    # Caching is optional; a failed admission cannot suppress BFS.
                    counts['cache_admission_budget_misses']+=1
                else:cache.remember(rawroot,(external(v) for v in parents),counts)
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
