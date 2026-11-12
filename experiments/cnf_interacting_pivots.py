"""Prioritize interacting pivot choices without claiming others are redundant."""
from experiments.cnf_pivot_alternatives import alternatives,open_ancestors,selected_pivot,verify_trial,covered
from experiments.cnf_variable_elimination import _limit
from experiments.cnf_additive_elimination import check_additive_elimination


def rank_interactions(cnf,selected,rows,counts):
    neighbors=set()
    for clause in cnf:
        support={abs(l) for l in clause};counts['interaction_scan_literals']+=len(clause)
        if selected in support:neighbors.update(support)
    counts['interacting_candidates']+=sum(r['variable'] in neighbors for r in rows)
    counts['independent_candidates']+=sum(r['variable'] not in neighbors for r in rows)
    return sorted(rows,key=lambda r:(r['variable'] not in neighbors,r['score'])),neighbors


def search(h,root,counts,*,ancestor_limit=4,trial_limit=8):
    _limit(ancestor_limit);_limit(trial_limit)
    if not trial_limit:return []
    sources=open_ancestors(h,root,ancestor_limit,counts);candidates=[]
    for key in sources:
        node=h._load(key);selected=selected_pivot(node)
        rows=alternatives(node['cnf'],selected,counts,pair_limit=h.config['elimination_pair_limit'],
            candidate_limit=h.config['elimination_candidate_limit'],clause_growth_limit=h.config['clause_growth_limit'])
        rows,neighbors=rank_interactions(node['cnf'],selected,rows,counts)
        candidates.append((key,rows,neighbors))
    records=[];successes=set()
    for rank in range(max((len(rows) for _,rows,_ in candidates),default=0)):
        for key,rows,neighbors in candidates:
            if rank>=len(rows) or key in successes:continue
            row=rows[rank];node=h._load(key)
            target=check_additive_elimination(node['cnf'],dict(variable=row['variable']),counts,
                pair_limit=h.config['elimination_pair_limit'],clause_growth_limit=h.config['clause_growth_limit'])
            if target!=row['target']:raise ValueError('Incorrect proposed target')
            edge=h._edge(target,node['depth']);summary=h._load(edge['key'])['summary']
            record=dict(source=key,variable=row['variable'],edge=edge,summary=summary)
            if verify_trial(h,record,counts):successes.add(key)
            records.append(record);counts['recognition_trials']+=1
            counts['interacting_trials' if row['variable'] in neighbors else 'independent_trials']+=1
            if len(records)>=trial_limit or covered(h,root,successes,counts):return records
    return records
