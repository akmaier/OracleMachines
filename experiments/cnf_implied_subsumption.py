"""Expose terminal families using existing probe proofs and indexed subsets.

No new propagation pass is made. Ordinary signed subsets retain priority; only
their failures try all original proved binary implications as subset witnesses.
The indexing-only mode accepts byte-identical old signed-subsumption archives.
"""
from experiments.cnf_learning_activity import ActivityLearningInventory
from experiments.cnf_pattern_inventory import encode
from experiments.cnf_signed_subsumption import SignedSubsumptionInventory, subsumption_certificate


def indexed_certificate(cnf, counts, *, phase='discovery'):
    """Produce the same first-retained-witness certificate as the old search.

    Equal-width distinct sets cannot contain one another. Exact duplicates use
    a retained-set lookup. Repeated literals within a clause use the old policy
    because its ordering is by list length, not set cardinality.
    """
    sets = [frozenset(c) for c in cnf]
    counts['subset_index_preparation_literals'] += sum(map(len, cnf))
    if any(len(s) != len(c) for s, c in zip(sets, cnf)):
        counts['subset_index_fallbacks'] += 1
        return subsumption_certificate(cnf, counts, phase=phase)
    prefix = 'subsumption_' + phase + '_'
    counts[prefix + 'calls'] += 1
    counts[prefix + 'literal_visits'] += sum(map(len, cnf))
    kept, removed, exact = [], [], {}
    for j in sorted(range(len(cnf)), key=lambda j: (len(cnf[j]), j)):
        witness = None
        for k in kept:
            counts['subset_index_width_checks'] += 1
            if len(sets[k]) >= len(sets[j]):
                break
            counts[prefix + 'subset_tests'] += 1
            if sets[k] <= sets[j]:
                witness = k
                break
        if witness is None:
            counts['subset_index_exact_lookups'] += 1
            witness = exact.get(sets[j])
        if witness is None:
            kept.append(j); exact[sets[j]] = j
        else:
            removed.append([j, witness])
    return dict(kept=sorted(kept), removed=removed)


def check_indexed_subsumption(cnf, certificate, counts, *, phase='check'):
    if not isinstance(certificate, dict) or set(certificate) != {'kept', 'removed'}:
        raise ValueError('Invalid indexed subsumption fields')
    kept, removed = certificate['kept'], certificate['removed']
    if (not isinstance(kept, list) or not isinstance(removed, list) or
            any(type(i) is not int or not 0 <= i < len(cnf) for i in kept) or
            any(not isinstance(pair, list) or len(pair) != 2 or
                any(type(i) is not int or not 0 <= i < len(cnf) for i in pair)
                for pair in removed)):
        raise ValueError('Invalid indexed source indices')
    if sorted(kept + [j for j, _ in removed]) != list(range(len(cnf))):
        raise ValueError('Indexed subsumption must cover every clause exactly once')
    retained = set(kept); sets = [set(c) for c in cnf]
    for j, k in removed:
        counts['subsumption_verified_witnesses'] += 1
        if k not in retained or not sets[k] <= sets[j]:
            raise ValueError('Invalid retained signed-subset witness')
    if certificate != indexed_certificate(cnf, counts, phase=phase):
        raise ValueError('Incorrect indexed subsumption policy')
    return tuple(tuple(cnf[i]) for i in kept)


def original_implications(cnf, attempts, counts):
    """Internal: attempts must first be discovered/checked against this source.

    Reconstruct every distinct, absent binary consequence with its original
    assumption/unit coordinates. In particular, retain binary-transitive ones.
    No saved clause or origin is accepted without reconstruction.
    """
    clauses = {tuple(c) for c in cnf}; result = []
    counts['implied_subset_source_literals'] += sum(map(len, cnf))
    for ai, attempt in enumerate(attempts):
        assumption = attempt['variable'] * (1 if attempt['value'] else -1)
        for ui, (lit, _) in enumerate(attempt['certificate']['units']):
            counts['implied_subset_unit_visits'] += 1
            clause = tuple(sorted((-assumption, lit)))
            if len(set(clause)) != 2 or clause[0] == -clause[1] or clause in clauses:
                continue
            clauses.add(clause)
            result.append(dict(attempt=ai, unit=ui, clause=list(clause)))
    counts['implied_subset_clauses'] += len(result)
    return result


