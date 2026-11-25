"""Use compiler-owned residual preparation at publication and unchanged contexts.

A frame is produced only by ordinary normalization. Its publisher constructs its
own CNF/header and offers that immutable result to exactly one verifier call.
All proof rules and child checks still run. No content cache or persistent format
change. Requires the same exclusive synchronous solver use as the compiler.
"""
from unittest.mock import patch
from experiments import cnf_layered_feedback as prior
from experiments.cnf_conditional_unit_support import match,fixed_pairs,restrict,propagate
native=prior.native;frozen=prior.frozen
validate=prior.validate;_plan=prior._plan


def prepare_frame(solver,raw,counts):
    cnf,names,key=solver._canonical(raw);counts['prepared_frame_builds']+=1
    canonical_names=tuple(range(1,len(names)+1));triple=(cnf,canonical_names,key)
    def publish(proof):
        # The only accepted argument is a proof, never a caller-supplied CNF,
        # canonical triple or key. The header comes from this producer's result.
        node=dict(format=native.FORMAT,cnf=list(map(list,cnf)),answer=False,proof=proof)
        own_raw=node['cnf'];original=solver._canonical;pending=True
        def consume(raw):
            nonlocal pending
            if pending and raw is own_raw:
                pending=False;solver._canonical=original
                counts['prepared_header_reuses']+=1
                counts['prepared_header_literal_slots']+=sum(map(len,cnf))
                return triple
            return original(raw)
        with patch.object(solver,'_canonical',consume):solver._store(key,node)
        return key
    return cnf,names,key,publish


def _compile(solver,templates,seed,new,program,prepared,counts,*,reuse_frames=True):
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
    return trace(2,program['proof'],{})


def compile_program(solver,source,templates,seed,closure,new,program,counts,*,select_support=True,reuse_frames=True):
    prepared=validate(source,templates,seed,closure,new,program,counts)
    if program['status']!='refuted' or program['mode']!='feedback':raise ValueError('Complete layered feedback refutation required')
    source=prepared[0];root=native.token(source,counts);old=solver._read(root,source,purpose='layer_root')
    if old is not None:
        if old['answer']:raise ValueError('Contradictory layered root')
        counts['layer_root_hits']+=1;return root
    plan=_plan(source,templates,seed,new,program,prepared,counts) if select_support else None
    if plan is None:return _compile(solver,templates,seed,new,program,prepared,counts,reuse_frames=reuse_frames)
    child=_compile(solver,plan['templates'],plan['seed'],plan['new'],plan['program'],plan['prepared'],counts,reuse_frames=reuse_frames)
    if child!=root:
        solver._store(root,dict(format=native.FORMAT,cnf=list(map(list,source)),answer=False,
            proof=dict(kind='component',clauses=plan['indices'],child=child)))
        counts['layer_support_wrappers']+=1
    return root


def compile_extension(solver,source,templates,prefix,seed,closure,new,program,counts,*,reuse_frames=True):
    frames,tail=frozen.bind_prefix(source,templates,prefix,counts);ts=[h['template'] for h in tail['hints']]
    validate(tail['local'],ts,seed,closure,new,program,counts)
    if program['status']!='refuted' or program['mode']!='feedback':raise ValueError('Complete feedback extension required')
    root=native.token(tuple(map(tuple,source)),counts);old=solver._read(root,tuple(map(tuple,source)),purpose='feedback_extension')
    if old is not None:
        if old['answer']:raise ValueError('Contradictory feedback extension')
        counts['extension_root_hits']+=1;return root
    key=compile_program(solver,tail['local'],ts,seed,closure,new,program,counts,reuse_frames=reuse_frames)
    for frame in reversed(frames):
        state=frame['state'];forced=frame['forced'];profile=dict(clauses=state['graph'],paths={forced:frame['path']})
        excluded=frozen.frozen.compile_path(solver,state['local'],state['hints'],profile,forced,counts,path_limit=prefix['path_limit'])
        cnf=state['local'];keyroot=native.token(cnf,counts)
        solver._store(keyroot,dict(format=native.FORMAT,cnf=list(map(list,cnf)),answer=False,
            proof=dict(kind='split',variable=abs(forced),low=excluded if forced>0 else key,high=key if forced>0 else excluded)))
        key=keyroot;counts['extension_prefix_splits']+=1
    if key!=root:raise ValueError('Changed feedback extension root')
    return key
