"""Exact source splits without a prerequisite binary-probe trace.

Both unit-closed cofactors are acquired explicitly and retained before pattern
expansion. Selection is heuristic; only the source restrictions, unit reasons,
variable transports and independently justified child plans prove coverage.
"""
from collections import Counter
import json
from experiments.cnf_conditioning import shortest_balanced_choices
from experiments.cnf_pattern_inventory import encode
from experiments.cnf_residual_dag import restrict,holds
from experiments.cnf_simplification import discover_simplification,check_simplification,simplification_reconstruction
from experiments.cnf_single_pass_check import reconstruct_single_pass
from experiments.cnf_selected_routes import SelectedRoutes
from experiments.cnf_positive_primitives import PositiveReplay
from experiments.cnf_variable_elimination import _limit

TABLE='cnf_bootstrap_splits_v1'
KIND='bootstrap_split'


def initialize(h):
    h.db.execute(f'CREATE TABLE IF NOT EXISTS {TABLE} (id TEXT PRIMARY KEY,payload TEXT NOT NULL)')
    h.db.commit()


def record_key(record):return encode([record['source'],record['variable']])


def source_node(h,source,variable):
    node=h._load(source)
    if node is None:raise ValueError('Missing bootstrap source')
    if type(variable) is not int or variable not in {abs(l) for c in node['cnf'] for l in c}:
        raise ValueError('Split variable must occur in its source')
    return node


def verify(h,record,counts):
    if (type(record) is not dict or set(record)!={'source','variable','branches'}
            or type(record['source']) is not str or type(record['branches']) is not list
            or len(record['branches'])!=2):raise ValueError('Both bootstrap polarities are required')
    node=source_node(h,record['source'],record['variable']);targets=[];fixed=[]
    for value,branch in zip((False,True),record['branches'],strict=True):
        if type(branch) is not dict or set(branch)!={'certificate','edge'}:
            raise ValueError('Invalid bootstrap branch fields')
        target,closure=check_simplification(restrict(node['cnf'],{record['variable']:value},counts),
            branch['certificate'],counts,units=True,pure=False)
        if not {abs(l) for c in target for l in c} < {abs(l) for c in node['cnf'] for l in c}:
            raise ValueError('Bootstrap cofactor must reduce support')
        _,names,key=h._canonical(target,node['depth'])
        if encode(branch['edge'])!=encode(dict(key=key,names=names)):
            raise ValueError('Incorrect bootstrap child binding')
        assignment={record['variable']:value};assignment.update(closure)
        targets.append(target);fixed.append(assignment)
    counts['verified_bootstrap_splits']+=1
    return targets,fixed


def acquire_record(h,source,variable,counts):
    """A saved record is independently rechecked, never treated as a verdict."""
    node=source_node(h,source,variable);key=encode([source,variable])
    row=h.db.execute(f'SELECT payload FROM {TABLE} WHERE id=?',(key,)).fetchone()
    counts['bootstrap_lookups']+=1
    if row is not None:
        counts['bootstrap_read_bytes']+=len(row[0].encode());record=json.loads(row[0])
        if record_key(record)!=key:raise ValueError('Foreign saved split')
        verify(h,record,counts);counts['bootstrap_reused_pairs']+=1;return record
    branches=[]
    for value in (False,True):
        raw=restrict(node['cnf'],{variable:value},counts)
        certificate=discover_simplification(raw,counts,units=True,pure=False)
        counts['bootstrap_fresh_assumptions']+=1
        target,_=check_simplification(raw,certificate,counts,units=True,pure=False)
        _,names,child=h._canonical(target,node['depth'])
        branches.append(dict(certificate=certificate,edge=dict(key=child,names=names)))
    record=dict(source=source,variable=variable,branches=branches);verify(h,record,counts)
    payload=encode(record)
    with h.db:h.db.execute(f'INSERT INTO {TABLE} VALUES (?,?)',(key,payload))
    counts['bootstrap_written_bytes']+=len(key.encode())+len(payload.encode())
    counts['bootstrap_new_pairs']+=1;return record


def choices(h,source,counts,limit=4):
    _limit(limit);node=h._load(source)
    if node is None:raise ValueError('Missing bootstrap source')
    return shortest_balanced_choices(node['cnf'],limit,counts)


def size_rank(h,record,counts):
    targets,_=verify(h,record,counts)
    return [max(len({abs(l) for c in t for l in c}) for t in targets),
            sum(sum(map(len,t)) for t in targets),record['variable']]


def attach(h,routes,record,counts):
    verify(h,record,counts);children=[b['edge']['key'] for b in record['branches']]
    if any(h._load(k) is None for k in children):return False
    item=(dict(kind=KIND,id=record_key(record)),children)
    if item not in routes.by_source[record['source']]:routes.by_source[record['source']].append(item)
    return True


def lift(h,record,value,model):
    if type(value) is not bool:raise ValueError('Expected Boolean branch')
    _,fixed=verify(h,record,Counter());edge=record['branches'][int(value)]['edge'];node=h._load(edge['key'])
    if node is None or any(i not in model or type(model[i]) is not bool for i in range(1,len(edge['names'])+1)) or not holds(node['cnf'],model):
        raise ValueError('Invalid bootstrap child model')
    source=h._load(record['source'])['cnf'];result={abs(l):False for c in source for l in c}
    result.update(fixed[int(value)]);result.update((v,model[i]) for i,v in enumerate(edge['names'],1))
    if not holds(source,result):raise ValueError('Bootstrap lift violates source')
    return result


class BootstrapRoutes(SelectedRoutes):
    def __init__(self,h,records):
        super().__init__(h,[[],[],[],[],[]]);self.bootstraps={}
        for record in records:
            key=record_key(record)
            if key in self.bootstraps and encode(record)!=encode(self.bootstraps[key]):
                raise ValueError('Conflicting bootstrap split')
            self.bootstraps[key]=record

    def select(self,h,source,rule):
        if type(rule) is not dict or rule.get('kind')!=KIND:return super().select(h,source,rule)
        if set(rule)!={'kind','id'} or type(rule['id']) is not str:raise ValueError('Invalid bootstrap rule')
        record=self.bootstraps.get(rule['id'])
        if record is None or record['source']!=source or not attach(h,self,record,self.counts):
            raise ValueError('Missing bootstrap premises')


def verify_positive(h,certificate,roots,records,counts):
    replay=PositiveReplay(h,[[],[],[],[],[]],counts);replay.routes=BootstrapRoutes(h,records)
    with simplification_reconstruction(reconstruct_single_pass):replay.verify(certificate,roots)
    return replay
