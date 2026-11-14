"""Schedule retained obligations, then uncovered original-input residuals.

The caller supplies the complete checked route catalog and current root closure
flags. This is a selected-path scheduler, not a complete search of alternatives
or a coverage certificate. It does no acquisition and never resets a budget.
Pending ordinary targets keep their source so the saved forced trace can resume.
"""
from experiments.cnf_split_frontier import frontier
from experiments.cnf_target_probe import remaining
from experiments.cnf_trace_split import record_key


def select(h, routes, evidence, roots, closed, counts):
    if len(evidence) != 5 or len(roots) != len(closed):
        raise ValueError('Five evidence lists and one closure flag per root required')
    retained = frontier(h, routes, evidence[3], counts)
    if retained['pending']:
        row = retained['pending'][0]
        split = next((r for r in evidence[3] if record_key(r) == row.get('split')), None)
        if 'split' in row and split is None:
            raise ValueError('Missing retained split record')
        return dict(mode='resume_retained_split' if split else 'resume_retained_probe',
                    source=row['source'], pending_split=split, pending=row,
                    selected_original_cases=[], retained=retained)
    if retained['leaves']:
        return dict(mode='retained_leaf', source=retained['leaves'][0]['source'],
                    pending_split=None, selected_original_cases=[], retained=retained)

    cases = [i for i, flag in enumerate(closed) if not flag]
    rows = remaining(h, [dict(source=roots[i], target=roots[i]) for i in cases], routes, counts)
    leaves = {}; bindings = {}
    for case, row in zip(cases, rows, strict=True):
        if row['closed'] or not row['leaves']:
            raise ValueError('Stale coverage or missing original frontier')
        for leaf in row['leaves']:
            source = leaf['source']
            if source in leaves and leaves[source] != leaf:
                raise ValueError('Inconsistent shared original leaf')
            leaves[source] = leaf
            bindings.setdefault(source, []).append(case)

    def rank(source):
        cnf = h._load(source)['cnf']
        return (not leaves[source]['pending'], len({abs(l) for c in cnf for l in c}),
                sum(map(len, cnf)), source)

    ordered = sorted(leaves, key=rank)
    navigation = dict(cases=cases, frontiers=rows,
                      ranked_sources=[dict(source=s, rank=list(rank(s)),
                                           selected_original_cases=bindings[s]) for s in ordered])
    if not ordered:
        return dict(mode='all_originals_closed', source=None, pending_split=None,
                    selected_original_cases=[], retained=retained, navigation=navigation)
    source = ordered[0]
    return dict(mode='resume_original_probe' if leaves[source]['pending'] else 'original_leaf',
                source=source, pending_split=None, leaf=leaves[source],
                selected_original_cases=bindings[source], retained=retained, navigation=navigation)
