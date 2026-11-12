"""Two exact pivot steps through retained divergent routes, with admission caps.

An admission budget counts every newly entered recognizer state, including
descendants and unfinished ancestors. Completed certificates remain ordinary
immutable records; stopping discovery asserts neither closure nor UNSAT.
"""
from collections import Counter, defaultdict, deque
from experiments.cnf_anchored_subsets import AnchoredAdditiveInventory
from experiments.cnf_pivot_alternatives import alternatives,verify_trial,covered
from experiments.cnf_additive_elimination import check_additive_elimination,lift_additive_elimination
from experiments.cnf_variable_elimination import _limit
from experiments.cnf_pattern_inventory import encode


class AdmissionExhausted(Exception):
    pass


class BudgetedInventory(AnchoredAdditiveInventory):
    def set_admission_budget(self,limit):
        _limit(limit);self.admission_limit=limit;self.admitted=set();self.admission_counts=Counter()

    def _discover(self,cnf,depth):
        if not hasattr(self,'admission_limit'):
            raise ValueError('Set an explicit recognition admission budget')
        _,_,key=self._canonical(cnf,depth)
        if key not in self.admitted:
            if len(self.admitted)>=self.admission_limit:
                self.admission_counts['denied_states']+=1
                raise AdmissionExhausted('Recognition admission budget exhausted')
            self.admitted.add(key);self.admission_counts['entered_states']+=1
        else:self.admission_counts['reentered_states']+=1
        return super()._discover(cnf,depth)


def selected_children(node):
    if node['summary']['closed']:return []
    if node['kind']=='and':return [e['key'] for e in node['edges']]
    if node['kind']=='or':return [e['key'] for e in node['alternatives'][node['selected']]['edges']]
    if 'edge' in node:return [node['edge']['key']]
    if node['kind']=='unresolved':return []
    raise ValueError('Unknown open node')


class FrontierIndex:
    """In-process immutable-history memo, including exact leaf multiplicity."""
    def __init__(self,h):self.h=h;self.memo={};self.active=set();self.counts=Counter()

    def frontier(self,key):
        self.counts['frontier_requests']+=1
        if key in self.memo:self.counts['frontier_hits']+=1;return self.memo[key]
        if key in self.active:raise ValueError('Cyclic selected frontier')
        node=self.h._load(key)
        if node is None:raise ValueError('Missing frontier node')
        self.active.add(key);result=Counter()
        try:
            if node['kind']=='unresolved':result[key]=1
            else:
                for child in selected_children(node):result.update(self.frontier(child))
        finally:self.active.remove(key)
        self.memo[key]=result;self.counts['frontier_nodes']+=1;return result

    def literals(self,frontier):
        return sum(self.h._load(k)['profile']['shape']['literals']*n for k,n in frontier.items())


def coupled_key(record):return encode([record['source'],record['variables']])


def project_pair(cnf,variables,counts,*,pair_limit=64,clause_growth_limit=2):
    if type(variables) is not list or len(variables)!=2 or any(type(v) is not int or v<=0 for v in variables) or variables[0]==variables[1]:
        raise ValueError('Invalid pair pivots')
    intermediate=check_additive_elimination(cnf,dict(variable=variables[0]),counts,
        pair_limit=pair_limit,clause_growth_limit=clause_growth_limit)
    target=check_additive_elimination(intermediate,dict(variable=variables[1]),counts,
        pair_limit=pair_limit,clause_growth_limit=clause_growth_limit)
    return intermediate,target


def lift_pair(cnf,variables,model,counts,*,pair_limit=64,clause_growth_limit=2):
    intermediate,_=project_pair(cnf,variables,counts,pair_limit=pair_limit,clause_growth_limit=clause_growth_limit)
    first_model=lift_additive_elimination(intermediate,dict(variable=variables[1]),model,counts,
        pair_limit=pair_limit,clause_growth_limit=clause_growth_limit)
    return lift_additive_elimination(cnf,dict(variable=variables[0]),first_model,counts,
        pair_limit=pair_limit,clause_growth_limit=clause_growth_limit)


def check_pair(h,first,second,counts):
    """Reconstruct both projections in original source coordinates."""
    verify_trial(h,first,counts)
    node=h._load(first['source']);a=first['variable']
    if type(second) is not int or second<=0 or second==a:raise ValueError('Invalid second pivot')
    _,target=project_pair(node['cnf'],[a,second],counts,
        pair_limit=h.config['elimination_pair_limit'],clause_growth_limit=h.config['clause_growth_limit'])
    return target


