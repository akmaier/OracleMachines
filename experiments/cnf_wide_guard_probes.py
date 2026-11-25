"""Bounded unit probes reusing one exact clause-occurrence index.

Checked guards are necessary consequences with explicit source proofs. Extended
unit traces never publish native facts without reconstructing source-only proof
leaves and splits. Open/budget results are not SAT verdicts.
"""
from collections import Counter,deque
from experiments import cnf_residual_dag as native
from experiments import cnf_guard_shortening_context as frozen
from experiments.cnf_shortening_prepared_source import PreparedSource
from experiments.cnf_conditional_unit_support import check_template,materialize


class ProbeLimit(RuntimeError):pass


class UnitIndex:
    def __init__(self,clauses,counts):
        self.clauses=tuple(map(tuple,clauses));self.occurrences={};self.lengths=[];self.xors=[];self.units=[];self.empty=None
        for cid,cl in enumerate(self.clauses):
            self.lengths.append(len(cl));x=0
            if not cl:self.empty=cid
            if len(cl)==1:self.units.append((cl[0],cid))
            for lit in cl:
                counts['probe_index_literals']+=1;x^=lit;self.occurrences.setdefault(lit,[]).append(cid)
            self.xors.append(x)
        counts['probe_index_builds']+=1
        counts['probe_index_peak_literals']=max(counts['probe_index_peak_literals'],sum(self.lengths))

    def probe(self,assumption,counts,remaining,trace_limit):
        left=self.lengths[:];xors=self.xors[:];satisfied=[False]*len(left);assigned={};trace=[];queue=deque(self.units)
        counts['probe_initialization_clauses']+=len(left);counts['unit_probes']+=1
        if self.empty is not None:return dict(units=[],conflict=self.empty)
        def assign(lit):
            assigned[abs(lit)]=lit>0
            for cid in self.occurrences.get(lit,()):
                if remaining()<=0:raise ProbeLimit('work_limit')
                counts['probe_occurrence_visits']+=1;satisfied[cid]=True
            for cid in self.occurrences.get(-lit,()):
                if remaining()<=0:raise ProbeLimit('work_limit')
                counts['probe_occurrence_visits']+=1
                if satisfied[cid]:continue
                left[cid]-=1;xors[cid]^=-lit
                if left[cid]==0:return cid
                if left[cid]==1:queue.append((xors[cid],cid));counts['probe_queue_insertions']+=1
            return None
        if assumption is not None:
            conflict=assign(assumption)
            if conflict is not None:return dict(units=trace,conflict=conflict)
        while queue:
            lit,cid=queue.popleft()
            if abs(lit) in assigned:
                if assigned[abs(lit)]!=(lit>0):return dict(units=trace,conflict=cid)
                continue
            if satisfied[cid]:continue
            if len(trace)>=trace_limit:raise ProbeLimit('trace_limit')
            trace.append([lit,cid]);counts['probe_units']+=1
            conflict=assign(lit)
            if conflict is not None:return dict(units=trace,conflict=conflict)
        counts['probe_open_closures']+=1
        return None


def prepare(source,templates,mode,counts):
    if mode not in ('source','binary','all'):raise ValueError('Unknown guard mode')
    owned=PreparedSource.prepare(source,templates,counts);state=owned.state({},counts)
    source=owned.source;basis={cl:dict(kind='source',index=i) for i,cl in enumerate(source)}
    hints=[]
    for h in state['hints']:
        if mode=='source' or (mode=='binary' and len(h['clause'])>2):continue
        hints.append(h);basis.setdefault(tuple(h['clause']),dict(kind='guard',index=h['origin_template']))
    clauses=tuple(sorted(basis));counts['probe_selected_guards']+=len(hints)
    return source,state,clauses,[basis[cl] for cl in clauses]


def roots(source):
    score=Counter(l for cl in source if len(cl)>2 for l in cl)
    variables={abs(l) for cl in source for l in cl}
    return sorted((s*v for v in variables for s in (-1,1)),key=lambda l:(-score[l],l))


