"""Bounded probes on a checked feedback closure, with exact residual reuse."""
from collections import deque
from experiments import cnf_probe_feedback as feedback
from experiments.cnf_conditional_unit_support import fixed_pairs,transport,materialize
frozen=feedback.frozen;support=feedback.support;native=feedback.native


def check_closure(clauses,closure,counts):
    if type(closure) is not dict or set(closure)!={'units','assignment'} or type(closure['units']) is not list:raise ValueError('Invalid closure fields')
    fixed={}
    for row in closure['units']:
        if type(row) is not list or len(row)!=2:raise ValueError('Invalid closure step')
        lit,cid=row
        if type(lit) is not int or not lit or abs(lit) in fixed or type(cid) is not int or not 0<=cid<len(clauses):raise ValueError('Invalid closure reason')
        cl=clauses[cid];counts['closure_checked_literals']+=len(cl)
        if lit not in cl or any(abs(l) not in fixed or fixed[abs(l)]==(l>0) for l in cl if l!=lit):raise ValueError('Closure reason is not unit')
        fixed[abs(lit)]=lit>0
    if fixed_pairs(closure['assignment'])!=fixed:raise ValueError('Wrong closure assignment')
    for cl in clauses:
        counts['closure_fixed_point_literals']+=len(cl)
        if not any(fixed.get(abs(l))==(l>0) for l in cl) and sum(abs(l) not in fixed for l in cl)<2:raise ValueError('Not an open unit fixed point')
    return fixed


def residual_bank(clauses,fixed,counts):
    origins={}
    for cid,cl in enumerate(clauses):
        left=[];satisfied=False
        for lit in cl:
            counts['closure_condition_literals']+=1
            if abs(lit) not in fixed:left.append(lit)
            elif fixed[abs(lit)]==(lit>0):satisfied=True
        if not satisfied:origins.setdefault(tuple(left),cid)
    reduced=tuple(sorted(origins));counts['closure_residual_clauses']+=len(reduced);counts['closure_residual_literals']+=sum(map(len,reduced))
    return reduced,[origins[cl] for cl in reduced]


def discover(source,templates,seed,closure,counts,*,mode='conditioned',probe_limit=64,work_limit=262144,trace_limit=256):
    if mode not in ('restart','conditioned') or any(type(v) is not int or v<1 for v in (probe_limit,work_limit,trace_limit)):raise ValueError('Invalid closure probe bounds')
    prepared=feedback.prepare(source,templates,seed,counts);source,base,basis,clauses,origins=prepared
    fixed=check_closure(clauses,closure,counts);reduced,ids=residual_bank(clauses,fixed,counts)
    active={abs(l) for cl in reduced for l in cl};queue=deque(l for l in frozen.roots(source) if abs(l) in active)
    prefix=closure['units'] if mode=='conditioned' else [];bank=reduced if mode=='conditioned' else clauses
    index=frozen.UnitIndex(bank,counts);start=counts['probe_occurrence_visits'];records=[];found={};tested=set();promoted=None
    counts['closure_removed_variables']+=len(fixed);counts['closure_active_variables']+=len(active)
    def result(status,reason,terminal=None):return dict(status=status,reason=reason,mode=mode,probes=records,terminal=terminal,trace_limit=trace_limit)
    try:
        if len(prefix)>trace_limit:return result('unresolved','trace_limit')
        while queue or promoted is not None:
            priority=promoted is not None;root=promoted if priority else queue.popleft();promoted=None
            if root in tested:counts['closure_duplicate_skips']+=1;continue
            if len(tested)>=probe_limit:return result('unresolved','probe_limit')
            tested.add(root);counts['probe_roots']+=1;counts['closure_promoted_probes' if priority else 'closure_base_probes']+=1
            proof=index.probe(root,counts,lambda:work_limit-(counts['probe_occurrence_visits']-start),trace_limit-len(prefix))
            if proof is None:continue
            if mode=='conditioned':
                proof=dict(units=[list(p) for p in prefix]+[[l,ids[cid]] for l,cid in proof['units']],conflict=ids[proof['conflict']])
                counts['closure_lifted_steps']+=len(prefix)
            records.append(dict(assumption=root,proof=proof));found[root]=len(records)-1;counts['probe_exclusions']+=1
            if -root in found:return result('refuted','opposite_probes',dict(low=found[-abs(root)],high=found[abs(root)]))
            if -root not in tested:promoted=-root
    except frozen.ProbeLimit as error:return result('unresolved',str(error))
    return result('unresolved','complete')


