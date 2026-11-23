"""Lift checked conflict leaves to source-bound conditional unit supports.

Only unit/empty leaves reached through unit, split or component nodes are
supported. Other endpoints stay explicitly unresolved. A matched template proves
UNSAT only under its recorded assumptions; it is not a whole-query verdict.
"""
from collections import Counter
from experiments.cnf_residual_dag import restrict,propagate,FORMAT
from experiments.cnf_clause_deletion_guard import clause_set

FORMAT_HINT='conditional-unit-support-v1'


class ExtractionBudget(RuntimeError):pass


def fixed_pairs(pairs):
    if type(pairs) is not list:raise ValueError('Assignment pairs must be a list')
    fixed={}
    for p in pairs:
        if type(p) is not list or len(p)!=2:raise ValueError('Invalid assignment pair')
        v,b=p
        if type(v) is not int or v<=0 or type(b) is not bool or v in fixed:raise ValueError('Invalid assignment')
        fixed[v]=b
    return fixed


def check_template(template,counts=None):
    c=Counter() if counts is None else counts
    if type(template) is not dict or set(template)!={'clauses','assumptions','trace','conflict'}:raise ValueError('Invalid template fields')
    clauses=template['clauses']
    if type(clauses) is not list or any(type(cl) is not list for cl in clauses):raise ValueError('Invalid clauses')
    members=clause_set(clauses,c)
    if [list(cl) for cl in sorted(members)]!=clauses:raise ValueError('Template clauses must be sorted and unique')
    fixed=fixed_pairs(template['assumptions'])
    if type(template['trace']) is not list:raise ValueError('Invalid trace')
    def clause(cid):
        if type(cid) is not int or not 0<=cid<len(clauses):raise ValueError('Invalid reason index')
        c['template_checked_reason_literals']+=len(clauses[cid]);return clauses[cid]
    for step in template['trace']:
        if type(step) is not list or len(step)!=2:raise ValueError('Invalid trace step')
        lit,cid=step;reason=clause(cid)
        if type(lit) is not int or not lit or abs(lit) in fixed or lit not in reason:raise ValueError('Invalid forced literal')
        if any(abs(x) not in fixed or fixed[abs(x)]==(x>0) for x in reason if x!=lit):raise ValueError('Non-forced template step')
        fixed[abs(lit)]=lit>0
    if any(abs(l) not in fixed or fixed[abs(l)]==(l>0) for l in clause(template['conflict'])):raise ValueError('Template has no conflict')
    c['templates_checked']+=1
    return members


def extract(solver,source,*,node_limit=64,literal_limit=65536):
    if any(type(v) is not int or v<1 for v in (node_limit,literal_limit)):raise ValueError('Invalid extraction limits')
    source=tuple(tuple(cl) for cl in source)
    counts=Counter();root,names,key=solver._canonical(source);start=solver._read(key,root,purpose='conditional_origin')
    if start is None or start['answer'] is not False:raise ValueError('Checked negative origin required')
    entries=[]
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
    def walk(nodekey,mapping,fixed,guards,trace):
        if counts['conditional_node_visits']>=node_limit:raise ExtractionBudget('Node occurrence budget')
        node=solver._read(nodekey,purpose='conditional_path')
        if node is None or node['answer'] is not False:raise ValueError('Missing negative path node')
        cnf=tuple(map(tuple,node['cnf']));size=sum(map(len,cnf))
        if counts['conditional_node_literals']+size>literal_limit:raise ExtractionBudget('Path literal budget')
        counts['conditional_node_visits']+=1;counts['conditional_node_literals']+=size
        proof=node['proof'];kind=proof['kind']
        if kind not in ('empty','units','split','component'):
            counts['conditional_unsupported_endpoints']+=1;return dict(unresolved=nodekey,kind=kind)
        # Original source clauses remain distinct from their reduced images.
        # Choose the first original representative of each current residual.
        origins={}
        for cid,cl in enumerate(root):
            reduced=restrict((cl,),fixed,counts)
            if reduced:origins.setdefault(tuple(reduced[0]),cid)
        def literal(l):return (1 if l>0 else -1)*mapping[abs(l)]
        root_ids=[origins[tuple(sorted(literal(l) for l in cl))] for cl in cnf]
        def descend(child,assignment,newguards,newtrace,subset=None):
            raw=restrict(cnf if subset is None else subset,assignment,counts)
            normalized,oldnames,actual=solver._canonical(raw)
            if actual!=child:raise ValueError('Wrong conditioned child')
            mapped={i+1:mapping[v] for i,v in enumerate(oldnames)}
            updated={**fixed,**{mapping[v]:b for v,b in assignment.items()}}
            return walk(child,mapped,updated,newguards,newtrace)
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
    tree=walk(key,dict(enumerate(range(1,len(names)+1),1)),{}, {},[])
    return dict(format=FORMAT_HINT,source=[list(cl) for cl in source],origin=key,entries=entries,tree=tree),dict(counts)


