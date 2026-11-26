"""Compile joint cross-pivot implications under one global shortcut allowance."""
from experiments import cnf_cross_pivot_feedback as joint
from experiments.cnf_conditioned_saturation_native import (
    native,frozen,feedback,DirectUnits,checked_options,slice_trace,prepare_frame,
    match,fixed_pairs,restrict,propagate)


def prepare(*inputs,summary,counts,**closures):
    base=feedback.prepare(*inputs,counts=counts,**closures)
    joint.validate(base[29],summary,counts,order_source=base[0])
    if summary['status']!='refuted':raise ValueError('Joint refutation required')
    entries=dict(zip(base[29],base[30]));branches=[]
    for index,lemma in enumerate(summary['lemmas']):
        lit=lemma['assumption'];saturation=lemma['saturation']
        entries.setdefault((-lit,),dict(kind='cross_pivot',index=index))
        local=dict(zip(base[29],base[30]));local.setdefault((lit,),dict(kind='condition',index=index))
        clauses=tuple(sorted(local));branch=(*base[:-2],clauses,[local[cl] for cl in clauses])
        for i,row in enumerate(saturation['rounds']):
            local=dict(zip(branch[-2],branch[-1]))
            for j,probe in enumerate(row['search']['program']['probes']):local.setdefault((-probe['assumption'],),dict(kind=f'saturation_probe_{i}',index=j))
            clauses=tuple(sorted(local));branch=(*branch,clauses,[local[cl] for cl in clauses])
        if saturation['reason']=='units':proof=saturation['proof']
        else:
            _,units,conflict=native.propagate(branch[-2],counts)
            if conflict is None:raise ValueError('Failed branch has no unit refutation')
            proof=dict(units=units,conflict=conflict)
        frozen.check_trace(base[0],branch[-2],None,proof,counts,max(saturation['trace_limit'],len(proof['units'])))
        branches.append((branch,proof,saturation))
    clauses=tuple(sorted(entries));prepared=(*base,clauses,[entries[cl] for cl in clauses])
    return prepared,branches


def _compile(solver,inputs,program,prepared,counts,*,branches,shortcut='all',unit_work_limit=262144,unit_trace_limit=256):
    source=prepared[0];templates=inputs[1]
    books={'probe':(0,inputs[2]),'new_probe':(1,inputs[4]),'third_probe':(2,inputs[6]['program']),
           'cursor_probe':(3,inputs[8]['program']),'b4_cursor_probe':(4,inputs[10]['program']),
           'b5_cursor_probe':(5,inputs[12]['program']),'b6_cursor_probe':(6,inputs[14]['program']),
           'b6_comparison_probe':(6,inputs[17]['program']),'b7_probe':(7,inputs[16]['program']),'joint_probe':(8,inputs[18]['program']),
           'b8_comparison_probe':(8,inputs[20]['program']),'b9_probe':(9,inputs[19]['program']),'b10_probe':(10,inputs[21]['program']),
           'b10_comparison_probe':(10,inputs[23]['program']),'b11_probe':(11,inputs[22]['program']),
           'b12_source_probe':(12,inputs[24]['program']),'b12_unseen_probe':(12,inputs[25]['program']),
           'b11_continuation_probe':(11,inputs[26]['program']),'b13_probe':(13,inputs[27]['program'])}
    environments=[(prepared[1::2],prepared[2::2],books)]
    for branch,proof,saturation in branches:
        local_books={**books,**{f'saturation_probe_{i}':(14+i,row['search']['program']) for i,row in enumerate(saturation['rounds'])}}
        environments.append((branch[1::2],branch[2::2],local_books))
    direct=DirectUnits(counts,unit_work_limit,unit_trace_limit);sliced={}
    def frame(context):return prepare_frame(solver,native.restrict_scan(source,context,counts),counts)
    def materialize(template,context):
        if not match(source,template,counts):raise ValueError('Template clauses are missing from target')
        assumptions=fixed_pairs(template['assumptions']);fixed=fixed_pairs(sorted([list(p) for p in context.items()]))
        if any(fixed.get(v)!=b for v,b in assumptions.items()):raise ValueError('Context does not extend template assumptions')
        local,names,key,publish=frame(context);old=solver._read(key,local,purpose='saturation_native_conditional')
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
        publish(proof);counts['saturation_native_conditional_publications']+=1;return key
    def leaf(env,stage,cid,context):
        banks,entries,books=environments[env]
        entry=entries[stage][cid];kind=entry['kind'];i=entry['index']
        if kind in ('source','guard'):
            cl=banks[stage][cid]
            template=dict(clauses=[list(cl)],assumptions=sorted([[abs(l),l<0] for l in cl]),trace=[],conflict=0) if kind=='source' else templates[i]
            return materialize(template,context)
        if kind=='cross_pivot':
            branch,proof,saturation=branches[i];lit=program['lemmas'][i]['assumption']
            if context.get(abs(lit))!=(lit>0):raise ValueError('Cross-pivot premise missing')
            counts['cross_native_branch_expansions']+=1
            return trace(i+1,14+len(saturation['rounds']),proof,context)
        if kind=='condition':raise ValueError('A branch condition cannot justify its own excluded context')
        if kind not in books:raise ValueError('Unknown joint proof origin')
        lower,book=books[kind]
        if lower>=stage:raise ValueError('Non-decreasing proof dependency')
        row=book['probes'][i];lit=row['assumption']
        if context.get(abs(lit))!=(lit>0):raise ValueError('Failed probe premise missing')
        counts['saturation_native_expanded_'+kind]+=1
        return trace(env,lower,row['proof'],context,lit)
    def trace(env,stage,proof,context,assumption=None):
        banks,_,_=environments[env]
        key=(env,stage,assumption,tuple(map(tuple,proof['units'])),proof['conflict'])
        counts['slice_key_steps']+=len(proof['units'])
        if key not in sliced:
            sliced[key]=slice_trace(banks[stage],proof,assumption,counts)[0]
            counts['slice_unique_traces']+=1
        else:counts['slice_memo_hits']+=1
        proof=sliced[key]
        def walk(i,context):
            prepared_frame=frame(context);cnf,names,key,publish=prepared_frame
            old=solver._read(key,cnf,purpose='saturation_native_existing')
            if old is not None:
                if old['answer']:raise ValueError('Contradictory joint cache')
                counts['saturation_native_native_hits']+=1;return key
            if () in cnf:publish(dict(kind='empty'));return key
            if shortcut!='off' and (shortcut=='all' or i==0) and direct.close(prepared_frame):return key
            if i==len(proof['units']):return leaf(env,stage,proof['conflict'],context)
            lit,cid=proof['units'][i];v=abs(lit);bit=lit>0
            if v in context:
                counts['saturation_native_fixed_trace_steps']+=1
                return walk(i+1,context) if context[v]==bit else leaf(env,stage,cid,context)
            excluded=leaf(env,stage,cid,{**context,v:not bit})
            if v not in names:
                if excluded!=key:raise ValueError('Changed absent coordinate')
                counts['saturation_native_absent_lifts']+=1;return key
            live=walk(i+1,{**context,v:bit})
            publish(dict(kind='split',variable=names.index(v)+1,low=excluded if bit else live,high=live if bit else excluded))
            counts['saturation_native_native_splits']+=1;return key
        return walk(0,context)
    return trace(0,15,program['proof'],{})


