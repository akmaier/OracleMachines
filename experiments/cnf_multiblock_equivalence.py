"""Simultaneous source-checked substitution of disjoint binary SCC blocks.

One SCC pass discovers all blocks; two trees certify each. Native children are
acquired after one combined substitution. Single-block negatives retain v2;
multiple-block negatives use explicit v3 records. Recursive search is unchanged.
"""
from collections import Counter,deque
import json,time
from experiments.cnf_binary_core_cache import transport,encode
from experiments.cnf_compact_equivalence import CompactEquivalenceStore,source_from_key,FORMAT as V2
from experiments.cnf_binary_equivalence import FORMAT as V1
from experiments.cnf_targeted_backbone import AccountedTargetedBackboneSolver
from experiments.cnf_probe_equivalence import substitute_block
from experiments.cnf_residual_dag import FORMAT as NATIVE_FORMAT,holds

FORMAT='binary-equivalence-negative-v3'
TABLE='cnf_binary_equivalence_v3'


def discover_all(cnf,counts):
    counts['multi_discovery_calls']+=1
    ids=[];wide=False
    for cid,c in enumerate(cnf):
        counts['multi_width_checks']+=1
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
            counts['multi_graph_edges']+=1
    seen=set();order=[]
    for root in graph:
        if root in seen:continue
        seen.add(root);stack=[(root,iter(graph[root]))]
        while stack:
            v,edges=stack[-1];edge=next(edges,None)
            if edge is None:order.append(v);stack.pop()
            else:
                u,_=edge;counts['multi_scc_edge_visits']+=1
                if u not in seen:seen.add(u);stack.append((u,iter(graph[u])))
    labels={};groups=[]
    for root in reversed(order):
        if root in labels:continue
        label=len(groups);group=[];labels[root]=label;todo=[root]
        while todo:
            v=todo.pop();group.append(v)
            for u,_ in reverse[v]:
                counts['multi_scc_edge_visits']+=1
                if u not in labels:labels[u]=label;todo.append(u)
        groups.append(group)
    if any(labels[v]==labels[-v] for v in labels):
        counts['multi_inconsistent_binary_skips']+=1;return None
    choices=[sorted(g,key=abs) for g in groups if len(g)>1 and min(g,key=abs)>0]
    if not choices:
        counts['multi_no_block']+=1;return None
    results=[]
    for members in sorted(choices,key=lambda g:(-len(g),g[0])):
        rep=members[0]
        # Store the two trees once, rather than a separate path for every member.
        def tree(adjacency):
            counts['multi_tree_searches']+=1
            parents={rep:None};todo=deque([rep])
            while todo:
                v=todo.popleft()
                for u,cid in adjacency[v]:
                    counts['multi_tree_edge_visits']+=1
                    if labels[u]==labels[rep] and u not in parents:
                        parents[u]=(v,cid);todo.append(u)
            counts['multi_tree_entries']+=len(parents)
            return parents
        forward=tree(graph);backward=tree(reverse)
        out=[[forward[v][0],v,forward[v][1]] for v in members[1:]]
        into=[[v,backward[v][0],backward[v][1]] for v in members[1:]]
        counts['multi_certificate_edges']+=len(out)+len(into)
        counts['multi_blocks_found']+=1;counts['multi_variables_merged']+=len(members)-1
        results.append(dict(representative=rep,forward=out,backward=into))
    return results

def check_tree(cnf,evidence,counts):
    if type(evidence) is not dict or set(evidence)!={'representative','forward','backward'}:
        raise ValueError('Invalid equivalence evidence')
    rep=evidence['representative']
    if type(rep) is not int or rep<=0:
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
            counts['multi_checked_edges']+=1
            # View both certificates as a tree directed away from the root.
            if name=='backward':start,end=end,start
            if end==rep or end in parents:raise ValueError('Duplicate parent or incoming root edge')
            parents[end]=start;vertices.update((start,end));graph.setdefault(start,[]).append(end)
        if len(vertices)!=len(edges)+1 or len({abs(v) for v in vertices})!=len(vertices):
            raise ValueError('Invalid tree support')
        seen={rep};todo=[rep]
        while todo:
            for nxt in graph.get(todo.pop(),()):
                counts['multi_certificate_walk_edges']+=1
                if nxt not in seen:seen.add(nxt);todo.append(nxt)
        if seen!=vertices:raise ValueError('Disconnected or cyclic equivalence tree')
        supports.append(vertices)
    if supports[0]!=supports[1]:raise ValueError('Mismatched equivalence trees')
    mapping={abs(v):rep if v>0 else -rep for v in supports[0]}
    return mapping


def check_blocks(cnf,evidence,counts):
    if type(evidence) is not list or not evidence:raise ValueError('Missing equivalence blocks')
    mapping={}
    for block in evidence:
        part=check_tree(cnf,block,counts)
        if mapping.keys()&part.keys():raise ValueError('Overlapping equivalence blocks')
        mapping.update(part)
    target=substitute_block(cnf,dict(mapping=sorted(mapping.items())),counts)
    if not {abs(l) for c in target for l in c}<{abs(l) for c in cnf for l in c}:raise ValueError('No multiblock progress')
    counts['multi_checked_blocks']+=len(evidence)
    return target,mapping


def dependency(s,key,node):
    if (type(node) is not dict or set(node)!={'format','answer','evidence'} or node['format']!=FORMAT
            or node['answer'] is not False or type(node['evidence']) is not list or len(node['evidence'])<2):
        raise ValueError('Invalid multiple-block node')
    cnf=source_from_key(s,key);target,_=check_blocks(cnf,node['evidence'],s.counts)
    expected,_,child=s._canonical(target);result=s._read(child,expected,purpose='certificate')
    if result is None or result['answer'] is not False:raise ValueError('Missing native negative quotient')
    s.counts['multi_nodes_checked']+=1
    return cnf,child


