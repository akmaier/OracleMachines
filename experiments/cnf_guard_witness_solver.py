"""Discover tentative short-guard contradictions before preparing local proofs.

A tentative graph is a filter, never proof authority. Every selected guard edge
must acquire an exact local certificate before the inherited native compiler
can publish a refutation. Missing supports remove candidates within a budget.
"""
from experiments import cnf_residual_dag as native
from experiments.cnf_guard_closure_solver import GuardClosureSolver, transport_short


class WitnessGuardClosureSolver(GuardClosureSolver):
    def __init__(self, *args, witness_retries=32, graph_checks=1024, **kwargs):
        if any(type(n) is not int or n < 1 for n in (witness_retries, graph_checks)):
            raise ValueError('Positive witness and graph limits required')
        self.witness_retries = witness_retries
        self.graph_checks = graph_checks
        super().__init__(*args, **kwargs)

    def solve(self, source):
        try:
            return super().solve(source)
        finally:
            if self.closure_summary is not None:
                self.closure_summary['limits'].update(
                    witness_retries=self.witness_retries, graph_checks=self.graph_checks)

    def _guard_closure(self, cnf):
        c = self.closure_counts
        c['sites'] += 1
        parent = self.guard_parents[-1] if self.guard_parents else None
        if parent is None or parent['cnf'] is not cnf:
            c['unbound_sites'] += 1
            return None
        if self.closure_records is None:
            members = set(self.guard_source)
            self.closure_records = []
            for template in self.guard_templates:
                c['source_support_clauses'] += len(template['clauses'])
                if all(tuple(cl) in members for cl in template['clauses']):
                    self.closure_records.append((template, sum(map(len, template['clauses']))))
        fixed = parent['fixed']
        inverse = {v: k for k, v in parent['mapping'].items()}
        candidates = []
        for template, size in self.closure_records:
            if c['candidate_checks'] >= self.closure_checks:
                c['check_limit_misses'] += 1
                break
            c['candidate_checks'] += 1
            missing = []
            compatible = True
            for variable, value in template['assumptions']:
                c['guard_pair_checks'] += 1
                if variable in fixed:
                    if fixed[variable] != value:
                        compatible = False
                        break
                else:
                    missing.append((variable, value))
            if not compatible or len(missing) > (2 if self.closure_mode == 'binary' else 1):
                continue
            if any(v not in inverse for v, _ in missing):
                c['absent_guard_variables'] += 1
                continue
            clause = tuple(sorted(-inverse[v] if b else inverse[v] for v, b in missing))
            candidates.append((template, size, missing, clause))
            c['tentative_width_' + str(len(clause))] += 1
        c['peak_site_candidates'] = max(c['peak_site_candidates'], len(candidates))
        rejected = set()
        checked = {}

        def validate(index):
            if index in checked:
                c['local_witness_reuses'] += 1
                return checked[index]
            if index in rejected:
                return None
            template, size, missing, clause = candidates[index]
            if c['reserved_support_literals'] + size > self.closure_literals:
                c['literal_limit_misses'] += 1
                rejected.add(index)
                return None
            c['reserved_support_literals'] += size
            c['witness_support_checks'] += 1
            hint = transport_short(cnf, template, missing, parent, c)
            if hint is None:
                rejected.add(index)
                return None
            assert tuple(hint['clause']) == clause
            checked[index] = hint
            c['accepted_width_' + str(len(clause))] += 1
            return hint

        # An empty candidate is itself the proposed witness; it still needs a
        # local unit certificate. No implication path can justify it instead.
        for index, (_, _, _, clause) in enumerate(candidates):
            if not clause:
                hint = validate(index)
                if hint is not None:
                    c['closed_empty'] += 1
                    return dict(kind='units', trace=hint['proof']['units'], conflict=hint['proof']['conflict'])
                if len(rejected) >= self.witness_retries:
                    c['witness_retry_limit_misses'] += 1
                    return None

        original = {cl for cl in cnf if len(cl) <= 2}
        for width in (1, 2):
            if width == 2 and self.closure_mode == 'units':
                break
            while True:
                active = [i for i, item in enumerate(candidates)
                          if i not in rejected and 0 < len(item[3]) <= width]
                if not any(len(candidates[i][3]) == width for i in active):
                    break
                # Match the eager gate's first opposite-unit pair, including
                # the last preceding duplicate support for its other polarity.
                units = {}
                pair = None
                if width == 1:
                    for index in active:
                        lit = candidates[index][3][0]
                        units[lit] = index
                        if -lit in units:
                            pair = [units[lit], units[-lit]]
                            break
                if c['tentative_graph_checks'] >= self.graph_checks:
                    c['graph_limit_misses'] += 1
                    return None
                c['tentative_graph_checks'] += 1
                if pair is not None:
                    graph = sorted({candidates[i][3] for i in pair})
                    tier = 'opposite_units'
                else:
                    graph = sorted(original | {candidates[i][3] for i in active})
                    tier = 'unit_binary' if width == 1 else 'binary_guards'
                    c['graph_calls'] += 1
                c['graph_clauses'] += len(graph)
                _, proof = native.two_cnf(graph, c)
                if proof is None:
                    c['tentative_satisfiable_graphs'] += 1
                    break
                c['tentative_contradictions'] += 1
                paths = (proof['forward'], proof['backward'])
                if any(len(path) > self.path_limit for path in paths):
                    c['path_limit_misses'] += 1
                    return None
                if c['reserved_edges'] + sum(map(len, paths)) > self.closure_edges:
                    c['edge_limit_misses'] += 1
                    return None
                # Original edges need no transported hint. Keep all alternative
                # supports for each proposed guard clause until one checks.
                used = {graph[cid] for path in paths for _, cid in path} - original
                hints = []
                failed = False
                for clause in sorted(used):
                    choices = pair if pair is not None else active
                    hint = None
                    for index in choices:
                        if candidates[index][3] != clause:
                            continue
                        hint = validate(index)
                        if hint is not None:
                            break
                        if len(rejected) >= self.witness_retries:
                            c['witness_retry_limit_misses'] += 1
                            return None
                    if hint is None:
                        failed = True
                        break
                    hints.append(hint)
                if failed:
                    c['unsupported_witness_retries'] += 1
                    continue
                return self._compile_closure(cnf, hints, graph, proof, tier)
        c['inconclusive_sites'] += 1
        return None