def discover(source,templates,counts,*,mode='all',probe_limit=64,work_limit=262144,trace_limit=256):
    if any(type(v) is not int or v<1 for v in (probe_limit,work_limit,trace_limit)):raise ValueError('Positive probe bounds required')
    source,state,clauses,basis=prepare(source,templates,mode,counts);index=UnitIndex(clauses,counts)
    start=counts['probe_occurrence_visits'];records=[];found={}
    def remaining():return work_limit-(counts['probe_occurrence_visits']-start)
    def result(status,reason,terminal=None):return dict(status=status,reason=reason,mode=mode,probes=records,terminal=terminal,trace_limit=trace_limit)
    try:
        initial=index.probe(None,counts,remaining,trace_limit)
        if initial is not None:return result('refuted','units',dict(proof=initial))
        for i,root in enumerate(roots(source)):
            if i>=probe_limit:return result('unresolved','probe_limit')
            counts['probe_roots']+=1;proof=index.probe(root,counts,remaining,trace_limit)
            if proof is None:continue
            records.append(dict(assumption=root,proof=proof));found[root]=len(records)-1;counts['probe_exclusions']+=1
            if -root in found:return result('refuted','opposite_probes',dict(low=found[-abs(root)],high=found[abs(root)]))
    except ProbeLimit as error:return result('unresolved',str(error))
    return result('unresolved','complete')


def check_trace(source,clauses,assumption,proof,counts,limit):
    variables={abs(l) for cl in source for l in cl}
    if assumption is not None and (type(assumption) is not int or not assumption or abs(assumption) not in variables):raise ValueError('Invalid probe assumption')
    if type(proof) is not dict or set(proof)!={'units','conflict'} or type(proof['units']) is not list or len(proof['units'])>limit:raise ValueError('Invalid probe proof')
    assigned={} if assumption is None else {abs(assumption):assumption>0}
    def clause(cid):
        if type(cid) is not int or not 0<=cid<len(clauses):raise ValueError('Invalid probe clause')
        counts['probe_checked_literals']+=len(clauses[cid]);return clauses[cid]
    for pair in proof['units']:
        if type(pair) is not list or len(pair)!=2:raise ValueError('Invalid probe unit')
        lit,cid=pair;reason=clause(cid)
        if type(lit) is not int or not lit or abs(lit) in assigned or lit not in reason:raise ValueError('Invalid probe unit literal')
        if any(abs(l) not in assigned or assigned[abs(l)]==(l>0) for l in reason if l!=lit):raise ValueError('Probe reason is not unit')
        assigned[abs(lit)]=lit>0
    if any(abs(l) not in assigned or assigned[abs(l)]==(l>0) for l in clause(proof['conflict'])):raise ValueError('Missing probe conflict')
    counts['checked_probe_proofs']+=1


def validate(source,templates,program,counts):
    if type(program) is not dict or set(program)!={'status','reason','mode','probes','terminal','trace_limit'}:raise ValueError('Invalid probe program')
    if program['status'] not in ('refuted','unresolved') or type(program['trace_limit']) is not int or program['trace_limit']<1 or type(program['probes']) is not list:raise ValueError('Invalid probe program bounds')
    source,state,clauses,basis=prepare(source,templates,program['mode'],counts);seen=set()
    for probe in program['probes']:
        if type(probe) is not dict or set(probe)!={'assumption','proof'} or probe['assumption'] in seen:raise ValueError('Invalid repeated probe')
        check_trace(source,clauses,probe['assumption'],probe['proof'],counts,program['trace_limit']);seen.add(probe['assumption'])
    if program['status']=='refuted':
        end=program['terminal']
        if program['reason']=='units':
            if type(end) is not dict or set(end)!={'proof'}:raise ValueError('Invalid unit terminal')
            check_trace(source,clauses,None,end['proof'],counts,program['trace_limit'])
        elif program['reason']=='opposite_probes':
            if type(end) is not dict or set(end)!={'low','high'} or any(type(end[k]) is not int or not 0<=end[k]<len(program['probes']) for k in end):raise ValueError('Invalid split terminal')
            a=program['probes'][end['low']]['assumption'];b=program['probes'][end['high']]['assumption']
            if not a<0 or b!=-a:raise ValueError('Probes are not opposite')
        else:raise ValueError('Invalid refutation reason')
    elif program['terminal'] is not None or program['reason'] not in ('complete','probe_limit','work_limit','trace_limit'):raise ValueError('Invalid unresolved outcome')
    return source,state,clauses,basis