class MultiEquivalenceStore:
    def __init__(self,solver,*,create=False):
        self.solver=solver;self.checked={};self.old=CompactEquivalenceStore(solver,create=create)
        if create:
            solver.db.execute(f'CREATE TABLE IF NOT EXISTS {TABLE} (id TEXT PRIMARY KEY,payload TEXT NOT NULL)');solver.db.commit()
        self.exists=bool(solver.db.execute('SELECT 1 FROM sqlite_master WHERE name=?',(TABLE,)).fetchone())

    def read(self,key):
        s=self.solver
        if key in self.checked:s.counts['multi_memory_hits']+=1;return self.checked[key]
        if self.exists:
            s.counts['multi_database_lookups']+=1
            row=s.db.execute(f'SELECT payload FROM {TABLE} WHERE id=?',(key,)).fetchone()
            if row is not None:
                s.counts['multi_read_bytes']+=len(row[0].encode());node=json.loads(row[0]);dependency(s,key,node)
                self.checked[key]=node;return node
        node=self.old.read(key)
        if node is not None:self.checked[key]=node
        return node

    def publish(self,key,cnf,evidence,child):
        if len(evidence)==1:
            node=self.old.publish(key,cnf,evidence[0],child);self.checked[key]=node;return node
        s=self.solver;node=dict(format=FORMAT,answer=False,evidence=evidence)
        expected,derived=dependency(s,key,node)
        if cnf!=expected or child!=derived:raise ValueError('Multiblock publication mismatch')
        payload=encode(node);s.counts['multi_serialized_bytes']+=len(payload.encode())
        with s.db:cursor=s.db.execute(f'INSERT OR IGNORE INTO {TABLE} VALUES (?,?)',(key,payload))
        if cursor.rowcount:
            s.counts['multi_inserted_nodes']+=1;s.counts['multi_inserted_bytes']+=len(key)+len(payload);self.checked[key]=node
        else:self.checked.pop(key,None);node=self.read(key)
        return node


class MultiCoreCache:
    def __init__(self,solver,enabled=True):self.solver=solver;self.enabled=enabled;self.checked={}

    def find(self,cnf):
        c=self.solver.counts
        if not self.enabled:return discover_all(cnf,c)
        c['multi_cache_calls']+=1;ids=[];wide=False
        for cid,clause in enumerate(cnf):
            c['multi_cache_source_clause_scans']+=1
            if len(clause)<2:return None
            if len(clause)==2:ids.append(cid)
            else:wide=True
        if not ids or not wide:return None
        core=tuple(cnf[cid] for cid in ids);key='binary-core-all-v1:'+encode(core)
        c['multi_cache_key_literal_units']+=2*len(core);c['multi_cache_key_bytes']+=len(key.encode())
        if key in self.checked:c['multi_cache_hits']+=1;evidence=self.checked[key]
        else:
            c['multi_cache_misses']+=1;evidence=discover_all(core+((1,2,3),),c);self.checked[key]=evidence
        if evidence is None:return None
        c['multi_cache_selected_blocks']+=len(evidence)
        return [transport(block,ids,c) for block in evidence]


class MultiEquivalenceSolver(AccountedTargetedBackboneSolver):
    def __init__(self,*args,cache=True,**kwargs):
        super().__init__(*args,**kwargs);self.equivalences=MultiEquivalenceStore(self,create=True);self.binary_cores=MultiCoreCache(self,cache)

    def solve(self,source):
        began=time.perf_counter();self.counts=Counter();cnf,names,root=self._canonical(source)
        native=self._read(root,cnf) if self.reuse else None;authority='native';model=None
        if native is not None:
            if native['answer']:model=dict(enumerate(native['model'],1))
        elif self.reuse and self.equivalences.read(root) is not None:authority=self.equivalences.checked[root]['format']
        else:
            evidence=self.binary_cores.find(cnf) if self.leaves else None
            if evidence is None:model,_=self._visit(cnf)
            else:
                target,mapping=check_blocks(cnf,evidence,self.counts)
                self.counts['multi_applied_blocks']+=len(evidence);self.counts['multi_applied_merges']+=len(mapping)-len(evidence)
                child_model,child=self._visit(target)
                if child_model is None:
                    node=self.equivalences.publish(root,cnf,evidence,child);authority=node['format']
                else:
                    model={v:False for v in range(1,len(names)+1)};model.update(child_model)
                    for variable,signed in mapping.items():model[variable]=model[abs(signed)] if signed>0 else not model[abs(signed)]
                    if not holds(cnf,model):raise ValueError('Invalid multiblock model lift')
                    self.counts['multi_positive_lifts']+=1;self.counts['multi_lift_variables']+=len(mapping)
                    self._store(root,dict(format=NATIVE_FORMAT,cnf=[list(c) for c in cnf],answer=True,model=[model[v] for v in range(1,len(names)+1)]))
        external=None if model is None else {old:model.get(i,False) for i,old in enumerate(names,1)}
        if external is not None and not holds(source,external):raise ValueError('Invalid source witness')
        self.counts['source_witness_literal_payload']+=sum(map(len,source)) if external is not None else 0
        nodes,payload=self.archive_storage()
        return dict(answer=external is not None,model=external,root=root,authority=authority,metrics=dict(self.counts),
            seconds=time.perf_counter()-began,archive_nodes=nodes,archive_payload_bytes=payload)
