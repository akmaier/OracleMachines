from collections import Counter
from copy import deepcopy
from itertools import product
import json, random, unittest
from experiments import cnf_shared_b12_preparation as c
from experiments import cnf_b10_probe_feedback as feedback
from solver.test_cnf_b12_progress_order import fixtures, study
from solver.test_cnf_shared_b10_preparation import history, close


def record(key):
    return next(r for r in fixtures() if (r['target'], r['event']) == key)


def upper_history(source, bounds=(31, 17, 23)):
    previous = history(source)
    if previous is None: return None
    original, kw = previous
    b10 = c.shared.discover(*original, **kw, counts=Counter(), probe_limit=1, trace_limit=bounds[0])
    comparison = c.shared.discover(*original, **kw, counts=Counter(), probe_limit=2, trace_limit=bounds[1])
    if any(r['program']['status'] == 'refuted' for r in (b10, comparison)): return None
    full = (*original, b10)
    prepared = feedback.prepare(*full, **kw, counts=Counter())
    cl = close(prepared[23])
    if cl is None: return None
    b11_kw = dict(**kw, next_closure=cl)
    upper = c.b11.discover(*full, **b11_kw, counts=Counter(), probe_limit=1, trace_limit=bounds[2])
    if upper['program']['status'] == 'refuted': return None
    combined = close(tuple(sorted(set(prepared[23]) | {
        (-p['assumption'],) for r in (upper, comparison) for p in r['program']['probes']})))
    return None if combined is None else ((*full, upper, comparison), dict(**b11_kw, latest_closure=combined))


