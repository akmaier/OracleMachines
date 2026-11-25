"""One checked unit-propagation feedback pass over retained probe exclusions.

Each learned unit has an independent failed-probe proof on the original bank.
The feedback pass adds no new assumed probes and does not iterate discovery.
"""
from experiments import cnf_wide_guard_probes as frozen
from experiments import cnf_probe_support as support
from experiments.cnf_conditional_unit_support import transport,materialize
native=frozen.native


def prepare(source,templates,seed,counts):
    source,state,base,basis=frozen.validate(source,templates,seed,counts)
    if seed['status']!='unresolved':raise ValueError('Unresolved seed required')
    origins={cl:entry for cl,entry in zip(base,basis)}
    for i,row in enumerate(seed['probes']):
        clause=(-row['assumption'],);counts['feedback_exclusions']+=1
        if clause not in origins:origins[clause]=dict(kind='probe',index=i);counts['feedback_added_units']+=1
    clauses=tuple(sorted(origins))
    return source,base,basis,clauses,[origins[cl] for cl in clauses]


def discover(source,templates,seed,counts,*,work_limit=262144,trace_limit=256):
    if any(type(v) is not int or v<1 for v in (work_limit,trace_limit)):raise ValueError('Positive feedback bounds required')
    source,base,basis,clauses,origins=prepare(source,templates,seed,counts)
    index=frozen.UnitIndex(clauses,counts);start=counts['probe_occurrence_visits']
    try:proof=index.probe(None,counts,lambda:work_limit-(counts['probe_occurrence_visits']-start),trace_limit)
    except frozen.ProbeLimit as error:return dict(status='unresolved',reason=str(error),trace_limit=trace_limit,proof=None)
    return dict(status='refuted' if proof is not None else 'unresolved',reason='units' if proof is not None else 'open',trace_limit=trace_limit,proof=proof)


def validate(source,templates,seed,program,counts):
    if (type(program) is not dict or set(program)!={'status','reason','trace_limit','proof'} or
            type(program['trace_limit']) is not int or program['trace_limit']<1):raise ValueError('Invalid feedback program')
    prepared=prepare(source,templates,seed,counts);source,base,basis,clauses,origins=prepared
    if program['status']=='refuted' and program['reason']=='units':frozen.check_trace(source,clauses,None,program['proof'],counts,program['trace_limit'])
    elif not (program['status']=='unresolved' and program['reason'] in ('open','work_limit','trace_limit') and program['proof'] is None):raise ValueError('Invalid feedback outcome')
    return prepared


def _plan(source,templates,seed,program,prepared,counts):
    source,base,basis,clauses,origins=prepared
    top,_=support.slice_trace(clauses,program['proof'],None,counts);used={};ids=set();guards=set()
    def collect(cid):
        entry=basis[cid]
        if entry['kind']=='source':ids.add(entry['index'])
        else:guards.add(entry['index'])
    for cid in {top['conflict']}|{i for _,i in top['units']}:
        entry=origins[cid]
        if entry['kind']=='probe':
            index=entry['index'];row=seed['probes'][index]
            proof,_=support.slice_trace(base,row['proof'],row['assumption'],counts);used[index]=dict(assumption=row['assumption'],proof=proof)
            for j in {proof['conflict']}|{i for _,i in proof['units']}:collect(j)
        elif entry['kind']=='source':ids.add(entry['index'])
        else:guards.add(entry['index'])
    positions={cl:i for i,cl in enumerate(source)}
    for i in guards:
        for cl in templates[i]['clauses']:counts['feedback_support_clause_visits']+=1;ids.add(positions[tuple(cl)])
    ids=sorted(ids);small,names=native.normalize([source[i] for i in ids],counts);mapping={v:i+1 for i,v in enumerate(names)}
    required={abs(l) for l,_ in top['units']}|{abs(r['assumption']) for r in used.values()}
    required.update(abs(l) for r in used.values() for l,_ in r['proof']['units'])
    required.update(v for i in guards for v,_ in templates[i]['assumptions'])
    counts['feedback_source_literals']+=sum(map(len,source));counts['feedback_support_literals']+=sum(len(source[i]) for i in ids)
    counts['feedback_used_exclusions']+=len(used)
    if not required<=mapping.keys():counts['feedback_coordinate_fallbacks']+=1;return None
    def lit(l):return mapping[abs(l)]*(1 if l>0 else -1)
    selected=[transport(templates[i],mapping,counts) for i in sorted(guards)]
    _,_,newbase,_=frozen.prepare(small,selected,seed['mode'],counts);bpos={cl:i for i,cl in enumerate(newbase)}
    def remap(bank,proof,lookup):
        def cid(i):return lookup[tuple(sorted(lit(l) for l in bank[i]))]
        return dict(units=[[lit(l),cid(i)] for l,i in proof['units']],conflict=cid(proof['conflict']))
    compactseed=dict(seed,reason='complete',probes=[dict(assumption=lit(r['assumption']),proof=remap(base,r['proof'],bpos)) for _,r in sorted(used.items())])
    _,_,_,newbank,_=prepare(small,selected,compactseed,counts)
    compact=dict(program,proof=remap(clauses,top,{cl:i for i,cl in enumerate(newbank)}))
    checked=validate(small,selected,compactseed,compact,counts)
    return dict(source=small,templates=selected,seed=compactseed,program=compact,indices=ids,prepared=checked)


