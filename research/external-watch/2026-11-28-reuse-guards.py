"""Independent finite checks for the 28 November external research watch.

Run from any directory with Python 3; stdout is deterministic JSON. No external
code is executed. Truth enumeration does not use the OracleMachines solver;
the existing resolution checker is used only for the explicit guard control.
This is not a verification of the external general circuit theorem.
"""

import hashlib
import itertools
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from experiments import cnf_resolution_learning as resolution


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def models(cnf, n):
    return [
        list(bits)
        for bits in itertools.product((0, 1), repeat=n)
        if all(any(bits[abs(lit) - 1] == (lit > 0) for lit in clause)
               for clause in cnf)
    ]


def reuse_guard():
    source = [[1, 2]]
    added = [1]
    edit = [-1]
    cases = {
        "source": source,
        "source_with_added_clause": source + [added],
        "edited_target": source + [edit],
        "target_with_unsafe_reuse": source + [edit, added],
    }
    tables = {key: {"cnf": cnf, "models_x_y": models(cnf, 2)}
              for key, cnf in cases.items()}
    require([len(row["models_x_y"]) for row in tables.values()] == [3, 2, 1, 0],
            "Satisfiability-preserving reuse counterexample changed")
    require(all(-added[0] not in clause for clause in source),
            "The source-side RAT pivot condition must be vacuous")
    require(any(-added[0] in clause for clause in cases["edited_target"]),
            "The target must invalidate the vacuous pivot condition")
    forged = dict(format=resolution.FORMAT, kind="unknown", witness=None,
                  derivations=[[0, [], added]], conclusion=None)
    try:
        resolution.check_result(source, forged)
    except ValueError as error:
        rejection = str(error)
    else:
        raise AssertionError("The resolution checker accepted a non-consequence")
    require(rejection == "Changed learned clause", "Unexpected rejection reason")

    # A valid resolution consequence remains safe under every two-variable
    # strengthening. Include the empty clause, units and all binary clauses.
    safe_source = [[-1, 2], [1, 2]]
    safe_clause = [2]
    checked = dict(format=resolution.FORMAT, kind="unknown", witness=None,
                   derivations=[[0, [[1, 1]], safe_clause]], conclusion=None)
    resolution.check_result(safe_source, checked)
    clauses = [[sign * var for var, sign in enumerate(signs, 1) if sign]
               for signs in itertools.product((-1, 0, 1), repeat=2)]
    strengthenings = 0
    for included in itertools.product((False, True), repeat=len(clauses)):
        target = safe_source + [c for c, keep in zip(clauses, included) if keep]
        require(models(target, 2) == models(target + [safe_clause], 2),
                "An entailed clause changed a strengthened model set")
        strengthenings += 1
    return {
        "cases": tables,
        "source_rat_on_x": "vacuous: no source clause contains NOT x",
        "target_rat_on_x": "fails: the resolvent with NOT x is empty; target is SAT",
        "entailed_by_source": False,
        "forged_resolution_rejection": rejection,
        "safe_control": {"source": safe_source, "entailed_clause": safe_clause,
                         "proof": checked, "checked_strengthenings": strengthenings},
        "scope": "Counterexample to unguarded transport of a SAT-preserving addition; not a bug in either implementation.",
    }


def monotone_obstructions():
    """Exhaust t=1,r=0 specifications, using independent full-table search."""
    rows = []
    for n in range(4):
        masks = range(1 << n)
        comparable = [(a, b) for a in masks for b in masks if a & b == a]
        functions = [table for table in itertools.product((0, 1), repeat=1 << n)
                     if all(table[a] <= table[b] for a, b in comparable)]
        feasible = infeasible = 0
        # Missing samples are equivalent to {0,1}; this includes every partial
        # specification on distinct masks. All three allowed lists are closed.
        for allowed in itertools.product(((0,), (1,), (0, 1)), repeat=1 << n):
            fits = any(all(table[a] in allowed[a] for a in masks)
                       for table in functions)
            obstructions = [(a, b) for a, b in comparable
                            if allowed[a] == (1,) and allowed[b] == (0,)]
            require(fits == (not obstructions), "Two-sample characterization failed")
            if fits:
                # Explicit upward-closure construction, separate from search.
                constructed = tuple(int(any(allowed[a] == (1,) and a & b == a
                                            for a in masks)) for b in masks)
                require(constructed in functions, "Constructed function is not monotone")
                require(all(constructed[a] in allowed[a] for a in masks),
                        "Constructed function violates an allowed output")
                feasible += 1
            else:
                a, b = obstructions[0]
                require(a != b, "Obstruction must use two distinct samples")
                require(not any(table[a] == 1 and table[b] == 0 for table in functions),
                        "Claimed two-sample obstruction is feasible")
                infeasible += 1
        rows.append(dict(variables=n, input_masks=1 << n,
                         monotone_functions=len(functions),
                         specifications=feasible + infeasible,
                         feasible=feasible, infeasible=infeasible))
    require([row["monotone_functions"] for row in rows] == [2, 3, 6, 20],
            "Full truth-table enumeration failed")
    require(sum(row["specifications"] for row in rows) == 6654,
            "Specification census changed")
    return {
        "parameters": {"taps": 1, "not_gates": 0, "max_variables": 3,
                       "and_or_gate_budget": None, "constants_allowed": [0, 1]},
        "rows": rows,
        "specifications": sum(row["specifications"] for row in rows),
        "infeasible": sum(row["infeasible"] for row in rows),
        "sharp_example": {"variables": 1, "masks": [0, 1],
                          "required_outputs": [1, 0],
                          "after_deleting_mask_0": "constant 0",
                          "after_deleting_mask_1": "constant 1"},
        "scope": "Only the t=1,r=0 special case; no Lean build or general circuit-bound verification.",
    }


def main():
    checker_path = ROOT / "experiments/cnf_resolution_learning.py"
    report = {
        "date": "2026-11-28",
        "research_checkpoint": "7d3fad8d749daa3423a141c74dc362efdc02905c",
        "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "resolution_checker_sha256": hashlib.sha256(checker_path.read_bytes()).hexdigest(),
        "sources": ["https://arxiv.org/abs/2508.09851v1",
                    "https://pequalnp.com/lemma#L-lib-1313",
                    "https://github.com/JLDC/pequalnp-proofs/blob/bde913e54059b1353b142b62c9a3e618e9d2280c/lean/PEqualNP/Outside/L_lib_1313.lean"],
        "reuse_guard": reuse_guard(),
        "monotone_obstructions": monotone_obstructions(),
        "external_code_executed": False,
        "external_benchmarks_reproduced": False,
        "production_solver_changed": False,
    }
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
