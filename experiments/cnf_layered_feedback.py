"""One feedback pass using two acyclic layers of checked failed probes."""
from experiments import cnf_closure_probes as prior
from experiments.cnf_conditional_unit_support import transport,materialize
frozen=prior.frozen;feedback=prior.feedback;support=prior.support;native=prior.native


def add_layer(prepared,new,counts):
    source,base,basis,first,origins=prepared
    prior.check_program(source,first,new,counts)
    if new['status']!='unresolved':raise ValueError('Unresolved new probe layer required')
    second={cl:entry for cl,entry in zip(first,origins)}
    for i,row in enumerate(new['probes']):
        cl=(-row['assumption'],);counts['layer_exclusions']+=1
        if cl not in second:second[cl]=dict(kind='new_probe',index=i);counts['layer_added_units']+=1
    bank=tuple(sorted(second))
    return (*prepared,bank,[second[cl] for cl in bank])


def prepare(source,templates,seed,closure,new,counts):
    prepared=feedback.prepare(source,templates,seed,counts)
    fixed=prior.check_closure(prepared[3],closure,counts)
    result=add_layer(prepared,new,counts)
    if any(abs(row['assumption']) in fixed for row in new['probes']):raise ValueError('New probe repeats closure assignment')
    return result


def discover(source,templates,seed,closure,new,counts,*,mode='feedback',work_limit=262144,trace_limit=256):
    if mode not in ('base','feedback') or any(type(v) is not int or v<1 for v in (work_limit,trace_limit)):raise ValueError('Invalid layered feedback bounds')
    prepared=prepare(source,templates,seed,closure,new,counts)
    bank=prepared[3] if mode=='base' else prepared[5]
    index=frozen.UnitIndex(bank,counts);start=counts['probe_occurrence_visits']
    try:proof=index.probe(None,counts,lambda:work_limit-(counts['probe_occurrence_visits']-start),trace_limit)
    except frozen.ProbeLimit as error:return dict(status='unresolved',reason=str(error),trace_limit=trace_limit,proof=None,mode=mode)
    return dict(status='refuted' if proof is not None else 'unresolved',reason='units' if proof is not None else 'open',trace_limit=trace_limit,proof=proof,mode=mode)


def check_program(prepared,program,counts):
    if (type(program) is not dict or set(program)!={'status','reason','trace_limit','proof','mode'} or type(program['trace_limit']) is not int or program['trace_limit']<1 or program['mode'] not in ('base','feedback')):raise ValueError('Invalid layered feedback program')
    bank=prepared[3] if program['mode']=='base' else prepared[5]
    if program['status']=='refuted' and program['reason']=='units':frozen.check_trace(prepared[0],bank,None,program['proof'],counts,program['trace_limit'])
    elif not (program['status']=='unresolved' and program['reason'] in ('open','work_limit','trace_limit') and program['proof'] is None):raise ValueError('Invalid layered feedback outcome')


def validate(source,templates,seed,closure,new,program,counts):
    prepared=prepare(source,templates,seed,closure,new,counts);check_program(prepared,program,counts)
    return prepared


