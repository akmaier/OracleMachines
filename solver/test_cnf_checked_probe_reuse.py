from collections import Counter
import copy
import itertools
import json
from pathlib import Path
import random
import tempfile
import unittest

from experiments.cnf_checked_probe_reuse import CheckedProbeReuseInventory
from experiments.cnf_implied_subsumption import ImpliedSubsumptionInventory
from experiments.cnf_pattern_inventory import encode
from experiments.cnf_residual_dag import normalize
from solver.test_cnf_implied_subsumption import implication_source
from solver.test_cnf_signed_subsumption import check_signed_tree


class CheckedProbeReuseTests(unittest.TestCase):
    def test_successful_exact_reuse_and_return_isolation(self):
        h=CheckedProbeReuseInventory();cnf,_=normalize(implication_source())
        proof=h._discover_probes(cnf);h.counts=Counter()
        first=h._check_probes(cnf,proof);before=h.counts['verified_probe_attempts']
        first[1][999]=True
        if isinstance(first[0],list):first[0].append([999])
        second=h._check_probes(cnf,proof)
        expected=ImpliedSubsumptionInventory._check_probes(h,cnf,proof)
        self.assertEqual(encode(second),encode(expected));self.assertNotIn(999,second[1])
        self.assertEqual(h.counts['checked_probe_hits'],1)
        self.assertEqual(h.counts['verified_probe_attempts'],2*before)
        self.assertLessEqual(h.probe_cache_state()['bytes'],h.probe_cache_state()['limit_bytes'])
        h.close();self.assertEqual(h.probe_cache_state()['entries'],0)

    def test_tuple_attempt_container_cannot_alias_valid_cached_json(self):
        h=CheckedProbeReuseInventory();cnf,_=normalize(implication_source())
        proof=h._discover_probes(cnf);h._check_probes(cnf,proof)
        bad=copy.deepcopy(proof);bad['attempts']=tuple(bad['attempts'])
        self.assertEqual(encode(proof),encode(bad))
        with self.assertRaises(ValueError):ImpliedSubsumptionInventory._check_probes(h,cnf,bad)
        hits=h.counts['checked_probe_hits'];entries=h.probe_cache_state()['entries']
        with self.assertRaises(ValueError):h._check_probes(cnf,bad)
        self.assertEqual(h.counts['checked_probe_hits'],hits)
        self.assertEqual(h.probe_cache_state()['entries'],entries)
        self.assertEqual(h.counts['checked_probe_uncacheable_inputs'],1);h.close()

    def test_changed_source_proof_and_policy_do_not_alias(self):
        h=CheckedProbeReuseInventory();cnf,_=normalize(implication_source())
        proof=h._discover_probes(cnf);h._check_probes(cnf,proof)
        bad=copy.deepcopy(proof)
        attempt=next(a for a in bad['attempts'] if a['certificate']['units'])
        attempt['certificate']['units'][0][1]=9999
        bad_bool=copy.deepcopy(proof);bad_bool['attempts'][0]['variable']=True
        bad_order=copy.deepcopy(proof);bad_order['attempts'].reverse()
        for malformed in (bad,bad_bool,bad_order):
            entries=h.probe_cache_state()['entries'];hits=h.counts['checked_probe_hits']
            with self.assertRaises(ValueError):h._check_probes(cnf,malformed)
            self.assertEqual(h.probe_cache_state()['entries'],entries)
            self.assertEqual(h.counts['checked_probe_hits'],hits)
        for changed in (cnf+((99,),),tuple(reversed(cnf)),cnf[:-1]):
            hits=h.counts['checked_probe_hits']
            try:expected=ImpliedSubsumptionInventory._check_probes(h,changed,proof)
            except ValueError:
                with self.assertRaises(ValueError):h._check_probes(changed,proof)
            else:self.assertEqual(encode(h._check_probes(changed,proof)),encode(expected))
            self.assertEqual(h.counts['checked_probe_hits'],hits)
        h.config['probe_limit']=0;hits=h.counts['checked_probe_hits']
        with self.assertRaises(ValueError):h._check_probes(cnf,proof)
        self.assertEqual(h.counts['checked_probe_hits'],hits)
        h.config['probe_limit']=4;h._check_probes(cnf,proof)
        self.assertEqual(h.counts['checked_probe_hits'],hits+1);h.close()

    def test_disabled_oversized_lru_and_limits(self):
        cnf,_=normalize(implication_source());h=CheckedProbeReuseInventory();proof=h._discover_probes(cnf)
        h._check_probes(cnf,proof);entry_size=h.probe_cache_state()['bytes'];h.close()
        for budget in (0,1,entry_size-1,entry_size):
            h=CheckedProbeReuseInventory(checked_probe_bytes=budget)
            for _ in range(2):h._check_probes(cnf,proof)
            self.assertLessEqual(h.probe_cache_state()['bytes'],budget)
            self.assertEqual(h.counts['checked_probe_hits'],int(budget==entry_size))
            if budget and budget<entry_size:self.assertEqual(h.counts['checked_probe_oversize'],2)
            h.close()
        h=CheckedProbeReuseInventory(checked_probe_bytes=entry_size+32)
        h._check_probes(cnf,proof);other=tuple(tuple(l*10 for l in c) for c in cnf)
        other_proof=h._discover_probes(other);h._check_probes(other,other_proof)
        self.assertGreater(h.counts['checked_probe_evictions'],0)
        h._check_probes(cnf,proof);self.assertEqual(h.counts['checked_probe_hits'],0)
        self.assertLessEqual(h.probe_cache_state()['peak_bytes'],entry_size+32);h.close()
        for invalid in (-1,True,1.5,'1024'):
            with self.assertRaises(ValueError):CheckedProbeReuseInventory(checked_probe_bytes=invalid)

    def test_saved_frontier_checks_and_mutation_rejection(self):
        rows=json.loads(Path('experiments/results/cnf-implied-subsumption/mechanisms.json').read_text())['frontier']
        old=ImpliedSubsumptionInventory();new=CheckedProbeReuseInventory(checked_probe_bytes=32768)
        for row in rows:
            cnf=row['cnf'];proof=row['probing'];expected=old._check_probes(cnf,proof)
            self.assertEqual(encode(expected),encode(new._check_probes(cnf,proof)))
            self.assertEqual(encode(expected),encode(new._check_probes(cnf,proof)))
            bad=copy.deepcopy(proof)
            if bad['attempts']:bad['attempts'].pop()
            else:bad['unexpected']=True
            with self.assertRaises(ValueError):new._check_probes(cnf,bad)
        self.assertEqual(len(rows),148);self.assertGreater(new.counts['checked_probe_hits'],0)
        old.close();new.close()

    def test_small_fibers_and_byte_identical_cold_archive(self):
        clauses=[tuple(s*(i+1) for i,s in enumerate(signs) if s)
                 for signs in itertools.product((-1,0,1),repeat=2)]
        cases=[[c for i,c in enumerate(clauses) if mask>>i&1] for mask in range(512)]
        rng=random.Random(202611091100)
        cases += [implication_source()]+[[tuple(rng.choice((-1,1))*v for v in rng.sample(range(1,7),3))
                                         for _ in range(24)] for _ in range(20)]
        with tempfile.TemporaryDirectory() as tmp:
            snapshots=[]
            for cls in (ImpliedSubsumptionInventory,CheckedProbeReuseInventory):
                path=Path(tmp)/f'{cls.__name__}.db';h=cls(path,max_depth=1)
                for source in cases:
                    result=h.inspect(source);check_signed_tree(h,result['root']['key'])
                snapshots.append(dict(h.db.execute('SELECT id,payload FROM cnf_patterns_v1')))
                h.close()
            self.assertEqual(snapshots[0],snapshots[1])
            path=Path(tmp)/'ImpliedSubsumptionInventory.db';raw=path.read_bytes()
            h=CheckedProbeReuseInventory(path,max_depth=1);self.assertEqual(h.probe_cache_state()['entries'],0)
            for source in cases:
                result=h.inspect(source)
                self.assertEqual(result['metrics'].get('inserted_nodes',0),0)
                self.assertEqual(result['metrics']['inserted_sources'],0)
            h.close();self.assertEqual(raw,path.read_bytes())

    def test_cold_corruption_is_checked_before_admission(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'history.db';h=ImpliedSubsumptionInventory(path,max_depth=0)
            result=h.inspect(implication_source());key=result['root']['key'];bad=copy.deepcopy(h._load(key))
            attempt=next(a for a in bad['profile']['probing']['attempts'] if a['certificate']['units'])
            attempt['certificate']['units'][0][1]=9999
            with h.db:h.db.execute('UPDATE cnf_patterns_v1 SET payload=? WHERE id=?',(encode(bad),key))
            h.close();h=CheckedProbeReuseInventory(path,max_depth=0)
            with self.assertRaises(ValueError):h.inspect(implication_source())
            self.assertEqual(h.probe_cache_state()['entries'],0);h.close()
