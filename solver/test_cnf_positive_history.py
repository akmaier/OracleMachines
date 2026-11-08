"""Checked delta histories: exact source replay, cold checks and invalidation."""
import itertools
import json
from pathlib import Path
import tempfile
import unittest

from experiments.cnf_positive_history import PositiveHistory, UnsupportedExpansion
from experiments.cnf_residual_dag import holds
from experiments.compare_cnf_matching import domain_cnf
from experiments.compare_cnf_residuals import pigeonhole


class PositiveHistoryTests(unittest.TestCase):
    def test_sat_unsat_and_sparse_source_names(self):
        for base, expected in ((pigeonhole(3), False), (domain_cnf([range(3)] * 3), True),
                               ([(3, 900), (-3, -900)], True)):
            with tempfile.TemporaryDirectory() as temporary:
                path = Path(temporary) / "history.sqlite3"
                history = PositiveHistory(path)
                initial = history.prepare(base)
                source, version = list(map(tuple, base)), initial["version"]
                for step in range(1, 9):
                    clause = tuple(base[0]) + (10000 + step,)
                    result = history.append(version, clause)
                    version = result["version"]
                    source.append(clause)
                    self.assertEqual(result["answer"], expected)
                    self.assertEqual(result["metrics"].get("verified_versions"), 1)
                    self.assertEqual(result["metrics"].get("index_build_literal_payload", 0), 0)
                    self.assertEqual(result["solver_metrics"], {})
                    self.assertEqual(history.materialize(version)["cnf"], tuple(source))
                    if expected:
                        self.assertTrue(holds(source, history.witness(version)["model"]))
                old = list(history.db.iterdump())
                history.close()
                history = PositiveHistory(path)
                cold = history.query(version)
                self.assertEqual(cold["answer"], expected)
                self.assertEqual(cold["metrics"]["verified_versions"], 9)
                self.assertEqual(cold["metrics"]["verified_bases"], 1)
                self.assertEqual(history.materialize(version)["cnf"], tuple(source))
                self.assertEqual(list(history.db.iterdump()), old)
                history.close()

    def test_all_models_preserved_for_positive_extensions(self):
        base = [(1, 2), (-1, -2)]
        history = PositiveHistory()
        root = history.prepare(base)["version"]
        for size in range(1, 5):
            for clause in itertools.combinations(range(1, 5), size):
                if {1, 2}.issubset(clause):
                    version = history.append(root, clause)["version"]
                    source = history.materialize(version)["cnf"]
                    for values in itertools.product((False, True), repeat=4):
                        assignment = dict(zip(range(1, 5), values))
                        self.assertEqual(holds(base, assignment), holds(source, assignment))
                else:
                    before = list(history.db.iterdump())
                    with self.assertRaises(UnsupportedExpansion):
                        history.append(root, clause)
                    self.assertEqual(before, list(history.db.iterdump()))
        history.close()

    def test_forks_repeated_operations_and_original_rows(self):
        history = PositiveHistory()
        root = history.prepare([(1, 2), (-1, -2)])["version"]
        old = list(history.db.execute("SELECT * FROM cnf_residual_v1"))
        self.assertEqual(history.prepare([(1, 2), (-1, -2)])["version"], root)
        a = history.append(root, [1, 2, 3])["version"]
        b = history.append(root, [2, 1, 4, 4])["version"]
        self.assertNotEqual(a, b)
        repeated = history.append(root, [1, 2, 3])
        self.assertEqual(repeated["version"], a)
        self.assertEqual(repeated["metrics"].get("inserted_versions", 0), 0)
        self.assertEqual(history.materialize(a)["cnf"][-1], (1, 2, 3))
        self.assertEqual(history.materialize(b)["cnf"][-1], (2, 1, 4, 4))
        self.assertEqual(history.materialize(root)["cnf"], ((1, 2), (-1, -2)))
        self.assertEqual(old, list(history.db.execute("SELECT * FROM cnf_residual_v1")))
        history.close()

    def test_changed_constraints_require_a_new_base(self):
        history = PositiveHistory()
        root = history.prepare([(1, 2), (-1,), (-2,)])["version"]
        self.assertFalse(history.query(root)["answer"])
        # Removing a supporting choice changes UNSAT to SAT. It cannot be
        # represented by append; a freshly solved base gets a different ID.
        new = history.prepare([(-1,), (-2,)])["version"]
        self.assertTrue(history.query(new)["answer"])
        with self.assertRaises(UnsupportedExpansion):
            history.append(new, [1, 2, 3])
        self.assertFalse(history.query(root)["answer"])
        for invalid in ([], [0], [True], [1.0], [-1, 2], "12"):
            before = list(history.db.iterdump())
            with self.assertRaises(ValueError):
                history.append(root, invalid)
            self.assertEqual(before, list(history.db.iterdump()))
        for invalid in (True, 0, -1, 1.0, 10000):
            with self.assertRaises(ValueError):
                history.query(invalid)
        history.close()

    def test_cold_tampering_is_rejected(self):
        mutations = ("witness", "clause", "cycle", "foreign_base", "source_root", "base_model")
        for mutation in mutations:
            with tempfile.TemporaryDirectory() as temporary:
                path = Path(temporary) / "history.sqlite3"
                history = PositiveHistory(path)
                root = history.prepare([(1, 2, 3), (-1, -2, -3)])["version"]
                other = history.prepare([(4, 5), (-4, -5)])["version"]
                version = history.append(root, [1, 2, 3, 4])["version"]
                base_id = history.checked[root][0]
                with history.db:
                    if mutation in ("witness", "clause"):
                        payload = json.loads(history.db.execute(
                            "SELECT payload FROM cnf_positive_versions_v1 WHERE id=?", (version,)).fetchone()[0])
                        payload.update(witness=1) if mutation == "witness" else payload.update(clause=[3, 4])
                        history.db.execute("UPDATE cnf_positive_versions_v1 SET payload=? WHERE id=?", (json.dumps(payload), version))
                    elif mutation == "cycle":
                        history.db.execute("UPDATE cnf_positive_versions_v1 SET parent=? WHERE id=?", (version, version))
                    elif mutation == "foreign_base":
                        history.db.execute("UPDATE cnf_positive_versions_v1 SET parent=? WHERE id=?", (other, version))
                    else:
                        payload = json.loads(history.db.execute(
                            "SELECT payload FROM cnf_positive_bases_v1 WHERE id=?", (base_id,)).fetchone()[0])
                        if mutation == "source_root":
                            payload["source"].append([-1])
                            history.db.execute("UPDATE cnf_positive_bases_v1 SET payload=? WHERE id=?", (json.dumps(payload), base_id))
                        else:
                            node = json.loads(history.db.execute("SELECT payload FROM cnf_residual_v1 WHERE id=?", (payload["root"],)).fetchone()[0])
                            node["model"] = [False] * 3
                            history.db.execute("UPDATE cnf_residual_v1 SET payload=? WHERE id=?", (json.dumps(node), payload["root"]))
                history.close()
                history = PositiveHistory(path)
                with self.assertRaises(ValueError, msg=mutation):
                    history.query(version)
                history.close()

    def test_long_cold_chain_and_constant_warm_base_work(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "history.sqlite3"
            history = PositiveHistory(path)
            version = history.prepare([(1, 2), (-1, -2)])["version"]
            for step in range(1200):
                result = history.append(version, [1, 2, 10 + step])
                version = result["version"]
                self.assertEqual(result["metrics"]["containment_probes"], 2)
                self.assertEqual(result["metrics"]["verified_versions"], 1)
                self.assertEqual(result["solver_metrics"], {})
            history.close()

            history = PositiveHistory(path)
            result = history.query(version)
            self.assertTrue(result["answer"])
            self.assertEqual(result["metrics"]["verified_versions"], 1201)
            self.assertEqual(result["metrics"]["verified_bases"], 1)
            warm = history.query(version)
            self.assertEqual(warm["metrics"], {"version_memory_hits": 1})
            history.close()

    def test_decision_rules_exhaustive_small_clauses(self):
        literals = (1, -1, 2, -2, 3, -3)
        clauses = [c for n in range(7) for c in itertools.combinations(literals, n)]
        for base in ([], [(1, 2)], [(1, 2), (-1, -2)], [(1,), (-1,)], [()]):
            history = PositiveHistory()
            initial = history.prepare(base)
            root, answer = initial["version"], initial["answer"]
            model = history.witness(root)["model"]
            for clause in clauses:
                before = list(history.db.iterdump())
                if answer and not holds([clause], model):
                    with self.assertRaises(UnsupportedExpansion):
                        history.append_decision(root, clause)
                    self.assertEqual(before, list(history.db.iterdump()))
                    continue
                result = history.append_decision(root, clause)
                source = history.materialize(result["version"])["cnf"]
                self.assertEqual(source, tuple(map(tuple, base)) + (clause,))
                actual = any(holds(source, dict(zip((1, 2, 3), values)))
                             for values in itertools.product((False, True), repeat=3))
                self.assertEqual(result["answer"], actual)
                self.assertEqual(result["solver_metrics"], {})
                self.assertEqual(result["metrics"].get("containment_probes", 0), 0)
                if answer:
                    self.assertTrue(holds(source, model))
            history.close()

    def test_model_failure_is_not_unsat_and_models_can_shrink(self):
        history = PositiveHistory()
        root = history.prepare([(1, 2)])["version"]
        model = history.witness(root)["model"]
        true_var = next(v for v in (1, 2) if model[v])
        accepted = history.append_decision(root, [true_var])["version"]
        # This removes a different base model: decision reuse is not equivalence.
        alternative = {1: True, 2: True, true_var: False}
        self.assertTrue(holds([(1, 2)], alternative))
        self.assertFalse(holds(history.materialize(accepted)["cnf"], alternative))
        with self.assertRaises(UnsupportedExpansion):
            history.append_decision(root, [-true_var])
        self.assertTrue(history.prepare([(1, 2), (-true_var,)])["answer"])
        # Fresh variables are false in the total extension, even with sparse IDs.
        good = history.append_decision(root, [-10**20])["version"]
        self.assertTrue(holds(history.materialize(good)["cnf"], history.witness(good)["model"]))
        with self.assertRaises(UnsupportedExpansion):
            history.append_decision(good, [10**20])
        with self.assertRaises(UnsupportedExpansion):
            history.append_decision(root, [])
        history.close()

    def test_decision_mixed_protocols_replay_and_invalid_tail(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "history.sqlite3"
            history = PositiveHistory(path)
            root = history.prepare([(1, 2), (-1, -2)])["version"]
            legacy = history.append(root, [2, 1, 3])["version"]
            first = history.append_decision(legacy, [-900, -900])["version"]
            last = history.append(first, [1, 2, 4])["version"]
            self.assertEqual(history.append_decision(legacy, [-900, -900])["version"], first)
            for invalid in ([-900, 0], [-900, True], [-900, 1.0], "12", None):
                before = list(history.db.iterdump())
                with self.assertRaises(ValueError):
                    history.append_decision(last, invalid)
                self.assertEqual(before, list(history.db.iterdump()))
            source = history.materialize(last)["cnf"]
            before = list(history.db.iterdump())
            history.close()
            history = PositiveHistory(path)
            self.assertTrue(history.query(last)["answer"])
            self.assertEqual(history.materialize(last)["cnf"], source)
            self.assertTrue(holds(source, history.witness(last)["model"]))
            self.assertEqual(before, list(history.db.iterdump()))
            history.close()

    def test_decision_cold_forgery_rejected(self):
        for mutation in ("false_model", "unsat_on_sat", "model_on_unsat", "invalid_tail", "cross_base"):
            with tempfile.TemporaryDirectory() as temporary:
                path = Path(temporary) / "history.sqlite3"
                history = PositiveHistory(path)
                sat = history.prepare([(1,)])["version"]
                unsat = history.prepare([(2,), (-2,)])["version"]
                root = unsat if mutation == "model_on_unsat" else sat
                version = history.append_decision(root, [-900])["version"]
                payload = json.loads(history.db.execute(
                    "SELECT payload FROM cnf_positive_versions_v1 WHERE id=?", (version,)).fetchone()[0])
                if mutation == "false_model":
                    payload["clause"] = [-1]
                elif mutation == "unsat_on_sat":
                    payload["kind"] = "append-unsat"
                elif mutation == "model_on_unsat":
                    payload["kind"] = "append-model"
                elif mutation == "invalid_tail":
                    payload["clause"] = [-900, 0]
                with history.db:
                    history.db.execute("UPDATE cnf_positive_versions_v1 SET payload=? WHERE id=?",
                                       (json.dumps(payload), version))
                    if mutation == "cross_base":
                        history.db.execute("UPDATE cnf_positive_versions_v1 SET parent=? WHERE id=?", (unsat, version))
                history.close()
                history = PositiveHistory(path)
                with self.assertRaises(ValueError, msg=mutation):
                    history.query(version)
                history.close()

    def test_long_unsat_decision_history(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "history.sqlite3"
            history = PositiveHistory(path)
            version = history.prepare([(1,), (-1,)])["version"]
            for step in range(1200):
                clause = ([], [-step - 2], [step + 2], [step + 2, -step - 2])[step % 4]
                result = history.append_decision(version, clause)
                self.assertFalse(result["answer"])
                self.assertEqual(result["solver_metrics"], {})
                self.assertEqual(result["metrics"].get("model_literal_probes", 0), 0)
                self.assertEqual(result["metrics"].get("containment_probes", 0), 0)
                version = result["version"]
            before = list(history.db.iterdump())
            history.close()
            history = PositiveHistory(path)
            result = history.query(version)
            self.assertFalse(result["answer"])
            self.assertEqual(result["metrics"]["verified_versions"], 1201)
            self.assertEqual(result["metrics"]["unsat_extension_checks"], 1200)
            self.assertEqual(before, list(history.db.iterdump()))
            history.close()


if __name__ == "__main__":
    unittest.main()
