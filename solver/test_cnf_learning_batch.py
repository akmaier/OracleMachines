from collections import Counter,defaultdict
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from experiments.cnf_learning_batch import acquire,search,selection
from experiments.cnf_coupled_pivots import AdmissionExhausted


class SharedHistory:
    def __init__(self):self.resets=0;self.cached=set();self.admitted=set()
    def set_admission_budget(self,limit):self.resets+=1;self.admission_limit=limit;self.admitted=set()
    def _edge(self,target,depth):
        for key in target:
            if key in self.cached:continue
            if key not in self.admitted:
                if len(self.admitted)>=self.admission_limit:raise AdmissionExhausted()
                self.admitted.add(key)
            self.cached.add(key)
        return dict(key=target[-1])
    def _load(self,source):return dict(cnf=((1,2),),depth=0,kind='unresolved',summary=dict(closed=False))


class LearningBatchTests(unittest.TestCase):
    def test_selection_separates_pending_exhausted_and_acquired_open_targets(self):
        h=SharedHistory();original=h._load
        h._load=lambda key:None if key=='missing' else original(key)
        identities=('ready','pending','open','exhausted','covered','successful')
        bases={key:dict(source=key,probing=dict(status='forced' if key=='successful' else 'clear')) for key in identities}
        records={key:dict(base_sha256=key,offset=4,probing=dict(attempts=[None]*8),
            edge=None if key=='exhausted' else dict(key='missing' if key=='pending' else 'existing'))
            for key in ('pending','open','exhausted')}
        blocks=SimpleNamespace(bases=bases,records=records,context=lambda h,i,c:(None,None,list(range(1,9))))
        routes=SimpleNamespace(learned_blocks=blocks)
        with patch('experiments.cnf_learning_batch.compose',side_effect=lambda h,roots,r,c:([roots[0]=='covered'],{})):
            rows=selection(h,routes,Counter())
        self.assertEqual(rows[0]['base_sha256'],'pending')
        self.assertEqual({r['base_sha256']:r['reason'] for r in rows},dict(ready='ready',pending='pending',
            open='acquired_open_target',exhausted='exhausted',covered='covered',successful='successful_base'))
        self.assertEqual(next(r for r in rows if r['base_sha256']=='ready')['remaining'],4)

    def test_global_and_per_target_caps_preserve_completed_work(self):
        h=SharedHistory();h.set_admission_budget(5)
        edge,pending,added=acquire(h,['a','b','c'],0,total_limit=5,target_limit=2)
        self.assertTrue(pending);self.assertEqual(added,{'a','b'});self.assertEqual(h.admission_limit,5)
        edge,pending,added=acquire(h,['a','b','c'],0,total_limit=5,target_limit=2)
        self.assertFalse(pending);self.assertEqual(added,{'c'})
        _,pending,added=acquire(h,['d','e','f'],0,total_limit=5,target_limit=3)
        self.assertTrue(pending);self.assertEqual(added,{'d','e'});self.assertEqual(h.resets,1)
        _,pending,added=acquire(h,['a','c'],0,total_limit=5,target_limit=0)
        self.assertFalse(pending);self.assertFalse(added);self.assertEqual(len(h.admitted),5)

    def test_round_robin_steps_and_persist_before_acquisition(self):
        h=SharedHistory();events=[];offsets=defaultdict(lambda:4)
        blocks=SimpleNamespace(bases={x:dict(source=x) for x in ('a','b')},records={})
        def advance(h,identity,counts):
            offset=offsets[identity];offsets[identity]+=4
            rec=dict(base_sha256=identity,width=4,offset=offset,probing=dict(status='clear'),edge=None)
            if identity=='a' and offset==8:rec['probing']['status']='forced';rec['edge']=dict(key='a2')
            from experiments.cnf_learning_continuation import record_key
            blocks.records[record_key(rec)]=rec
            return rec,['a1','a2']
        blocks.advance=advance;routes=SimpleNamespace(learned_blocks=blocks,refresh_learning=lambda h:None)
        original=h._edge
        def edge(*args):
            self.assertEqual(events[-1],('a',8));return original(*args)
        h._edge=edge
        with patch('experiments.cnf_learning_batch.compose',return_value=([False],{})):
            result=search(h,routes,[dict(base_sha256=x,reason='ready') for x in ('a','b')],Counter(),
                lambda rec:events.append((rec['base_sha256'],rec['offset'])),step_limit=4,state_limit=2,target_limit=2)
        self.assertEqual(events,[('a',4),('b',4),('a',8),('b',8)])
        self.assertEqual(result['queued'],['b']);self.assertEqual(h.resets,1)
        self.assertEqual(result['recognitions'][0]['admitted'],['a1','a2'])

    def test_covered_sources_and_zero_budget_do_not_discover(self):
        h=SharedHistory();blocks=SimpleNamespace(bases={'a':dict(source='a')},records={})
        blocks.advance=lambda *args:self.fail('unexpected discovery')
        routes=SimpleNamespace(learned_blocks=blocks,refresh_learning=lambda h:None)
        chosen=[dict(base_sha256='a',reason='ready')]
        result=search(h,routes,chosen,Counter(),lambda r:None,step_limit=0)
        self.assertEqual(result['queued'],['a']);self.assertFalse(result['visits'])
        with patch('experiments.cnf_learning_batch.compose',return_value=([True],{})):
            result=search(h,routes,chosen,Counter(),lambda r:None)
        self.assertEqual(result['skipped_covered'],['a']);self.assertFalse(result['visits'])
        for key in ('step_limit','state_limit','target_limit'):
            with self.assertRaises(ValueError):search(h,routes,chosen,Counter(),lambda r:None,**{key:True})


if __name__=='__main__':unittest.main()
