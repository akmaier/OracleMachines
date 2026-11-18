"""Checked whole-source substitution from one binary SCC equivalence block.

Top-level acquisition only. Negative quotient dependencies live in an explicit
extension table; recursive native search never reads it. Old native readers and
proof formats remain unchanged. SAT lifts publish ordinary full-source models.
"""
from collections import Counter,deque
import json,time
from experiments.cnf_targeted_backbone import AccountedTargetedBackboneSolver
from experiments.cnf_residual_dag import FORMAT as NATIVE_FORMAT,holds
from experiments.cnf_probe_equivalence import substitute_block

FORMAT='binary-equivalence-negative-v1'
TABLE='cnf_binary_equivalence_v1'


def discover(cnf,counts):
    counts['equiv_discovery_calls']+=1
    ids=[];wide=False
    for cid,c in enumerate(cnf):
        counts['equiv_width_checks']+=1
        if len(c)<2:return None
        if len(c)==2:ids.append(cid)
        else:wide=True
    if not ids or not wide:return None
    graph={};reverse={}
    for cid in ids:
        a,b=cnf[cid]
        for u,v in ((-a,b),(-b,a)):
            graph.setdefault(u,[]).append((v,cid));graph.setdefault(v,[])
            reverse.setdefault(v,[]).append((u,cid));reverse.setdefault(u,[])
            counts['equiv_graph_edges']+=1
    seen=set();order=[]
    for root in graph:
        if root in seen:continue
        seen.add(root);stack=[(root,iter(graph[root]))]
        while stack:
            v,edges=stack[-1];edge=next(edges,None)
            if edge is None:order.append(v);stack.pop()
            else:
                u,_=edge;counts['equiv_scc_edge_visits']+=1
                if u not in seen:seen.add(u);stack.append((u,iter(graph[u])))
    labels={};groups=[]
    for root in reversed(order):
        if root in labels:continue
        label=len(groups);group=[];labels[root]=label;todo=[root]
        while todo:
            v=todo.pop();group.append(v)
            for u,_ in reverse[v]:
                counts['equiv_scc_edge_visits']+=1
                if u not in labels:labels[u]=label;todo.append(u)
        groups.append(group)
    if any(labels[v]==labels[-v] for v in labels):
        counts['equiv_inconsistent_binary_skips']+=1;return None
    choices=[sorted(g,key=abs) for g in groups if len(g)>1 and min(g,key=abs)>0]
    if not choices:
        counts['equiv_no_block']+=1;return None
    members=min(choices,key=lambda g:(-len(g),g[0]));rep=members[0]
    # Store the two trees once, rather than a separate path for every member.
    def tree(adjacency):
        counts['equiv_tree_searches']+=1
        parents={rep:None};todo=deque([rep])
        while todo:
            v=todo.popleft()
            for u,cid in adjacency[v]:
                counts['equiv_tree_edge_visits']+=1
                if labels[u]==labels[rep] and u not in parents:
                    parents[u]=(v,cid);todo.append(u)
        counts['equiv_tree_entries']+=len(parents)
        return parents
    forward=tree(graph);backward=tree(reverse)
    out=[[forward[v][0],v,forward[v][1]] for v in members[1:]]
    into=[[v,backward[v][0],backward[v][1]] for v in members[1:]]
    counts['equiv_certificate_edges']+=len(out)+len(into)
    counts['equiv_blocks_found']+=1;counts['equiv_variables_merged']+=len(members)-1
    return dict(representative=rep,forward=out,backward=into)


def check_substitution(cnf,evidence,counts):
    if type(evidence) is not dict or set(evidence)!={'representative','forward','backward'}:
        raise ValueError('Invalid equivalence evidence')
    rep=evidence['representative'];variables={abs(l) for c in cnf for l in c}
    if type(rep) is not int or rep<=0 or rep not in variables:
        raise ValueError('Invalid representative')
    supports=[]
    for name in ('forward','backward'):
        edges=evidence[name]
        if type(edges) is not list or not edges:raise ValueError('Missing equivalence tree')
        graph={};vertices={rep};parents={}
        for edge in edges:
            if type(edge) is not list or len(edge)!=3:raise ValueError('Invalid tree edge')
            start,end,cid=edge
            if (type(start) is not int or not start or type(end) is not int or not end
                    or type(cid) is not int or not 0<=cid<len(cnf) or len(cnf[cid])!=2
                    or cnf[cid]!=tuple(sorted((-start,end)))):raise ValueError('Unsupported binary implication')
            counts['equiv_checked_edges']+=1
            # View both certificates as a tree directed away from the root.
            if name=='backward':start,end=end,start
            if end==rep or end in parents:raise ValueError('Duplicate parent or incoming root edge')
            parents[end]=start;vertices.update((start,end));graph.setdefault(start,[]).append(end)
        if len(vertices)!=len(edges)+1 or len({abs(v) for v in vertices})!=len(vertices):
            raise ValueError('Invalid tree support')
        seen={rep};todo=[rep]
        while todo:
            for nxt in graph.get(todo.pop(),()):
                counts['equiv_certificate_walk_edges']+=1
                if nxt not in seen:seen.add(nxt);todo.append(nxt)
        if seen!=vertices:raise ValueError('Disconnected or cyclic equivalence tree')
        supports.append(vertices)
    if supports[0]!=supports[1]:raise ValueError('Mismatched equivalence trees')
    mapping={abs(v):rep if v>0 else -rep for v in supports[0]}
    target=substitute_block(cnf,dict(mapping=sorted(mapping.items())),counts)
    if not {abs(l) for c in target for l in c}<variables:raise ValueError('Substitution made no progress')
    return target,mapping


