from collections import Counter
import json
from pathlib import Path
import unittest
from experiments.cnf_interacting_pivots import rank_interactions,search
from experiments.cnf_pivot_alternatives import verify_trial
from experiments.cnf_anchored_subsets import AnchoredAdditiveInventory
from experiments.cnf_pattern_inventory import encode


class InteractingPivotTests(unittest.TestCase):
    def test_priority_preserves_every_candidate_and_secondary_order(self):
        source=((1,-2,3),(-1,4),(5,6));rows=[dict(variable=v,score=(v,)) for v in (5,3,6,2,4)]
        counts=Counter();ranked,neighbors=rank_interactions(source,1,rows,counts)
        self.assertEqual([r['variable'] for r in ranked],[2,3,4,5,6])
        self.assertEqual(neighbors,{1,2,3,4});self.assertEqual(counts['interacting_candidates'],3)
        self.assertEqual(counts['independent_candidates'],2);self.assertEqual(counts['interaction_scan_literals'],7)
        self.assertEqual({encode(r) for r in rows},{encode(r) for r in ranked})

    def test_bound_exact_checker_and_repeated_results(self):
        source=json.loads(Path('solver/fixtures/pivot-alternatives.json').read_text())['source']
        h=AnchoredAdditiveInventory(max_depth=0,probe_limit=4,learn_limit=4,clause_growth_limit=2)
        root=h.inspect(source)['root']['key'];counts=Counter()
        records=search(h,root,counts,ancestor_limit=2,trial_limit=3)
        self.assertEqual(len(records),3);self.assertEqual(counts['interacting_trials']+counts['independent_trials'],3)
        for record in records:verify_trial(h,record,Counter())
        before=h.storage();self.assertEqual(encode(search(h,root,Counter(),ancestor_limit=2,trial_limit=3)),encode(records))
        self.assertEqual(before,h.storage());self.assertEqual(search(h,root,Counter(),trial_limit=0),[])
        h.close()


if __name__=='__main__':unittest.main()