def verify_coupled(h,record,first_trials,counts):
    if type(record) is not dict or set(record)!={'source','variables','edge','summary'}:
        raise ValueError('Invalid coupled record fields')
    if type(record['source']) is not str or type(record['variables']) is not list or len(record['variables'])!=2:
        raise ValueError('Invalid coupled source or pivots')
    a,b=record['variables']
    if type(a) is not int or type(b) is not int or min(a,b)<=0 or a==b:
        raise ValueError('Invalid coupled pivots')
    first=first_trials.get(encode([record['source'],a]))
    if first is None or first['source']!=record['source'] or first['variable']!=a:
        raise ValueError('Missing exact retained first trial')
    target=check_pair(h,first,b,counts);node=h._load(record['source'])
    h._check_edge(record['edge'],target,node['depth']);child=h._load(record['edge']['key'])
    if encode(record['summary'])!=encode(child['summary']):raise ValueError('Incorrect coupled closure')
    counts['verified_coupled_trials']+=1;return child['summary']['closed']


def select_divergent(h,root,by_source,index,limit,counts):
    _limit(limit)
    if not limit:return []
    queue=deque([root]);seen=set();candidates=[]
    while queue:
        key=queue.popleft()
        if key in seen:continue
        seen.add(key);node=h._load(key);counts['selection_nodes']+=1
        if node is None:raise ValueError('Missing original plan')
        if node['summary']['closed']:continue
        for first in by_source.get(key,()):
            counts['prior_trials_compared']+=1
            before=index.frontier(key);after=index.frontier(first['edge']['key'])
            if before==after:counts['reconvergent_trials_skipped']+=1;continue
            if first['summary']['closed']:continue
            old_size=index.literals(before);new_size=index.literals(after)
            candidates.append(((new_size-old_size,new_size,len(after),len(seen),first['variable']),first))
        queue.extend(selected_children(node))
    candidates.sort(key=lambda item:item[0]);counts['divergent_trials_available']+=len(candidates)
    chosen=[record for _,record in candidates[:limit]];counts['first_trials_selected']+=len(chosen)
    return chosen


def search(h,root,first_trials,known_coupled,index,counts,*,route_limit=4,trial_limit=8,state_limit=32):
    for limit in (route_limit,trial_limit,state_limit):_limit(limit)
    h.set_admission_budget(state_limit)
    if not trial_limit:return [],None
    by_source=defaultdict(list)
    for first in first_trials.values():
        by_source[first['source']].append(first);counts['first_trial_index_records']+=1
    selected=select_divergent(h,root,by_source,index,route_limit,counts);choices=[]
    for first in selected:
        verify_trial(h,first,counts);node=h._load(first['source']);a=first['variable']
        intermediate=check_additive_elimination(node['cnf'],dict(variable=a),counts,
            pair_limit=h.config['elimination_pair_limit'],clause_growth_limit=h.config['clause_growth_limit'])
        rows=alternatives(intermediate,None,counts,pair_limit=h.config['elimination_pair_limit'],
            candidate_limit=h.config['elimination_candidate_limit'],clause_growth_limit=h.config['clause_growth_limit'])
        neighbors=set()
        for clause in node['cnf']:
            counts['interaction_source_literals']+=len(clause)
            if a in clause or -a in clause:neighbors.update(map(abs,clause))
        retained=[r for r in rows if r['variable'] in neighbors]
        counts['noninteracting_candidates_skipped']+=len(rows)-len(retained)
        counts['interacting_second_candidates']+=len(retained);choices.append((first,retained))
    records=[];successes=set()
    for rank in range(max((len(rows) for _,rows in choices),default=0)):
        for first,rows in choices:
            if rank>=len(rows) or first['source'] in successes:continue
            row=rows[rank];a=first['variable'];b=row['variable'];identity=encode([first['source'],[a,b]])
            if identity in known_coupled:
                saved=known_coupled[identity]
                if coupled_key(saved)!=identity:raise ValueError('Incorrect cached coupled identity')
                if verify_coupled(h,saved,first_trials,counts):successes.add(first['source'])
                counts['reused_coupled_trials']+=1
            else:
                target=check_pair(h,first,b,counts)
                if target!=row['target']:raise ValueError('Incorrect second projection proposal')
                node=h._load(first['source'])
                try:edge=h._edge(target,node['depth'])
                except AdmissionExhausted:
                    counts['budget_stopped_trials']+=1
                    # No fake edge or summary is persisted. Completed descendants
                    # remain checked nodes; this resumable attempt is only a log.
                    return records,dict(source=first['source'],variables=[a,b],reason='admission_limit')
                summary=h._load(edge['key'])['summary']
                record=dict(source=first['source'],variables=[a,b],edge=edge,summary=summary)
                if verify_coupled(h,record,first_trials,counts):successes.add(first['source'])
                records.append(record);counts['completed_coupled_trials']+=1
            if len(records)>=trial_limit or covered(h,root,successes,counts):return records,None
    return records,None
