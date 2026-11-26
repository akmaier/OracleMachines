"""Compose checked B10 failures and reconstruct source-only refutations.

Every newly derived unit follows a checked failed assumption on bank 10. Native
proof reconstruction follows it back to that bank, never to the augmented bank.
"""
from experiments import cnf_b10_probe_cursor as probe
from experiments.cnf_prepared_publication import prepare_frame
from experiments.cnf_conditional_unit_support import match,fixed_pairs,restrict,propagate
native=probe.engine.native;frozen=probe.engine.frozen
DirectUnits=probe.prior.prior.joint.DirectUnits;checked_options=probe.prior.prior.joint.checked_options


def prepare(*inputs,closure,feedback_closure,joint_closure,counts):
    if len(inputs)!=22:raise ValueError('B10 inputs and full probe result required')
    prepared=probe.validate(*inputs[:-1],closure=closure,feedback_closure=feedback_closure,joint_closure=joint_closure,result=inputs[-1],counts=counts)
    bank={cl:entry for cl,entry in zip(prepared[21],prepared[22])}
    for i,row in enumerate(inputs[-1]['program']['probes']):
        cl=(-row['assumption'],);counts['b10_probe_feedback_exclusions']+=1
        if cl not in bank:bank[cl]=dict(kind='b10_probe',index=i);counts['b10_probe_feedback_added_units']+=1
    clauses=tuple(sorted(bank));return (*prepared,clauses,[bank[cl] for cl in clauses])


def discover(*inputs,closure,feedback_closure,joint_closure,counts,work_limit=262144,trace_limit=256):
    if any(type(v) is not int or v<1 for v in (work_limit,trace_limit)):raise ValueError('Invalid feedback bounds')
    prepared=prepare(*inputs,closure=closure,feedback_closure=feedback_closure,joint_closure=joint_closure,counts=counts);index=frozen.UnitIndex(prepared[23],counts);start=counts['probe_occurrence_visits']
    try:proof=index.probe(None,counts,lambda:work_limit-(counts['probe_occurrence_visits']-start),trace_limit)
    except frozen.ProbeLimit as error:return dict(status='unresolved',reason=str(error),trace_limit=trace_limit,proof=None)
    return dict(status='refuted' if proof is not None else 'unresolved',reason='units' if proof is not None else 'open',trace_limit=trace_limit,proof=proof)


def validate(*inputs,closure,feedback_closure,joint_closure,program,counts):
    if type(program) is not dict or set(program)!={'status','reason','trace_limit','proof'} or type(program['trace_limit']) is not int or program['trace_limit']<1:raise ValueError('Invalid feedback program')
    prepared=prepare(*inputs,closure=closure,feedback_closure=feedback_closure,joint_closure=joint_closure,counts=counts)
    if program['status']=='refuted' and program['reason']=='units':frozen.check_trace(prepared[0],prepared[23],None,program['proof'],counts,program['trace_limit'])
    elif not (program['status']=='unresolved' and program['reason'] in ('open','work_limit','trace_limit') and program['proof'] is None):raise ValueError('Invalid feedback outcome')
    return prepared


