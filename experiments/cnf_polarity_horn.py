"""Certified Horn renaming at exhausted pattern leaves.

The established pair-constraint reduction finds variable flips, not a SAT model.
An auxiliary refutation excludes renamable-Horn membership, never original SAT.
Earlier reductions and conditioning retain priority; failures and caps persist.
"""
from itertools import combinations

from experiments.cnf_pattern_inventory import encode
from experiments.cnf_residual_dag import holds, two_cnf
from experiments.cnf_single_pass_inventory import SinglePassCheckInventory


def _source(cnf, counts):
    """Require distinct literals within each non-tautological source clause."""
    support = set(); pairs = 0
    for clause in cnf:
        if any(type(lit) is not int or not lit for lit in clause):
            raise ValueError('Invalid polarity source literal')
        literals = set(clause)
        if len(literals) != len(clause) or any(-lit in literals for lit in clause):
            raise ValueError('Polarity source clauses must be normalized')
        counts['polarity_source_literal_visits'] += len(clause)
        support.update(map(abs, clause)); pairs += len(clause)*(len(clause)-1)//2
    return support, pairs


def _limit(limit):
    if type(limit) is not int or limit < 0:
        raise ValueError('Polarity pair limit must be a nonnegative integer')


def discover_polarity(cnf, counts, *, pair_limit=65536):
    _limit(pair_limit); _, size = _source(cnf, counts)
    counts['polarity_discovery_calls'] += 1
    if size > pair_limit:
        counts['polarity_budget_stops'] += 1
        return dict(outcome='unresolved', reason='pair_limit', pairs=size, limit=pair_limit)
    pairs = []; origins = []
    for cid, clause in enumerate(cnf):
        for i, j in combinations(range(len(clause)), 2):
            pairs.append((clause[i], clause[j])); origins.append((cid, i, j))
    counts['polarity_pair_constraints'] += size
    model, refutation = two_cnf(pairs, counts)
    if model is not None:
        counts['polarity_recognized'] += 1
        return dict(outcome='recognized', pairs=size, flipped=sorted(v for v, value in model.items() if value))
    counts['polarity_excluded'] += 1
    # Persist source coordinates, not another complete quadratic pair formula.
    return dict(outcome='excluded', pairs=size, variable=refutation['variable'],
                **{name: [[target, *origins[cid]] for target, cid in refutation[name]]
                   for name in ('forward', 'backward')})


def check_polarity(cnf, certificate, counts, *, pair_limit=65536):
    """Direct Horn check or source-linked auxiliary paths; no SCC rediscovery."""
    _limit(pair_limit); support, size = _source(cnf, counts)
    counts['polarity_check_calls'] += 1
    if (type(certificate) is not dict or type(certificate.get('pairs')) is not int or
            certificate['pairs'] != size):
        raise ValueError('Invalid polarity pair count')
    if size > pair_limit:
        expected = dict(outcome='unresolved', reason='pair_limit', pairs=size, limit=pair_limit)
        if encode(certificate) != encode(expected):
            raise ValueError('Invalid polarity budget result')
        counts['polarity_verified_budget_stops'] += 1
        return None
    outcome = certificate.get('outcome')
    if outcome == 'recognized':
        if set(certificate) != {'outcome', 'pairs', 'flipped'}:
            raise ValueError('Invalid polarity certificate fields')
        flipped = certificate['flipped']
        if (type(flipped) is not list or any(type(v) is not int or v not in support for v in flipped)
                or flipped != sorted(set(flipped))):
            raise ValueError('Invalid polarity flip list')
        selected = set(flipped)
        target = tuple(tuple(-lit if abs(lit) in selected else lit for lit in clause) for clause in cnf)
        counts['polarity_transform_literals'] += sum(map(len, cnf))
        if any(sum(lit > 0 for lit in clause) > 1 for clause in target):
            raise ValueError('Polarity result is not Horn')
        counts['polarity_verified_renamings'] += 1
        return target
    if outcome != 'excluded' or set(certificate) != {'outcome', 'pairs', 'variable', 'forward', 'backward'}:
        raise ValueError('Missing polarity recognition or exclusion')
    variable = certificate['variable']
    if type(variable) is not int or variable not in support:
        raise ValueError('Invalid auxiliary conflict variable')
    for name, start, finish in (('forward', variable, -variable), ('backward', -variable, variable)):
        path = certificate[name]
        if type(path) is not list or not path:
            raise ValueError('Missing auxiliary implication path')
        previous = start
        for edge in path:
            if (type(edge) is not list or len(edge) != 4 or any(type(v) is not int for v in edge)):
                raise ValueError('Invalid auxiliary implication edge')
            target, cid, i, j = edge
            if not 0 <= cid < len(cnf) or not 0 <= i < j < len(cnf[cid]):
                raise ValueError('Invalid auxiliary source coordinates')
            a, b = cnf[cid][i], cnf[cid][j]
            if not ((a == -previous and b == target) or (b == -previous and a == target)):
                raise ValueError('Unjustified auxiliary implication')
            previous = target; counts['polarity_verified_path_edges'] += 1
        if previous != finish:
            raise ValueError('Incomplete auxiliary conflict path')
    counts['polarity_verified_exclusions'] += 1
    return None


