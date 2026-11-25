"""Close native residuals by bounded ordinary unit propagation before expanding.

Only source clauses in the current canonical residual support these shortcuts.
Open and interrupted attempts fall back to the checked five-bank compiler.
All incoming provenance and native proof rules remain independently checked.
"""
from collections import Counter
from experiments import cnf_cursor_feedback as prior
from experiments.cnf_prepared_publication import prepare_frame
from experiments.cnf_conditional_unit_support import match,fixed_pairs,restrict,propagate
native=prior.native;frozen=prior.frozen
validate=prior.validate;_plan=prior._plan


def checked_options(shortcut,work_limit,trace_limit):
    if shortcut not in ('off','layer','all') or any(type(v) is not int or v<1 for v in (work_limit,trace_limit)):
        raise ValueError('Invalid direct unit closure bounds')
    return dict(shortcut=shortcut,unit_work_limit=work_limit,unit_trace_limit=trace_limit)


class DirectUnits:
    """Query-local work allowance; never retain an index across contexts.

Charge each gate clause, then index clause/literal slots and occurrence visits.
A rejected index reservation spends no index work. Gate scanning still counts.
This allowance excludes the unchanged compiler, publication and proof checking.
"""
    def __init__(self,counts,work_limit,trace_limit):
        checked_options('all',work_limit,trace_limit)
        self.counts=counts;self.remaining=work_limit;self.trace_limit=trace_limit

    def close(self,frame):
        cnf,_,_,publish=frame;c=self.counts;c['direct_candidates']+=1
        if self.remaining<=0:c['direct_budget_skips']+=1;return False
        slots=0;has_unit=False
        for cl in cnf:
            if self.remaining<=0:c['direct_budget_skips']+=1;return False
            self.remaining-=1;c['direct_gate_clauses']+=1
            slots+=1+len(cl);has_unit|=len(cl)==1
        if not has_unit:c['direct_no_unit_skips']+=1;return False
        if slots>self.remaining:c['direct_budget_skips']+=1;return False
        self.remaining-=slots;c['direct_index_slots']+=slots;c['direct_attempts']+=1
        local=Counter();index=frozen.UnitIndex(cnf,local)
        try:
            proof=index.probe(None,local,lambda:self.remaining-local['probe_occurrence_visits'],self.trace_limit)
        except frozen.ProbeLimit as error:
            c['direct_'+str(error)+'_fallbacks']+=1;proof=None
        finally:
            self.remaining-=local['probe_occurrence_visits']
            for key,value in local.items():
                if key=='probe_index_peak_literals':c['direct_'+key]=max(c['direct_'+key],value)
                else:c['direct_'+key]+=value
        if proof is None:c['direct_fallbacks']+=1;return False
        publish(dict(kind='units',trace=proof['units'],conflict=proof['conflict']))
        c['direct_refutations']+=1;return True


def _compile(solver,templates,seed,new,third,fourth,program,prepared,counts,*,shortcut="all",unit_work_limit=262144,unit_trace_limit=256):
    source,base,basis,first,origins,second,origins2,thirdbank,origins3,fourthbank,origins4=prepared
    direct=DirectUnits(counts,unit_work_limit,unit_trace_limit)
    banks=(base,first,second,thirdbank,fourthbank);entries=(basis,origins,origins2,origins3,origins4)
    def frame(context,offered=None):
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
        lower={'probe':0,'new_probe':1,'third_probe':2,'cursor_probe':3}[kind]
        if lower>=stage:raise ValueError('Non-decreasing proof dependency')
        row=(seed,new,third['program'],fourth)[lower]['probes'][i];lit=row['assumption']
        if context.get(abs(lit))!=(lit>0):raise ValueError('Failed probe premise missing')
        counts[('layer_expanded_old','layer_expanded_new','layer_expanded_third','layer_expanded_cursor')[lower]]+=1
        return trace(lower,row['proof'],context,offered)
    def trace(stage,proof,context,offered=None):
        def walk(i,context,offered=None):
            prepared_frame=frame(context,offered);cnf,names,key,publish=prepared_frame
            old=solver._read(key,cnf,purpose='layer_existing')
            if old is not None:
                if old['answer']:raise ValueError('Contradictory layered cache')
                counts['layer_native_hits']+=1;return key
            if () in cnf:publish(dict(kind='empty'));return key
            if shortcut!='off' and (shortcut=='all' or i==0) and direct.close(prepared_frame):return key
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
    return trace(4,program['proof'],{})


def compile_program(solver,source,templates,seed,closure,new,next_closure,third,feedback_closure,probe_cursor,program,counts,*,select_support=True,shortcut="all",unit_work_limit=262144,unit_trace_limit=256):
    options=checked_options(shortcut,unit_work_limit,unit_trace_limit)
    prepared=validate(source,templates,seed,closure,new,next_closure,third,feedback_closure,probe_cursor,program,counts)
    if program['status']!='refuted' or program['mode']!='feedback':raise ValueError('Complete third feedback refutation required')
    source=prepared[0];root=native.token(source,counts);old=solver._read(root,source,purpose='third_feedback_root')
    if old is not None:
        if old['answer']:raise ValueError('Contradictory layered root')
        counts['layer_root_hits']+=1;return root
    plan=_plan(source,templates,seed,new,third,probe_cursor['program'],program,prepared,counts) if select_support else None
    if plan is None:return _compile(solver,templates,seed,new,third,probe_cursor['program'],program,prepared,counts,**options)
    child=_compile(solver,plan['templates'],plan['seed'],plan['new'],plan['third'],plan['fourth'],plan['program'],plan['prepared'],counts,**options)
    if child!=root:
        solver._store(root,dict(format=native.FORMAT,cnf=list(map(list,source)),answer=False,
            proof=dict(kind='component',clauses=plan['indices'],child=child)))
        counts['layer_support_wrappers']+=1
    return root


def compile_extension(solver,source,templates,prefix,seed,closure,new,next_closure,third,feedback_closure,probe_cursor,program,counts,*,shortcut="all",unit_work_limit=262144,unit_trace_limit=256):
    options=checked_options(shortcut,unit_work_limit,unit_trace_limit)
    frames,tail=frozen.bind_prefix(source,templates,prefix,counts);ts=[h['template'] for h in tail['hints']]
    validate(tail['local'],ts,seed,closure,new,next_closure,third,feedback_closure,probe_cursor,program,counts)
    if program['status']!='refuted' or program['mode']!='feedback':raise ValueError('Complete feedback extension required')
    root=native.token(tuple(map(tuple,source)),counts);old=solver._read(root,tuple(map(tuple,source)),purpose='feedback_extension')
    if old is not None:
        if old['answer']:raise ValueError('Contradictory feedback extension')
        counts['extension_root_hits']+=1;return root
    key=compile_program(solver,tail['local'],ts,seed,closure,new,next_closure,third,feedback_closure,probe_cursor,program,counts,**options)
    for frame in reversed(frames):
        state=frame['state'];forced=frame['forced'];profile=dict(clauses=state['graph'],paths={forced:frame['path']})
        excluded=frozen.frozen.compile_path(solver,state['local'],state['hints'],profile,forced,counts,path_limit=prefix['path_limit'])
        cnf=state['local'];keyroot=native.token(cnf,counts)
        solver._store(keyroot,dict(format=native.FORMAT,cnf=list(map(list,cnf)),answer=False,
            proof=dict(kind='split',variable=abs(forced),low=excluded if forced>0 else key,high=key if forced>0 else excluded)))
        key=keyroot;counts['extension_prefix_splits']+=1
    if key!=root:raise ValueError('Changed feedback extension root')
    return key
