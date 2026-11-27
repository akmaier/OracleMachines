from collections import Counter
from copy import deepcopy
from itertools import combinations,product
from unittest.mock import patch
import json,random,unittest
from experiments import cnf_factor_clause_width as f
from experiments import cnf_semantic_buckets as b


def representable(n,bits,width):
    # Independent exhaustive conjunction of every entailed candidate clause.
    accepted=[]
    for size in range(min(width,n)+1):
        for slots in combinations(range(n),size):
            for signs in product((False,True),repeat=size):
                clause=[(i,value) for i,value in zip(slots,signs)]
                if all(not bits>>row&1 or any(bool(row>>i&1)==value for i,value in clause) for row in range(1<<n)):accepted.append(clause)
    return all(bool(bits>>row&1)==all(any(bool(row>>i&1)==value for i,value in clause) for clause in accepted) for row in range(1<<n))


class FactorClauseWidthTests(unittest.TestCase):
    def test_all_three_variable_relations_and_widths(self):
        for n in range(4):
            for bits in range(1<<(1<<n)):
                factor=dict(scope=list(range(1,n+1)),bits=bits)
                for width in range(n+1):
                    proof,_=f.discover(factor,width);self.assertEqual(f.check(factor,proof),proof['status'])
                    self.assertEqual(proof['status']=='cover',representable(n,bits,width))
                    self.assertIn(proof['status'],('cover','obstruction'))

    def test_seeded_tables(self):
        rng=random.Random(2711271800)
        for _ in range(80):
            n=rng.randrange(4,7);factor=dict(scope=list(range(1,n+1)),bits=rng.getrandbits(1<<n));width=rng.randrange(1,4)
            proof,_=f.discover(factor,width);f.check(factor,proof);self.assertEqual(proof['status']=='cover',representable(n,factor['bits'],width))

    def test_budget_is_unknown_not_impossibility(self):
        factor=dict(scope=[1,2,3],bits=0b10010110)
        for budget in (0,1,6,10):
            proof,diag=f.discover(factor,2,budget);f.check(factor,proof);self.assertLessEqual(diag['spent'],budget);self.assertEqual(proof['status'],'unresolved')

    def test_parity_obstruction_requires_full_clause_width(self):
        factor=dict(scope=[2,7,11,30],bits=sum(1<<r for r in range(16) if r.bit_count()%2))
        for width in range(4):
            proof,_=f.discover(factor,width);self.assertEqual(f.check(factor,proof),'obstruction')
        proof,_=f.discover(factor,4);self.assertEqual(f.check(factor,proof),'cover')

    def test_cover_tampering(self):
        factor=dict(scope=[1,2,3],bits=0b11101110);proof,_=f.discover(factor,2)
        self.assertEqual(proof['status'],'cover')
        for mutate in (lambda p:p['clauses'].clear(),lambda p:p['clauses'][0].append(99),lambda p:p['clauses'].append(p['clauses'][0][:])):
            bad=deepcopy(proof);mutate(bad)
            with self.assertRaises(ValueError):f.check(factor,bad)

    def test_obstruction_tampering(self):
        factor=dict(scope=[1,2,3],bits=0b10010110);proof,_=f.discover(factor,2);self.assertEqual(proof['status'],'obstruction')
        for mutate in (lambda p:p['obstruction']['witnesses'].pop(),lambda p:p['obstruction'].__setitem__('row',1),lambda p:p['obstruction']['witnesses'].__setitem__(0,0),lambda p:p.__setitem__('width',3)):
            bad=deepcopy(proof);mutate(bad)
            with self.assertRaises(ValueError):f.check(factor,bad)

    def test_exact_scope_transport(self):
        factor=dict(scope=[1,2,3],bits=0b11101110);proof,_=f.discover(factor,2);names={1:5,2:17,3:103}
        other=dict(scope=list(names.values()),bits=factor['bits']);proof['scope']=other['scope'];proof['clauses']=[[names[abs(l)]*(1 if l>0 else -1) for l in c] for c in proof['clauses']]
        self.assertEqual(f.check(other,proof),'cover')

    def test_changed_table_rejected(self):
        factor=dict(scope=[1,2],bits=7);proof,_=f.discover(factor,2)
        with self.assertRaises(ValueError):f.check(dict(scope=[1,2],bits=6),proof)

    def test_cold_checker_has_no_acquisition(self):
        factor=dict(scope=[1,2,3],bits=0b10010110);proof,_=f.discover(factor,2)
        with patch.object(f,'discover',side_effect=AssertionError('discovery')):self.assertEqual(f.check(factor,json.loads(json.dumps(proof))),'obstruction')

    def test_prefix_sat_transport(self):
        source=[[11,17,23,29]];prefix,_=b.discover(source,work_limit=1)
        self.assertEqual(prefix['status'],'unresolved');prefix['limits']['work_limit']=262144
        proof,_=f.discover_prefix(source,prefix,width=4);got=f.check_prefix(source,prefix,json.loads(json.dumps(proof)))
        self.assertTrue(got['answer']);self.assertTrue(b.native.holds(source,got['model']))

    def test_prefix_unsat_transport_and_active_factor_coverage(self):
        source=[[1,2],[1,-2],[-1,2],[-1,-2]];prefix,_=b.discover(source,work_limit=1);prefix['limits']['work_limit']=262144
        proof,_=f.discover_prefix(source,prefix,2);self.assertFalse(f.check_prefix(source,prefix,proof)['answer'])
        bad=deepcopy(proof);bad['entries'].pop()
        with self.assertRaises(ValueError):f.check_prefix(source,prefix,bad)

    def test_projection_allowance_not_reset(self):
        source=[[1,2],[1,-2]];prefix,_=b.discover(source,work_limit=1);proof,_=f.discover_prefix(source,prefix,2)
        self.assertIsNone(f.check_prefix(source,prefix,proof)['answer']);bad=deepcopy(proof);bad['terminal']['limits']['work_limit']=262144
        with self.assertRaises(ValueError):f.check_prefix(source,prefix,bad)

    def test_prefix_cold_replay_and_changed_witness(self):
        source=[[1,2],[1,-2]];prefix,_=b.discover(source,work_limit=1);prefix['limits']['work_limit']=262144;proof,_=f.discover_prefix(source,prefix,2)
        with patch.object(f,'discover',side_effect=AssertionError('cover')),patch.object(b,'discover',side_effect=AssertionError('bucket')):self.assertTrue(f.check_prefix(source,prefix,json.loads(json.dumps(proof)))['answer'])
        proof['model']=[False,False]
        with self.assertRaises(ValueError):f.check_prefix(source,prefix,proof)

    def test_invalid_policies_and_factor_encodings(self):
        for factor in (dict(scope=[1,1],bits=1),dict(scope=[True],bits=1),dict(scope=[1],bits=4),dict(scope=[1],bits=True)):
            with self.assertRaises(ValueError):f.discover(factor)
        for opts in (dict(width=True),dict(budget=-1),dict(width=13)):
            with self.assertRaises(ValueError):f.discover(dict(scope=[1],bits=1),**opts)


if __name__=='__main__':unittest.main()
