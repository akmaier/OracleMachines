"""Expose existing families by signed subsumption at exhausted discovery leaves.

Earlier reductions and conditioning retain priority. Failed searches and exact
source-index witnesses persist. A smaller core is followed only when the basic
classifier recognizes it; this adds no recursive budget or general SAT claim.
"""
from experiments.cnf_learning_activity import ActivityLearningInventory
from experiments.cnf_pattern_inventory import classify, encode
from experiments.cnf_residual_dag import holds, normalize


def subsumption_certificate(cnf, counts, *, phase='discovery'):
    """Keep all inclusion-minimal clauses, using signed literals throughout.

    Sorting by length makes every witness a retained source clause, never a
    removed intermediate. The input is normalized in the inventory, but this
    helper also handles duplicate clauses and the empty clause.
    """
    prefix = 'subsumption_' + phase + '_'
    counts[prefix + 'calls'] += 1
    counts[prefix + 'literal_visits'] += sum(map(len, cnf))
    sets = [set(c) for c in cnf]
    kept, removed = [], []
    for j in sorted(range(len(cnf)), key=lambda j: (len(cnf[j]), j)):
        witness = None
        for k in kept:
            counts[prefix + 'subset_tests'] += 1
            if sets[k] <= sets[j]:
                witness = k
                break
        if witness is None:
            kept.append(j)
        else:
            removed.append([j, witness])
    return dict(kept=sorted(kept), removed=removed)


def check_subsumption(cnf, certificate, counts):
    """Check coverage and retained signed witnesses before replaying policy.

    The first checks establish logical equivalence independently of discovery.
    The final replay also binds failed searches to this deterministic policy.
    Checking is charged explicitly; it is not a constant-time certificate step.
    """
    if not isinstance(certificate, dict) or set(certificate) != {'kept', 'removed'}:
        raise ValueError('Invalid subsumption fields')
    kept, removed = certificate['kept'], certificate['removed']
    if (not isinstance(kept, list) or not isinstance(removed, list) or
            any(type(i) is not int or not 0 <= i < len(cnf) for i in kept) or
            any(not isinstance(pair, list) or len(pair) != 2 or
                any(type(i) is not int or not 0 <= i < len(cnf) for i in pair)
                for pair in removed)):
        raise ValueError('Invalid subsumption source indices')
    if sorted(kept + [j for j, _ in removed]) != list(range(len(cnf))):
        raise ValueError('Subsumption must cover every source clause exactly once')
    retained = set(kept)
    sets = [set(c) for c in cnf]
    for j, k in removed:
        counts['subsumption_verified_witnesses'] += 1
        if k not in retained or not sets[k] <= sets[j]:
            raise ValueError('Invalid retained signed-subset witness')
    if certificate != subsumption_certificate(cnf, counts, phase='check'):
        raise ValueError('Incomplete or reordered subsumption search')
    return tuple(tuple(cnf[i]) for i in kept)


class SignedSubsumptionInventory(ActivityLearningInventory):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.config['terminal_subsumption'] = 'signed-minimal-family-v1'

    def _core_profile(self, core):
        normalized, _ = normalize(core, self.counts)
        return classify(normalized, self.config['parity_width'], self.counts)

    def _discover_profile(self, cnf, depth, profile, groups):
        node = super()._discover_profile(cnf, depth, profile, groups)
        if node['kind'] != 'unresolved':
            return node
        certificate = subsumption_certificate(cnf, self.counts)
        core = tuple(cnf[i] for i in certificate['kept'])
        core_profile = self._core_profile(core)
        node['subsumption'] = dict(certificate=certificate, core_profile=core_profile)
        if any(v == 'recognized' for v in core_profile['outcomes'].values()):
            if not certificate['removed']:
                raise ValueError('Family exposure requires strict clause decrease')
            edge = self._edge(core, depth)
            node.update(kind='subsumption', edge=edge, summary=self._summary([edge]))
            self.counts['subsumption_family_exposures'] += 1
        else:
            self.counts['subsumption_unexposed_searches'] += 1
        return node

    def _check_profile(self, key, node, cnf, profile, groups):
        if node.get('kind') not in ('subsumption', 'unresolved'):
            return super()._check_profile(key, node, cnf, profile, groups)
        # Establish that the old policy is exhausted here, including all its
        # previous reductions, priorities, remaining depth and candidate budget.
        old = {k: v for k, v in node.items() if k not in ('subsumption', 'edge')}
        old.update(kind='unresolved', summary=dict(closed=False, unresolved_leaves=1,
                   unresolved_literals=profile['shape']['literals']))
        super()._check_profile(key, old, cnf, profile, groups)
        saved = node.get('subsumption')
        if not isinstance(saved, dict) or set(saved) != {'certificate', 'core_profile'}:
            raise ValueError('Missing terminal subsumption search')
        core = check_subsumption(cnf, saved['certificate'], self.counts)
        actual = self._core_profile(core)
        if encode(actual) != encode(saved['core_profile']):
            raise ValueError('Invalid reduced-core recognition')
        exposed = any(v == 'recognized' for v in actual['outcomes'].values())
        fields = {'cnf', 'depth', 'profile', 'kind', 'summary', 'subsumption'}
        if exposed:
            if (set(node) != fields | {'edge'} or node['kind'] != 'subsumption'
                    or not saved['certificate']['removed']):
                raise ValueError('Missing strict family-exposing reduction')
            self._check_edge(node['edge'], core, node['depth'])
            summary = self._summary([node['edge']])
            if not summary['closed']:
                raise ValueError('Exposed family must close its child')
        else:
            if set(node) != fields or node['kind'] != 'unresolved':
                raise ValueError('Unexposed core must retain the original leaf')
            summary = old['summary']
        if encode(node['summary']) != encode(summary):
            raise ValueError('Invalid subsumption summary')

    def lift(self, key, child_model):
        node = self._load(key)
        if node['kind'] != 'subsumption':
            return super().lift(key, child_model)
        edge = node['edge']; child = self._load(edge['key'])
        if (any(i not in child_model or type(child_model[i]) is not bool
                for i in range(1, len(edge['names']) + 1)) or
                not holds(child['cnf'], child_model)):
            raise ValueError('Invalid subsumption child model')
        model = {abs(lit): False for c in node['cnf'] for lit in c}
        model.update((v, child_model[i]) for i, v in enumerate(edge['names'], 1))
        if not holds(node['cnf'], model):
            raise ValueError('Lift violates subsumption source')
        return model
