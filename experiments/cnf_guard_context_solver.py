"""Reuse immutable source preparation across a selected guard witness.

The local context is created lazily within one _guard_closure call, never stored
on the solver or in a certificate. Every clause, unit reason and conflict is
still checked. Frozen native readers remain independent publication authority.
"""
from dataclasses import dataclass
from types import MappingProxyType
from experiments import cnf_residual_dag as native
from experiments.cnf_pattern_inventory import encode
from experiments.cnf_conditional_unit_support import check_template
from experiments.cnf_guard_support_solver import SupportGuardClosureSolver


@dataclass(frozen=True, slots=True)
class LocalContext:
    core: tuple
    positions: object
    inverse: object
    fixed: object
    variables: int

    @classmethod
    def prepare(cls, cnf, parent, counts):
        if parent['cnf'] is not cnf:
            raise ValueError('Context must bind the current local source')
        core = tuple(tuple(cl) for cl in cnf)
        canonical, names = native.normalize(core, counts)
        if encode(core) != encode(canonical) or names != tuple(range(1, len(names)+1)):
            raise ValueError('Hint source must be the exact normalized core')
        positions = {cl: i for i, cl in enumerate(core)}
        counts['position_clauses'] += len(core)
        counts['context_preparations'] += 1
        counts['context_literal_slots'] += sum(map(len, core))
        counts['context_peak_clause_slots'] = max(counts['context_peak_clause_slots'], len(core))
        counts['context_peak_literal_slots'] = max(counts['context_peak_literal_slots'], sum(map(len, core)))
        return cls(core, MappingProxyType(positions),
                   MappingProxyType({v: k for k, v in parent['mapping'].items()}),
                   MappingProxyType(dict(parent['fixed'])), len(names))


def check_bound_rup(context, clause, proof, counts):
    """Check each reason against the immutable source validated by prepare.

    Contexts are local implementation state, not portable proof authority.
    Reason indices refer to the original normalized core, not a restricted list.
    """
    core = context.core
    if (any(type(l) is not int or not l or not 1 <= abs(l) <= context.variables for l in clause)
            or list(clause) != sorted(set(clause)) or any(-l in clause for l in clause)):
        raise ValueError('Invalid core hint clause')
    counts['context_hint_checks'] += 1
    if not isinstance(proof, dict) or set(proof) != {'units', 'conflict'}:
        raise ValueError('Invalid core hint proof fields')
    assigned = {abs(l): l < 0 for l in clause}
    if not isinstance(proof['units'], list):
        raise ValueError('Invalid hint unit sequence')
    for entry in proof['units']:
        if not isinstance(entry, (list, tuple)) or len(entry) != 2:
            raise ValueError('Invalid hint unit entry')
        lit, cid = entry
        if (type(lit) is not int or not lit or abs(lit) in assigned or
                type(cid) is not int or not 0 <= cid < len(core)):
            raise ValueError('Invalid hint unit reason')
        reason = core[cid]
        counts['hint_check_literals'] += len(reason)
        if lit not in reason or any(abs(other) not in assigned or assigned[abs(other)] == (other > 0)
                                   for other in reason if other != lit):
            raise ValueError('Hint step is not forced by its core')
        assigned[abs(lit)] = lit > 0
    conflict = proof['conflict']
    if type(conflict) is not int or not 0 <= conflict < len(core):
        raise ValueError('Invalid hint conflict index')
    counts['hint_check_literals'] += len(core[conflict])
    if any(abs(l) not in assigned or assigned[abs(l)] == (l > 0) for l in core[conflict]):
        raise ValueError('Hint trace does not refute its negation')
    counts['verified_core_hints'] += 1


def transport_bound(context, template, missing, counts):
    """Transport a query-validated support, checking the actual local clauses."""
    inverse = context.inverse
    if any(v not in inverse for v, _ in missing):
        counts['absent_guard_variables'] += 1
        return None
    fixed = context.fixed
    positions = context.positions
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
    check_bound_rup(context, clause, proof, counts)
    return dict(clause=clause, template=lifted, proof=proof)


class ContextGuardClosureSolver(SupportGuardClosureSolver):
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
        context = None

        def validate(index):
            nonlocal context
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
            if context is None:
                context = LocalContext.prepare(cnf, parent, c)
            hint = transport_bound(context, template, missing, c)
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
