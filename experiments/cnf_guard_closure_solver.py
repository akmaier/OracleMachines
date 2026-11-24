"""Optional local closure from supported short guards at ordinary probe sites.

The consequence graph never supplies a SAT verdict. Negative paths compile to
the existing source-bound unit/split certificates. All misses retain ordinary
probe selection; tracking requires an exclusive synchronous session.
"""
from collections import Counter
from experiments import cnf_residual_dag as native
from experiments.cnf_guard_probe_solver import GuardProbeSolver
from experiments.cnf_guard_interactions import compile_path
from experiments.cnf_conditional_unit_support import check_template
from experiments.cnf_hint_transport import check_rup
from experiments.cnf_partial_residual_pool import charge


class _LocalClosure(Exception):
    def __init__(self, proof):
        self.proof = proof


def transport_short(cnf, template, missing, parent, counts):
    """Transport a query-validated support, checking the actual local clauses."""
    inverse = {v: k for k, v in parent['mapping'].items()}
    if any(v not in inverse for v, _ in missing):
        counts['absent_guard_variables'] += 1
        return None
    fixed = parent['fixed']
    positions = {cl: i for i, cl in enumerate(cnf)}
    counts['position_clauses'] += len(cnf)
    translated = []
    for clause in template['clauses']:
        reduced = []
        for lit in clause:
            counts['support_literal_visits'] += 1
            if abs(lit) in fixed:
                if fixed[abs(lit)] == (lit > 0):
                    reduced = None
                    break
            elif abs(lit) not in inverse:
                counts['local_support_misses'] += 1
                return None
            else:
                reduced.append(inverse[abs(lit)] * (1 if lit > 0 else -1))
        result = None if reduced is None else tuple(sorted(reduced))
        if result is not None and result not in positions:
            counts['local_support_misses'] += 1
            return None
        translated.append(result)
    clauses = sorted({cl for cl in translated if cl is not None})
    ids = {cl: i for i, cl in enumerate(clauses)}
    trace = []
    conflict = None
    for lit, cid in template['trace']:
        counts['trace_steps'] += 1
        if abs(lit) in fixed:
            if fixed[abs(lit)] == (lit > 0):
                continue
            conflict = ids[translated[cid]]
            break
        trace.append([inverse[abs(lit)] * (1 if lit > 0 else -1), ids[translated[cid]]])
    if conflict is None:
        conflict = ids[translated[template['conflict']]]
    assumptions = sorted([[inverse[v], b] for v, b in missing])
    lifted = dict(clauses=[list(cl) for cl in clauses], assumptions=assumptions,
                  trace=trace, conflict=conflict)
    check_template(lifted, counts)
    clause = sorted(-v if b else v for v, b in assumptions)
    proof = dict(units=[[lit, positions[clauses[cid]]] for lit, cid in trace],
                 conflict=positions[clauses[conflict]])
    check_rup(cnf, clause, proof, counts)
    return dict(clause=clause, template=lifted, proof=proof)