class EquivalenceStore:
    def __init__(self,solver,*,create=False):
        self.solver=solver;self.checked={}
        if create:
            solver.db.execute(f'CREATE TABLE IF NOT EXISTS {TABLE} (id TEXT PRIMARY KEY,payload TEXT NOT NULL)');solver.db.commit()

    def verify(self,key,node):
        s=self.solver
        if (type(node) is not dict or set(node)!={'format','cnf','answer','evidence','child'}
                or node['format']!=FORMAT or node['answer'] is not False):raise ValueError('Invalid equivalence node')
        cnf,_,actual=s._canonical(node['cnf'])
        if actual!=key or node['cnf']!=[list(c) for c in cnf]:raise ValueError('Wrong equivalence source')
        target,_=check_substitution(cnf,node['evidence'],s.counts)
        # This reader explicitly requires an ordinary native negative child.
        s._negative_child(node['child'],target)
        s.counts['equiv_nodes_checked']+=1
        return node

    def read(self,key):
        s=self.solver
        if key in self.checked:s.counts['equiv_memory_hits']+=1;return self.checked[key]
        s.counts['equiv_database_lookups']+=1
        row=s.db.execute(f'SELECT payload FROM {TABLE} WHERE id=?',(key,)).fetchone()
        if row is None:return None
        s.counts['equiv_read_bytes']+=len(row[0].encode())
        node=self.verify(key,json.loads(row[0]));self.checked[key]=node;return node

    def publish(self,key,cnf,evidence,child):
        s=self.solver;node=dict(format=FORMAT,cnf=[list(c) for c in cnf],answer=False,evidence=evidence,child=child)
        self.verify(key,node);payload=json.dumps(node,sort_keys=True,separators=(',',':'))
        s.counts['equiv_serialized_bytes']+=len(payload.encode())
        with s.db:cursor=s.db.execute(f'INSERT OR IGNORE INTO {TABLE} VALUES (?,?)',(key,payload))
        if cursor.rowcount:
            s.counts['equiv_inserted_nodes']+=1;s.counts['equiv_inserted_bytes']+=len(key)+len(payload)
            self.checked[key]=node
        else:
            self.checked.pop(key,None);node=self.read(key)
        return node


class BinaryEquivalenceSolver(AccountedTargetedBackboneSolver):
    """Opt-in top-level API: negative extension roots are not native roots."""
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs);self.equivalences=EquivalenceStore(self,create=True)

    def solve(self,source):
        began=time.perf_counter();self.counts=Counter();cnf,names,root=self._canonical(source)
        native=self._read(root,cnf) if self.reuse else None;authority='native';model=None
        if native is not None:
            if native['answer']:model=dict(enumerate(native['model'],1))
        elif self.reuse and self.equivalences.read(root) is not None:authority=FORMAT
        else:
            evidence=discover(cnf,self.counts) if self.leaves else None
            if evidence is None:model,_=self._visit(cnf)
            else:
                target,mapping=check_substitution(cnf,evidence,self.counts)
                child_model,child=self._visit(target)
                if child_model is None:
                    self.equivalences.publish(root,cnf,evidence,child);authority=FORMAT
                else:
                    model={v:False for v in range(1,len(names)+1)};model.update(child_model)
                    for variable,signed in mapping.items():model[variable]=model[abs(signed)] if signed>0 else not model[abs(signed)]
                    if not holds(cnf,model):raise ValueError('Invalid equivalence model lift')
                    self.counts['equiv_positive_lifts']+=1;self.counts['equiv_lift_variables']+=len(mapping)
                    self._store(root,dict(format=NATIVE_FORMAT,cnf=[list(c) for c in cnf],answer=True,model=[model[v] for v in range(1,len(names)+1)]))
        external=None if model is None else {old:model.get(i,False) for i,old in enumerate(names,1)}
        if external is not None and not holds(source,external):raise ValueError('Invalid source witness')
        self.counts['source_witness_literal_payload']+=sum(map(len,source)) if external is not None else 0
        nodes,payload=self.archive_storage()
        return dict(answer=external is not None,model=external,root=root,authority=authority,metrics=dict(self.counts),
            seconds=time.perf_counter()-began,archive_nodes=nodes,archive_payload_bytes=payload)
