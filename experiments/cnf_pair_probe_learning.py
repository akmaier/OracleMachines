"""Source-bound binary consequences with shared single-assumption prefixes."""
from collections import Counter,deque
from experiments import cnf_probe_buckets as probes
native=probes.native


def propagate(cnf,index,state,queue,counts):
    occ,_,empty=index;fixed,pending,satisfied,trace=state
    if empty is not None:return empty
    while queue:
        literal,reason=queue.popleft()
        if reason in satisfied:continue
        if abs(literal) in fixed:
            if fixed[abs(literal)]!=(literal>0):return reason
            continue
        fixed[abs(literal)]=literal>0
        if reason is not None:trace.append([literal,reason])
        for cid in occ.get(literal,()):satisfied.add(cid);counts['pair_occurrence_visits']+=1
        for cid in occ.get(-literal,()):
            counts['pair_occurrence_visits']+=1
            if cid in satisfied:continue
            remaining=pending.get(cid,len(cnf[cid]))-1;pending[cid]=remaining
            if not remaining:return cid
            if remaining==1:
                clause=cnf[cid];counts['pair_reason_scans']+=len(clause)
                unset=[l for l in clause if abs(l) not in fixed];assert len(unset)==1
                queue.append((unset[0],cid))
    return None


def prefix(cnf,index,assumption,counts):
    counts['pair_prefix_builds']+=1;state=({}, {}, set(), [])
    conflict=propagate(cnf,index,state,deque([(assumption,None),*index[1]]),counts)
    return state,dict(assumption=assumption,trace=state[3][:],conflict=conflict)


def extend(cnf,index,prepared,second,counts):
    state,head=prepared
    if head['conflict'] is not None:return [],None
    fixed,pending,satisfied,_=state
    if abs(second) in fixed:
        return ([], 'assumption') if fixed[abs(second)]!=(second>0) else ([],None)
    counts['pair_copied_state_entries']+=len(fixed)+len(pending)+len(satisfied)
    local=(dict(fixed),dict(pending),set(satisfied),[])
    conflict=propagate(cnf,index,local,deque([(second,None)]),counts)
    return local[3],conflict


def discover(cnf,counts=None,*,mode='shared',pair_limit=256,learn_limit=32):
    counts=Counter() if counts is None else counts
    if mode not in ('restart','shared') or any(type(x) is not int or not 1<=x<=4096 for x in (pair_limit,learn_limit)):raise ValueError('Invalid pair policy')
    frequency=Counter(abs(l) for c in cnf for l in c);counts['pair_rank_literals']+=sum(map(len,cnf))
    variables=sorted(frequency,key=lambda v:(-frequency[v],v));existing=set(cnf)
    index=probes.prepare_index(cnf,counts);heads=[];lemmas=[];head_ids={};attempts=0;skipped=0;cached=None;last=None;reason='exhausted'
    for i,v in enumerate(variables):
        for first in (v,-v):
            for w in variables[i+1:]:
                for second in (w,-w):
                    clause=tuple(sorted((-first,-second)))
                    if clause in existing:skipped+=1;continue
                    if attempts>=pair_limit or len(lemmas)>=learn_limit:
                        reason='pair-limit' if attempts>=pair_limit else 'learn-limit'
                        return dict(prefixes=heads,clauses=lemmas),dict(attempts=attempts,skipped=skipped,reason=reason)
                    if mode=='shared' and last==first:prepared=cached;counts['pair_prefix_hits']+=1
                    else:prepared=prefix(cnf,index,first,counts);last=first;cached=prepared
                    trace,conflict=extend(cnf,index,prepared,second,counts);attempts+=1;counts['pair_attempts']+=1
                    if prepared[1]['conflict'] is None and conflict is None:continue
                    if first not in head_ids:head_ids[first]=len(heads);heads.append(prepared[1])
                    lemmas.append(dict(prefix=head_ids[first],second=second,trace=trace,conflict=conflict));counts['pair_learned_clauses']+=1
    return dict(prefixes=heads,clauses=lemmas),dict(attempts=attempts,skipped=skipped,reason=reason)


def check(cnf,evidence,counts=None,*,pair_limit=256,learn_limit=32):
    counts=Counter() if counts is None else counts;variables={abs(l) for c in cnf for l in c}
    if type(evidence) is not dict or set(evidence)!={'prefixes','clauses'}:raise ValueError('Invalid pair evidence')
    heads=evidence['prefixes'];lemmas=evidence['clauses']
    if type(heads) is not list or type(lemmas) is not list or len(lemmas)>min(pair_limit,learn_limit) or len(heads)>len(lemmas):raise ValueError('Invalid pair evidence bounds')
    def literal(l):
        if type(l) is not int or abs(l) not in variables:raise ValueError('Invalid pair literal')
    def clause(cid):
        if type(cid) is not int or not 0<=cid<len(cnf):raise ValueError('Invalid pair reason')
        counts['pair_checked_literals']+=len(cnf[cid]);return cnf[cid]
    def trace(fixed,steps):
        if type(steps) is not list or len(steps)>len(variables)-len(fixed):raise ValueError('Invalid pair trace')
        for step in steps:
            if type(step) is not list or len(step)!=2:raise ValueError('Invalid pair step')
            l,cid=step;literal(l);c=clause(cid)
            if abs(l) in fixed or any(abs(a) in fixed and fixed[abs(a)]==(a>0) for a in c) or [a for a in c if abs(a) not in fixed]!=[l]:raise ValueError('Unsupported pair unit')
            fixed[abs(l)]=l>0
    def conflict(fixed,cid):
        if not all(abs(l) in fixed and fixed[abs(l)]!=(l>0) for l in clause(cid)):raise ValueError('Unsupported pair conflict')
    prepared=[];starts=set()
    for h in heads:
        if type(h) is not dict or set(h)!={'assumption','trace','conflict'}:raise ValueError('Invalid pair prefix')
        a=h['assumption'];literal(a)
        if a in starts:raise ValueError('Duplicate pair prefix')
        starts.add(a);fixed={abs(a):a>0};trace(fixed,h['trace'])
        if h['conflict'] is not None:conflict(fixed,h['conflict'])
        prepared.append(fixed);counts['pair_checked_prefixes']+=1
    learned=[];seen=set();used=set()
    for ev in lemmas:
        if type(ev) is not dict or set(ev)!={'prefix','second','trace','conflict'}:raise ValueError('Invalid pair clause')
        i=ev['prefix'];b=ev['second'];literal(b)
        if type(i) is not int or not 0<=i<len(heads):raise ValueError('Invalid pair reference')
        a=heads[i]['assumption']
        if abs(a)==abs(b):raise ValueError('Repeated pair variable')
        used.add(i);fixed=dict(prepared[i]);counts['pair_checked_copy_entries']+=len(fixed)
        if heads[i]['conflict'] is not None:
            if ev['trace']!=[] or ev['conflict'] is not None:raise ValueError('Invalid conflicting-prefix tail')
        elif abs(b) in fixed and fixed[abs(b)]!=(b>0):
            if ev['trace']!=[] or ev['conflict']!='assumption':raise ValueError('Invalid assumption clash')
        else:
            fixed[abs(b)]=b>0;trace(fixed,ev['trace']);conflict(fixed,ev['conflict'])
        c=tuple(sorted((-a,-b)))
        if c in seen or c in cnf:raise ValueError('Duplicate or existing learned clause')
        seen.add(c);learned.append(c);counts['pair_checked_clauses']+=1
    if used!=set(range(len(heads))):raise ValueError('Unused pair prefix')
    return tuple(learned)
