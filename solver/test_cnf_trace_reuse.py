from collections import Counter
import copy
from itertools import combinations, product
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from experiments.cnf_coupled_pivots import BudgetedInventory, AdmissionExhausted
from experiments.cnf_pattern_inventory import encode
from experiments.cnf_residual_dag import holds, restrict, normalize
from experiments.cnf_simplification import discover_simplification
from experiments.cnf_common_consequence import first_common_pair
from experiments.cnf_probe_equivalence import first_equivalence_pair, substitute_block
from experiments.cnf_trace_reuse import (check_pair, make_record, verify_rewrite,
    lift_rewrite, source_attempts, TraceRoutes, read_attempt)
from experiments.cnf_route_composition import compose, verify_plan
from experiments.cnf_residual_dag import ResidualSolver


class TraceReuseTests(unittest.TestCase):
    def test_small_pair_implications_and_substitution_fibers(self):
        clauses = [tuple(v*s for v,s in zip(vs, signs)) for width in (2,3)
                   for vs in combinations((1,2,3), width) for signs in product((-1,1), repeat=width)]
        used = Counter()
        for size in range(1,4):
            for cnf in combinations(clauses, size):
                for variable in sorted({abs(l) for c in cnf for l in c}):
                    attempts = [dict(variable=variable, value=b, certificate=discover_simplification(
                        restrict(cnf, {variable:b}, Counter()), Counter(), pure=False)) for b in (False,True)]
                    if any(a['certificate']['conflict'] is not None for a in attempts): continue
                    check_pair(cnf, attempts, Counter())
                    common = first_common_pair(attempts, Counter())
                    equiv = first_equivalence_pair(attempts, Counter())
                    for values in product((False,True), repeat=3):
                        model = dict(zip((1,2,3), values))
                        if common and holds(cnf, model):
                            self.assertTrue(all(model[abs(l)] == (l>0) for l in common['literals']))
                            used['common'] += 1
                        if equiv:
                            target = substitute_block(cnf, equiv, Counter())
                            lifted = dict(model)
                            for v, rep in equiv['mapping']:
                                lifted[v] = model[abs(rep)] if rep>0 else not model[abs(rep)]
                            self.assertEqual(holds(target, model), holds(cnf, lifted))
                            if holds(cnf, model):
                                self.assertEqual(model, lifted)
                            used['equivalence'] += 1
        self.assertGreater(used['common'],0); self.assertGreater(used['equivalence'],0)

    def history(self, path):
        fixture = json.loads(Path('solver/fixtures/trace-reuse.json').read_text())
        h = BudgetedInventory(path, **fixture['options']); h.set_admission_budget(32)
        for table in ('cnf_pivot_trials_v1','cnf_coupled_trials_v1','cnf_growth_trials_v1',
                      'cnf_probe_windows_v1','cnf_probe_continuations_v1'):
            h.db.execute(f'CREATE TABLE IF NOT EXISTS {table} (id TEXT PRIMARY KEY,payload TEXT NOT NULL)')
        self.assertEqual(h._edge(fixture['cnf'], fixture['depth'])['key'], fixture['source'])
        with h.db:
            for b in fixture['blocks']:
                h.db.execute(f"INSERT OR IGNORE INTO {b['table']} VALUES (?,?)", (b['id'], encode(b['payload'])))
        return h, fixture

    def test_pending_target_restart_and_model_lift_without_rediscovery(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td)/'history'; h,f = self.history(path); h.set_admission_budget(0)
            record = make_record(h, f['source'], f['record']['references'], Counter())
            self.assertEqual(record, f['record']); target,_ = verify_rewrite(h,record,Counter())
            routes = TraceRoutes(h,[record]); self.assertNotIn(f['source'],routes.by_source)
            with self.assertRaises(AdmissionExhausted): h._edge(target,f['depth'])
            self.assertFalse(compose(h,[f['source']],routes,Counter())[0][0]); h.close()
            h,f = self.history(path); h.set_admission_budget(32)
            self.assertEqual(h._edge(target,f['depth']),record['edge'])
            routes = TraceRoutes(h,[record]); closed,plan = compose(h,[f['source']],routes,Counter())
            verify_plan(h,plan,[f['source']] if closed[0] else [],routes,Counter())
            child = h._load(record['edge']['key']); solver = ResidualSolver()
            answer = solver.solve(child['cnf'])
            if answer['answer']:
                model = lift_rewrite(h,record,answer['model'],Counter()); self.assertTrue(holds(f['cnf'],model))
            solver.close(); h.close(); before = path.read_bytes()
            h,f = self.history(path); h.set_admission_budget(0)
            with patch('experiments.cnf_failed_literal.discover_probes',side_effect=AssertionError('new probe')):
                routes = TraceRoutes(h,[record]); verify_rewrite(h,record,Counter())
            self.assertEqual(compose(h,[f['source']],routes,Counter())[0],closed)
            h.close(); self.assertEqual(path.read_bytes(),before)

    def test_tampered_refs_pair_reasons_and_residual_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            h,f = self.history(Path(td)/'history'); record=f['record']; bads=[]
            for field,value in [('table','cnf_residual_v1'),('id','missing'),('index',True),('index',999),('index',-1)]:
                bad=copy.deepcopy(record); bad['references'][0][field]=value; bads.append(bad)
            bad=copy.deepcopy(record); bad['references'].reverse(); bads.append(bad)
            bad=copy.deepcopy(record); bad['references'][1]=bad['references'][0]; bads.append(bad)
            bad=copy.deepcopy(record); bad['reduction']['witness']['mapping'][1][1]*=-1; bads.append(bad)
            bad=copy.deepcopy(record); bad['edge']['names'].reverse(); bads.append(bad)
            bad=copy.deepcopy(record); bad['edge']['key']=f['source']; bads.append(bad)
            for bad in bads:
                with self.assertRaises(ValueError): verify_rewrite(h,bad,Counter())
            ref=record['references'][0]; payload=json.loads(h.db.execute(f"SELECT payload FROM {ref['table']} WHERE id=?",(ref['id'],)).fetchone()[0])
            payload['probing']['attempts'][ref['index']]['certificate']['units'][0][1]=99999
            with h.db: h.db.execute(f"UPDATE {ref['table']} SET payload=? WHERE id=?",(encode(payload),ref['id']))
            with self.assertRaises(ValueError): verify_rewrite(h,record,Counter())
            h.close()

    def test_scan_uses_source_only_and_keeps_exact_references(self):
        with tempfile.TemporaryDirectory() as td:
            h,f = self.history(Path(td)/'history'); counts=Counter()
            attempts,refs=source_attempts(h,f['source'],counts)
            self.assertEqual(len(attempts),32)
            for a,ref in zip(attempts,refs): self.assertEqual(read_attempt(h,f['source'],ref,Counter()),a)
            pair=first_equivalence_pair(attempts,Counter())['pair']
            self.assertEqual(make_record(h,f['source'],refs[2*pair:2*pair+2],Counter()),f['record'])
            self.assertEqual(counts['exhaustion_checked_attempts'],32); h.close()


if __name__ == '__main__': unittest.main()
