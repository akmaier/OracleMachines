"""Compile opposite B3 probes using the unchanged four-bank provenance rules."""
from experiments import cnf_probe_cursor as candidate
from experiments.cnf_prepared_publication import prepare_frame
from experiments.cnf_conditional_unit_support import transport,match,fixed_pairs,restrict,propagate
feedback=candidate.feedback.feedback
layered=candidate.feedback.layered
frozen=candidate.frozen;support=candidate.feedback.support;native=candidate.native
add_layer=candidate.feedback.add_layer


def _plan(source,templates,seed,new,third,program,prepared,counts):
    source,base,basis,first,origins,second,origins2,thirdbank,origins3=prepared
    tops=[];assumptions=[]
    for side in ('low','high'):
        row=program['probes'][program['terminal'][side]]
        top,_=support.slice_trace(thirdbank,row['proof'],row['assumption'],counts)
        tops.append(top);assumptions.append(row['assumption'])
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
    for top in tops:
        for cid in {top['conflict']}|{i for _,i in top['units']}:collect(origins3[cid])
    positions={cl:i for i,cl in enumerate(source)}
    for i in guards:
        for cl in templates[i]['clauses']:counts['layer_support_clause_visits']+=1;ids.add(positions[tuple(cl)])
    ids=sorted(ids);small,names=native.normalize([source[i] for i in ids],counts);mapping={v:i+1 for i,v in enumerate(names)}
    required={abs(l) for top in tops for l,_ in top['units']}|{abs(l) for l in assumptions}
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
    compact=dict(program,probes=[dict(assumption=lit(a),proof=remap(thirdbank,t,checked[7])) for a,t in zip(assumptions,tops)],terminal=dict(low=0,high=1))
    candidate.prior.check_program(small,checked[7],compact,counts)
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
    lo=program['probes'][program['terminal']['low']];hi=program['probes'][program['terminal']['high']]
    low=trace(3,lo['proof'],{abs(lo['assumption']):False})
    high=trace(3,hi['proof'],{abs(hi['assumption']):True})
    _,names,key,publish=prepare_frame(solver,source,counts)
    publish(dict(kind='split',variable=names.index(abs(lo['assumption']))+1,low=low,high=high))
    counts['cursor_pair_splits']+=1;return key


def compile_program(solver,source,templates,seed,closure,new,next_closure,third,feedback_closure,result,counts,*,select_support=True):
    prepared=candidate.validate(source,templates,seed,closure,new,next_closure,third,feedback_closure,result,counts)
    program=result['program']
    if program['status']!='refuted':raise ValueError('Complete third feedback refutation required')
    source=prepared[0];root=native.token(source,counts);old=solver._read(root,source,purpose='cursor_root')
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


def compile_extension(solver,source,templates,prefix,seed,closure,new,next_closure,third,feedback_closure,result,counts):
    frames,tail=frozen.bind_prefix(source,templates,prefix,counts);ts=[h['template'] for h in tail['hints']]
    candidate.validate(tail['local'],ts,seed,closure,new,next_closure,third,feedback_closure,result,counts)
    program=result['program']
    if program['status']!='refuted':raise ValueError('Complete feedback extension required')
    root=native.token(tuple(map(tuple,source)),counts);old=solver._read(root,tuple(map(tuple,source)),purpose='feedback_extension')
    if old is not None:
        if old['answer']:raise ValueError('Contradictory feedback extension')
        counts['extension_root_hits']+=1;return root
    key=compile_program(solver,tail['local'],ts,seed,closure,new,next_closure,third,feedback_closure,result,counts)
    for frame in reversed(frames):
        state=frame['state'];forced=frame['forced'];profile=dict(clauses=state['graph'],paths={forced:frame['path']})
        excluded=frozen.frozen.compile_path(solver,state['local'],state['hints'],profile,forced,counts,path_limit=prefix['path_limit'])
        cnf=state['local'];keyroot=native.token(cnf,counts)
        solver._store(keyroot,dict(format=native.FORMAT,cnf=list(map(list,cnf)),answer=False,
            proof=dict(kind='split',variable=abs(forced),low=excluded if forced>0 else key,high=key if forced>0 else excluded)))
        key=keyroot;counts['extension_prefix_splits']+=1
    if key!=root:raise ValueError('Changed feedback extension root')
    return key