class SharedB12PreparationTests(unittest.TestCase):
    def test_all_orders_results_and_banks_equal_with_one_prefix(self):
        for row in fixtures():
            args = study.arguments(row); kw = study.options(row)
            for order in ('source', 'unseen'):
                cc = Counter(); old = Counter()
                result = c.discover(*args, **kw, ordering=order, counts=cc)
                self.assertEqual(result, c.prior.discover(*args, **kw, ordering=order, counts=old))
                self.assertEqual(c.validate(*args, **kw, ordering=order, result=result, counts=Counter()),
                                 c.prior.validate(*args, **kw, ordering=order, result=result, counts=Counter()))
                self.assertEqual(cc['shared_b12_prefix_preparations'], 1)
                self.assertEqual(cc['shared_b12_histories_checked'], 3)
                self.assertEqual(old['context_preparations'], 2 * cc['context_preparations'])
                for key in ('probe_roots', 'probe_occurrence_visits', 'cursor_completed_probes', 'b12_imported_completed'):
                    self.assertEqual(cc[key], old[key])

    def test_every_history_source_and_closure_is_checked(self):
        args = study.arguments(record((67, 63))); kw = study.options(record((67, 63)))
        for slot in (12, 14, 16, 17, 18, 19, 20, 21, 22, 23):
            bad = deepcopy(args); bad[slot]['cursor']['binding'] = 'changed'
            for module in (c, c.prior):
                with self.assertRaises(ValueError): module.discover(*bad, **kw, counts=Counter())
        for key in kw:
            bad = deepcopy(kw); bad[key]['assignment'].append([9999, True])
            with self.assertRaises(ValueError): c.discover(*args, **bad, counts=Counter())
        bad = deepcopy(args); bad[0][0].append(9999)
        with self.assertRaises(ValueError): c.discover(*bad, **kw, counts=Counter())

    def test_distinct_history_trace_bounds_get_distinct_bindings(self):
        args, kw = upper_history(((1, 2),)); cc = Counter()
        result = c.discover(*args, **kw, counts=cc)
        self.assertEqual(result, c.prior.discover(*args, **kw, counts=Counter()))
        self.assertEqual(cc['shared_b12_bindings_reused'], 0)
        self.assertEqual(c.validate(*args, **kw, result=result, counts=Counter()),
                         c.prior.validate(*args, **kw, result=result, counts=Counter()))
        bad = deepcopy(args); bad[23]['program']['trace_limit'] = 31
        with self.assertRaises(ValueError): c.discover(*bad, **kw, counts=Counter())

    def test_cold_and_interrupted_continuations_match_both_orders(self):
        row = record((67, 63)); args = study.arguments(row); kw = study.options(row)
        for order in ('source', 'unseen'):
            first = c.discover(*args, **kw, ordering=order, counts=Counter(), probe_limit=1)
            result = c.discover(*args, **kw, ordering=order, cursor=json.loads(json.dumps(first['cursor'])), counts=Counter(), probe_limit=63)
            self.assertEqual(result, c.prior.discover(*args, **kw, ordering=order, counts=Counter()))
            stopped = c.discover(*args, **kw, ordering=order, counts=Counter(), work_limit=1)
            self.assertEqual(stopped['program']['reason'], 'work_limit')
            self.assertEqual(c.discover(*args, **kw, ordering=order, cursor=stopped['cursor'], counts=Counter()), result)

    def test_policies_bounds_and_invalid_controls(self):
        row = fixtures()[0]; args = study.arguments(row); kw = study.options(row)
        for options in (dict(policy='restart'), dict(policy='matched'), dict(trace_limit=1), dict(work_limit=1)):
            result = c.discover(*args, **kw, counts=Counter(), **options)
            self.assertEqual(result, c.prior.discover(*args, **kw, counts=Counter(), **options))
            c.validate(*args, **kw, result=result, counts=Counter())
        for options in (dict(policy='trusted'), dict(trace_limit=True), dict(work_limit=0), dict(ordering='unchecked')):
            with self.assertRaises(ValueError): c.discover(*args, **kw, counts=Counter(), **options)
        result = c.discover(*args, **kw, counts=Counter())
        self.assertEqual((result['program']['status'], result['program']['reason']), ('unresolved', 'complete'))

    def test_private_copy_before_caller_mutation_for_search_and_check(self):
        row = record((67, 63)); original = study.arguments(row); original_kw = study.options(row)
        expected = c.prior.discover(*original, **original_kw, counts=Counter())
        for validate in (False, True):
            args, kw, result = deepcopy((original, original_kw, expected))
            class MutatingCounter(Counter):
                def __setitem__(self, key, value):
                    super().__setitem__(key, value)
                    if key == 'shared_b12_owned_copies':
                        args[23]['cursor']['binding'] = 'caller changed'
                        kw['latest_closure']['assignment'].append([9999, True])
                        result['cursor']['binding'] = 'caller changed'
            if validate:
                self.assertEqual(c.validate(*args, **kw, result=result, counts=MutatingCounter()),
                                 c.prior.validate(*original, **original_kw, result=expected, counts=Counter()))
            else:
                self.assertEqual(c.discover(*args, **kw, cursor=result['cursor'], counts=MutatingCounter(), probe_limit=1),
                                 c.prior.discover(*original, **original_kw, cursor=expected['cursor'], counts=Counter(), probe_limit=1))
            with self.assertRaises(ValueError): c.discover(*args, **kw, counts=Counter())

    def test_result_and_each_original_bank_proof_corruption_rejected(self):
        row = record((67, 63)); args = study.arguments(row); kw = study.options(row)
        result = c.discover(*args, **kw, counts=Counter())
        for kind in ('program', 'binding', 'proof', 'schedule', 'format', 'ordering', 21, 22, 23):
            a, r = deepcopy((args, result)); options = {}
            if kind == 'program': r['program']['probes'] = []
            elif kind == 'binding': r['cursor']['binding'] = 'bad'
            elif kind == 'proof': r['cursor']['probes'][0]['proof']['conflict'] = 999999
            elif kind == 'schedule': r['cursor']['completed'].reverse()
            elif kind == 'format': r['cursor']['format'] = 'unchecked'
            elif kind == 'ordering': options['ordering'] = 'source'
            else:
                # B11 has no failed probes at this case; use its program/cursor
                # agreement check, and mutate actual proof reasons for both B10s.
                if a[kind]['cursor']['probes']: a[kind]['cursor']['probes'][0]['proof']['conflict'] = 999999
                else: a[kind]['program']['reason'] = 'refuted'
            with self.assertRaises(ValueError, msg=str(kind)):
                c.validate(*a, **kw, **options, result=r, counts=Counter())

    def test_alternate_valid_closure_order_is_not_canonicalized_away(self):
        for row in fixtures():
            args = study.arguments(row); kw = study.options(row)
            prepared = c.prior.prepare(*args, **kw, counts=Counter())[0]
            for i in range(len(kw['latest_closure']['units']) - 1):
                alt = deepcopy(kw); units = alt['latest_closure']['units']; units[i:i+2] = reversed(units[i:i+2])
                try: c.engine.prior.check_closure(prepared[25], alt['latest_closure'], Counter())
                except ValueError: continue
                for order in ('source', 'unseen'):
                    result = c.discover(*args, **alt, ordering=order, counts=Counter())
                    self.assertEqual(result, c.prior.discover(*args, **alt, ordering=order, counts=Counter()))
                    c.prior.validate(*args, **alt, ordering=order, result=result, counts=Counter())
                return
        self.fail('Fixture needs a valid alternate closure ordering')

    def test_exhaustive_small_and_generated_formulas_against_models(self):
        signed = ((-2,), (-1,), (1,), (2,), (-2,-1), (-2,1), (-1,2), (1,2)); rng = random.Random(26112612)
        cases = [(2, [signed[i] for i in range(8) if mask >> i & 1]) for mask in range(256)]
        cases += [(5, [[v*rng.choice((-1,1)) for v in rng.sample(range(1,6), rng.randrange(2,5))] for _ in range(rng.randrange(6,23))]) for _ in range(70)]
        checked = 0
        for n, source in cases:
            source = c.engine.native.normalize(source)[0]; cl = close(source)
            if cl is None: continue
            source = c.engine.native.normalize(c.engine.native.restrict_scan(source, dict(cl['assignment']), Counter()))[0]
            h = upper_history(source)
            if h is None: continue
            args, kw = h; checked += 1
            models = [dict(enumerate(bits,1)) for bits in product((False,True), repeat=n) if c.engine.native.holds(args[0], dict(enumerate(bits,1)))]
            for order in ('source', 'unseen'):
                result = c.discover(*args, **kw, ordering=order, counts=Counter())
                self.assertEqual(result, c.prior.discover(*args, **kw, ordering=order, counts=Counter()))
                self.assertEqual(c.validate(*args, **kw, ordering=order, result=result, counts=Counter()),
                                 c.prior.validate(*args, **kw, ordering=order, result=result, counts=Counter()))
                for row in result['program']['probes']:
                    lit = row['assumption']; self.assertTrue(all(m[abs(lit)] != (lit > 0) for m in models))
                if result['program']['status'] == 'refuted': self.assertFalse(models)
        self.assertGreater(checked, 60)


if __name__ == '__main__': unittest.main()
