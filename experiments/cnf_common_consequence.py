"""Reuse both assumption traces to obtain checked necessary assignments.

The old probe phase is unchanged. If all its attempts are inconclusive, use all
common literals of the first eligible pair. This is established look-ahead
reasoning, not a new tractability result. Remaining pairs stay in the record.
"""
from experiments.cnf_failed_literal import FailedLiteralInventory, discover_probes, check_probes
from experiments.cnf_pattern_inventory import encode
from experiments.cnf_residual_dag import restrict
from experiments.cnf_simplification import discover_simplification, check_simplification


def first_common_pair(attempts, counts):
    """Called after discovery or validation of complete, non-conflicting pairs."""
    for i in range(0, len(attempts), 2):
        low, high = attempts[i:i+2]
        a = {lit for lit, _ in low['certificate']['units']}
        b = {lit for lit, _ in high['certificate']['units']}
        counts['common_intersection_unit_visits'] += (len(low['certificate']['units']) +
                                                    len(high['certificate']['units']))
        common = sorted(a & b, key=abs)
        if common:
            return dict(pair=i//2, literals=common)
    return None


def discover_common_probes(cnf, limit, counts, *, _discover_attempt=None):
    result = discover_probes(cnf, limit, counts, _discover_attempt=_discover_attempt)
    if result['status'] != 'clear':
        return result
    witness = first_common_pair(result['attempts'], counts)
    if witness is None:
        return result
    fixed = {abs(lit): lit > 0 for lit in witness['literals']}
    closure = discover_simplification(restrict(cnf, fixed, counts), counts, pure=False)
    counts['common_rewrites_discovered'] += 1
    counts['common_literals_discovered'] += len(fixed)
    return dict(status='common', attempts=result['attempts'], witness=witness, closure=closure)


def check_common_probes(cnf, result, limit, counts, *, _check_attempt=None):
    if result.get('status') != 'common':
        target, fixed = check_probes(cnf, result, limit, counts, _check_attempt=_check_attempt)
        if result['status'] == 'clear' and first_common_pair(result['attempts'], counts) is not None:
            raise ValueError('Omitted common-consequence rewrite')
        return target, fixed
    if set(result) != {'status', 'attempts', 'witness', 'closure'}:
        raise ValueError('Invalid common-consequence fields')
    # Reconstruct assumptions from the parent and check both traces in full;
    # matching unit literals alone is not a certificate of either implication.
    check_probes(cnf, dict(status='clear', attempts=result['attempts']), limit, counts,
                         _check_attempt=_check_attempt)
    expected = first_common_pair(result['attempts'], counts)
    if expected is None or encode(result['witness']) != encode(expected):
        raise ValueError('Invalid common pair or literal intersection')
    fixed = {abs(lit): lit > 0 for lit in expected['literals']}
    target, closure_fixed = check_simplification(restrict(cnf, fixed, counts), result['closure'], counts, pure=False)
    fixed.update(closure_fixed)
    if not {abs(lit) for c in target for lit in c} < {abs(lit) for c in cnf for lit in c}:
        raise ValueError('Common closure must strictly reduce support')
    counts['verified_common_rewrites'] += 1
    return target, fixed


class CommonConsequenceInventory(FailedLiteralInventory):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.config['common_consequences'] = 'first-complete-pair-v1'

    def _discover_probes(self, cnf):
        return discover_common_probes(cnf, self.config['probe_limit'], self.counts)

    def _check_probes(self, cnf, result):
        return check_common_probes(cnf, result, self.config['probe_limit'], self.counts)

    @staticmethod
    def _uses_probe(profile):
        return profile['probing']['status'] in ('forced', 'common')
