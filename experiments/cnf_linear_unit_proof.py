"""Preorder unit/partition certificates with implicit, independently checked contexts.

The frozen unit search is unchanged. Packing is an untrusted representation
conversion; only the source checker grants authority. No proof compression or
search bound for unrestricted SAT is implied.
"""
from collections import Counter
from experiments import cnf_unit_partition as prior
FORMAT='cnf-linear-unit-proof-v1'
RESULT='cnf-linear-unit-result-v1'


def pack(source, proof, counts=None):
    counts=Counter() if counts is None else counts
    if type(proof) is not dict or set(proof)!={'format','seed','nodes'} or proof['format']!=prior.EXCLUSION or type(proof['nodes']) is not dict:
        raise ValueError('Invalid packing input')
    clauses,names,seed=prior.prior.prepare(source,proof['seed'],0,counts)
    bits={v:1<<i for i,v in enumerate(names)};pending=[(0,0)];seen=set();rows=[]
    while pending:
        mask,kept=pending.pop();key=f'{mask}:{kept}'
        if key in seen or key not in proof['nodes']:raise ValueError('Incomplete or cyclic packing input')
        seen.add(key);node=proof['nodes'][key];counts['linear_pack_contexts']+=1
        if type(node) is not dict or type(node.get('units')) is not list:raise ValueError('Invalid packing node')
        for index in node['units']:
            if type(index) is not int or not 0<=index<len(clauses):raise ValueError('Invalid packing unit')
            counts['linear_pack_literal_charge']+=len(clauses[index])
            free=[lit for lit in clauses[index] if not (mask|kept)&bits[abs(lit)]]
            if len(free)!=1:raise ValueError('Invalid packing deduction')
            lit=free[0]
            if (lit>0)!=seed[abs(lit)]:mask|=bits[abs(lit)]
            else:kept|=bits[abs(lit)]
        if set(node)=={'units','blocked'}:rows.append([node['units'][:],node['blocked']])
        elif set(node)=={'units','clause','order'}:
            order=node['order']
            if type(order) is not list or not order or any(type(v) is not int or v not in bits for v in order):raise ValueError('Invalid packing order')
            rows.append([node['units'][:],node['clause'],order[:]]);children=[];prefix=kept
            for v in order:
                children.append((mask|bits[v],prefix));prefix|=bits[v]
            counts['linear_pack_edges']+=len(children);pending.extend(reversed(children))
        else:raise ValueError('Invalid packing fields')
    if len(seen)!=len(proof['nodes']):raise ValueError('Unreachable packing input')
    return dict(format=FORMAT,seed=proof['seed'],nodes=rows)


def check_exclusion(source, proof, counts=None):
    """Replay an exact preorder tree using a partial-assignment undo trail."""
    counts=Counter() if counts is None else counts
    if type(proof) is not dict or set(proof)!={'format','seed','nodes'} or proof['format']!=FORMAT or type(proof['nodes']) is not list:
        raise ValueError('Invalid linear proof')
    clauses,names,seed=prior.prior.prepare(source,proof['seed'],0,counts)
    fixed={};trail=[];pending=[('enter',())];cursor=0

    def assign(v,value):
        if v in fixed:raise ValueError('Repeated fixed variable')
        fixed[v]=value;trail.append(v);counts['linear_check_assignments']+=1

    def clause(index):
        if type(index) is not int or not 0<=index<len(clauses):raise ValueError('Invalid clause index')
        counts['linear_check_literal_charge']+=len(clauses[index]);return clauses[index]

    def free(index):
        result=[]
        for lit in clause(index):
            v=abs(lit)
            if v not in fixed:result.append(lit)
            elif fixed[v]==(lit>0):raise ValueError('Satisfied unit/conflict premise')
        return result

    while pending:
        action,payload=pending.pop()
        if action=='undo':
            while len(trail)>payload:del fixed[trail.pop()];counts['linear_check_undos']+=1
            continue
        mark=len(trail)
        for v,value in payload:assign(v,value)
        pending.append(('undo',mark))
        if cursor==len(proof['nodes']):raise ValueError('Missing subtree')
        node=proof['nodes'][cursor];cursor+=1;counts['linear_contexts_checked']+=1
        if type(node) is not list or len(node) not in (2,3) or type(node[0]) is not list:raise ValueError('Invalid linear node')
        for index in node[0]:
            available=free(index)
            if len(available)!=1:raise ValueError('Nonunit deduction')
            lit=available[0];assign(abs(lit),lit>0);counts['linear_deductions_checked']+=1
        if len(node)==2:
            if free(node[1]):raise ValueError('Unblocked leaf')
        else:
            c=clause(node[1]);order=node[2]
            if any(fixed.get(abs(lit),seed[abs(lit)])==(lit>0) for lit in c):raise ValueError('Satisfied split clause')
            available={abs(lit) for lit in c if abs(lit) not in fixed}
            if type(order) is not list or any(type(v) is not int for v in order) or not available or len(order)!=len(available) or set(order)!=available:
                raise ValueError('Incomplete split order')
            prefix=[];children=[]
            for v in order:
                children.append(('enter',tuple(prefix+[(v,not seed[v])])))
                counts['linear_check_branch_values']+=len(prefix)+1;prefix.append((v,seed[v]))
            pending.extend(reversed(children))
    if cursor!=len(proof['nodes']):raise ValueError('Trailing unreachable nodes')
    return dict(answer=False,model=None)


def check_result(source, proof, counts=None):
    counts=Counter() if counts is None else counts
    if type(proof) is not dict or set(proof)!={'format','kind','certificate'} or proof['format']!=RESULT:raise ValueError('Invalid linear result')
    if proof['kind']=='sat':return prior.prior.previous.check(source,proof['certificate'],counts)
    if proof['kind']=='unsat':return check_exclusion(source,proof['certificate'],counts)
    if proof['kind']=='unknown' and proof['certificate'] is None:
        prior.prior.previous.capacity.canonical(source,counts);return dict(answer=None,model=None)
    raise ValueError('Invalid linear verdict')


def solve(source, counts=None):
    counts=Counter() if counts is None else counts
    result=prior.discover(source,counts)
    kind='sat' if result['witness'] is not None else ('unsat' if result['exclusion'] is not None else 'unknown')
    cert=result['witness'] if kind=='sat' else (pack(source,result['exclusion'],counts) if kind=='unsat' else None)
    proof=dict(format=RESULT,kind=kind,certificate=cert);check_result(source,proof,counts)
    return proof,result['diagnostic']
