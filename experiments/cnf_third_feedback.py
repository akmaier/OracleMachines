"""Propagate B2 failures once, preserving four acyclic proof banks.

No new assumed probe is run. Native reconstruction expands third-stage failures
on B2, second-stage failures on B1 and original failures on B0. All earlier
proof sources remain frozen; this is an optional experimental recognizer.
"""
from experiments import cnf_changed_closure_probes as changed
from experiments.cnf_prepared_publication import prepare_frame
from experiments.cnf_conditional_unit_support import transport,match,fixed_pairs,restrict,propagate
layered=changed.layered
frozen=layered.frozen;feedback=layered.feedback;support=layered.support;native=layered.native


def add_layer(prepared, third, counts):
    source,base,basis,first,origins,second,origins2=prepared
    if third['action']=='unchanged':return (*prepared,second,origins2)
    if third['action']!='searched':raise ValueError('Invalid third-stage action')
    program=third['program'];changed.prior.check_program(source,second,program,counts)
    if program['status']!='unresolved':raise ValueError('Unresolved third stage required')
    return _append_checked(prepared,third,counts)


def prepare(source,templates,seed,closure,new,next_closure,third,counts):
    prepared=changed.validate(source,templates,seed,closure,new,next_closure,third,counts)
    # The searched program was checked above. Reuse that validation here; the
    # private assembler below does not accept public unvalidated proof inputs.
    if third['action']=='searched' and third['program']['status']!='unresolved':
        raise ValueError('Unresolved third stage required')
    return _append_checked(prepared,third,counts)


def _append_checked(prepared,third,counts):
    if third['action']=='unchanged':return (*prepared,prepared[5],prepared[6])
    bank={cl:entry for cl,entry in zip(prepared[5],prepared[6])}
    for i,row in enumerate(third['program']['probes']):
        cl=(-row['assumption'],);counts['third_exclusions']+=1
        if cl not in bank:bank[cl]=dict(kind='third_probe',index=i);counts['third_added_units']+=1
    clauses=tuple(sorted(bank))
    return (*prepared,clauses,[bank[cl] for cl in clauses])


def discover(source,templates,seed,closure,new,next_closure,third,counts,*,mode='feedback',work_limit=262144,trace_limit=256):
    if mode not in ('base','feedback') or any(type(v) is not int or v<1 for v in (work_limit,trace_limit)):
        raise ValueError('Invalid third feedback bounds')
    prepared=prepare(source,templates,seed,closure,new,next_closure,third,counts)
    bank=prepared[5] if mode=='base' else prepared[7]
    index=frozen.UnitIndex(bank,counts);start=counts['probe_occurrence_visits']
    try:proof=index.probe(None,counts,lambda:work_limit-(counts['probe_occurrence_visits']-start),trace_limit)
    except frozen.ProbeLimit as error:
        return dict(status='unresolved',reason=str(error),trace_limit=trace_limit,proof=None,mode=mode)
    return dict(status='refuted' if proof is not None else 'unresolved',reason='units' if proof is not None else 'open',trace_limit=trace_limit,proof=proof,mode=mode)


def check_program(prepared,program,counts):
    if (type(program) is not dict or set(program)!={'status','reason','trace_limit','proof','mode'}
        or type(program['trace_limit']) is not int or program['trace_limit']<1 or program['mode'] not in ('base','feedback')):
        raise ValueError('Invalid third feedback program')
    bank=prepared[5] if program['mode']=='base' else prepared[7]
    if program['status']=='refuted' and program['reason']=='units':
        frozen.check_trace(prepared[0],bank,None,program['proof'],counts,program['trace_limit'])
    elif not (program['status']=='unresolved' and program['reason'] in ('open','work_limit','trace_limit') and program['proof'] is None):
        raise ValueError('Invalid third feedback outcome')


def validate(source,templates,seed,closure,new,next_closure,third,program,counts):
    prepared=prepare(source,templates,seed,closure,new,next_closure,third,counts)
    check_program(prepared,program,counts)
    return prepared