def _plan(source,templates,seed,new,program,prepared,counts):
    source,base,basis,first,origins,second,origins2=prepared
    top,_=support.slice_trace(second,program['proof'],None,counts)
    used_old={};used_new={};ids=set();guards=set()
    def collect(entry):
        kind=entry['kind'];i=entry['index']
        if kind=='source':ids.add(i)
        elif kind=='guard':guards.add(i)
        elif kind=='probe':
            if i in used_old:return
            row=seed['probes'][i];proof,_=support.slice_trace(base,row['proof'],row['assumption'],counts)
            used_old[i]=dict(assumption=row['assumption'],proof=proof)
            for j in {proof['conflict']}|{j for _,j in proof['units']}:collect(basis[j])
        elif kind=='new_probe':
            if i in used_new:return
            row=new['probes'][i];proof,_=support.slice_trace(first,row['proof'],row['assumption'],counts)
            used_new[i]=dict(assumption=row['assumption'],proof=proof)
            for j in {proof['conflict']}|{j for _,j in proof['units']}:collect(origins[j])
        else:raise ValueError('Unknown proof origin')
    for cid in {top['conflict']}|{i for _,i in top['units']}:collect(origins2[cid])
    positions={cl:i for i,cl in enumerate(source)}
    for i in guards:
        for cl in templates[i]['clauses']:counts['layer_support_clause_visits']+=1;ids.add(positions[tuple(cl)])
    ids=sorted(ids);small,names=native.normalize([source[i] for i in ids],counts);mapping={v:i+1 for i,v in enumerate(names)}
    required={abs(l) for l,_ in top['units']}
    for rows in (used_old,used_new):
        required.update(abs(r['assumption']) for r in rows.values())
        required.update(abs(l) for r in rows.values() for l,_ in r['proof']['units'])
    required.update(v for i in guards for v,_ in templates[i]['assumptions'])
    counts['layer_source_literals']+=sum(map(len,source));counts['layer_support_literals']+=sum(len(source[i]) for i in ids)
    counts['layer_used_old']+=len(used_old);counts['layer_used_new']+=len(used_new)
    if not required<=mapping.keys():counts['layer_coordinate_fallbacks']+=1;return None
    def lit(l):return mapping[abs(l)]*(1 if l>0 else -1)
    selected=[transport(templates[i],mapping,counts) for i in sorted(guards)]
    def remap(bank,proof,newbank):
        positions={cl:i for i,cl in enumerate(newbank)}
        def cid(i):return positions[tuple(sorted(lit(l) for l in bank[i]))]
        return dict(units=[[lit(l),cid(i)] for l,i in proof['units']],conflict=cid(proof['conflict']))
    _,_,newbase,_=frozen.prepare(small,selected,seed['mode'],counts)
    compactseed=dict(seed,reason='complete',probes=[dict(assumption=lit(r['assumption']),proof=remap(base,r['proof'],newbase)) for _,r in sorted(used_old.items())])
    first_prepared=feedback.prepare(small,selected,compactseed,counts)
    compactnew=dict(new,reason='complete',probes=[dict(assumption=lit(r['assumption']),proof=remap(first,r['proof'],first_prepared[3])) for _,r in sorted(used_new.items())])
    checked=add_layer(first_prepared,compactnew,counts)
    compact=dict(program,proof=remap(second,top,checked[5]));check_program(checked,compact,counts)
    return dict(source=small,templates=selected,seed=compactseed,new=compactnew,program=compact,indices=ids,prepared=checked)


