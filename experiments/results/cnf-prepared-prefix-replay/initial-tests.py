from collections import Counter
from copy import deepcopy
from itertools import product
import json,random,unittest
from experiments import cnf_prepared_prefix_replay as c,compare_cnf_prepared_prefix_replay as study
from experiments.cnf_stopped_support import conditional_unit
from experiments.cnf_hint_transport import check_rup


def event(source,fixed=None,subset=None):
    fixed={} if fixed is None else fixed
    raw=c.native.restrict_scan(source,fixed,Counter()) if subset is None else subset
    local,names=c.native.normalize(raw)
    return dict(root=c.native.token(local,Counter()),mapping=[list(x) for x in enumerate(names,1)],fixed=sorted([list(x) for x in fixed.items()]))


def template(cl):return dict(clauses=[list(cl)],assumptions=[[abs(l),l<0] for l in sorted(cl,key=abs)],trace=[],conflict=0)


def checked(source,templates,e):
    got=c.local_hints(source,templates,e,Counter());expected=c.frozen.local_hints(source,templates,e,Counter())
    if got!=expected:raise AssertionError('Different reconstruction')
    for hint in got[1]:check_rup(got[0],hint['clause'],hint['proof'],Counter())
    return got


class PreparedPrefixReplayTests(unittest.TestCase):
    def test_current_corpus_matches_all_states_and_proof_checks(self):
        p=study.base.load(study.PARENT/'protocol.json');seen=0
        for target in p['targets']:
            source,ts,refs,events=study.prior.inputs(p,target)
            for ref,seed in refs:
                cc=Counter();fc=Counter();before=deepcopy((source,ts,ref,events[ref['event']]))
                self.assertEqual(c.bind(source,ts,ref,events[ref['event']],cc),study.prior.bind(source,ts,ref,events[ref['event']],fc))
                self.assertEqual(cc['replay_local_contexts'],1);self.assertEqual(cc['verified_core_hints'],fc['verified_core_hints'])
                self.assertEqual(cc['hint_check_literals'],fc['hint_check_literals']);self.assertLess(cc['normalization_literal_visits'],fc['normalization_literal_visits'])
                self.assertEqual(before,(source,ts,ref,events[ref['event']]));seen+=1
        self.assertEqual(seen,16)

    def test_synthetic_novel_repeated_empty_single_and_missing_support(self):
        for case in study.synthetic_cases():
            source,ts,e=case['source'],case['templates'],case['event'];local,hints,whole=checked(source,ts,e)
            cc=Counter();c.local_hints(source,ts,e,cc)
            if case['kind']=='none':self.assertEqual(cc['replay_local_contexts'],0)
            elif case['kind']=='missing-support':self.assertEqual(hints,[]);self.assertFalse(whole);self.assertEqual(cc['replay_local_contexts'],1)
            else:self.assertEqual(len(hints),len(ts));self.assertTrue(whole);self.assertEqual(cc['replay_local_contexts'],1)

    def test_conditioned_component_renaming_and_absent_support(self):
        source=c.native.normalize([[-1,-2,3],[-1,-2,-3],[4,5,6]])[0]
        t=conditional_unit(source,[[1,True],[2,True]],Counter())
        local,hints,whole=checked(source,[t],event(source,{1:True}));self.assertTrue(whole);self.assertEqual(hints[0]['clause'],[-1])
        local,hints,whole=checked(source,[t],event(source,{1:True},((4,5,6),)));self.assertFalse(whole);self.assertEqual(hints,[])
        edited=c.native.normalize([[-1,-2,3],[4,5,6]])[0]
        _,hints,_=checked(edited,[t],event(edited));self.assertEqual(hints,[])

    def test_malformed_coordinate_source_and_subset_bindings_rejected(self):
        source=c.native.normalize([[1,2],[2,3]])[0];ts=[template(source[0])];e=event(source)
        for kind in ('duplicate','absent','overlap','fixed','root','subset','source'):
            s=deepcopy(source);bad=deepcopy(e)
            if kind=='duplicate':bad['mapping'].append(bad['mapping'][0])
            elif kind=='absent':bad['mapping'][0][1]=9999
            elif kind=='overlap':bad['fixed']=[[1,True]]
            elif kind=='fixed':bad['fixed']=[[9999,True]]
            elif kind=='root':bad['root']='bad'
            elif kind=='subset':bad['root']=c.native.token(((-1,-2),),Counter());bad['mapping']=[[1,1],[2,2]]
            else:s=(*s,s[0])
            for module in (c,c.frozen):
                with self.assertRaises(ValueError):module.local_hints(s,ts,bad,Counter())

    def test_malformed_original_template_proofs_never_become_hints(self):
        source=c.native.normalize([[-1,-2,3],[-1,-2,-3]])[0];t=conditional_unit(source,[[1,True],[2,True]],Counter())
        for kind in ('conflict','reason','literal','assumptions'):
            bad=deepcopy(t)
            if kind=='conflict':bad['conflict']=99999
            elif kind=='reason':bad['trace'][0][1]=99999
            elif kind=='literal':bad['trace'][0][0]*=-1
            else:bad['assumptions']=[[1,True]]
            for module in (c,c.frozen):
                with self.assertRaises(ValueError):module.local_hints(source,[bad],event(source),Counter())

    def test_owned_inputs_and_prefix_survive_caller_mutation(self):
        source=[[1,2]];ts=[template((1,2))];e=event(source);row=dict(program=dict(status='unresolved',steps=[],path_limit=256));expected=c.bind(source,ts,row,e,Counter())
        class MutatingCounter(Counter):
            def __setitem__(self,key,value):
                super().__setitem__(key,value)
                if key=='replay_owned_copies':source[0][0]=9999;ts[0]['conflict']=9999;e['root']='bad';row['program']['status']='refuted'
        self.assertEqual(c.bind(source,ts,row,e,MutatingCounter()),expected)
        with self.assertRaises(ValueError):c.bind(source,ts,row,e,Counter())

    def test_nonempty_binary_prefix_and_invalid_path_keep_frozen_checks(self):
        source=c.native.normalize([[1,2],[1,-2],[3,4,5]])[0];e=event(source);local,hints,_=checked(source,[],e)
        p=c.prefix.frozen.discover(local,[],Counter());self.assertEqual(p['status'],'unresolved');self.assertGreater(len(p['steps']),0)
        row=dict(program=p);self.assertEqual(c.bind(source,[],row,e,Counter()),study.prior.bind(source,[],row,e,Counter()))
        bad=deepcopy(row);bad['program']['steps'][0]['forced']*= -1
        with self.assertRaises(ValueError):c.bind(source,[],bad,e,Counter())

    def test_exhaustive_small_sources_and_entailed_clauses(self):
        clauses=((1,),(-1,),(2,),(-2,),(-2,-1),(-2,1),(-1,2),(1,2))
        for mask in range(256):
            source,names=c.native.normalize([cl for i,cl in enumerate(clauses) if mask>>i&1]);ts=[template(cl) for cl in source]
            local,hints,_=checked(source,ts,event(source))
            for bits in product((False,True),repeat=len(names)):
                model=dict(enumerate(bits,1))
                if c.native.holds(local,model):self.assertTrue(all(c.native.holds([h['clause']],model) for h in hints))

    def test_generated_conditioning_and_unlabelled_subsets(self):
        rng=random.Random(260709)
        for _ in range(70):
            source,names=c.native.normalize([[v*rng.choice((-1,1)) for v in rng.sample(range(1,7),rng.randrange(2,5))] for _ in range(rng.randrange(6,20))]);ts=[]
            for _ in range(6):
                assignments=[[v,rng.choice((False,True))] for v in range(1,len(names)+1)]
                t=conditional_unit(source,assignments,Counter())
                if t is not None:ts.append(t)
            fixed={v:rng.choice((False,True)) for v in rng.sample(range(1,len(names)+1),min(2,len(names)))}
            raw=c.native.restrict_scan(source,fixed,Counter());subset=raw[::2]
            for e in (event(source),event(source,fixed),event(source,fixed,subset)):
                local,hints,_=checked(source,ts,e);n=max((abs(l) for cl in local for l in cl),default=0)
                for bits in product((False,True),repeat=n):
                    model=dict(enumerate(bits,1))
                    if c.native.holds(local,model):self.assertTrue(all(c.native.holds([h['clause']],model) for h in hints))


if __name__=='__main__':unittest.main()