def _compile(solver,inputs,program,prepared,counts,*,shortcut='all',unit_work_limit=262144,unit_trace_limit=256):
    source=prepared[0];templates=inputs[1];banks=prepared[1::2];entries=prepared[2::2]
    books={'probe':(0,inputs[2]),'new_probe':(1,inputs[4]),'third_probe':(2,inputs[6]['program']),
           'cursor_probe':(3,inputs[8]['program']),'b4_cursor_probe':(4,inputs[10]['program']),
           'b5_cursor_probe':(5,inputs[12]['program']),'b6_cursor_probe':(6,inputs[14]['program']),
           'b6_comparison_probe':(6,inputs[17]['program']),'b7_probe':(7,inputs[16]['program']),'joint_probe':(8,inputs[18]['program']),
           'b8_comparison_probe':(8,inputs[20]['program']),'b9_probe':(9,inputs[19]['program']),'b10_probe':(10,inputs[21]['program'])}
    direct=DirectUnits(counts,unit_work_limit,unit_trace_limit)
    def frame(context):return prepare_frame(solver,native.restrict_scan(source,context,counts),counts)
    def materialize(template,context):
        if not match(source,template,counts):raise ValueError('Template clauses are missing from target')
        assumptions=fixed_pairs(template['assumptions']);fixed=fixed_pairs(sorted([list(p) for p in context.items()]))
        if any(fixed.get(v)!=b for v,b in assumptions.items()):raise ValueError('Context does not extend template assumptions')
        local,names,key,publish=frame(context);old=solver._read(key,local,purpose='b10_probe_feedback_conditional')
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
        publish(proof);counts['b10_probe_feedback_conditional_publications']+=1;return key
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
        counts['b10_probe_feedback_expanded_'+kind]+=1
        return trace(lower,row['proof'],context)
    def trace(stage,proof,context):
        def walk(i,context):
            prepared_frame=frame(context);cnf,names,key,publish=prepared_frame
            old=solver._read(key,cnf,purpose='b10_probe_feedback_existing')
            if old is not None:
                if old['answer']:raise ValueError('Contradictory joint cache')
                counts['b10_probe_feedback_native_hits']+=1;return key
            if () in cnf:publish(dict(kind='empty'));return key
            if shortcut!='off' and (shortcut=='all' or i==0) and direct.close(prepared_frame):return key
            if i==len(proof['units']):return leaf(stage,proof['conflict'],context)
            lit,cid=proof['units'][i];v=abs(lit);bit=lit>0
            if v in context:
                counts['b10_probe_feedback_fixed_trace_steps']+=1
                return walk(i+1,context) if context[v]==bit else leaf(stage,cid,context)
            excluded=leaf(stage,cid,{**context,v:not bit})
            if v not in names:
                if excluded!=key:raise ValueError('Changed absent coordinate')
                counts['b10_probe_feedback_absent_lifts']+=1;return key
            live=walk(i+1,{**context,v:bit})
            publish(dict(kind='split',variable=names.index(v)+1,low=excluded if bit else live,high=live if bit else excluded))
            counts['b10_probe_feedback_native_splits']+=1;return key
        return walk(0,context)
    return trace(11,program['proof'],{})


def compile_program(solver,*inputs,program,closure,feedback_closure,joint_closure,counts,shortcut='all',unit_work_limit=262144,unit_trace_limit=256):
    options=checked_options(shortcut,unit_work_limit,unit_trace_limit)
    prepared=validate(*inputs,closure=closure,feedback_closure=feedback_closure,joint_closure=joint_closure,program=program,counts=counts)
    if program['status']!='refuted':raise ValueError('Complete joint refutation required')
    source=prepared[0];root=native.token(source,counts);old=solver._read(root,source,purpose='b10_probe_feedback_root')
    if old is not None:
        if old['answer']:raise ValueError('Contradictory joint root')
        counts['b10_probe_feedback_root_hits']+=1;return root
    return _compile(solver,inputs,program,prepared,counts,**options)


def compile_extension(solver,source,templates,prefix,*inputs,program,closure,feedback_closure,joint_closure,counts,shortcut='all',unit_work_limit=262144,unit_trace_limit=256):
    options=checked_options(shortcut,unit_work_limit,unit_trace_limit)
    frames,tail=frozen.bind_prefix(source,templates,prefix,counts);ts=[h['template'] for h in tail['hints']]
    validate(tail['local'],ts,*inputs,closure=closure,feedback_closure=feedback_closure,joint_closure=joint_closure,program=program,counts=counts)
    if program['status']!='refuted':raise ValueError('Complete joint extension required')
    root=native.token(tuple(map(tuple,source)),counts);old=solver._read(root,tuple(map(tuple,source)),purpose='b10_probe_feedback_extension')
    if old is not None:
        if old['answer']:raise ValueError('Contradictory joint extension')
        counts['b10_probe_feedback_extension_hits']+=1;return root
    key=compile_program(solver,tail['local'],ts,*inputs,closure=closure,feedback_closure=feedback_closure,joint_closure=joint_closure,program=program,counts=counts,**options)
    for frame in reversed(frames):
        state=frame['state'];forced=frame['forced'];profile=dict(clauses=state['graph'],paths={forced:frame['path']})
        excluded=frozen.frozen.compile_path(solver,state['local'],state['hints'],profile,forced,counts,path_limit=prefix['path_limit'])
        cnf=state['local'];keyroot=native.token(cnf,counts)
        solver._store(keyroot,dict(format=native.FORMAT,cnf=list(map(list,cnf)),answer=False,
            proof=dict(kind='split',variable=abs(forced),low=excluded if forced>0 else key,high=key if forced>0 else excluded)))
        key=keyroot;counts['b10_probe_feedback_prefix_splits']+=1
    if key!=root:raise ValueError('Changed joint extension root')
    return key