def _compile(solver,templates,seed,new,program,prepared,counts):
    source,base,basis,first,origins,second,origins2=prepared
    banks=(base,first,second);entries=(basis,origins,origins2)
    def canonical(context):return solver._canonical(native.restrict_scan(source,context,counts))
    def leaf(stage,cid,context):
        entry=entries[stage][cid];kind=entry['kind'];i=entry['index']
        if kind in ('source','guard'):
            cl=banks[stage][cid]
            template=(dict(clauses=[list(cl)],assumptions=sorted([[abs(l),l<0] for l in cl]),trace=[],conflict=0)
                      if kind=='source' else templates[i])
            return materialize(solver,source,template,context=sorted([list(p) for p in context.items()]),counts=counts)['root']
        lower=0 if kind=='probe' else 1
        if lower>=stage:raise ValueError('Non-decreasing proof dependency')
        row=(seed if lower==0 else new)['probes'][i];lit=row['assumption']
        if context.get(abs(lit))!=(lit>0):raise ValueError('Failed probe premise missing')
        counts['layer_expanded_old' if lower==0 else 'layer_expanded_new']+=1
        return trace(lower,row['proof'],context)
    def trace(stage,proof,context):
        def walk(i,context):
            cnf,names,key=canonical(context);old=solver._read(key,cnf,purpose='layer_existing')
            if old is not None:
                if old['answer']:raise ValueError('Contradictory layered cache')
                counts['layer_native_hits']+=1;return key
            if () in cnf:
                solver._store(key,dict(format=native.FORMAT,cnf=list(map(list,cnf)),answer=False,proof=dict(kind='empty')));return key
            if i==len(proof['units']):return leaf(stage,proof['conflict'],context)
            lit,cid=proof['units'][i];v=abs(lit);bit=lit>0
            if v in context:
                counts['layer_fixed_trace_steps']+=1
                return walk(i+1,context) if context[v]==bit else leaf(stage,cid,context)
            excluded=leaf(stage,cid,{**context,v:not bit})
            if v not in names:
                if excluded!=key:raise ValueError('Changed absent coordinate')
                counts['layer_absent_lifts']+=1;return key
            live=walk(i+1,{**context,v:bit})
            solver._store(key,dict(format=native.FORMAT,cnf=list(map(list,cnf)),answer=False,
                proof=dict(kind='split',variable=names.index(v)+1,low=excluded if bit else live,high=live if bit else excluded)))
            counts['layer_native_splits']+=1;return key
        return walk(0,context)
    return trace(2,program['proof'],{})


def compile_program(solver,source,templates,seed,closure,new,program,counts,*,select_support=True):
    prepared=validate(source,templates,seed,closure,new,program,counts)
    if program['status']!='refuted' or program['mode']!='feedback':raise ValueError('Complete layered feedback refutation required')
    source=prepared[0];root=native.token(source,counts);old=solver._read(root,source,purpose='layer_root')
    if old is not None:
        if old['answer']:raise ValueError('Contradictory layered root')
        counts['layer_root_hits']+=1;return root
    plan=_plan(source,templates,seed,new,program,prepared,counts) if select_support else None
    if plan is None:return _compile(solver,templates,seed,new,program,prepared,counts)
    child=_compile(solver,plan['templates'],plan['seed'],plan['new'],plan['program'],plan['prepared'],counts)
    if child!=root:
        solver._store(root,dict(format=native.FORMAT,cnf=list(map(list,source)),answer=False,
            proof=dict(kind='component',clauses=plan['indices'],child=child)))
        counts['layer_support_wrappers']+=1
    return root


def compile_extension(solver,source,templates,prefix,seed,closure,new,program,counts):
    frames,tail=frozen.bind_prefix(source,templates,prefix,counts);ts=[h['template'] for h in tail['hints']]
    validate(tail['local'],ts,seed,closure,new,program,counts)
    if program['status']!='refuted' or program['mode']!='feedback':raise ValueError('Complete feedback extension required')
    root=native.token(tuple(map(tuple,source)),counts);old=solver._read(root,tuple(map(tuple,source)),purpose='feedback_extension')
    if old is not None:
        if old['answer']:raise ValueError('Contradictory feedback extension')
        counts['extension_root_hits']+=1;return root
    key=compile_program(solver,tail['local'],ts,seed,closure,new,program,counts)
    for frame in reversed(frames):
        state=frame['state'];forced=frame['forced'];profile=dict(clauses=state['graph'],paths={forced:frame['path']})
        excluded=frozen.frozen.compile_path(solver,state['local'],state['hints'],profile,forced,counts,path_limit=prefix['path_limit'])
        cnf=state['local'];keyroot=native.token(cnf,counts)
        solver._store(keyroot,dict(format=native.FORMAT,cnf=list(map(list,cnf)),answer=False,
            proof=dict(kind='split',variable=abs(forced),low=excluded if forced>0 else key,high=key if forced>0 else excluded)))
        key=keyroot;counts['extension_prefix_splits']+=1
    if key!=root:raise ValueError('Changed feedback extension root')
    return key
