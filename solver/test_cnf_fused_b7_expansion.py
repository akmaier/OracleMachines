from collections import Counter
from copy import deepcopy
from itertools import product
from pathlib import Path
import json,random,unittest
from experiments import cnf_fused_b7_expansion as f,compare_cnf_b7_probe_cursor as study
from solver.test_cnf_b7_probe_cursor import tiny
c=f.c


def args_for(changed):
    rows=json.loads(Path('experiments/results/cnf-b7-probe-cursor/remaining.json').read_text())['rows']
    row=next(r for r in rows if (r['target'],r['event'])==((37,40) if changed else (1,0)))
    return tuple(row[k] for k in study.FIELDS)


def split(args,**options):
    closure=study.compose(args,Counter())
    return dict(closure=closure,result=c.discover(*args,closure,Counter(),**options))


class FusedB7ExpansionTests(unittest.TestCase):
    def test_fused_and_rebuild_match_split_on_changed_and_unchanged_inputs(self):
        for changed in (False,True):
            args=args_for(changed);saved=deepcopy(args)
            for policy in ('restart','matched','reuse'):
                cc=Counter();actual=f.expand(*args,counts=cc,policy=policy)
                self.assertEqual(actual,split(args,policy=policy));self.assertEqual(actual,f.expand(*args,counts=Counter(),policy=policy,reuse_unchanged=False))
                self.assertEqual(cc['expansion_empty_layers_reused'],int(not changed));self.assertEqual(args,saved)
                c.validate(*args,actual['closure'],actual['result'],Counter())

    def test_empty_branch_still_checks_complete_prior_result(self):
        args=args_for(False)
        for kind in ('binding','old_binding','program','source','closure','schedule','extra'):
            bad=deepcopy(args)
            if kind=='binding':bad[-1]['cursor']['binding']='different'
            elif kind=='old_binding':bad[12]['cursor']['binding']='different'
            elif kind=='program':bad[-1]['program']['status']='sat'
            elif kind=='source':bad[0][0].append(999)
            elif kind=='closure':bad[13]['assignment'].append([999,True])
            elif kind=='schedule':bad[-1]['cursor']['completed']*=2
            else:bad[-1]['checked']=True
            with self.assertRaises(ValueError):f.expand(*bad,counts=Counter())

    def test_changed_proofs_cannot_be_hidden_by_empty_program(self):
        args=args_for(True)
        for kind in ('empty','forward','reason','bool_limit','bad_cursor'):
            bad=deepcopy(args)
            if kind=='empty':bad[-1]['program']['probes']=[]
            elif kind=='forward':bad[-1]['cursor']['probes'][0]['proof']['conflict']=len(f.old.validate(*args[:-1],args[-1],Counter())[13])
            elif kind=='reason':bad[-1]['program']['reason']='trusted'
            elif kind=='bool_limit':bad[-1]['program']['trace_limit']=True
            else:bad[-1]['cursor']=None
            with self.assertRaises(ValueError):f.expand(*bad,counts=Counter())

    def test_preserves_valid_alternate_closure_trace_in_empty_branch(self):
        from experiments import cnf_probe_cursor as b3,cnf_b4_probe_cursor as b4,cnf_b5_probe_cursor as b5
        source=c.native.normalize(((1,),(2,),(3,4)))[0]
        fixed,trace,conflict=c.native.propagate(source,Counter());self.assertIsNone(conflict)
        closure=dict(units=trace,assignment=sorted([list(x) for x in fixed.items()]))
        seed=dict(status='unresolved',reason='probe_limit',mode='all',trace_limit=256,terminal=None,probes=[])
        args=(source,[],seed,closure,dict(seed,mode='conditioned'),closure,dict(action='unchanged',program=None),closure)
        for engine in (b3,b4,b5):
            args=(*args,engine.discover(*args,Counter(),**({'policy':'all'} if engine is b4 else {})),closure)
        args=(*args[:-1],dict(closure,units=list(reversed(closure['units']))))
        history=f.old.discover(*args,Counter());args=(*args,history)
        self.assertEqual(history['program']['probes'],[])
        p=f.expand(*args,counts=Counter());q=f.expand(*args,counts=Counter(),reuse_unchanged=False)
        self.assertEqual(p['closure'],args[13]);self.assertNotEqual(p['closure']['units'],q['closure']['units'])
        for r in (p,q):c.validate(*args,r['closure'],r['result'],Counter());self.assertNotEqual(r['result']['program']['status'],'sat')

    def test_trace_change_prevents_history_handoff(self):
        args=args_for(False);cc=Counter();p=f.expand(*args,counts=cc,trace_limit=257)
        self.assertEqual(cc['b7_imported_cursors'],0);self.assertEqual(p,split(args,trace_limit=257))
        bad=json.loads(json.dumps(p['result']['cursor']))
        with self.assertRaises(ValueError):f.expand(*args,counts=Counter(),cursor=bad)

    def test_serialized_continuation_and_result_alias_isolation(self):
        args=args_for(True);saved=deepcopy(args);p=f.expand(*args,counts=Counter(),probe_limit=8)
        cursor=json.loads(json.dumps(p['result']['cursor']));q=f.expand(*args,counts=Counter(),cursor=cursor,probe_limit=8)
        self.assertEqual(q,f.expand(*args,counts=Counter(),probe_limit=16));self.assertEqual(args,saved)
        p['closure']['units'].clear();p['result']['cursor']['probes'].clear();self.assertEqual(args,saved)
        c.validate(*args,q['closure'],q['result'],Counter())

    def test_interruption_terminal_and_invalid_options(self):
        args=tiny(((-2,-1),(-2,1),(-1,2),(1,2)))[:-1];cc=Counter();p=f.expand(*args,counts=cc,work_limit=1)
        self.assertEqual(p['result']['program']['reason'],'work_limit');self.assertLessEqual(cc['probe_occurrence_visits'],1)
        q=f.expand(*args,counts=Counter(),cursor=p['result']['cursor']);self.assertEqual(q,split(args))
        self.assertEqual(q['result']['program']['status'],'refuted');c.validate(*args,q['closure'],q['result'],Counter())
        self.assertEqual(q,f.expand(*args,counts=Counter(),cursor=q['result']['cursor']))
        for options in (dict(reuse_unchanged=1),dict(policy='trusted'),dict(probe_limit=0),dict(work_limit=True),dict(trace_limit=0)):
            with self.assertRaises(ValueError):f.expand(*args,counts=Counter(),**options)
        with self.assertRaises(ValueError):f.expand(*args[:-1],counts=Counter())

    def test_composition_conflict_and_closed_prior_are_rejected_explicitly(self):
        from solver.test_cnf_b6_probe_cursor import tiny as old_tiny
        args=old_tiny(((1,2),(1,-2),(3,4),(3,-4),(5,6),(5,-6),(-1,-3,-5)))
        history=f.old.discover(*args,Counter())
        with self.assertRaisesRegex(ValueError,'Contradictory composition'):f.expand(*args,history,counts=Counter())
        args=old_tiny(((-2,-1),(-2,1),(-1,2),(1,2)));history=f.old.discover(*args,Counter())
        with self.assertRaisesRegex(ValueError,'Unresolved B6'):f.expand(*args,history,counts=Counter())

    def test_exhaustive_and_generated_small_truth(self):
        clauses=((-2,-1),(-2,1),(-1,2),(1,2));rng=random.Random(260302);checked=0
        cases=[(2,[clauses[i] for i in range(4) if mask>>i&1]) for mask in range(16)]
        cases += [(5,[[v*rng.choice((-1,1)) for v in rng.sample(range(1,6),rng.randrange(2,5))] for _ in range(rng.randrange(6,23))]) for _ in range(100)]
        for n,source in cases:
            full=tiny(source)
            if full is None:continue
            args=full[:-1];p=f.expand(*args,counts=Counter());self.assertEqual(p,split(args));c.validate(*args,p['closure'],p['result'],Counter());checked+=1
            models=[dict(enumerate(bits,1)) for bits in product((False,True),repeat=n) if c.native.holds(args[0],dict(enumerate(bits,1)))]
            if p['result']['program']['status']=='refuted':self.assertFalse(models)
            for row in p['result']['program']['probes']:self.assertTrue(all(m[abs(row['assumption'])]!=(row['assumption']>0) for m in models))
        self.assertGreater(checked,90)


if __name__=='__main__':unittest.main()