def _compile(solver,templates,seed,program,prepared,counts):
    source,base,basis,clauses,origins=prepared
    def canonical(context):return solver._canonical(native.restrict_scan(source,context,counts))
    def basic_leaf(cid,context):
        entry=basis[cid];cl=base[cid]
        template=(dict(clauses=[list(cl)],assumptions=sorted([[abs(l),l<0] for l in cl]),trace=[],conflict=0)
                  if entry['kind']=='source' else templates[entry['index']])
        return materialize(solver,source,template,context=sorted([list(p) for p in context.items()]),counts=counts)['root']
    def trace(proof,leaf,context):
        def walk(i,context):
            cnf,names,key=canonical(context);old=solver._read(key,cnf,purpose='feedback_existing')
            if old is not None:
                if old['answer']:raise ValueError('Contradictory feedback cache')
                counts['feedback_native_hits']+=1;return key
            if () in cnf:
                solver._store(key,dict(format=native.FORMAT,cnf=list(map(list,cnf)),answer=False,proof=dict(kind='empty')));return key
            if i==len(proof['units']):return leaf(proof['conflict'],context)
            lit,cid=proof['units'][i];v=abs(lit);bit=lit>0
            if v in context:
                counts['feedback_fixed_trace_steps']+=1
                return walk(i+1,context) if context[v]==bit else leaf(cid,context)
            excluded=leaf(cid,{**context,v:not bit})
            if v not in names:
                if excluded!=key:raise ValueError('Changed absent coordinate')
                counts['feedback_absent_lifts']+=1;return key
            live=walk(i+1,{**context,v:bit})
            solver._store(key,dict(format=native.FORMAT,cnf=list(map(list,cnf)),answer=False,
                proof=dict(kind='split',variable=names.index(v)+1,low=excluded if bit else live,high=live if bit else excluded)))
            counts['feedback_native_splits']+=1;return key
        return walk(0,context)
    base_positions={cl:i for i,cl in enumerate(base)}
    def feedback_leaf(cid,context):
        entry=origins[cid]
        if entry['kind']!='probe':return basic_leaf(base_positions[clauses[cid]],context)
        row=seed['probes'][entry['index']];lit=row['assumption']
        if context.get(abs(lit))!=(lit>0):raise ValueError('Failed probe premise missing')
        counts['feedback_expanded_exclusions']+=1
        return trace(row['proof'],basic_leaf,context)
    return trace(program['proof'],feedback_leaf,{})


def compile_program(solver,source,templates,seed,program,counts,*,select_support=True):
    prepared=validate(source,templates,seed,program,counts)
    if program['status']!='refuted':raise ValueError('Complete feedback refutation required')
    source=prepared[0];root=native.token(source,counts);old=solver._read(root,source,purpose='feedback_root')
    if old is not None:
        if old['answer']:raise ValueError('Contradictory feedback root')
        counts['feedback_root_hits']+=1;return root
    plan=_plan(source,templates,seed,program,prepared,counts) if select_support else None
    if plan is None:return _compile(solver,templates,seed,program,prepared,counts)
    child=_compile(solver,plan['templates'],plan['seed'],plan['program'],plan['prepared'],counts)
    if child!=root:
        solver._store(root,dict(format=native.FORMAT,cnf=list(map(list,source)),answer=False,
            proof=dict(kind='component',clauses=plan['indices'],child=child)))
        counts['feedback_support_wrappers']+=1
    return root


def compile_extension(solver,source,templates,prefix,seed,program,counts):
    frames,tail=frozen.bind_prefix(source,templates,prefix,counts);ts=[h['template'] for h in tail['hints']]
    validate(tail['local'],ts,seed,program,counts)
    if program['status']!='refuted':raise ValueError('Complete feedback extension required')
    root=native.token(tuple(map(tuple,source)),counts);old=solver._read(root,tuple(map(tuple,source)),purpose='feedback_extension')
    if old is not None:
        if old['answer']:raise ValueError('Contradictory feedback extension')
        counts['extension_root_hits']+=1;return root
    key=compile_program(solver,tail['local'],ts,seed,program,counts)
    for frame in reversed(frames):
        state=frame['state'];forced=frame['forced'];profile=dict(clauses=state['graph'],paths={forced:frame['path']})
        excluded=frozen.frozen.compile_path(solver,state['local'],state['hints'],profile,forced,counts,path_limit=prefix['path_limit'])
        cnf=state['local'];keyroot=native.token(cnf,counts)
        solver._store(keyroot,dict(format=native.FORMAT,cnf=list(map(list,cnf)),answer=False,
            proof=dict(kind='split',variable=abs(forced),low=excluded if forced>0 else key,high=key if forced>0 else excluded)))
        key=keyroot;counts['extension_prefix_splits']+=1
    if key!=root:raise ValueError('Changed feedback extension root')
    return key
