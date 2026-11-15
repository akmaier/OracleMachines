"""Recognize already canonical CNFs before repeating sorting and renaming.

Every accepted source is scanned. No result, certificate or mutable-object
identity is trusted. Other inputs retain the original normalization semantics.
This changes representation work only, not recognition or acquisition policy.
"""
from types import MethodType

from experiments.cnf_residual_dag import normalize
from experiments.cnf_pattern_inventory import FORMAT, encode
from experiments.cnf_coupled_pivots import BudgetedInventory


def canonical_source(cnf, counts):
    """Return the original normal form and names, with a checked linear fast path."""
    counts['canonical_precheck_calls'] += 1
    if type(cnf) not in (list, tuple):
        counts['canonical_fallback_calls'] += 1
        return normalize(cnf, counts)
    clauses = []
    support = set()
    previous_clause = None
    visits = 0
    valid = True
    for clause in cnf:
        if type(clause) not in (list, tuple):
            valid = False
            break
        current = tuple(clause)
        # Validate elements before tuple comparison: unusual elements can have
        # user-defined comparison semantics that the original path never calls.
        previous_literal = None
        local = set()
        for literal in current:
            visits += 1
            if type(literal) is not int or not literal:
                valid = False
                break
            variable = abs(literal)
            if ((previous_literal is not None and literal <= previous_literal)
                    or variable in local):
                valid = False
                break
            previous_literal = literal
            local.add(variable)
            support.add(variable)
        if not valid:
            break
        if (previous_clause is not None and current <= previous_clause) or (not current and len(cnf) != 1):
            valid = False
            break
        clauses.append(current)
        previous_clause = current
    counts['canonical_precheck_literal_visits'] += visits
    if valid and (not support or max(support) == len(support)):
        # All variables are positive integers in 1..max(support). Equal size
        # proves there are no gaps, so the old sorted renaming is the identity.
        counts['canonical_order_reuses'] += 1
        counts['canonical_reused_literal_slots'] += visits
        return tuple(clauses), tuple(range(1, len(support) + 1))
    counts['canonical_fallback_calls'] += 1
    return normalize(cnf, counts)


def canonical_key(view, cnf, depth):
    normalized, names = canonical_source(cnf, view.counts)
    key = encode([FORMAT, view.config, depth, normalized])
    view.counts['key_serialized_bytes'] += len(key.encode())
    return normalized, list(names), key


class CanonicalSourceInventory(BudgetedInventory):
    """Same keys and certificates in both policy views, with independent scans."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.prepared._canonical = MethodType(canonical_key, self.prepared)

    _canonical = canonical_key
