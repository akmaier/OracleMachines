"""Compose saved source implications, then use them in bounded CNF lookahead.

The graph is a diagnostic of the retained binary theory, not a decision of its
nonbinary source. Learned clauses are justified directly on the original source
before any augmented-source probe may use them. Existing trace bytes stay in
their original archive; each new record interns its required references once.
"""
from collections import Counter, defaultdict, deque

from experiments.cnf_trace_reuse import read_attempt, TraceRoutes
from experiments.cnf_probe_exhaustion import check_clear_attempts
from experiments.cnf_probe_equivalence import discover_equivalence_probes, check_equivalence_probes
from experiments.cnf_probe_learning import learning_batch, augment
from experiments.cnf_pattern_inventory import encode
from experiments.cnf_residual_dag import holds

LEARN_LIMIT = 16
PROBE_LIMIT = 4


def implication_graph(cnf, attempts, counts):
    check_clear_attempts(cnf, attempts, counts)
    graph = {s*abs(l): set() for c in cnf for l in c for s in (-1,1)}
    for clause in cnf:
        counts['graph_source_literals'] += len(clause)
        if len(clause) == 2:
            a,b = clause; graph[-a].add(b); graph[-b].add(a)
    for attempt in attempts:
        x = attempt['variable'] * (1 if attempt['value'] else -1)
        for lit,_ in attempt['certificate']['units']:
            graph[x].add(lit); graph[-lit].add(-x)
            counts['graph_trace_units'] += 1
    counts['graph_vertices'] += len(graph)
    counts['graph_edges'] += sum(map(len, graph.values()))
    return graph


def graph_conclusions(reachable):
    return dict(forced_literals=sorted(-x for x,vs in reachable.items() if -x in vs),
        equivalences=[[x,y] for x in sorted(reachable) if x>0 for y in sorted(reachable[x])
                      if abs(y)>x and x in reachable[y]],
        contradictory_variables=[x for x in sorted(reachable) if x>0 and -x in reachable[x] and x in reachable[-x]])


def discover_graph(graph, counts):
    trees=[]; reachable={}
    for root in sorted(graph):
        seen={root}; queue=deque([root]); tree=[[root,root]]
        while queue:
            x=queue.popleft(); counts['graph_discovery_edges'] += len(graph[x])
            for y in sorted(graph[x]):
                if y not in seen:
                    seen.add(y); queue.append(y); tree.append([y,x])
        trees.append(tree); reachable[root]=seen
    return dict(trees=trees,conclusions=graph_conclusions(reachable))


def check_graph(graph, certificate, counts):
    """Tree paths prove membership; edge closure proves no reachable node omitted."""
    if type(certificate) is not dict or set(certificate)!={'trees','conclusions'}:
        raise ValueError('Invalid graph certificate')
    trees=certificate['trees']
    if type(trees) is not list or len(trees)!=len(graph): raise ValueError('Missing graph root')
    reachable={}
    for root,tree in zip(sorted(graph),trees,strict=True):
        if type(tree) is not list or not tree or encode(tree[0])!=encode([root,root]):
            raise ValueError('Incorrect reachability root')
        seen={root}
        for item in tree[1:]:
            if (type(item) is not list or len(item)!=2 or any(type(v) is not int for v in item)):
                raise ValueError('Invalid graph path item')
            vertex,parent=item
            if vertex in seen or parent not in seen or vertex not in graph[parent]:
                raise ValueError('Unproved graph reachability')
            seen.add(vertex); counts['verified_graph_path_edges'] += 1
        for vertex in seen:
            counts['graph_closure_check_edges'] += len(graph[vertex])
            if not graph[vertex] <= seen: raise ValueError('Incomplete graph closure')
        reachable[root]=seen
    if encode(certificate['conclusions'])!=encode(graph_conclusions(reachable)):
        raise ValueError('Incorrect graph conclusions')
    return certificate['conclusions']


def record_key(record):
    return encode([record['source'],record['references'],record['clauses'],LEARN_LIMIT,PROBE_LIMIT])


