"""Compile only the source support of a checked terminal unit-probe proof.

Causal slicing and coordinate transport change representation, not proof rules.
A checked native component wrapper lifts the refuted subset to the whole source.
"""
from experiments import cnf_wide_guard_probes as frozen
from experiments.cnf_conditional_unit_support import transport
native=frozen.native


def slice_trace(clauses,proof,assumption,counts):
    needed={abs(l) for l in clauses[proof['conflict']]};kept=[]
    for lit,cid in reversed(proof['units']):
        counts['support_trace_steps']+=1
        if abs(lit) not in needed:continue
        needed.remove(abs(lit));needed.update(abs(l) for l in clauses[cid] if l!=lit)
        kept.append([lit,cid])
    if not needed<=({abs(assumption)} if assumption is not None else set()):raise ValueError('Unclosed probe dependencies')
    counts['support_trace_kept']+=len(kept)
    return dict(units=list(reversed(kept)),conflict=proof['conflict']),bool(needed)


def prepare_support(source,templates,program,counts):
    source,state,clauses,basis=frozen.validate(source,templates,program,counts)
    if program['status']!='refuted':raise ValueError('Complete refutation required')
    end=program['terminal'];proofs=[];assumptions=[]
    if program['reason']=='units':
        proof,_=slice_trace(clauses,end['proof'],None,counts);proofs=[proof];assumptions=[None]
    else:
        for side in ('low','high'):
            row=program['probes'][end[side]];proof,dependent=slice_trace(clauses,row['proof'],row['assumption'],counts)
            if not dependent:
                proofs=[proof];assumptions=[None];counts['support_independent_branch']+=1;break
            proofs.append(proof);assumptions.append(row['assumption'])
    positions={cl:i for i,cl in enumerate(source)};ids=set();used=set()
    for proof in proofs:
        for cid in {proof['conflict']}|{cid for _,cid in proof['units']}:
            entry=basis[cid];counts['support_reason_clauses']+=1
            if entry['kind']=='source':ids.add(entry['index'])
            else:
                used.add(entry['index'])
                for cl in templates[entry['index']]['clauses']:
                    counts['support_template_clauses']+=1;ids.add(positions[tuple(cl)])
    ids=sorted(ids);small,names=native.normalize([source[i] for i in ids],counts);mapping={v:i+1 for i,v in enumerate(names)}
    required={abs(l) for p in proofs for l,_ in p['units']}|{abs(l) for l in assumptions if l is not None}
    required.update(v for i in used for v,_ in templates[i]['assumptions'])
    counts['support_source_clauses']+=len(source);counts['support_selected_clauses']+=len(ids)
    counts['support_source_literals']+=sum(map(len,source));counts['support_selected_literals']+=sum(len(source[i]) for i in ids)
    if not required<=mapping.keys():
        counts['support_coordinate_fallbacks']+=1;return None
    def lit(l):return mapping[abs(l)]*(1 if l>0 else -1)
    selected=[transport(templates[i],mapping,counts) for i in sorted(used)]
    _,_,bank,_=frozen.prepare(small,selected,program['mode'],counts);lookup={cl:i for i,cl in enumerate(bank)}
    def trace(p):
        def cid(i):return lookup[tuple(sorted(lit(l) for l in clauses[i]))]
        return dict(units=[[lit(l),cid(i)] for l,i in p['units']],conflict=cid(p['conflict']))
    if assumptions==[None]:compact=dict(program,reason='units',probes=[],terminal=dict(proof=trace(proofs[0])))
    else:compact=dict(program,probes=[dict(assumption=lit(l),proof=trace(p)) for l,p in zip(assumptions,proofs)],terminal=dict(low=0,high=1))
    frozen.validate(small,selected,compact,counts)
    return dict(source=source,indices=ids,small=small,templates=selected,program=compact)


def compile_program(solver,source,templates,program,counts):
    plan=prepare_support(source,templates,program,counts)
    if plan is None:return frozen.compile_program(solver,source,templates,program,counts)
    source=plan['source'];root=native.token(source,counts);old=solver._read(root,source,purpose='probe_support_root')
    if old is not None:
        if old['answer']:raise ValueError('Contradictory support root')
        counts['support_root_hits']+=1;return root
    child=frozen.compile_program(solver,plan['small'],plan['templates'],plan['program'],counts)
    if child!=root:
        solver._store(root,dict(format=native.FORMAT,cnf=list(map(list,source)),answer=False,
            proof=dict(kind='component',clauses=plan['indices'],child=child)))
        counts['support_wrappers']+=1
    return root


def compile_extension(solver,source,templates,prefix,program,counts):
    frames,tail=frozen.bind_prefix(source,templates,prefix,counts);ts=[h['template'] for h in tail['hints']]
    frozen.validate(tail['local'],ts,program,counts)
    if program['status']!='refuted':raise ValueError('Complete extension required')
    root=native.token(tuple(map(tuple,source)),counts);old=solver._read(root,tuple(map(tuple,source)),purpose='probe_support_extension')
    if old is not None:
        if old['answer']:raise ValueError('Contradictory extension root')
        counts['extension_root_hits']+=1;return root
    key=compile_program(solver,tail['local'],ts,program,counts)
    for frame in reversed(frames):
        state=frame['state'];forced=frame['forced'];profile=dict(clauses=state['graph'],paths={forced:frame['path']})
        excluded=frozen.frozen.compile_path(solver,state['local'],state['hints'],profile,forced,counts,path_limit=prefix['path_limit'])
        cnf=state['local'];keyroot=native.token(cnf,counts)
        solver._store(keyroot,dict(format=native.FORMAT,cnf=list(map(list,cnf)),answer=False,
            proof=dict(kind='split',variable=abs(forced),low=excluded if forced>0 else key,high=key if forced>0 else excluded)))
        key=keyroot;counts['extension_prefix_splits']+=1
    if key!=root:raise ValueError('Changed extension root')
    return key