def check_program(source,clauses,program,counts):
    if type(program) is not dict or set(program)!={'status','reason','mode','probes','terminal','trace_limit'}:raise ValueError('Invalid closure probe program')
    if program['mode'] not in ('restart','conditioned') or type(program['trace_limit']) is not int or program['trace_limit']<1 or type(program['probes']) is not list:raise ValueError('Invalid closure program bounds')
    seen=set()
    for row in program['probes']:
        if type(row) is not dict or set(row)!={'assumption','proof'} or type(row['assumption']) is not int or row['assumption'] in seen:raise ValueError('Invalid closure probe')
        frozen.check_trace(source,clauses,row['assumption'],row['proof'],counts,program['trace_limit']);seen.add(row['assumption'])
    if program['status']=='refuted':
        end=program['terminal']
        if program['reason']!='opposite_probes' or type(end) is not dict or set(end)!={'low','high'} or any(type(end[k]) is not int or not 0<=end[k]<len(program['probes']) for k in end):raise ValueError('Invalid closure terminal')
        low=program['probes'][end['low']]['assumption'];high=program['probes'][end['high']]['assumption']
        if not low<0 or high!=-low:raise ValueError('Closure probes are not opposite')
    elif not (program['status']=='unresolved' and program['terminal'] is None and program['reason'] in ('complete','probe_limit','work_limit','trace_limit')):raise ValueError('Invalid closure outcome')


def validate(source,templates,seed,closure,program,counts):
    prepared=feedback.prepare(source,templates,seed,counts);fixed=check_closure(prepared[3],closure,counts)
    check_program(prepared[0],prepared[3],program,counts)
    if any(abs(row['assumption']) in fixed for row in program['probes']):raise ValueError('Probe repeats a closure assignment')
    return prepared


def _plan(source,templates,seed,program,prepared,counts):
    source,base,basis,clauses,origins=prepared
    tops=[];assumptions=[]
    for side in ('low','high'):
        row=program['probes'][program['terminal'][side]]
        top,_=support.slice_trace(clauses,row['proof'],row['assumption'],counts);tops.append(top);assumptions.append(row['assumption'])
    used={};ids=set();guards=set()
    def collect(cid):
        entry=basis[cid]
        if entry['kind']=='source':ids.add(entry['index'])
        else:guards.add(entry['index'])
    for cid in set().union(*({top['conflict']}|{i for _,i in top['units']} for top in tops)):
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
    required={abs(l) for top in tops for l,_ in top['units']}|{abs(r['assumption']) for r in used.values()}|{abs(l) for l in assumptions}
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
    _,_,_,newbank,_=feedback.prepare(small,selected,compactseed,counts)
    compact=dict(program,probes=[dict(assumption=lit(l),proof=remap(clauses,top,{cl:i for i,cl in enumerate(newbank)})) for l,top in zip(assumptions,tops)],terminal=dict(low=0,high=1))
    checked=feedback.prepare(small,selected,compactseed,counts);check_program(small,checked[3],compact,counts)
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
    root=native.token(source,counts);old=solver._read(root,source,purpose='closure_pair_root')
    if old is not None:
        if old['answer']:raise ValueError('Contradictory closure pair')
        return root
    lo=program['probes'][program['terminal']['low']];hi=program['probes'][program['terminal']['high']]
    low=trace(lo['proof'],feedback_leaf,{abs(lo['assumption']):False})
    high=trace(hi['proof'],feedback_leaf,{abs(hi['assumption']):True})
    solver._store(root,dict(format=native.FORMAT,cnf=list(map(list,source)),answer=False,
        proof=dict(kind='split',variable=abs(lo['assumption']),low=low,high=high)))
    counts['closure_pair_splits']+=1;return root


def compile_program(solver,source,templates,seed,closure,program,counts,*,select_support=True):
    prepared=validate(source,templates,seed,closure,program,counts)
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


def compile_extension(solver,source,templates,prefix,seed,closure,program,counts):
    frames,tail=frozen.bind_prefix(source,templates,prefix,counts);ts=[h['template'] for h in tail['hints']]
    validate(tail['local'],ts,seed,closure,program,counts)
    if program['status']!='refuted':raise ValueError('Complete feedback extension required')
    root=native.token(tuple(map(tuple,source)),counts);old=solver._read(root,tuple(map(tuple,source)),purpose='feedback_extension')
    if old is not None:
        if old['answer']:raise ValueError('Contradictory feedback extension')
        counts['extension_root_hits']+=1;return root
    key=compile_program(solver,tail['local'],ts,seed,closure,program,counts)
    for frame in reversed(frames):
        state=frame['state'];forced=frame['forced'];profile=dict(clauses=state['graph'],paths={forced:frame['path']})
        excluded=frozen.frozen.compile_path(solver,state['local'],state['hints'],profile,forced,counts,path_limit=prefix['path_limit'])
        cnf=state['local'];keyroot=native.token(cnf,counts)
        solver._store(keyroot,dict(format=native.FORMAT,cnf=list(map(list,cnf)),answer=False,
            proof=dict(kind='split',variable=abs(forced),low=excluded if forced>0 else key,high=key if forced>0 else excluded)))
        key=keyroot;counts['extension_prefix_splits']+=1
    if key!=root:raise ValueError('Changed feedback extension root')
    return key
