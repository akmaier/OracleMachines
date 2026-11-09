"""Independent one-pass reconstruction with lazy copying of affected clauses.

There is no retained cache or discovery-index dependency. Exact built-in clauses
are inspected directly. A falsified occurrence triggers a prefix copy; untouched
tuple clauses are shared. Unusual inputs fall back to the original checker scan.
"""
from experiments.cnf_simplification import reconstruct_simplification_scan


def reconstruct_single_pass(cnf, assigned, counts, *, units):
    if (type(assigned) is not dict or any(type(v) is not int or v <= 0 or type(b) is not bool
                                        for v, b in assigned.items())):
        counts['single_check_fallback_calls'] += 1
        return reconstruct_simplification_scan(cnf, assigned, counts, units=units)
    counts['single_check_calls'] += 1
    counts['single_check_assignment_entries'] += len(assigned)
    current = []
    positions = visited = shared = shared_literals = rebuilt = copied = dropped = fallbacks = 0
    try:
        for clause in cnf:
            positions += 1
            if type(clause) not in (tuple, list):
                fallbacks += 1
                current.extend(reconstruct_simplification_scan((clause,), assigned, counts, units=units))
                continue
            residual = None
            satisfied = unusual = False
            for i, lit in enumerate(clause):
                visited += 1
                if type(lit) is not int or not lit:
                    unusual = True
                    break
                value = assigned.get(abs(lit))
                if value is None:
                    if residual is not None:
                        residual.append(lit)
                        copied += 1
                elif value == (lit > 0):
                    satisfied = True
                    break
                elif residual is None:
                    residual = list(clause[:i])
                    copied += i
            if unusual:
                fallbacks += 1
                current.extend(reconstruct_simplification_scan((clause,), assigned, counts, units=units))
                continue
            if satisfied:
                dropped += 1
                continue
            if residual is None:
                result = tuple(clause)
                if type(clause) is tuple:
                    shared += 1
                    shared_literals += len(clause)
                else:
                    copied += len(clause)
            else:
                result = tuple(residual)
                rebuilt += 1
            if units and len(result) <= 1:
                raise ValueError('Incomplete unit fixed point')
            current.append(result)
    finally:
        counts.update(single_check_clause_positions=positions, single_check_literal_visits=visited,
                      single_check_shared_clauses=shared, single_check_shared_literals=shared_literals,
                      single_check_rebuilt_clauses=rebuilt, single_check_copied_literals=copied,
                      single_check_dropped_clauses=dropped, single_check_fallback_clauses=fallbacks)
    return current
