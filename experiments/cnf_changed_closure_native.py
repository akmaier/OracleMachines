"""Compile opposite B2 probes through strictly decreasing B2/B1/B0 provenance.

Adapted from the frozen layered support planner and publication handoff compiler.
The only new terminal is an opposite-assumption split. Publication-only reuse is
retained; native checks and both existing cold readers remain unchanged.
"""
from experiments import cnf_changed_closure_probes as candidate
from experiments.cnf_prepared_publication import prepare_frame
from experiments.cnf_conditional_unit_support import transport,match,fixed_pairs,restrict,propagate
layered=candidate.layered
frozen=layered.frozen;feedback=layered.feedback;support=layered.support;native=layered.native
add_layer=layered.add_layer


def _plan(source,templates,seed,new,program,prepared,counts):
    source,base,basis,first,origins,second,origins2=prepared
    tops=[];assumptions=[]
    for side in ('low','high'):
        row=program['probes'][program['terminal'][side]]
        top,_=support.slice_trace(second,row['proof'],row['assumption'],counts)
        tops.append(top);assumptions.append(row['assumption'])
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
    for top in tops:
        for cid in {top['conflict']}|{i for _,i in top['units']}:collect(origins2[cid])
    positions={cl:i for i,cl in enumerate(source)}
    for i in guards:
        for cl in templates[i]['clauses']:counts['layer_support_clause_visits']+=1;ids.add(positions[tuple(cl)])
    ids=sorted(ids);small,names=native.normalize([source[i] for i in ids],counts);mapping={v:i+1 for i,v in enumerate(names)}
    required={abs(l) for top in tops for l,_ in top['units']}|{abs(l) for l in assumptions}
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
    compact=dict(program,probes=[dict(assumption=lit(a),proof=remap(second,t,checked[5])) for a,t in zip(assumptions,tops)],terminal=dict(low=0,high=1))
    candidate.prior.check_program(small,checked[5],compact,counts)
    return dict(source=small,templates=selected,seed=compactseed,new=compactnew,program=compact,indices=ids,prepared=checked)


def _compile(solver,templates,seed,new,program,prepared,counts,*,reuse_frames=False):
    source,base,basis,first,origins,second,origins2=prepared
    banks=(base,first,second);entries=(basis,origins,origins2)
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
        lower=0 if kind=='probe' else 1
        if lower>=stage:raise ValueError('Non-decreasing proof dependency')
        row=(seed if lower==0 else new)['probes'][i];lit=row['assumption']
        if context.get(abs(lit))!=(lit>0):raise ValueError('Failed probe premise missing')
        counts['layer_expanded_old' if lower==0 else 'layer_expanded_new']+=1
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
    low=trace(2,lo['proof'],{abs(lo['assumption']):False})
    high=trace(2,hi['proof'],{abs(hi['assumption']):True})
    _,names,key,publish=prepare_frame(solver,source,counts)
    publish(dict(kind='split',variable=names.index(abs(lo['assumption']))+1,low=low,high=high))
    counts['changed_closure_pair_splits']+=1;return key


def compile_program(solver,source,templates,seed,closure,new,next_closure,result,counts,*,select_support=True):
    prepared=candidate.validate(source,templates,seed,closure,new,next_closure,result,counts)
    if result['action']!='searched' or result['program']['status']!='refuted':
        raise ValueError('Complete changed-closure refutation required')
    program=result['program'];source=prepared[0];root=native.token(source,counts)
    old=solver._read(root,source,purpose='changed_closure_root')
    if old is not None:
        if old['answer']:raise ValueError('Contradictory changed-closure root')
        counts['changed_closure_root_hits']+=1;return root
    plan=_plan(source,templates,seed,new,program,prepared,counts) if select_support else None
    if plan is None:return _compile(solver,templates,seed,new,program,prepared,counts)
    child=_compile(solver,plan['templates'],plan['seed'],plan['new'],plan['program'],plan['prepared'],counts)
    if child!=root:
        solver._store(root,dict(format=native.FORMAT,cnf=list(map(list,source)),answer=False,
            proof=dict(kind='component',clauses=plan['indices'],child=child)))
        counts['layer_support_wrappers']+=1
    return root


def compile_extension(solver,source,templates,prefix,seed,closure,new,next_closure,result,counts):
    frames,tail=frozen.bind_prefix(source,templates,prefix,counts);ts=[h['template'] for h in tail['hints']]
    candidate.validate(tail['local'],ts,seed,closure,new,next_closure,result,counts)
    if result['action']!='searched' or result['program']['status']!='refuted':
        raise ValueError('Complete changed-closure extension required')
    root=native.token(tuple(map(tuple,source)),counts)
    old=solver._read(root,tuple(map(tuple,source)),purpose='changed_closure_extension')
    if old is not None:
        if old['answer']:raise ValueError('Contradictory changed-closure extension')
        counts['extension_root_hits']+=1;return root
    key=compile_program(solver,tail['local'],ts,seed,closure,new,next_closure,result,counts)
    for frame in reversed(frames):
        state=frame['state'];forced=frame['forced'];profile=dict(clauses=state['graph'],paths={forced:frame['path']})
        excluded=frozen.frozen.compile_path(solver,state['local'],state['hints'],profile,forced,counts,path_limit=prefix['path_limit'])
        cnf=state['local'];keyroot=native.token(cnf,counts)
        solver._store(keyroot,dict(format=native.FORMAT,cnf=list(map(list,cnf)),answer=False,
            proof=dict(kind='split',variable=abs(forced),low=excluded if forced>0 else key,high=key if forced>0 else excluded)))
        key=keyroot;counts['extension_prefix_splits']+=1
    if key!=root:raise ValueError('Changed extension root')
    return key
