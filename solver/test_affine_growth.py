"""Affine growth: exhaustive boundary sets, independent full-history elimination,
immutable versions, poisoned archives, failures, replay and protocol boundaries."""
import itertools
import random
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from experiments.affine_reference import equation,flattened_sat
from solver.persistent import PersistentSolver
from solver.resources import BudgetExceeded,stop_process


def holds(equations,values):
    return all(sum(a and b for a,b in zip(r['coefficients'],values))%2==r['rhs'] for r in equations)


def frontier(width,previous,equations):
    return {v for v in itertools.product((False,True),repeat=width)
            if any(holds(equations,u+v) for u in previous)}


def solutions(width,summary):
    return {v for v in itertools.product((False,True),repeat=width) if holds(summary,v)}


class AffineGrowthTests(unittest.TestCase):
    def check_report(self,result):
        self.assertLessEqual(result['summary_rows'],result['width']+1)
        self.assertEqual(result['summary_cells'],result['summary_rows']*(result['width']+1))
        self.assertLessEqual(result['summary_cells'],result['summary_cell_bound'])
        self.assertFalse(result['counted_complete'])
        self.assertLessEqual(result['reference_cell_charge'],result['reference_cell_budget'])

    def test_random_branching_frontiers_match_exhaustive_sets(self):
        rng=random.Random(2401);answers=set()
        with tempfile.TemporaryDirectory() as d,PersistentSolver(Path(d)/'s.db') as s:
            for width in (1,2,3):
                initial=s.affine_grow(width,summary=True)
                versions=[(initial,set(itertools.product((False,True),repeat=width)),[])]
                for _ in range(45):
                    parent,old,batches=rng.choice(versions)
                    rows=[equation(width,[i for i in range(2*width) if rng.getrandbits(1)],bool(rng.getrandbits(1)))
                          for _ in range(rng.randrange(0,2*width+3))]
                    result=s.affine_grow(base=parent['state'],equations=rows,summary=True)
                    expected=frontier(width,old,rows)
                    self.assertEqual(solutions(width,result['summary']),expected)
                    self.assertIs(result['answer'],bool(expected));answers.add(result['answer'])
                    self.assertEqual(result['steps'],parent['steps']+1)
                    self.assertIs(result['answer'],flattened_sat(width,batches+[rows]))
                    self.check_report(result)
                    saved=s.affine_grow(base=parent['state'],summary=True)
                    self.assertEqual(solutions(width,saved['summary']),old)
                    versions.append((result,expected,batches+[rows]))
        self.assertEqual(answers,{True,False})

    def test_wide_growth_matches_complete_original_system(self):
        rng=random.Random(2402)
        with tempfile.TemporaryDirectory() as d,PersistentSolver(Path(d)/'s.db',query_timeout=60) as s:
            for width in (8,32,64,128):
                state=s.affine_grow(width);batches=[]
                for step in range(6):
                    rows=[equation(width,(i,width+i),bool(rng.getrandbits(1))) for i in range(width)]
                    if step==5:rows+=[equation(width,(),True)]
                    batches.append(rows)
                    state=s.affine_grow(base=state['state'],equations=rows)
                    self.assertIs(state['answer'],flattened_sat(width,batches))
                    self.check_report(state)

    def test_redundancy_empty_append_and_contradiction(self):
        with tempfile.TemporaryDirectory() as d,PersistentSolver(Path(d)/'s.db') as s:
            a=s.affine_grow(2)
            rows=[equation(2,(2,),True)]*20+[equation(2,(),False)]*20
            b=s.affine_grow(base=a['state'],equations=rows,summary=True)
            self.assertTrue(b['answer']);self.assertEqual(b['summary_rows'],1)
            c=s.affine_grow(base=b['state'],equations=[equation(2,(0,),False)])
            self.assertFalse(c['answer'])
            self.assertFalse(s.affine_grow(base=c['state'],equations=[])['answer'])
            empty=s.affine_grow(base=b['state'],equations=[],summary=True)
            self.assertEqual(empty['summary'],[]);self.assertEqual(empty['steps'],2)
            self.assertTrue(s.affine_grow(base=b['state'])['answer'])

    def test_restart_replays_source_and_ignores_poisoned_answers(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'s.db'
            with PersistentSolver(path) as s:
                a=s.affine_grow(1,[equation(1,(1,),True)])
                b=s.affine_grow(base=a['state'],equations=[equation(1,(0,),False)])
                c=s.affine_grow(base=a['state'],equations=[])
                with s.db:
                    s.db.execute('UPDATE affine_states SET answer=1-answer')
                    s.db.execute("UPDATE knowledge_objects SET payload=? WHERE kind='affine_result'",(b'poisoned',))
            with PersistentSolver(path) as s:
                checked=s.affine_grow(base=b['state']);self.assertFalse(checked['answer'])
                self.assertEqual(checked['affine_updates']['replayed_versions'],3)
                self.assertTrue(s.affine_grow(base=a['state'])['answer'])
                self.assertTrue(s.affine_grow(base=c['state'])['answer'])
                self.assertEqual(s.affine_grow(base=b['state'])['affine_updates']['replayed_versions'],0)
                # A new engine namespace must adopt original inputs, never old answers.
                s.engine_id='independent-test-namespace'
                del s.affine_growth
                self.assertFalse(s.affine_grow(base=b['state'])['answer'])
                self.assertEqual(s.db.execute('SELECT count(*) FROM affine_states WHERE engine=?',(s.engine_id,)).fetchone()[0],1)

    def test_worker_restart_and_database_rollback_preserve_versions(self):
        with tempfile.TemporaryDirectory() as d,PersistentSolver(Path(d)/'s.db') as s:
            a=s.affine_grow(1,[equation(1,(1,),True)])
            before=s.db.execute('SELECT count(*) FROM knowledge_objects').fetchone()[0]
            original=s.affine_growth.store.put
            def fail(kind,value):
                if kind=='affine_result':raise RuntimeError('injected archive failure')
                return original(kind,value)
            with patch.object(s.affine_growth.store,'put',side_effect=fail):
                with self.assertRaisesRegex(RuntimeError,'injected'):
                    s.affine_grow(base=a['state'],equations=[equation(1,(0,),False)])
            self.assertEqual(s.db.execute('SELECT count(*) FROM knowledge_objects').fetchone()[0],before)
            self.assertTrue(s.affine_grow(base=a['state'])['answer'])
            stop_process(s.process);s.process=None
            result=s.affine_grow(base=a['state'])
            self.assertTrue(result['answer']);self.assertEqual(result['affine_updates']['replayed_versions'],2)

    def test_archive_corruption_and_forged_history_rejected(self):
        with tempfile.TemporaryDirectory() as d,PersistentSolver(Path(d)/'s.db') as s:
            initial=s.affine_grow(1)
            store=s.affine_growth.store
            bad=[dict(width=1,base=None,equations=[equation(1)]),
                 dict(width=2,base=initial['state'],equations=[]),
                 dict(width=1,base=7,equations=[]),dict(width=0,base=None,equations=[])]
            for node in bad:
                with s.db:token=store.put('affine_version',node)[0]
                with self.assertRaises(ValueError):s.affine_grow(base=token)
                self.assertTrue(s.affine_grow(base=initial['state'])['answer'])
            with s.db:s.db.execute('UPDATE knowledge_objects SET payload=? WHERE id=?',(b'corrupt',initial['state']))
            with self.assertRaises(ValueError):s.affine_grow(base=initial['state'])

    def test_input_validation_and_budget_preserve_archive(self):
        with tempfile.TemporaryDirectory() as d,PersistentSolver(Path(d)/'s.db') as s:
            a=s.affine_grow(1)
            count=s.db.execute('SELECT count(*) FROM knowledge_objects').fetchone()[0]
            for kwargs in (dict(width=True),dict(width=0),dict(width=129),dict(base=a['state'],width=1),
                           dict(base=a['state'],summary=1),dict(base='missing'),
                           *[dict(base=a['state'],equations=x) for x in (False,[{}],
                             [dict(coefficients=[True,1],rhs=False)],[dict(coefficients=[True],rhs=False)],
                             [dict(coefficients=[True,False],rhs=1)],[equation(1)]*4097)]):
                with self.assertRaises(ValueError):s.affine_grow(**kwargs)
                self.assertEqual(s.db.execute('SELECT count(*) FROM knowledge_objects').fetchone()[0],count)
            s.max_input_bytes=200
            with self.assertRaises(BudgetExceeded):s.affine_grow(base=a['state'],equations=[equation(1)]*20)
            self.assertTrue(s.affine_grow(base=a['state'])['answer'])

    def test_native_rejects_forged_fields_and_identity_changes(self):
        with tempfile.TemporaryDirectory() as d,PersistentSolver(Path(d)/'s.db') as s:
            init=dict(mode='affine_init',id='a',width=1)
            self.assertTrue(s._request(init)['answer']);self.assertTrue(s._request(init)['answer'])
            good=dict(mode='affine_append',id='b',base='a',equations=[equation(1,(1,),True)])
            self.assertTrue(s._request(good)['answer'])
            invalid=[dict(init,width=2),dict(init,id='z',width=0),dict(init,id='z',width=129),
                     dict(good,id='z',base='missing'),dict(good,id='z',equations=[equation(2)]),
                     dict(good,id='z',equations=[dict(coefficients=[1,False],rhs=True)]),
                     dict(good,id='z',equations=[equation(1)]*4097),dict(good,equations=[]),
                     dict(mode='affine_query',root='b',summary=1),dict(mode='affine_query',root='missing',summary=False)]
            for request in invalid:
                with self.assertRaises(ValueError):s._request(request)
                self.assertTrue(s._request(dict(mode='affine_query',root='b',summary=False))['answer'])
            self.assertTrue(s._request(dict(good,id='maxrows',equations=[equation(1)]*4096))['answer'])

    def test_fixed_width_charge_does_not_grow_with_history(self):
        with tempfile.TemporaryDirectory() as d,PersistentSolver(Path(d)/'s.db') as s:
            width=4
            state=s.affine_grow(width,[equation(width,(width+i,),bool(i%2)) for i in range(width)])
            charges=set()
            rows=[equation(width,(i,width+i),True) for i in range(width)]
            for step in range(80):
                state=s.affine_grow(base=state['state'],equations=rows)
                self.assertTrue(state['answer']);self.assertEqual(state['summary_rows'],width)
                self.assertEqual(state['steps'],step+2)
                self.assertEqual(state['affine_updates']['replayed_versions'],0)
                self.assertEqual(state['affine_updates']['registered_versions'],1)
                charges.add(state['uncached_reference_cell_charge']);self.check_report(state)
            self.assertEqual(len(charges),1)

    def test_bounded_residency_grows_past_old_history_cap_and_replays(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'s.db'
            with PersistentSolver(path,native_affine_versions=2,query_timeout=60) as s:
                state=s.affine_grow(1,[equation(1,(1,),True)])
                first=state['state']
                for _ in range(4100):
                    state=s.affine_grow(base=state['state'],equations=[equation(1,(0,1),False)])
                    self.assertTrue(state['answer'])
                    self.assertLessEqual(state['affine_updates']['resident_versions'],2)
                last=state['state']
                self.assertEqual(state['steps'],4101)
                self.assertEqual(s._request(dict(mode='affine_stats'))['resident_versions'],2)
                self.assertTrue(s.affine_grow(base=first)['answer'])
                self.assertTrue(s.affine_grow(base=last)['answer'])
                self.assertEqual(s.db.execute('SELECT count(*) FROM affine_states').fetchone()[0],4101)
            with PersistentSolver(path,native_affine_versions=2,query_timeout=60) as s:
                loaded=s.affine_grow(base=last)
                self.assertTrue(loaded['answer'])
                self.assertEqual(loaded['affine_updates']['replayed_versions'],4102)
                self.assertEqual(loaded['affine_updates']['evicted_versions'],4100)
                self.assertEqual(s._request(dict(mode='affine_stats'))['resident_versions'],2)

    def test_evicted_parents_do_not_change_resident_children(self):
        with tempfile.TemporaryDirectory() as d,PersistentSolver(Path(d)/'s.db',native_affine_versions=3) as s:
            parent=s.affine_grow(1,[equation(1,(1,),True)])
            child=s.affine_grow(base=parent['state'],equations=[equation(1,(0,),False)])
            tail=s.affine_grow(base=child['state'],equations=[])
            self.assertFalse(tail['answer'])
            self.assertLessEqual(s._request(dict(mode='affine_stats'))['resident_versions'],3)
            # Native child decisions depend on their certified summaries, not
            # continued residency of ancestor names.
            s._request(dict(mode='affine_drop',ids=[parent['state']]))
            self.assertFalse(s._request(dict(mode='affine_query',root=child['state'],summary=False))['answer'])
            with self.assertRaises(ValueError):s._request(dict(mode='affine_query',root=parent['state'],summary=False))

    def test_failed_retention_transaction_recovers_with_bounded_store(self):
        with tempfile.TemporaryDirectory() as d,PersistentSolver(Path(d)/'s.db',native_affine_versions=2) as s:
            first=s.affine_grow(1,[equation(1,(1,),True)])
            original=s.affine_growth.store.put
            def fail(kind,value):
                if kind=='affine_result':raise RuntimeError('injected archive failure')
                return original(kind,value)
            with patch.object(s.affine_growth.store,'put',side_effect=fail):
                with self.assertRaises(RuntimeError):s.affine_grow(base=first['state'],equations=[])
            restored=s.affine_grow(base=first['state'])
            self.assertTrue(restored['answer'])
            self.assertEqual(restored['affine_updates']['native_resets'],1)
            self.assertEqual(s._request(dict(mode='affine_stats'))['resident_versions'],2)
            self.assertEqual(s.db.execute('SELECT count(*) FROM affine_states').fetchone()[0],1)

    def test_comparison_cnf_encoding_preserves_every_source_assignment(self):
        from experiments.compare_affine_growth import source_cnf
        width=2
        for coefficients in itertools.product((False,True),repeat=4):
            for rhs in (False,True):
                row=dict(coefficients=list(coefficients),rhs=rhs)
                clauses,n=source_cnf(width,[[row]])
                for original in itertools.product((False,True),repeat=4):
                    exists=False
                    for auxiliary in itertools.product((False,True),repeat=n-4):
                        values=original+auxiliary
                        if all(any(values[abs(lit)-1]==(lit>0) for lit in clause) for clause in clauses):
                            exists=True;break
                    self.assertEqual(exists,holds([row],original))
        # Auxiliary names must follow the entire original history, rather than
        # colliding with a later fresh block.
        batches=[[equation(2,(0,1,2),True)],[equation(2,(0,1,3),False)]]
        clauses,n=source_cnf(2,batches)
        for original in itertools.product((False,True),repeat=6):
            expected=holds(batches[0],original[:4]) and holds(batches[1],original[2:6])
            actual=any(all(any((original+aux)[abs(lit)-1]==(lit>0) for lit in clause) for clause in clauses)
                       for aux in itertools.product((False,True),repeat=n-6))
            self.assertEqual(actual,expected)

    def test_native_history_retry_keeps_original_parent_after_name_reuse(self):
        with tempfile.TemporaryDirectory() as d,PersistentSolver(Path(d)/'s.db') as s:
            initial=dict(mode='affine_init',id='a',width=1)
            s._request(initial)
            parent=dict(mode='affine_append',id='p',base='a',equations=[equation(1,(1,),True)])
            s._request(parent)
            child=dict(mode='affine_append',id='c',base='p',equations=[equation(1,(0,),True)])
            old=s._request(child)
            self.assertTrue(old['answer']);self.assertEqual(old['steps'],2)
            s._request(dict(mode='affine_drop',ids=['p','p','missing']))
            # An exact retry keeps the original child even without a live parent.
            self.assertEqual(s._request(child),old)
            changed=dict(parent,equations=[equation(1,(),True)])
            self.assertFalse(s._request(changed)['answer'])
            self.assertEqual(s._request(child),old)
            # A fresh name binds the current parent and is therefore negative.
            self.assertFalse(s._request(dict(child,id='fresh'))['answer'])
            self.assertTrue(s._request(dict(mode='affine_query',root='c',summary=False))['answer'])
            s._request(dict(mode='affine_drop',ids=['c']))
            self.assertFalse(s._request(child)['answer'])
            self.assertTrue(old['answer'])
            s._request(dict(mode='affine_reset'))
            self.assertEqual(s._request(dict(mode='affine_stats'))['resident_versions'],0)
            with self.assertRaisesRegex(ValueError,'Unknown affine root'):
                s._request(dict(mode='affine_query',root='c',summary=False))
            self.assertTrue(s._request(initial)['answer'])

    def test_native_row_decoding_failure_is_atomic(self):
        with tempfile.TemporaryDirectory() as d,PersistentSolver(Path(d)/'s.db') as s:
            s._request(dict(mode='affine_init',id='a',width=2))
            rows=[equation(2,(0,3),True),equation(2,(2,),False)]
            request=dict(mode='affine_append',id='b',base='a',equations=rows+rows)
            expected=flattened_sat(2,[rows+rows])
            original=s._request(request)
            self.assertEqual(original['answer'],expected)
            self.assertEqual(s._request(request),original)
            before=s._request(dict(mode='affine_stats'))
            bad_rows=[dict(coefficients=[False,True],rhs=False),
                      dict(coefficients=[False]*4,rhs=0),
                      dict(coefficients=[False,False,False,1],rhs=True),
                      dict(coefficients=[False]*4)]
            for row in bad_rows:
                with self.assertRaises(ValueError):
                    s._request(dict(request,id='bad',equations=rows+[row]))
                self.assertEqual(s._request(dict(mode='affine_stats')),before)
                self.assertEqual(s._request(request),original)
            with self.assertRaises(ValueError):s._request(dict(mode='affine_drop',ids=['a',7]))
            self.assertEqual(s._request(dict(mode='affine_stats')),before)
            self.assertTrue(s._request(dict(mode='affine_query',root='a',summary=False))['answer'])

    def test_invalid_resident_caps_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            for cap in (True,0,1,4097):
                with self.assertRaises(ValueError):PersistentSolver(Path(d)/'s.db',native_affine_versions=cap)

    def test_kernel_hit_rebinds_history_after_parent_eviction(self):
        with tempfile.TemporaryDirectory() as d,PersistentSolver(Path(d)/'s.db',native_affine_versions=2) as s:
            state=s.affine_grow(2,[equation(2,(2,),True),equation(2,(3,),False)])
            rows=[equation(2,(i,2+i),False) for i in range(2)]
            versions=[]
            for step in range(30):
                state=s.affine_grow(base=state['state'],equations=rows,summary=True)
                versions.append(state['state'])
                self.assertEqual(state['steps'],step+2)
                self.assertEqual(solutions(2,state['summary']),{(True,False)})
                self.assertEqual(state['affine_updates']['kernel_hits'],int(step>0))
                self.assertEqual(state['kernel_cache_hit'],step>0)
                self.assertGreater(state['uncached_reference_cell_charge'],0)
                if step>0:self.assertEqual(state['reference_cell_charge'],0)
            self.assertEqual(len(set(versions)),30)
            self.assertEqual(s.db.execute('SELECT count(*) FROM affine_states').fetchone()[0],31)
            query=s.affine_grow(base=versions[-1])
            for metric in ('kernel_hits','kernel_misses','kernel_key_cells','executed_reference_cells'):
                self.assertEqual(query['affine_updates'][metric],0)
            # The source archive survives both native eviction and process loss.
            stop_process(s.process);s.process=None
            replay=s.affine_grow(base=versions[-1],summary=True)
            self.assertEqual(replay['steps'],31)
            self.assertEqual(solutions(2,replay['summary']),{(True,False)})
            self.assertEqual(replay['affine_updates']['kernel_hits'],29)
            self.assertEqual(s._request(dict(mode='affine_stats'))['resident_versions'],2)

    def test_kernel_collision_checks_boundary_batch_and_width(self):
        with tempfile.TemporaryDirectory() as d,PersistentSolver(Path(d)/'s.db') as s:
            s._request(dict(mode='affine_cache_config',slots=1))
            s._request(dict(mode='affine_init',id='a',width=1))
            for name,value in (('p',True),('q',False)):
                s._request(dict(mode='affine_append',id=name,base='a',equations=[equation(1,(1,),value)]))
            def append(name,parent,rows):
                return s._request(dict(mode='affine_append',id=name,base=parent,equations=rows))
            rows=[equation(1,(0,),True)]
            first=append('one','p',rows)
            different=append('two','q',rows)
            self.assertTrue(first['answer']);self.assertFalse(different['answer'])
            self.assertFalse(first['kernel_cache_hit']);self.assertFalse(different['kernel_cache_hit'])
            self.assertTrue(different['kernel_evicted'])
            again=append('three','q',rows)
            self.assertTrue(again['kernel_cache_hit']);self.assertFalse(again['answer'])
            self.assertEqual(again['reference_cell_charge'],0)
            changed=append('four','q',[equation(1,(0,),False)])
            self.assertFalse(changed['kernel_cache_hit']);self.assertTrue(changed['answer'])
            s._request(dict(mode='affine_init',id='wide',width=2))
            self.assertFalse(append('wide-child','wide',[equation(2,(0,),False)])['kernel_cache_hit'])
            self.assertEqual(s._request(dict(mode='affine_stats'))['kernel_cache_entries'],1)

    def test_kernel_disabled_and_enabled_match_full_frontiers(self):
        rng=random.Random(2410)
        with tempfile.TemporaryDirectory() as d:
            with PersistentSolver(Path(d)/'off.db',affine_kernel_slots=0) as off,PersistentSolver(Path(d)/'on.db',affine_kernel_slots=1) as on:
                roots=[service.affine_grow(3) for service in (off,on)]
                versions=[(roots,set(itertools.product((False,True),repeat=3)))]
                for _ in range(50):
                    parents,old=rng.choice(versions)
                    rows=[equation(3,[i for i in range(6) if rng.getrandbits(1)],bool(rng.getrandbits(1)))
                          for _ in range(rng.randrange(5))]
                    results=[service.affine_grow(base=parent['state'],equations=rows,summary=True)
                             for service,parent in zip((off,on),parents)]
                    expected=frontier(3,old,rows)
                    for result in results:
                        self.assertEqual(solutions(3,result['summary']),expected)
                        self.assertEqual(result['answer'],bool(expected))
                    self.assertEqual(results[0]['summary'],results[1]['summary'])
                    self.assertFalse(results[0]['kernel_cache_hit'])
                    self.assertEqual(results[0]['kernel_key_cells'],0)
                    versions.append((results,expected))
                self.assertEqual(off._request(dict(mode='affine_stats'))['kernel_cache_entries'],0)
                self.assertLessEqual(on._request(dict(mode='affine_stats'))['kernel_cache_entries'],1)

    def test_kernel_configuration_atomic_and_reset_retains_cap(self):
        with tempfile.TemporaryDirectory() as d,PersistentSolver(Path(d)/'s.db') as s:
            s._request(dict(mode='affine_init',id='a',width=1))
            s._request(dict(mode='affine_cache_config',slots=1))
            request=dict(mode='affine_append',id='b',base='a',equations=[])
            s._request(request)
            before=s._request(dict(mode='affine_stats'))
            for slots in (True,-1,4097,'1'):
                with self.assertRaises(ValueError):s._request(dict(mode='affine_cache_config',slots=slots))
                self.assertEqual(s._request(dict(mode='affine_stats')),before)
            s._request(dict(mode='affine_cache_config',slots=0))
            self.assertTrue(s._request(dict(mode='affine_query',root='b',summary=False))['answer'])
            self.assertFalse(s._request(dict(request,id='c'))['kernel_cache_hit'])
            s._request(dict(mode='affine_reset'))
            self.assertEqual(s._request(dict(mode='affine_stats')),
                             dict(resident_versions=0,kernel_cache_entries=0,kernel_cache_slots=0))
            for cap in (True,-1,4097,'1'):
                with self.assertRaises(ValueError):PersistentSolver(Path(d)/'bad.db',affine_kernel_slots=cap)

    def test_kernel_rollback_clears_stale_entries_and_keeps_configuration(self):
        with tempfile.TemporaryDirectory() as d,PersistentSolver(Path(d)/'s.db',affine_kernel_slots=1) as s:
            first=s.affine_grow(1,[equation(1,(1,),True)])
            original=s.affine_growth.store.put
            def fail(kind,value):
                if kind=='affine_result':raise RuntimeError('injected archive failure')
                return original(kind,value)
            with patch.object(s.affine_growth.store,'put',side_effect=fail):
                with self.assertRaises(RuntimeError):
                    s.affine_grow(base=first['state'],equations=[])
            recovered=s.affine_grow(base=first['state'],equations=[])
            self.assertEqual(recovered['affine_updates']['native_resets'],1)
            self.assertFalse(recovered['kernel_cache_hit'])
            self.assertTrue(recovered['answer'])
            self.assertEqual(s._request(dict(mode='affine_stats'))['kernel_cache_slots'],1)
            self.assertEqual(s.db.execute('SELECT count(*) FROM affine_states').fetchone()[0],2)

    def test_native_version_capacity_is_refusal_not_false(self):
        with tempfile.TemporaryDirectory() as d,PersistentSolver(Path(d)/'s.db') as s:
            for i in range(4096):s._request(dict(mode='affine_init',id=str(i),width=1))
            with self.assertRaisesRegex(ValueError,'capacity'):s._request(dict(mode='affine_init',id='overflow',width=1))
            self.assertTrue(s._request(dict(mode='affine_query',root='0',summary=False))['answer'])
            self.assertTrue(s._request(dict(mode='affine_init',id='0',width=1))['answer'])