def _plan(source,templates,seed,new,third,program,prepared,counts):
    source,base,basis,first,origins,second,origins2,thirdbank,origins3=prepared
    top,_=support.slice_trace(thirdbank,program['proof'],None,counts)
    used_old={};used_new={};used_third={};ids=set();guards=set()
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
        elif kind=='third_probe':
            if i in used_third:return
            row=third['program']['probes'][i];proof,_=support.slice_trace(second,row['proof'],row['assumption'],counts)
            used_third[i]=dict(assumption=row['assumption'],proof=proof)
            for j in {proof['conflict']}|{j for _,j in proof['units']}:collect(origins2[j])
        else:raise ValueError('Unknown proof origin')
    for cid in {top['conflict']}|{i for _,i in top['units']}:collect(origins3[cid])
    positions={cl:i for i,cl in enumerate(source)}
    for i in guards:
        for cl in templates[i]['clauses']:counts['layer_support_clause_visits']+=1;ids.add(positions[tuple(cl)])
    ids=sorted(ids);small,names=native.normalize([source[i] for i in ids],counts);mapping={v:i+1 for i,v in enumerate(names)}
    required={abs(l) for l,_ in top['units']}
    for rows in (used_old,used_new,used_third):
        required.update(abs(r['assumption']) for r in rows.values())
        required.update(abs(l) for r in rows.values() for l,_ in r['proof']['units'])
    required.update(v for i in guards for v,_ in templates[i]['assumptions'])
    counts['layer_source_literals']+=sum(map(len,source));counts['layer_support_literals']+=sum(len(source[i]) for i in ids)
    counts['layer_used_old']+=len(used_old);counts['layer_used_new']+=len(used_new);counts['layer_used_third']+=len(used_third)
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
    checked=layered.add_layer(first_prepared,compactnew,counts)
    third_program=third['program'] if third['action']=='searched' else dict(status='unresolved',reason='complete',mode='conditioned',trace_limit=256,terminal=None)
    compactthird=dict(action='searched',program=dict(third_program,reason='complete',probes=[dict(assumption=lit(r['assumption']),proof=remap(second,r['proof'],checked[5])) for _,r in sorted(used_third.items())]))
    checked=add_layer(checked,compactthird,counts)
    compact=dict(program,proof=remap(thirdbank,top,checked[7]));check_program(checked,compact,counts)
    return dict(source=small,templates=selected,seed=compactseed,new=compactnew,third=compactthird,program=compact,indices=ids,prepared=checked)


def _compile(solver,templates,seed,new,third,program,prepared,counts,*,reuse_frames=False):
    source,base,basis,first,origins,second,origins2,thirdbank,origins3=prepared
    banks=(base,first,second,thirdbank);entries=(basis,origins,origins2,origins3)
    def frame(context,offered=None):
        if reuse_frames and offered is not None:
            counts['prepared_context_reuses']+=1;return offered
        return prepare_frame(solver,native.restrict_scan(source,context,counts),counts)
    def materialize(template,context,offered):
        if not match(source,template,counts):raise ValueError('Template clauses are missing from target')
        assumptions=fixed_pairs(template['assumptions']);fixed=fixed_pairs(sorted([list(p) for p in context.items()]))
        if any(fixed.get(v)!=b for v,b in assumptions.items()):raise ValueError('Context does not extend template assumptions')
        local,names,key,publish=frame(context,offered)
        old=solver._read(key,local,purpose='conditional_existing')
        if old is not None:
            if old['answer'] is not False:raise ValueError('Conflicting conditional answer')
            return key
        if () in local:proof=dict(kind='empty')
        else:
            rename={v:i+1 for i,v in enumerate(names)};positions={cl:i for i,cl in enumerate(local)}
            small=restrict(template['clauses'],fixed,counts)
            ids=sorted({positions[tuple(sorted((1 if l>0 else -1)*rename[abs(l)] for l in cl))] for cl in small})
            _,trace,conflict=propagate(tuple(local[i] for i in ids),counts)
            if conflict is None:raise ValueError('Conditioned support did not refute by units')
            proof=dict(kind='units',trace=[[l,ids[cid]] for l,cid in trace],conflict=ids[conflict])
        publish(proof);counts['conditional_publications']+=1;return key
    def leaf(stage,cid,context,offered=None):
        entry=entries[stage][cid];kind=entry['kind'];i=entry['index']
        if kind in ('source','guard'):
            cl=banks[stage][cid]
            template=(dict(clauses=[list(cl)],assumptions=sorted([[abs(l),l<0] for l in cl]),trace=[],conflict=0)
                      if kind=='source' else templates[i])
            return materialize(template,context,offered)
        lower={'probe':0,'new_probe':1,'third_probe':2}[kind]
        if lower>=stage:raise ValueError('Non-decreasing proof dependency')
        row=(seed,new,third['program'])[lower]['probes'][i];lit=row['assumption']
        if context.get(abs(lit))!=(lit>0):raise ValueError('Failed probe premise missing')
        counts[('layer_expanded_old','layer_expanded_new','layer_expanded_third')[lower]]+=1
        return trace(lower,row['proof'],context,offered)
    def trace(stage,proof,context,offered=None):
        def walk(i,context,offered=None):
            prepared_frame=frame(context,offered);cnf,names,key,publish=prepared_frame
            old=solver._read(key,cnf,purpose='layer_existing')
            if old is not None:
                if old['answer']:raise ValueError('Contradictory layered cache')
                counts['layer_native_hits']+=1;return key
            if () in cnf:publish(dict(kind='empty'));return key
            if i==len(proof['units']):return leaf(stage,proof['conflict'],context,prepared_frame)
            lit,cid=proof['units'][i];v=abs(lit);bit=lit>0
            if v in context:
                counts['layer_fixed_trace_steps']+=1
                return walk(i+1,context,prepared_frame) if context[v]==bit else leaf(stage,cid,context,prepared_frame)
            excluded=leaf(stage,cid,{**context,v:not bit})
            if v not in names:
                if excluded!=key:raise ValueError('Changed absent coordinate')
                counts['layer_absent_lifts']+=1;return key
            live=walk(i+1,{**context,v:bit})
            publish(dict(kind='split',variable=names.index(v)+1,low=excluded if bit else live,high=live if bit else excluded))
            counts['layer_native_splits']+=1;return key
        return walk(0,context,offered)
    return trace(3,program['proof'],{})