class PolarityHornInventory(SinglePassCheckInventory):
    def __init__(self, *args, polarity_pair_limit=65536, **kwargs):
        _limit(polarity_pair_limit)
        super().__init__(*args, **kwargs)
        self.config.update(terminal_polarity='horn-pair-certificates-v1', polarity_pair_limit=polarity_pair_limit)

    def _discover_profile(self, cnf, depth, profile, groups):
        node = super()._discover_profile(cnf, depth, profile, groups)
        if node['kind'] != 'unresolved':
            return node
        proof = discover_polarity(cnf, self.counts, pair_limit=self.config['polarity_pair_limit'])
        target = check_polarity(cnf, proof, self.counts, pair_limit=self.config['polarity_pair_limit'])
        node['polarity'] = proof
        if target is not None:
            edge = self._edge(target, depth)
            node.update(kind='polarity', edge=edge, summary=self._summary([edge]))
            self.counts['polarity_family_exposures'] += 1
        return node

    def _check_profile(self, key, node, cnf, profile, groups):
        if node.get('kind') not in ('polarity', 'unresolved'):
            if 'polarity' in node:
                raise ValueError('Unexpected terminal polarity search')
            return super()._check_profile(key, node, cnf, profile, groups)
        old = {k: v for k, v in node.items() if k not in ('polarity', 'edge')}
        old.update(kind='unresolved', summary=dict(closed=False, unresolved_leaves=1,
                                                  unresolved_literals=profile['shape']['literals']))
        # Replays all prior reduction/subsumption failure obligations first.
        super()._check_profile(key, old, cnf, profile, groups)
        target = check_polarity(cnf, node.get('polarity'), self.counts,
                                pair_limit=self.config['polarity_pair_limit'])
        fields = {'cnf', 'depth', 'profile', 'kind', 'summary', 'subsumption', 'polarity'}
        if target is None:
            if set(node) != fields or node['kind'] != 'unresolved':
                raise ValueError('Excluded or budgeted renaming must remain unresolved')
            summary = old['summary']
        else:
            if set(node) != fields | {'edge'} or node['kind'] != 'polarity':
                raise ValueError('Missing exact polarity edge')
            self._check_edge(node['edge'], target, node['depth'])
            child = self._load(node['edge']['key'])
            if child['profile']['outcomes']['horn'] != 'recognized':
                raise ValueError('Renamed child must be Horn')
            summary = self._summary([node['edge']])
            if not summary['closed']:
                raise ValueError('Renamed family must close')
        if encode(node['summary']) != encode(summary):
            raise ValueError('Incorrect polarity coverage summary')

    def lift(self, key, child_model):
        node = self._load(key)
        if node['kind'] != 'polarity':
            return super().lift(key, child_model)
        edge = node['edge']; child = self._load(edge['key'])
        if (any(i not in child_model or type(child_model[i]) is not bool for i in range(1, len(edge['names'])+1))
                or not holds(child['cnf'], child_model)):
            raise ValueError('Invalid renamed child model')
        fixed = set(node['polarity']['flipped'])
        result = {v: (not child_model[i]) if v in fixed else child_model[i]
                  for i, v in enumerate(edge['names'], 1)}
        if not holds(node['cnf'], result):
            raise ValueError('Lift violates polarity source')
        return result