class ImpliedSubsumptionInventory(SignedSubsumptionInventory):
    def __init__(self, *args, reuse_implications=True, **kwargs):
        if type(reuse_implications) is not bool:
            raise ValueError('reuse_implications must be Boolean')
        super().__init__(*args, **kwargs)
        self.reuse_implications = reuse_implications
        if reuse_implications:
            self.config['terminal_subsumption'] = 'implied-minimal-family-v1'

    @staticmethod
    def _recognized(profile):
        return any(v == 'recognized' for v in profile['outcomes'].values())

    def _find_core(self, cnf, profile, saved=None):
        """The profile's original probes are established before this method.

        The inherited node checker replays all original reasons before calling
        _check_profile. During discovery the original pass has already run.
        """
        if saved is not None and (not isinstance(saved, dict) or
                not {'certificate', 'core_profile'} <= set(saved)):
            raise ValueError('Missing original subset search')
        if saved is None:
            cert = indexed_certificate(cnf, self.counts)
            core = tuple(cnf[i] for i in cert['kept'])
        else:
            cert = saved['certificate']
            core = check_indexed_subsumption(cnf, cert, self.counts)
        core_profile = self._core_profile(core)
        data = dict(certificate=cert, core_profile=core_profile)
        if saved is not None and encode(saved['core_profile']) != encode(core_profile):
            raise ValueError('Invalid original subset profile')
        if self.reuse_implications and not self._recognized(core_profile):
            # Original probes are clear at an exhausted leaf. Their persisted
            # reasons justify this pool independently of the appended clauses.
            implications = original_implications(cnf, profile['probing'].get('attempts', []), self.counts)
            if implications:
                augmented = tuple(tuple(c) for c in cnf) + tuple(tuple(c['clause']) for c in implications)
                if saved is None:
                    augmented_cert = indexed_certificate(augmented, self.counts, phase='implied_discovery')
                    core = tuple(augmented[i] for i in augmented_cert['kept'])
                else:
                    proposed = saved.get('implied', {})
                    if not isinstance(proposed, dict) or encode(proposed.get('implications')) != encode(implications):
                        raise ValueError('Invalid original implication origins or clauses')
                    # The replay below has its own aggregate check counters;
                    # successful and failed original/augmented work are charged.
                    augmented_cert = proposed.get('certificate')
                    core = check_indexed_subsumption(augmented, augmented_cert, self.counts, phase='implied_check')
                core_profile = self._core_profile(core)
                data['implied'] = dict(implications=implications, certificate=augmented_cert,
                                       core_profile=core_profile)
            else:
                data['implied'] = dict(implications=[])
        if saved is not None and encode(data) != encode(saved):
            raise ValueError('Invalid implication-subset search or classification')
        return core, core_profile, data

    def _discover_profile(self, cnf, depth, profile, groups):
        # Preserve the fixed activity policy before either terminal search.
        node = ActivityLearningInventory._discover_profile(self, cnf, depth, profile, groups)
        if node['kind'] != 'unresolved':
            return node
        core, core_profile, data = self._find_core(cnf, profile)
        node['subsumption'] = data
        if self._recognized(core_profile):
            edge = self._edge(core, depth)
            node.update(kind='subsumption', edge=edge, summary=self._summary([edge]))
            self.counts['subsumption_family_exposures'] += 1
            self.counts['implied_subset_family_exposures'] += 'implied' in data
        else:
            self.counts['subsumption_unexposed_searches'] += 1
        return node

    def _check_profile(self, key, node, cnf, profile, groups):
        if node.get('kind') not in ('subsumption', 'unresolved'):
            return ActivityLearningInventory._check_profile(self, key, node, cnf, profile, groups)
        old = {k: v for k, v in node.items() if k not in ('subsumption', 'edge')}
        old.update(kind='unresolved', summary=dict(closed=False, unresolved_leaves=1,
                   unresolved_literals=profile['shape']['literals']))
        ActivityLearningInventory._check_profile(self, key, old, cnf, profile, groups)
        if 'subsumption' not in node:
            raise ValueError('Missing indexed terminal search')
        core, core_profile, _ = self._find_core(cnf, profile, node['subsumption'])
        fields = {'cnf', 'depth', 'profile', 'kind', 'summary', 'subsumption'}
        if self._recognized(core_profile):
            if set(node) != fields | {'edge'} or node['kind'] != 'subsumption':
                raise ValueError('Missing exposed family edge')
            self._check_edge(node['edge'], core, node['depth'])
            summary = self._summary([node['edge']])
            if not summary['closed']:
                raise ValueError('Exposed family must close its child')
        else:
            if set(node) != fields or node['kind'] != 'unresolved':
                raise ValueError('Unexposed implication core must remain unresolved')
            summary = old['summary']
        if encode(node['summary']) != encode(summary):
            raise ValueError('Invalid implication-subset summary')
