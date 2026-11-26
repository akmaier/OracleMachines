"""Compose independently checked B6/B7 failures without rebinding their proofs.

Native reconstruction follows each exclusion back to its original lower bank.
Open scheduling history supplies no axiom. All portable checks precede cache hits.
"""
from experiments import cnf_b7_probe_cursor as cursor
from experiments.cnf_prepared_publication import prepare_frame
from experiments.cnf_conditional_unit_support import match,fixed_pairs,restrict,propagate
native=cursor.native;frozen=cursor.frozen
DirectUnits=cursor.feedback.DirectUnits;checked_options=cursor.feedback.checked_options
MODES=('base','b6_only','b7_only','joint')


def prepare(*inputs,counts,mode='joint'):
    if len(inputs)!=18 or mode not in MODES:raise ValueError('Invalid joint feedback inputs or mode')
    prepared=cursor.validate(*inputs[:17],counts)
    lower=cursor.feedback.cursor.validate(*inputs[:14],inputs[17],counts)
    if inputs[16]['program']['status']!='unresolved' or inputs[17]['program']['status']!='unresolved':raise ValueError('Unresolved source histories required')
    counts['joint_bank_compare_literals']+=sum(map(len,prepared[13]))+sum(map(len,lower[13]))
    if lower!=prepared[:15]:raise ValueError('B6 comparison bank changed')
    bank={cl:entry for cl,entry in zip(prepared[15],prepared[16])}
    sources=[]
    if mode in ('b6_only','joint'):sources.append(('b6_comparison_probe',inputs[17]['program']))
    if mode in ('b7_only','joint'):sources.append(('b7_probe',inputs[16]['program']))
    for kind,program in sources:
        for i,row in enumerate(program['probes']):
            cl=(-row['assumption'],);counts['joint_exclusions']+=1
            if cl not in bank:bank[cl]=dict(kind=kind,index=i);counts['joint_added_units']+=1
    clauses=tuple(sorted(bank));return (*prepared,clauses,[bank[cl] for cl in clauses])


def discover(*inputs,counts,mode='joint',work_limit=262144,trace_limit=256):
    if any(type(v) is not int or v<1 for v in (work_limit,trace_limit)):raise ValueError('Invalid joint feedback bounds')
    prepared=prepare(*inputs,counts=counts,mode=mode);index=frozen.UnitIndex(prepared[17],counts);start=counts['probe_occurrence_visits']
    try:proof=index.probe(None,counts,lambda:work_limit-(counts['probe_occurrence_visits']-start),trace_limit)
    except frozen.ProbeLimit as error:return dict(status='unresolved',reason=str(error),trace_limit=trace_limit,proof=None,mode=mode)
    return dict(status='refuted' if proof is not None else 'unresolved',reason='units' if proof is not None else 'open',trace_limit=trace_limit,proof=proof,mode=mode)


def validate(*inputs,program,counts):
    if (type(program) is not dict or set(program)!={'status','reason','trace_limit','proof','mode'} or program['mode'] not in MODES
        or type(program['trace_limit']) is not int or program['trace_limit']<1):raise ValueError('Invalid joint feedback program')
    prepared=prepare(*inputs,counts=counts,mode=program['mode'])
    if program['status']=='refuted' and program['reason']=='units':frozen.check_trace(prepared[0],prepared[17],None,program['proof'],counts,program['trace_limit'])
    elif not (program['status']=='unresolved' and program['reason'] in ('open','work_limit','trace_limit') and program['proof'] is None):raise ValueError('Invalid joint feedback outcome')
    return prepared