def compile_program(solver,*inputs,summary,counts,shortcut='all',unit_work_limit=262144,unit_trace_limit=256,**closures):
    options=checked_options(shortcut,unit_work_limit,unit_trace_limit)
    prepared,branches=prepare(*inputs,summary=summary,counts=counts,**closures)
    source=prepared[0];root=native.token(source,counts);old=solver._read(root,source,purpose='cross_pivot_root')
    if old is not None:
        if old['answer']:raise ValueError('Contradictory cross-pivot root')
        counts['cross_native_root_hits']+=1;return root
    key=_compile(solver,inputs,summary,prepared,counts,branches=branches,**options)
    if key!=root:raise ValueError('Changed cross-pivot root')
    return key


def compile_extension(solver,source,templates,prefix,*inputs,summary,counts,shortcut='all',unit_work_limit=262144,unit_trace_limit=256,**closures):
    options=checked_options(shortcut,unit_work_limit,unit_trace_limit)
    frames,tail=frozen.bind_prefix(source,templates,prefix,counts);ts=[h['template'] for h in tail['hints']]
    prepare(tail['local'],ts,*inputs,summary=summary,counts=counts,**closures)
    root=native.token(tuple(map(tuple,source)),counts);old=solver._read(root,tuple(map(tuple,source)),purpose='cross_pivot_extension')
    if old is not None:
        if old['answer']:raise ValueError('Contradictory cross-pivot extension')
        counts['cross_native_extension_hits']+=1;return root
    key=compile_program(solver,tail['local'],ts,*inputs,summary=summary,counts=counts,**options,**closures)
    for frame in reversed(frames):
        state=frame['state'];forced=frame['forced'];profile=dict(clauses=state['graph'],paths={forced:frame['path']})
        excluded=frozen.frozen.compile_path(solver,state['local'],state['hints'],profile,forced,counts,path_limit=prefix['path_limit'])
        cnf=state['local'];keyroot=native.token(cnf,counts)
        solver._store(keyroot,dict(format=native.FORMAT,cnf=list(map(list,cnf)),answer=False,
            proof=dict(kind='split',variable=abs(forced),low=excluded if forced>0 else key,high=key if forced>0 else excluded)))
        key=keyroot;counts['cross_native_prefix_splits']+=1
    if key!=root:raise ValueError('Changed cross-pivot extension root')
    return key
