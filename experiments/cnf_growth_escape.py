"""Explicit one-step growth exceptions over an unchanged recognition history.

The exception is part of the trial identity, not the child's recognizer config.
A failed or interrupted attempt neither refutes the source nor excludes a class.
"""
from experiments.cnf_additive_elimination import check_additive_elimination
from experiments.cnf_coupled_pivots import AdmissionExhausted
from experiments.cnf_pattern_inventory import encode
from experiments.cnf_pivot_alternatives import alternatives
from experiments.cnf_variable_elimination import _limit


TABLE = 'cnf_growth_trials_v1'


def trial_key(record):
    return encode([record['source'], record['variable'], record['growth_limit']])


def source_node(h, source):
    if type(source) is not str:
        raise ValueError('Invalid escape source')
    node = h._load(source)
    if node is None or node['kind'] != 'unresolved' or node['summary']['closed']:
        raise ValueError('Escape must bind an unresolved source')
    return node


def verify_escape(h, record, counts, *, growth_limit=3):
    """Check one exact projection, its binding and the caller's growth policy."""
    _limit(growth_limit)
    if type(record) is not dict or set(record) != {'source', 'variable', 'growth_limit', 'edge', 'summary'}:
        raise ValueError('Invalid growth escape fields')
    if type(record['growth_limit']) is not int or record['growth_limit'] != growth_limit:
        raise ValueError('Incorrect growth escape policy')
    if type(record['variable']) is not int or record['variable'] <= 0:
        raise ValueError('Invalid escape pivot')
    node = source_node(h, record['source'])
    target = check_additive_elimination(node['cnf'], dict(variable=record['variable']), counts,
        pair_limit=h.config['elimination_pair_limit'], clause_growth_limit=growth_limit)
    h._check_edge(record['edge'], target, node['depth'])
    child = h._load(record['edge']['key'])
    if encode(record['summary']) != encode(child['summary']):
        raise ValueError('Incorrect escape summary')
    counts['verified_growth_trials'] += 1
    return child['summary']['closed']


def search(h, source, known, counts, *, growth_limit=3, state_limit=32):
    """Try minimum-growth admitted pivots, sharing one descendant admission cap.

    Minimum means among the enumerated candidates meeting the pair/candidate
    caps. Candidate preparation and all old checking are charged separately.
    Records are returned for the caller to persist; partial child proofs persist
    immediately through the inventory. Saved trials are independently rechecked.
    """
    _limit(growth_limit); _limit(state_limit)
    node = source_node(h, source)
    rows = alternatives(node['cnf'], None, counts,
        pair_limit=h.config['elimination_pair_limit'],
        candidate_limit=h.config['elimination_candidate_limit'],
        clause_growth_limit=growth_limit)
    minimum = min((len(r['target']) - len(node['cnf']) for r in rows), default=None)
    rows = [r for r in rows if len(r['target']) - len(node['cnf']) == minimum]
    counts['minimum_growth_candidates'] += len(rows)
    h.set_admission_budget(state_limit)
    records = []
    for row in rows:
        identity = encode([source, row['variable'], growth_limit])
        if identity in known:
            saved = known[identity]
            if trial_key(saved) != identity:
                raise ValueError('Incorrect saved escape identity')
            verify_escape(h, saved, counts, growth_limit=growth_limit)
            counts['reused_growth_trials'] += 1
            continue
        target = check_additive_elimination(node['cnf'], dict(variable=row['variable']), counts,
            pair_limit=h.config['elimination_pair_limit'], clause_growth_limit=growth_limit)
        if target != row['target']:
            raise ValueError('Incorrect proposed escape target')
        try:
            edge = h._edge(target, node['depth'])
        except AdmissionExhausted:
            counts['budget_stopped_trials'] += 1
            return records, dict(source=source, variable=row['variable'], growth_limit=growth_limit,
                                 reason='admission_limit')
        record = dict(source=source, variable=row['variable'], growth_limit=growth_limit,
                      edge=edge, summary=h._load(edge['key'])['summary'])
        verify_escape(h, record, counts, growth_limit=growth_limit)
        records.append(record)
        counts['completed_growth_trials'] += 1
    return records, None