def checked_augmentation(h, record, counts):
    if type(record) is not dict or set(record)!={'source','references','clauses','probing','edge'}:
        raise ValueError('Invalid trace-learning fields')
    if type(record['source']) is not str: raise ValueError('Invalid learning source')
    node=h._load(record['source'])
    if node is None or node['kind']!='unresolved': raise ValueError('Expected unresolved source')
    refs=record['references']; clauses=record['clauses']
    if (type(refs) is not list or type(clauses) is not list or
            not 1 <= len(refs) <= len(clauses) <= LEARN_LIMIT or len({encode(ref) for ref in refs})!=len(refs)):
        raise ValueError('Invalid learning bounds or duplicate reference')
    attempts=[read_attempt(h,record['source'],ref,counts) for ref in refs]
    check_clear_attempts(node['cnf'],attempts,counts)
    used=set(); seen=set(); batch=[]
    for item in clauses:
        if (type(item) is not dict or set(item)!={'reference','unit','clause'} or
                type(item['reference']) is not int or not 0<=item['reference']<len(refs) or
                type(item['unit']) is not int or item['unit']<0):
            raise ValueError('Invalid learned-clause reason')
        attempt=attempts[item['reference']]; units=attempt['certificate']['units']
        if item['unit']>=len(units): raise ValueError('Missing conditional unit')
        x=attempt['variable']*(1 if attempt['value'] else -1); literal=units[item['unit']][0]
        expected=sorted((-x,literal))
        if abs(x)==abs(literal) or encode(item['clause'])!=encode(expected) or tuple(expected) in seen:
            raise ValueError('Incorrect or duplicated learned clause')
        used.add(item['reference']); seen.add(tuple(expected)); batch.append(dict(clause=expected))
        counts['verified_saved_implications'] += 1
    if used!=set(range(len(refs))): raise ValueError('Unused learning evidence')
    return node,augment(node['cnf'],batch)


def verify_learning(h, record, counts):
    node,expanded=checked_augmentation(h,record,counts)
    target,fixed=check_equivalence_probes(expanded,record['probing'],PROBE_LIMIT,counts)
    if record['probing']['status']=='clear':
        if record['edge'] is not None: raise ValueError('Clear lookahead cannot create a rewrite')
    else:
        if not {abs(l) for c in target for l in c} < {abs(l) for c in node['cnf'] for l in c}:
            raise ValueError('Learning rewrite must strictly reduce support')
        _,names,key=h._canonical(target,node['depth'])
        if encode(record['edge'])!=encode(dict(key=key,names=names)):
            raise ValueError('Incorrect learned residual binding')
    counts['verified_trace_learning_records'] += 1
    return target,fixed


def acquire_learning(h, source, attempts, refs, counts):
    node=h._load(source)
    if node is None or node['kind']!='unresolved': raise ValueError('Expected unresolved source')
    if len(attempts)!=len(refs): raise ValueError('Missing attempt references')
    batch=learning_batch(node['cnf'],attempts,LEARN_LIMIT,counts)
    if not batch: return None
    selected=[]; indices={}; clauses=[]
    for item in batch:
        ref=refs[item['attempt']]; identity=encode(ref)
        if identity not in indices:
            indices[identity]=len(selected); selected.append(ref)
        clauses.append(dict(reference=indices[identity],unit=item['unit'],clause=item['clause']))
    record=dict(source=source,references=selected,clauses=clauses,probing=None,edge=None)
    # Establish implications on the exact source before searching the augmented CNF.
    node,expanded=checked_augmentation(h,record,counts)
    record['probing']=discover_equivalence_probes(expanded,PROBE_LIMIT,counts)
    target,_=check_equivalence_probes(expanded,record['probing'],PROBE_LIMIT,counts)
    if record['probing']['status']!='clear':
        _,names,key=h._canonical(target,node['depth']); record['edge']=dict(key=key,names=names)
    verify_learning(h,record,counts)
    return record


def lift_learning(h, record, child_model, counts):
    _,fixed=verify_learning(h,record,counts)
    edge=record['edge']
    if edge is None: raise ValueError('No learned rewrite')
    child=h._load(edge['key'])
    if (child is None or any(i not in child_model or type(child_model[i]) is not bool for i in range(1,len(edge['names'])+1))
            or not holds(child['cnf'],child_model)):
        raise ValueError('Invalid learned child model')
    cnf=h._load(record['source'])['cnf']; model={abs(l):False for c in cnf for l in c}
    model.update(fixed); model.update((v,child_model[i]) for i,v in enumerate(edge['names'],1))
    if record['probing']['status']=='equivalence':
        for v,rep in record['probing']['witness']['mapping']:
            model[v]=model[abs(rep)] if rep>0 else not model[abs(rep)]
    if not holds(cnf,model): raise ValueError('Learned lift violates source')
    return model


class LearnedTraceRoutes(TraceRoutes):
    def __init__(self,h,rewrites=(),learning=()):
        super().__init__(h,rewrites); self.learning={}
        for record in learning: self.add_learning(h,record)

    def add_learning(self,h,record):
        verify_learning(h,record,self.counts); identity=record_key(record)
        if identity in self.learning and encode(self.learning[identity])!=encode(record):
            raise ValueError('Conflicting learned record')
        self.learning[identity]=record
        if record['edge'] is None: return
        if h._load(record['edge']['key']) is None:
            self.counts['pending_trace_learning'] += 1; return
        item=(dict(kind='trace_learning',id=identity),[record['edge']['key']])
        if item not in self.by_source[record['source']]: self.by_source[record['source']].append(item)