def compile_program(solver,source,templates,seed,closure,new,next_closure,third,program,counts,*,select_support=True):
    prepared=validate(source,templates,seed,closure,new,next_closure,third,program,counts)
    if program['status']!='refuted' or program['mode']!='feedback':raise ValueError('Complete third feedback refutation required')
    source=prepared[0];root=native.token(source,counts);old=solver._read(root,source,purpose='third_feedback_root')
    if old is not None:
        if old['answer']:raise ValueError('Contradictory layered root')
        counts['layer_root_hits']+=1;return root
    plan=_plan(source,templates,seed,new,third,program,prepared,counts) if select_support else None
    if plan is None:return _compile(solver,templates,seed,new,third,program,prepared,counts)
    child=_compile(solver,plan['templates'],plan['seed'],plan['new'],plan['third'],plan['program'],plan['prepared'],counts)
    if child!=root:
        solver._store(root,dict(format=native.FORMAT,cnf=list(map(list,source)),answer=False,
            proof=dict(kind='component',clauses=plan['indices'],child=child)))
        counts['layer_support_wrappers']+=1
    return root


def compile_extension(solver,source,templates,prefix,seed,closure,new,next_closure,third,program,counts):
    frames,tail=frozen.bind_prefix(source,templates,prefix,counts);ts=[h['template'] for h in tail['hints']]
    validate(tail['local'],ts,seed,closure,new,next_closure,third,program,counts)
    if program['status']!='refuted' or program['mode']!='feedback':raise ValueError('Complete feedback extension required')
    root=native.token(tuple(map(tuple,source)),counts);old=solver._read(root,tuple(map(tuple,source)),purpose='feedback_extension')
    if old is not None:
        if old['answer']:raise ValueError('Contradictory feedback extension')
        counts['extension_root_hits']+=1;return root
    key=compile_program(solver,tail['local'],ts,seed,closure,new,next_closure,third,program,counts)
    for frame in reversed(frames):
        state=frame['state'];forced=frame['forced'];profile=dict(clauses=state['graph'],paths={forced:frame['path']})
        excluded=frozen.frozen.compile_path(solver,state['local'],state['hints'],profile,forced,counts,path_limit=prefix['path_limit'])
        cnf=state['local'];keyroot=native.token(cnf,counts)
        solver._store(keyroot,dict(format=native.FORMAT,cnf=list(map(list,cnf)),answer=False,
            proof=dict(kind='split',variable=abs(forced),low=excluded if forced>0 else key,high=key if forced>0 else excluded)))
        key=keyroot;counts['extension_prefix_splits']+=1
    if key!=root:raise ValueError('Changed feedback extension root')
    return key
