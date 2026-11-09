"""Optional exact signed substitution from already checked paired probes.

Use one star-shaped equivalence block from the first eligible pair, after the
failed-literal and common-consequence priorities. No extra probe is requested.
This is established equivalent-literal reasoning, not a new SAT tractability
result. Every clause is substituted; no interacting leftover is discarded.
"""
from experiments.cnf_common_consequence import (
    CommonConsequenceInventory, discover_common_probes, check_common_probes)
from experiments.cnf_pattern_inventory import encode
from experiments.cnf_residual_dag import holds


def first_equivalence_pair(attempts, counts):
    """After checking both non-conflicting traces, derive one signed block.

    A low-branch literal -y and high-branch literal y imply y=x; the opposite
    signs imply y=not x. Pick the smallest member as representative. Restricting
    each step to one pair avoids combining unchecked or inconsistent cycles.
    """
    for i in range(0, len(attempts), 2):
        low, high = attempts[i:i+2]
        a = {lit for lit, _ in low['certificate']['units']}
        b = {lit for lit, _ in high['certificate']['units']}
        counts['equivalence_intersection_unit_visits'] += len(a) + len(b)
        opposite = sorted((lit for lit in a if -lit in b), key=abs)
        if not opposite:
            continue
        # sign[v] says whether v equals the central probe variable.
        sign = {low['variable']: 1}
        sign.update((abs(lit), -1 if lit > 0 else 1) for lit in opposite)
        representative = min(sign)
        mapping = [[v, representative * sign[v] * sign[representative]] for v in sorted(sign)]
        return dict(pair=i//2, mapping=mapping)
    return None


def substitute_block(cnf, witness, counts):
    mapping = dict(witness['mapping'])
    counts['equivalence_substitution_literal_visits'] += sum(map(len, cnf))
    # Keep original representative IDs. The ordinary child edge subsequently
    # removes tautologies/duplicates and records its compact-name transport.
    return tuple(tuple(mapping.get(abs(lit), abs(lit)) * (1 if lit > 0 else -1)
                       for lit in clause) for clause in cnf)


def discover_equivalence_probes(cnf, limit, counts, *, _discover_attempt=None, _choices=None):
    result = discover_common_probes(cnf, limit, counts, _discover_attempt=_discover_attempt, _choices=_choices)
    if result['status'] != 'clear':
        return result
    witness = first_equivalence_pair(result['attempts'], counts)
    if witness is None:
        return result
    counts['equivalence_rewrites_discovered'] += 1
    counts['equivalence_variables_merged'] += len(witness['mapping']) - 1
    return dict(status='equivalence', attempts=result['attempts'], witness=witness)


def check_equivalence_probes(cnf, result, limit, counts, *, _check_attempt=None, _choices=None):
    if result.get('status') != 'equivalence':
        target, fixed = check_common_probes(cnf, result, limit, counts, _check_attempt=_check_attempt, _choices=_choices)
        if result['status'] == 'clear' and first_equivalence_pair(result['attempts'], counts) is not None:
            raise ValueError('Omitted equivalence rewrite')
        return target, fixed
    if set(result) != {'status', 'attempts', 'witness'}:
        raise ValueError('Invalid equivalence fields')
    # Replay every reason against this exact source and enforce earlier rules.
    check_common_probes(cnf, dict(status='clear', attempts=result['attempts']), limit, counts,
                         _check_attempt=_check_attempt, _choices=_choices)
    expected = first_equivalence_pair(result['attempts'], counts)
    if expected is None or encode(result['witness']) != encode(expected):
        raise ValueError('Invalid equivalence pair or signed transport')
    target = substitute_block(cnf, expected, counts)
    if not {abs(l) for c in target for l in c} < {abs(l) for c in cnf for l in c}:
        raise ValueError('Equivalence substitution must strictly reduce support')
    counts['verified_equivalence_rewrites'] += 1
    return target, {}


class ProbeEquivalenceInventory(CommonConsequenceInventory):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.config['probe_equivalences'] = 'first-pair-smallest-representative-v1'

    def _discover_probes(self, cnf):
        return discover_equivalence_probes(cnf, self.config['probe_limit'], self.counts)

    def _check_probes(self, cnf, result):
        return check_equivalence_probes(cnf, result, self.config['probe_limit'], self.counts)

    @staticmethod
    def _uses_probe(profile):
        return profile['probing']['status'] in ('forced', 'common', 'equivalence')

    def lift(self, key, child_model):
        node = self._load(key)
        if node['kind'] != 'probe' or node['profile']['probing']['status'] != 'equivalence':
            return super().lift(key, child_model)
        edge = node['edge']; child = self._load(edge['key'])
        if (any(i not in child_model or type(child_model[i]) is not bool
                for i in range(1, len(edge['names'])+1)) or not holds(child['cnf'], child_model)):
            raise ValueError('Invalid equivalence child model')
        self._check_probes(node['cnf'], node['profile']['probing'])
        model = {abs(lit): False for c in node['cnf'] for lit in c}
        model.update((v, child_model[i]) for i, v in enumerate(edge['names'], 1))
        for variable, signed_rep in node['profile']['probing']['witness']['mapping']:
            model[variable] = model[abs(signed_rep)] if signed_rep > 0 else not model[abs(signed_rep)]
        if not holds(node['cnf'], model):
            raise ValueError('Lift violates equivalence source')
        return model
