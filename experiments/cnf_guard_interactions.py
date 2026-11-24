"""Transport guard consequences locally and compose their binary implications.

The consequence graph is a necessary condition, not a replacement for the CNF.
Only native unit/split certificates may publish an actual source exclusion.
"""
from collections import Counter,deque
from experiments import cnf_residual_dag as native
from experiments.cnf_guard_probe_census import decode_key
from experiments.cnf_conditional_unit_support import check_template,fixed_pairs,materialize
from experiments.cnf_guard_certificate_solver import transport_checked
from experiments.cnf_hint_transport import check_rup


def local_hints(source,templates,event,counts):
    source=tuple(map(tuple,source));local=decode_key(event['root'])
    if native.normalize(source,counts)[0]!=source:raise ValueError('Canonical source required')
    fixed=fixed_pairs(event['fixed']);mapping=dict(event['mapping'])
    variables={abs(l) for cl in source for l in cl};local_vars={abs(l) for cl in local for l in cl}
    if (len(mapping)!=len(event['mapping']) or set(mapping)!=local_vars or
            any(type(v) is not int or type(w) is not int or w not in variables for v,w in mapping.items()) or
            len(set(mapping.values()))!=len(mapping) or not fixed.keys()<=variables or
            set(mapping.values())&fixed.keys()):raise ValueError('Invalid local coordinates')
    image={tuple(sorted(mapping[abs(l)]*(1 if l>0 else -1) for l in cl)) for cl in local}
    residual=set(native.restrict_scan(source,fixed,counts))
    if not image<=residual:raise ValueError('Not a conditioned source subset')
    inverse={v:k for k,v in mapping.items()};positions={cl:i for i,cl in enumerate(local)}
    members=set(source);out=[]
    for index,t in enumerate(templates):
        counts['template_candidates']+=1
        support=check_template(t,counts);guard=fixed_pairs(t['assumptions'])
        if not support<=members:counts['deleted_supports']+=1;continue
        if any(v in fixed and fixed[v]!=b for v,b in guard.items()):counts['incompatible_guards']+=1;continue
        missing=[(v,b) for v,b in guard.items() if v not in fixed]
        counts['compatible_width_'+str(len(missing))]+=1
        if any(v not in inverse for v,b in missing):counts['absent_guard_variables']+=1;continue
        translated=[];valid=True
        for cl in t['clauses']:
            raw=native.restrict_scan((cl,),fixed,counts)
            if not raw:translated.append(None);continue
            if any(abs(l) not in inverse for l in raw[0]):valid=False;break
            reduced=tuple(sorted(inverse[abs(l)]*(1 if l>0 else -1) for l in raw[0]))
            counts['local_containment_clauses']+=1
            if reduced not in positions:valid=False;break
            translated.append(reduced)
        if not valid:counts['local_support_misses']+=1;continue
        clauses=sorted({cl for cl in translated if cl is not None});ids={cl:i for i,cl in enumerate(clauses)}
        trace=[];conflict=None
        for lit,cid in t['trace']:
            counts['trace_transport_steps']+=1
            if abs(lit) in fixed:
                if fixed[abs(lit)]==(lit>0):continue
                conflict=ids[translated[cid]];break
            if translated[cid] is None or abs(lit) not in inverse:raise ValueError('Unbound surviving trace')
            trace.append([inverse[abs(lit)]*(1 if lit>0 else -1),ids[translated[cid]]])
        if conflict is None:conflict=ids[translated[t['conflict']]]
        assumptions=sorted([[inverse[v],b] for v,b in missing])
        lifted=dict(clauses=[list(cl) for cl in clauses],assumptions=assumptions,trace=trace,conflict=conflict)
        check_template(lifted,counts)
        clause=sorted(-v if b else v for v,b in assumptions)
        proof=dict(units=[[l,positions[clauses[cid]]] for l,cid in trace],conflict=positions[clauses[conflict]])
        check_rup(local,clause,proof,counts)
        out.append(dict(origin_template=index,clause=clause,template=lifted,proof=proof))
        counts['accepted_width_'+str(len(clause))]+=1
    return local,out,image==residual


def binary_paths(clauses,counts):
    clauses=tuple(sorted(set(tuple(cl) for cl in clauses)))
    if any(len(cl)>2 or list(cl)!=sorted(set(cl)) or any(type(l) is not int or not l or -l in cl for l in cl) for cl in clauses):
        raise ValueError('Expected non-tautological clauses of width at most two')
    if () in clauses:return dict(clauses=clauses,paths={},contradictory=[],empty=True)
    graph={};variables=set()
    for cid,cl in enumerate(clauses):
        a,b=cl[0],cl[-1];variables.update(map(abs,cl))
        graph.setdefault(-a,[]).append((b,cid));counts['graph_edges']+=1
        if a!=b:graph.setdefault(-b,[]).append((a,cid));counts['graph_edges']+=1
    paths={}
    for root in sorted(sign*v for v in variables for sign in (-1,1)):
        counts['reach_roots']+=1;parents={root:None};queue=deque([root])
        while queue and -root not in parents:
            current=queue.popleft()
            for nxt,cid in graph.get(current,()):
                counts['reach_edge_visits']+=1
                if nxt not in parents:parents[nxt]=(current,cid);queue.append(nxt)
        if -root in parents:
            path=[];current=-root
            while current!=root:
                prev,cid=parents[current];path.append([current,cid]);current=prev
            paths[-root]=list(reversed(path));counts['witness_edges']+=len(path)
    return dict(clauses=clauses,paths=paths,contradictory=sorted(v for v in variables if v in paths and -v in paths),empty=False)