def _compile(solver,inputs,program,prepared,counts,*,shortcut='all',unit_work_limit=262144,unit_trace_limit=256):
    source=prepared[0];templates=inputs[1];banks=prepared[1::2];entries=prepared[2::2]
    books={'probe':(0,inputs[2]),'new_probe':(1,inputs[4]),'third_probe':(2,inputs[6]['program']),
           'cursor_probe':(3,inputs[8]['program']),'b4_cursor_probe':(4,inputs[10]['program']),
           'b5_cursor_probe':(5,inputs[12]['program']),'b6_cursor_probe':(6,inputs[14]['program']),
           'b6_comparison_probe':(6,inputs[17]['program']),'b7_probe':(7,inputs[16]['program'])}
    direct=DirectUnits(counts,unit_work_limit,unit_trace_limit)
    def frame(context):return prepare_frame(solver,native.restrict_scan(source,context,counts),counts)
    def materialize(template,context):
        if not match(source,template,counts):raise ValueError('Template clauses are missing from target')
        assumptions=fixed_pairs(template['assumptions']);fixed=fixed_pairs(sorted([list(p) for p in context.items()]))
        if any(fixed.get(v)!=b for v,b in assumptions.items()):raise ValueError('Context does not extend template assumptions')
        local,names,key,publish=frame(context);old=solver._read(key,local,purpose='joint_conditional')
        if old is not None:
            if old['answer'] is not False:raise ValueError('Conflicting conditional answer')
            return key
        if () in local:proof=dict(kind='empty')
        else:
            rename={v:i+1 for i,v in enumerate(names)};positions={cl:i for i,cl in enumerate(local)};small=restrict(template['clauses'],fixed,counts)
            ids=sorted({positions[tuple(sorted((1 if l>0 else -1)*rename[abs(l)] for l in cl))] for cl in small})
            _,trace,conflict=propagate(tuple(local[i] for i in ids),counts)
            if conflict is None:raise ValueError('Conditioned source support did not refute')
            proof=dict(kind='units',trace=[[l,ids[cid]] for l,cid in trace],conflict=ids[conflict])
        publish(proof);counts['joint_conditional_publications']+=1;return key
    def leaf(stage,cid,context):
        entry=entries[stage][cid];kind=entry['kind'];i=entry['index']
        if kind in ('source','guard'):
            cl=banks[stage][cid]
            template=dict(clauses=[list(cl)],assumptions=sorted([[abs(l),l<0] for l in cl]),trace=[],conflict=0) if kind=='source' else templates[i]
            return materialize(template,context)
        if kind not in books:raise ValueError('Unknown joint proof origin')
        lower,book=books[kind]
        if lower>=stage:raise ValueError('Non-decreasing proof dependency')
        row=book['probes'][i];lit=row['assumption']
        if context.get(abs(lit))!=(lit>0):raise ValueError('Failed probe premise missing')
        counts['joint_expanded_'+kind]+=1
        return trace(lower,row['proof'],context)
    def trace(stage,proof,context):
        def walk(i,context):
            prepared_frame=frame(context);cnf,names,key,publish=prepared_frame
            old=solver._read(key,cnf,purpose='joint_existing')
            if old is not None:
                if old['answer']:raise ValueError('Contradictory joint cache')
                counts['joint_native_hits']+=1;return key
            if () in cnf:publish(dict(kind='empty'));return key
            if shortcut!='off' and (shortcut=='all' or i==0) and direct.close(prepared_frame):return key
            if i==len(proof['units']):return leaf(stage,proof['conflict'],context)
            lit,cid=proof['units'][i];v=abs(lit);bit=lit>0
            if v in context:
                counts['joint_fixed_trace_steps']+=1
                return walk(i+1,context) if context[v]==bit else leaf(stage,cid,context)
            excluded=leaf(stage,cid,{**context,v:not bit})
            if v not in names:
                if excluded!=key:raise ValueError('Changed absent coordinate')
                counts['joint_absent_lifts']+=1;return key
            live=walk(i+1,{**context,v:bit})
            publish(dict(kind='split',variable=names.index(v)+1,low=excluded if bit else live,high=live if bit else excluded))
            counts['joint_native_splits']+=1;return key
        return walk(0,context)
    return trace(8,program['proof'],{})


def compile_program(solver,*inputs,program,counts,shortcut='all',unit_work_limit=262144,unit_trace_limit=256):
    options=checked_options(shortcut,unit_work_limit,unit_trace_limit)
    prepared=validate(*inputs,program=program,counts=counts)
    if program['status']!='refuted':raise ValueError('Complete joint refutation required')
    source=prepared[0];root=native.token(source,counts);old=solver._read(root,source,purpose='joint_root')
    if old is not None:
        if old['answer']:raise ValueError('Contradictory joint root')
        counts['joint_root_hits']+=1;return root
    return _compile(solver,inputs,program,prepared,counts,**options)


def compile_extension(solver,source,templates,prefix,*inputs,program,counts,shortcut='all',unit_work_limit=262144,unit_trace_limit=256):
    options=checked_options(shortcut,unit_work_limit,unit_trace_limit)
    frames,tail=frozen.bind_prefix(source,templates,prefix,counts);ts=[h['template'] for h in tail['hints']]
    validate(tail['local'],ts,*inputs,program=program,counts=counts)
    if program['status']!='refuted':raise ValueError('Complete joint extension required')
    root=native.token(tuple(map(tuple,source)),counts);old=solver._read(root,tuple(map(tuple,source)),purpose='joint_extension')
    if old is not None:
        if old['answer']:raise ValueError('Contradictory joint extension')
        counts['joint_extension_hits']+=1;return root
    key=compile_program(solver,tail['local'],ts,*inputs,program=program,counts=counts,**options)
    for frame in reversed(frames):
        state=frame['state'];forced=frame['forced'];profile=dict(clauses=state['graph'],paths={forced:frame['path']})
        excluded=frozen.frozen.compile_path(solver,state['local'],state['hints'],profile,forced,counts,path_limit=prefix['path_limit'])
        cnf=state['local'];keyroot=native.token(cnf,counts)
        solver._store(keyroot,dict(format=native.FORMAT,cnf=list(map(list,cnf)),answer=False,
            proof=dict(kind='split',variable=abs(forced),low=excluded if forced>0 else key,high=key if forced>0 else excluded)))
        key=keyroot;counts['joint_prefix_splits']+=1
    if key!=root:raise ValueError('Changed joint extension root')
    return key