def transport(template,signed_map,counts=None):
    c=Counter() if counts is None else counts;check_template(template,c)
    if type(signed_map) is not dict or any(type(v) is not int or v<=0 or type(l) is not int or not l for v,l in signed_map.items()):raise ValueError('Invalid signed map')
    if len({abs(l) for l in signed_map.values()})!=len(signed_map):raise ValueError('Noninjective map')
    variables={abs(l) for cl in template['clauses'] for l in cl}|set(fixed_pairs(template['assumptions']))
    if not variables<=signed_map.keys():raise ValueError('Incomplete map')
    def lit(l):return signed_map[abs(l)]*(1 if l>0 else -1)
    changed=[tuple(sorted(lit(l) for l in cl)) for cl in template['clauses']];ordered=sorted(changed);position={cl:i for i,cl in enumerate(ordered)}
    ids={i:position[cl] for i,cl in enumerate(changed)};c['template_transport_literals']+=sum(map(len,changed))
    result=dict(clauses=[list(cl) for cl in ordered],assumptions=sorted([[abs(signed_map[v]),b if signed_map[v]>0 else not b] for v,b in fixed_pairs(template['assumptions']).items()]),
        trace=[[lit(l),ids[cid]] for l,cid in template['trace']],conflict=ids[template['conflict']])
    check_template(result,c);return result


def match(source,template,counts=None):
    c=Counter() if counts is None else counts;wanted=check_template(template,c);members=clause_set(source,c)
    c['conditional_containment_clauses']+=len(wanted)
    return wanted<=members


def materialize(solver,source,template,*,context=None,counts=None):
    """Publish only the conditioned target's native refutation, with no SAT search."""
    c=Counter() if counts is None else counts
    if not match(source,template,c):raise ValueError('Template clauses are missing from target')
    assumptions=fixed_pairs(template['assumptions']);fixed=assumptions if context is None else fixed_pairs(context)
    if any(fixed.get(v)!=b for v,b in assumptions.items()):raise ValueError('Context does not extend template assumptions')
    local,names,key=solver._canonical(restrict(source,fixed,c))
    old=solver._read(key,local,purpose='conditional_existing')
    if old is not None:
        if old['answer'] is not False:raise ValueError('Conflicting conditional answer')
        return dict(root=key,assignment=[[v,b] for v,b in sorted(fixed.items())],answer=False,conditional=True,inserted=False)
    if () in local:proof=dict(kind='empty')
    else:
        rename={v:i+1 for i,v in enumerate(names)};positions={cl:i for i,cl in enumerate(local)}
        small=restrict(template['clauses'],fixed,c)
        ids=sorted({positions[tuple(sorted((1 if l>0 else -1)*rename[abs(l)] for l in cl))] for cl in small})
        _,trace,conflict=propagate(tuple(local[i] for i in ids),c)
        if conflict is None:raise ValueError('Conditioned support did not refute by units')
        proof=dict(kind='units',trace=[[l,ids[cid]] for l,cid in trace],conflict=ids[conflict])
    solver._store(key,dict(format=FORMAT,cnf=[list(cl) for cl in local],answer=False,proof=proof));c['conditional_publications']+=1
    return dict(root=key,assignment=[[v,b] for v,b in sorted(fixed.items())],answer=False,conditional=True,inserted=True)