def inspect(local,hints,counts):
    guards=sorted({tuple(h['clause']) for h in hints});short=[cl for cl in guards if len(cl)<=2]
    original=[cl for cl in local if len(cl)<=2]
    profiles={}
    for mode,clauses in (('original',original),('guards',short),('combined',original+short)):
        c=Counter();profiles[mode]=binary_paths(clauses,c);counts.update({mode+'_'+k:v for k,v in c.items()})
    units={cl[0] for cl in guards if len(cl)==1}
    old=set(profiles['original']['paths']);alone=set(profiles['guards']['paths']);combined=set(profiles['combined']['paths'])
    groups=native.components(tuple(cl for cl in guards if cl),counts)
    supports={}
    for h in hints:supports.setdefault(tuple(h['clause']),set()).update(abs(l) for cl in h['template']['clauses'] for l in cl)
    shared=[set().union(*(supports[cl] for cl in group)) for group in groups]
    return dict(profiles=profiles,explicit_units=sorted(units),guard_composed=sorted(alone-units),
        mixed=sorted(combined-old-alone),new_candidates=sorted(combined-old-units),
        guards=guards,guard_components=len(groups),
        support_overlap_pairs=sum(bool(a&b) for i,a in enumerate(shared) for b in shared[i+1:]),
        component_guard_variables=[len({abs(l) for cl in g for l in cl}) for g in groups],
        source_components=len(native.components(local,counts)),
        subsumed_guards=sum(any(set(other)<set(cl) for other in guards) for cl in guards))


def compile_path(solver,source,hints,profile,forced,counts,*,path_limit=256):
    """Refute source|not(forced) by a path of checked local guard clauses.

    Each nontrivial edge excludes one branch with a saved unit proof. The live
    continuation follows the next literal until it contradicts the premise.
    No fresh SAT search or new native proof kind is used.
    """
    if type(path_limit) is not int or path_limit<1:raise ValueError('Invalid path limit')
    source=tuple(map(tuple,source));clauses=tuple(map(tuple,profile['clauses']))
    path=profile['paths'][forced]
    if not path or len(path)>path_limit:raise ValueError('Missing or oversized path')
    bank={}
    for h in hints:
        check_template(h['template'],counts)
        if not check_template(h['template'])<=set(source):raise ValueError('Missing local support')
        if h['clause']!=sorted(-v if b else v for v,b in h['template']['assumptions']):raise ValueError('Wrong guard clause')
        bank.setdefault(tuple(h['clause']),h['template'])
    for cl in source:
        if len(cl) in (1,2):bank[cl]=dict(clauses=[list(cl)],assumptions=sorted([[abs(l),l<0] for l in cl]),trace=[],conflict=0)
    current=-forced
    for nxt,cid in path:
        if (type(nxt) is not int or not nxt or type(cid) is not int or not 0<=cid<len(clauses)
                or clauses[cid]!=tuple(sorted({-current,nxt})) or clauses[cid] not in bank):raise ValueError('Invalid path edge')
        current=nxt
    if current!=forced:raise ValueError('Wrong path endpoint')
    def prepared(context):return solver._canonical(native.restrict_scan(source,context,counts))
    def leaf(template,context):
        child,names,key=prepared(context);old=solver._read(key,child,purpose='guard_path_leaf')
        if old is not None:
            if old['answer']:raise ValueError('Contradictory saved leaf')
            counts['existing_leaves']+=1;return key
        proof=transport_checked(template,context,{v:i+1 for i,v in enumerate(names)},child,counts)
        if proof is None:
            counts['support_propagation_fallbacks']+=1
            return materialize(solver,source,template,context=sorted([list(p) for p in context.items()]),counts=counts)['root']
        solver._store(key,dict(format=native.FORMAT,cnf=[list(cl) for cl in child],answer=False,proof=proof))
        counts['transported_leaves']+=1;return key
    def walk(index,context):
        child,names,key=prepared(context);old=solver._read(key,child,purpose='guard_path_existing')
        if old is not None:
            if old['answer']:raise ValueError('Contradictory saved path')
            counts['existing_path_nodes']+=1;return key
        if () in child:
            solver._store(key,dict(format=native.FORMAT,cnf=[list(cl) for cl in child],answer=False,proof=dict(kind='empty')));return key
        for i in range(index,len(path)):
            nxt,cid=path[i];v=abs(nxt);value=nxt>0;t=bank[clauses[cid]]
            if v in context:
                if context[v]==value:continue
                return leaf(t,context)
            excluded=leaf(t,{**context,v:not value})
            if v not in names:
                if excluded!=key:raise ValueError('Absent-variable lift changed cofactor')
                counts['absent_variable_lifts']+=1;return key
            live=walk(i+1,{**context,v:value})
            proof=dict(kind='split',variable=names.index(v)+1,low=excluded if value else live,high=live if value else excluded)
            solver._store(key,dict(format=native.FORMAT,cnf=[list(cl) for cl in child],answer=False,proof=proof))
            counts['composed_splits']+=1;return key
        raise ValueError('Path did not close its premise')
    return walk(0,{abs(forced):forced<0})
