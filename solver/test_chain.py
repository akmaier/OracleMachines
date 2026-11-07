import itertools
from pathlib import Path
import random
import tempfile
import unittest

from solver.persistent import PersistentSolver


def brute(edges,left,right):
    for values in itertools.product(range(2),repeat=len(edges)+1):
        if left&(1<<values[0]) and right&(1<<values[-1]) and all(
            mask & (1<<(2*values[i]+values[i+1])) for i,mask in enumerate(edges)):
            return True
    return False


class ChainTests(unittest.TestCase):
    def test_random_versions_restart_and_witnesses(self):
        rng=random.Random(193)
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'s.db';history=[]
            with PersistentSolver(path) as s:
                state=None;edges=[]
                for _ in range(45):
                    if not edges or len(edges)<7 and rng.randrange(3)==0:
                        added=[rng.randrange(16)];replace={};edges+=added
                    else:
                        added=[];i=rng.randrange(len(edges));edges[i]=rng.randrange(16);replace={i:edges[i]}
                    left,right=rng.randrange(4),rng.randrange(4)
                    result=s.chain(state,append=added,replace=replace,left=left,right=right,witness=True)
                    state=result['state'];history.append((state,list(edges),left,right))
                    self.assertEqual(result['answer'],brute(edges,left,right))
                    if result['answer']:
                        word=result['witness'];self.assertEqual(len(word),len(edges)+1)
                        self.assertTrue(left&(1<<word[0]) and right&(1<<word[-1]))
                        self.assertTrue(all(mask&(1<<(2*word[i]+word[i+1])) for i,mask in enumerate(edges)))
            with PersistentSolver(path) as s:
                for state,edges,left,right in history:
                    self.assertEqual(s.chain(state,left=left,right=right)['answer'],brute(edges,left,right))

    def test_logarithmic_replacement_and_branch_preservation(self):
        with tempfile.TemporaryDirectory() as d, PersistentSolver(Path(d)/'s.db') as s:
            first=s.chain(append=[6]*1024,left=1,right=1)
            changed=s.chain(first['state'],replace={511:9},left=1,right=1)
            self.assertFalse(changed['answer'])
            self.assertEqual(changed['chain']['compositions'],10)
            self.assertEqual(changed['chain']['node_writes'],11)
            self.assertLessEqual(changed['chain']['native_definitions'],11)
            self.assertTrue(s.chain(first['state'],left=1,right=1)['answer'])
            self.assertTrue(s.chain(changed['state'],append=[6],left=1,right=1)['answer'])

    def test_invalid_masks_indices_and_poisoned_summaries(self):
        with tempfile.TemporaryDirectory() as d, PersistentSolver(Path(d)/'s.db') as s:
            state=s.chain(append=[6,6])['state']
            for kwargs in [dict(append=[16]),dict(replace={2:6}),dict(left=4),dict(append=[True])]:
                with self.assertRaises(ValueError):s.chain(state,**kwargs)
            root=s.chain(state)['root'];node=s.chains.read(root)
            with self.assertRaises(ValueError):
                s._request(dict(mode='chain_define',nodes=[dict(id='forged',**(node|{'mask':0}))]))
            self.assertTrue(s.chain(state)['answer'])

if __name__=='__main__':unittest.main()