def compile_program(solver,source,templates,program,counts):
    source,state,clauses,basis=validate(source,templates,program,counts)
    if program['status']!='refuted':raise ValueError('Complete refutation required')
    def canonical(context):return solver._canonical(native.restrict_scan(source,context,counts))
    def leaf(cid,context):
        entry=basis[cid];clause=clauses[cid]
        template=(dict(clauses=[list(clause)],assumptions=sorted([[abs(l),l<0] for l in clause]),trace=[],conflict=0)
                  if entry['kind']=='source' else templates[entry['index']])
        return materialize(solver,source,template,context=sorted([list(p) for p in context.items()]),counts=counts)['root']
    def compile_trace(proof,assumption):
        def walk(i,context):
            cnf,names,key=canonical(context);old=solver._read(key,cnf,purpose='wide_probe_existing')
            if old is not None:
                if old['answer']:raise ValueError('Contradictory saved probe')
                counts['probe_native_hits']+=1;return key
            if () in cnf:
                solver._store(key,dict(format=native.FORMAT,cnf=list(map(list,cnf)),answer=False,proof=dict(kind='empty')));return key
            if i==len(proof['units']):return leaf(proof['conflict'],context)
            lit,cid=proof['units'][i];v=abs(lit);value=lit>0
            excluded=leaf(cid,{**context,v:not value})
            if v not in names:
                if excluded!=key:raise ValueError('Absent probe coordinate changed cofactor')
                counts['probe_absent_lifts']+=1;return key
            live=walk(i+1,{**context,v:value})
            solver._store(key,dict(format=native.FORMAT,cnf=list(map(list,cnf)),answer=False,
                proof=dict(kind='split',variable=names.index(v)+1,low=excluded if value else live,high=live if value else excluded)))
            counts['probe_native_splits']+=1;return key
        return walk(0,{} if assumption is None else {abs(assumption):assumption>0})
    cnf,names,key=canonical({});old=solver._read(key,cnf,purpose='wide_probe_root')
    if old is not None:
        if old['answer']:raise ValueError('Contradictory root')
        counts['probe_native_root_hits']+=1;return key
    end=program['terminal']
    if program['reason']=='units':return compile_trace(end['proof'],None)
    low=program['probes'][end['low']];high=program['probes'][end['high']]
    lowkey=compile_trace(low['proof'],low['assumption']);highkey=compile_trace(high['proof'],high['assumption'])
    solver._store(key,dict(format=native.FORMAT,cnf=list(map(list,cnf)),answer=False,
        proof=dict(kind='split',variable=abs(low['assumption']),low=lowkey,high=highkey)))
    counts['probe_native_splits']+=1;return key


def bind_prefix(source,templates,prefix,counts):
    source=frozen._source(source,templates,counts);fixed={};frames=[];support=set()
    if prefix['status']!='unresolved':raise ValueError('Unresolved binary prefix required')
    for step in prefix['steps']:
        state=frozen._state(source,templates,fixed,counts)
        forced,path=frozen._bind_path(step['path'],step['forced'],state,source,templates,fixed,support,counts,prefix['path_limit'])
        frames.append(dict(state=state,forced=forced,path=path));fixed[abs(step['forced'])]=step['forced']>0
    return frames,frozen._state(source,templates,fixed,counts)


def compile_extension(solver,source,templates,prefix,program,counts):
    frames,tail=bind_prefix(source,templates,prefix,counts);ts=[h['template'] for h in tail['hints']]
    # All portable proof checks precede lookup/publication of any new record.
    validate(tail['local'],ts,program,counts)
    if program['status']!='refuted':raise ValueError('Complete extension required')
    root=native.token(tuple(map(tuple,source)),counts);old=solver._read(root,tuple(map(tuple,source)),purpose='wide_extension_root')
    if old is not None:
        if old['answer']:raise ValueError('Contradictory extension root')
        counts['extension_root_hits']+=1;return root
    key=compile_program(solver,tail['local'],ts,program,counts)
    for frame in reversed(frames):
        state=frame['state'];forced=frame['forced'];profile=dict(clauses=state['graph'],paths={forced:frame['path']})
        excluded=frozen.compile_path(solver,state['local'],state['hints'],profile,forced,counts,path_limit=prefix['path_limit'])
        cnf=state['local'];keyroot=native.token(cnf,counts)
        solver._store(keyroot,dict(format=native.FORMAT,cnf=list(map(list,cnf)),answer=False,
            proof=dict(kind='split',variable=abs(forced),low=excluded if forced>0 else key,high=key if forced>0 else excluded)))
        key=keyroot;counts['extension_prefix_splits']+=1
    if key!=root:raise ValueError('Changed extension root')
    return key