class GuardClosureSolver(GuardProbeSolver):
    def __init__(self, *args, closure_mode='binary', closure_checks=100000,
                 closure_literals=1000000, closure_edges=4096, path_limit=256, **kwargs):
        if closure_mode not in ('units', 'binary'):
            raise ValueError('Invalid closure mode')
        if any(type(v) is not int or v < 1 for v in
               (closure_checks, closure_literals, closure_edges, path_limit)):
            raise ValueError('Positive closure limits required')
        if kwargs.get('guard_mode', 'tracking') != 'tracking':
            raise ValueError('Closure fallback must retain ordinary ordering')
        kwargs['guard_mode'] = 'tracking'
        self.closure_mode = closure_mode
        self.closure_checks = closure_checks
        self.closure_literals = closure_literals
        self.closure_edges = closure_edges
        self.path_limit = path_limit
        self.closure_summary = None
        super().__init__(*args, **kwargs)

    def solve(self, source):
        self.closure_counts = Counter()
        self.closure_records = None
        try:
            return super().solve(source)
        finally:
            self.closure_summary = dict(mode=self.closure_mode, counts=dict(self.closure_counts),
                bank_bytes=charge((self.guard_templates, self.closure_records)),
                limits=dict(checks=self.closure_checks, literals=self.closure_literals,
                            edges=self.closure_edges, path=self.path_limit))
            self.closure_records = None

    def _guard_choice(self, cnf, ordinary):
        proof = self._guard_closure(cnf)
        if proof is not None:
            raise _LocalClosure(proof)
        return super()._guard_choice(cnf, ordinary)

    def _expand_prepared(self, cnf):
        try:
            return super()._expand_prepared(cnf)
        except _LocalClosure as closed:
            return None, closed.proof

    def _compile_closure(self, cnf, hints, graph, proof, tier):
        c = self.closure_counts
        v = proof['variable']
        paths = {v: proof['backward'], -v: proof['forward']}
        edges = sum(map(len, paths.values()))
        if any(len(path) > self.path_limit for path in paths.values()):
            c['path_limit_misses'] += 1
            return None
        if c['reserved_edges'] + edges > self.closure_edges:
            c['edge_limit_misses'] += 1
            return None
        c['reserved_edges'] += edges
        used = {tuple(graph[cid]) for path in paths.values() for _, cid in path}
        needed = [hint for hint in hints if tuple(hint['clause']) in used]
        profile = dict(clauses=graph, paths=paths)
        low = compile_path(self, cnf, needed, profile, v, c, path_limit=self.path_limit)
        high = compile_path(self, cnf, needed, profile, -v, c, path_limit=self.path_limit)
        c['closed_' + tier] += 1
        return dict(kind='split', variable=v, low=low, high=high)

    def _guard_closure(self, cnf):
        c = self.closure_counts
        c['sites'] += 1
        parent = self.guard_parents[-1] if self.guard_parents else None
        if parent is None or parent['cnf'] is not cnf:
            c['unbound_sites'] += 1
            return None
        if self.closure_records is None:
            # GuardProbeSolver checked every template at query entry.
            members = set(self.guard_source)
            self.closure_records = []
            for template in self.guard_templates:
                c['source_support_clauses'] += len(template['clauses'])
                if all(tuple(cl) in members for cl in template['clauses']):
                    self.closure_records.append((template, sum(map(len, template['clauses']))))
        candidates = {0: [], 1: [], 2: []}
        fixed = parent['fixed']
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
            if compatible and len(missing) <= (2 if self.closure_mode == 'binary' else 1):
                candidates[len(missing)].append((template, size, missing))
        hints = []
        units = {}
        for width in (0, 1, 2):
            if width == 2 and self.closure_mode == 'units':
                break
            before = len(hints)
            for template, size, missing in candidates[width]:
                if c['reserved_support_literals'] + size > self.closure_literals:
                    c['literal_limit_misses'] += 1
                    continue
                c['reserved_support_literals'] += size
                hint = transport_short(cnf, template, missing, parent, c)
                if hint is None:
                    continue
                hints.append(hint)
                c['accepted_width_' + str(width)] += 1
                if width == 0:
                    c['closed_empty'] += 1
                    return dict(kind='units', trace=hint['proof']['units'], conflict=hint['proof']['conflict'])
                if width == 1:
                    lit = hint['clause'][0]
                    units[lit] = hint
                    if -lit in units:
                        graph = sorted([(lit,), (-lit,)])
                        _, proof = native.two_cnf(graph, c)
                        return self._compile_closure(cnf, [units[lit], units[-lit]], graph, proof, 'opposite_units')
            if width and len(hints) > before:
                graph = sorted(set(cl for cl in cnf if len(cl) <= 2) |
                               {tuple(h['clause']) for h in hints})
                c['graph_calls'] += 1
                c['graph_clauses'] += len(graph)
                _, proof = native.two_cnf(graph, c)
                if proof is not None:
                    return self._compile_closure(cnf, hints, graph, proof, 'unit_binary' if width == 1 else 'binary_guards')
        c['inconclusive_sites'] += 1
        return None
