"""Extend a checked ready support bank without re-extracting old proof supports.

Only the new catalog is traversed for support discovery. Old provenance and
negative cores are rechecked. New entries remain proposals until the unchanged
deferred materializer checks a negative core before using it.
"""
from collections import Counter
from copy import deepcopy
from experiments.cnf_deferred_support import discover
from experiments.cnf_clause_deletion_guard import clause_set,check_guard


def check_proposals(solver,prior,catalogs):
    """Check bindings/coverage; missing derived roots remain unproved proposals."""
    cores=prior['all_cores'];indices=prior['retained_indices'];members=[clause_set(c['source'],Counter()) for c in cores]
    if (prior['cores']!=[cores[i] for i in indices] or len(set(indices))!=len(indices)
            or len({tuple(sorted(m)) for m in members})!=len(members)):
        raise ValueError('Invalid prior frontier')
    if [d['core'] for d in prior['dominance']]!=list(range(len(cores))):raise ValueError('Missing dominance witness')
    for d in prior['dominance']:
        if d['retained'] not in indices or not members[d['retained']]<=members[d['core']]:raise ValueError('Invalid dominance witness')
    for i in indices:
        if any(j!=i and members[j]<=members[i] for j in indices):raise ValueError('Nonminimal containment frontier')
    expected=[(name,r['case']) for name,rs in catalogs for r in rs if r['answer'] is False and r['guard'] is not None]
    if [(o['catalog'],o['case']) for o in prior['origins']]!=expected or len(set(expected))!=len(expected):raise ValueError('Unbound prior origins')
    lookup={(name,r['case']):r for name,rs in catalogs for r in rs};first={};ready=0
    for o in prior['origins']:
        r=lookup[(o['catalog'],o['case'])];_,target=check_guard(solver,r['source'],r['guard']);cnf,_,key=solver._canonical(target)
        if solver._canonical(r['source'])[2]!=o['query_root'] or r['query_root']!=o['query_root']:raise ValueError('Unbound prior query')
        if key!=o['child_root'] or r['child']['root']!=key or r['child']['answer'] is not False or r['child']['model'] is not None or r['model'] is not None:raise ValueError('Unbound prior child')
        node=solver._read(key,cnf,purpose='incremental_origin')
        if node is None or node['answer'] is not False:raise ValueError('Missing negative origin')
        if not members[o['core']]<=clause_set(target,Counter()):raise ValueError('Proposal outside origin')
        first.setdefault(o['core'],key)
    if len(first)!=len(cores):raise ValueError('Unsupported prior proposal')
    for i,c in enumerate(cores):
        cnf,_,key=solver._canonical(c['source'])
        if key!=c['root'] or c['origin']!=first[i]:raise ValueError('Unbound prior support')
        node=solver._read(key,cnf,purpose='incremental_ready')
        if node is not None:
            if node['answer'] is not False:raise ValueError('Positive proposed support')
            ready+=1
    return dict(prior_sources_checked=len(expected),prior_ready_roots=ready,prior_pending_roots=len(cores)-ready)


def merge(prior,delta):
    """Preserve first-origin IDs and maintain the exact containment antichain."""
    cores=deepcopy(prior['all_cores']);origins=deepcopy(prior['origins']);counts=Counter()
    members=[clause_set(c['source'],counts) for c in cores]
    identities={tuple(sorted(m)):i for i,m in enumerate(members)}
    if len(identities)!=len(cores):raise ValueError('Duplicate prior supports')
    retained=list(prior['retained_indices']);remap={}
    for i,core in enumerate(delta['all_cores']):
        wanted=clause_set(core['source'],counts);key=tuple(sorted(wanted))
        if key in identities:remap[i]=identities[key];counts['duplicate_supports']+=1;continue
        index=len(cores);remap[i]=index;identities[key]=index;cores.append(deepcopy(core));members.append(wanted)
        counts['new_supports']+=1
        if any(members[j]<=wanted for j in retained):continue
        removed=[j for j in retained if wanted<=members[j]];counts['retired_frontier_entries']+=len(removed)
        retained=[j for j in retained if j not in removed]+[index]
    seen={(o['catalog'],o['case']) for o in origins}
    for origin in delta['origins']:
        identity=(origin['catalog'],origin['case'])
        if identity in seen:raise ValueError('Repeated source identity; do not reacquire an old batch')
        seen.add(identity);entry=deepcopy(origin);entry['core']=remap[origin['core']];origins.append(entry)
    retained.sort(key=lambda i:(len(members[i]),sorted(members[i])))
    dominance=[dict(core=i,retained=next(j for j in retained if members[j]<=m)) for i,m in enumerate(members)]
    return dict(cores=[cores[i] for i in retained],all_cores=cores,origins=origins,retained_indices=retained,dominance=dominance,
        counts=dict(delta['counts']),extraction_counts=dict(delta['extraction_counts']),merge_counts=dict(counts),deferred=True,
        limitation='Prior checked cores plus new source-bound proposals; only checked negative proofs justify target publication. Raw-coordinate containment only.')


def extend(solver,prior,old_catalogs,new_catalogs):
    old_ids={(name,r['case']) for name,rs in old_catalogs for r in rs}
    new_ids=[(name,r['case']) for name,rs in new_catalogs for r in rs]
    if old_ids.intersection(new_ids) or len(new_ids)!=len(set(new_ids)):
        raise ValueError('Repeated source identity; provide only a new batch')
    # Pending proposals are allowed, but cannot justify UNSAT before the frozen
    # materializer verifies an actual core. JSON is not a trusted proof flag.
    checked=check_proposals(solver,prior,old_catalogs)
    result=merge(prior,discover(solver,new_catalogs))
    result.update(checked)
    return result
