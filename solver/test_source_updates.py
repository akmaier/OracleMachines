"""Source edits against exhaustive truth tables, adversarial transport and replay."""
import itertools
import random
import tempfile
import unittest
from collections import Counter
from pathlib import Path

from solver.persistent import PersistentSolver
from solver.resources import BudgetExceeded
from solver.layered import compose


def sat(clauses,n):
    return any(all(any(a[abs(lit)-1]==(lit>0) for lit in clause) for clause in clauses)
               for a in itertools.product((False,True),repeat=n))


class SourceUpdateTests(unittest.TestCase):
    def test_source_verdict_requires_complete_minimal_root(self):
        with tempfile.TemporaryDirectory() as d,PersistentSolver(Path(d)/'s.db') as s:
            s._request(dict(mode='source_init',id='coverage',width=1,layers=[[1],[2],[3],[4]]))
            nodes=[];levels={}
            for height in range(4):
                for start in range(0,8,1<<height):
                    name=f'cover-{start}-{height}'
                    body=dict(id=name,layout='coverage',width=1,start=start,height=height,
                              mask=15 if start<3 else 9)
                    if height==0:body['clauses']=[]
                    else:body.update(left=levels[start,height-1],right=levels[start+(1<<(height-1)),height-1])
                    nodes.append(body);levels[start,height]=name
            s._request(dict(mode='source_define',nodes=nodes))
            for witness in (False,True):
                for bad in (levels[0,0],levels[0,1],levels[2,1],levels[3,0],levels[0,3]):
                    with self.assertRaisesRegex(ValueError,'cover the full partition'):
                        s._request(dict(mode='source_query',root=bad,witness=witness))
                    with self.assertRaisesRegex(ValueError,'cover the full partition'):
                        s._request(dict(mode='source_patch',base=bad,root=bad,edits=[],witness=witness))
                valid=s._request(dict(mode='source_query',root=levels[0,2],witness=witness))
                self.assertIs(valid['answer'],True)
                if witness:self.assertEqual(len(valid['witness']),4)
                else:self.assertIsNone(valid['witness'])
            with self.assertRaises(ValueError):
                s._request(dict(mode='source_query',root=levels[0,2],witness='invalid'))

    def test_returned_patch_verdict_matches_independent_flat_cnf(self):
        rng=random.Random(1904);answers=set()
        with tempfile.TemporaryDirectory() as d,PersistentSolver(Path(d)/'s.db') as s:
            for edges in (1,3,5):
                initial=s.source_cnf(1,[],[[i] for i in range(1,edges+2)])
                versions=[(initial,[[] for _ in range(edges)])]
                for step in range(18):
                    base,original=rng.choice(versions);buckets=list(original)
                    changes={}
                    for edge in rng.sample(range(edges),rng.randrange(1,edges+1)):
                        choices=([],[[]],[[edge+1]],[[edge+1,-edge-1],[edge+1,-edge-1]],
                                 [[edge+1],[-edge-2]],[[edge+1,edge+2]])
                        changes[edge]=choices[(step+edge)%len(choices)]
                        buckets[edge]=changes[edge]
                    updated=s.source_cnf(base=base['state'],replace=changes)
                    flat=[clause for bucket in buckets for clause in bucket]
                    expected=sat(flat,edges+1);answers.add(expected)
                    request=[dict(edge=i,clauses=c) for i,c in changes.items()];rng.shuffle(request)
                    for witness in (False,True):
                        result=s._request(dict(mode='source_patch',base=base['root'],root=updated['root'],
                                               edits=request,witness=witness))['verdict']
                        self.assertIs(result['answer'],expected)
                        direct=s._request(dict(mode='source_query',root=updated['root'],witness=witness))
                        self.assertIs(direct['answer'],expected)
                        if witness and expected:
                            self.assertEqual(len(result['witness']),edges+1)
                            values=[bool(word&1) for word in result['witness']]
                            self.assertTrue(all(any(values[abs(lit)-1]==(lit>0) for lit in clause) for clause in flat))
                        else:self.assertIsNone(result['witness'])
                    versions.append((updated,buckets))
        self.assertEqual(answers,{False,True})

    def test_patch_decoder_handles_full_batch_and_rejects_over_capacity(self):
        with tempfile.TemporaryDirectory() as d,PersistentSolver(Path(d)/'s.db') as s:
            s._request(dict(mode='source_init',id='patch-cap',width=1,layers=[[i] for i in range(1,4098)]))
            edits=[dict(edge=i,clauses=[]) for i in range(4096)]
            # The unknown root is reached only after decoding the entire legal
            # batch. This exercises the recursive decoder at its actual cap.
            with self.assertRaisesRegex(ValueError,'Unknown'):
                s._request(dict(mode='source_patch',base='missing',root='missing',edits=edits,witness=False))
            with self.assertRaisesRegex(ValueError,'batch exceeds capacity'):
                s._request(dict(mode='source_patch',base='missing',root='missing',edits=edits+[edits[0]],witness=False))
            self.assertTrue(s._request(dict(mode='source_init',id='after-cap',width=1,layers=[[1],[2]]))['valid'])

    def test_patch_checks_exact_requested_buckets_across_split_and_padding(self):
        with tempfile.TemporaryDirectory() as d,PersistentSolver(Path(d)/'s.db') as s:
            base=s.source_cnf(1,[],[[i] for i in range(1,7)])
            changes={0:[[1,-1],[1,-1]],4:[[5,-5]]}
            new=s.source_cnf(base=base['state'],replace=changes)
            self.assertTrue(new['answer'])
            self.assertEqual(new['source_updates']['patch_visits'],11)
            def patch(edits,old=base['root'],root=new['root']):
                return s._request(dict(mode='source_patch',base=old,root=root,edits=edits,witness=False))
            requested=[dict(edge=i,clauses=c) for i,c in changes.items()]
            for edits in (requested,list(reversed(requested))):
                result=patch(edits)
                self.assertTrue(result['verdict']['answer'])
                self.assertEqual(result['patch_visits'],11)
            # Every forged payload has the same universal relation. Counts,
            # literal order and the exact original clauses must still match.
            for clauses in ([],[[1,-1]],[[-1,1],[1,-1]]):
                with self.assertRaisesRegex(ValueError,'clauses differ'):
                    patch([dict(edge=0,clauses=clauses),requested[1]])
            for edits in ([],requested[:1],requested[1:]):
                with self.assertRaisesRegex(ValueError,'unedited'):
                    patch(edits)
            for edits in (requested+[requested[0]],requested+[dict(edge=5,clauses=[])],
                          [dict(edge=-1,clauses=[])],[dict(edge=0,clauses='invalid')]):
                with self.assertRaises(ValueError):patch(edits)
            self.assertEqual(patch([],old=new['root'])['patch_visits'],1)
            self.assertTrue(patch(requested,old=new['root'])['verdict']['answer'])
            self.assertTrue(s.source_cnf(base=base['state'])['answer'])

    def test_patch_rejects_equivalent_unedited_alias_and_wrong_partition(self):
        with tempfile.TemporaryDirectory() as d,PersistentSolver(Path(d)/'s.db') as s:
            s._request(dict(mode='source_init',id='patch-alias',width=1,layers=[[1],[2],[3]]))
            def leaf(name,start,clauses):
                return dict(id=name,layout='patch-alias',width=1,start=start,height=0,mask=15,clauses=clauses)
            def root(name,left,right):
                return dict(id=name,layout='patch-alias',width=1,start=0,height=1,mask=15,left=left,right=right)
            s._request(dict(mode='source_define',nodes=[leaf('a',0,[]),leaf('b',0,[[1,-1]]),
                leaf('r',1,[]),leaf('alias',1,[]),root('old','a','r'),root('new','b','r'),
                root('alias-root','b','alias')]))
            def patch(base,root,edits):
                return s._request(dict(mode='source_patch',base=base,root=root,edits=edits,witness=False))
            edit=[dict(edge=0,clauses=[[1,-1]])]
            self.assertTrue(patch('old','new',edit)['verdict']['answer'])
            with self.assertRaisesRegex(ValueError,'unedited'):patch('old','alias-root',edit)
            with self.assertRaisesRegex(ValueError,'partition'):patch('a','new',edit)
            with self.assertRaisesRegex(ValueError,'Unknown'):patch('missing','new',edit)
            with self.assertRaisesRegex(ValueError,'Unknown'):patch('missing','missing',[])
            self.assertTrue(patch('old','new',edit)['verdict']['answer'])

    def test_native_lifetime_matches_independent_live_graph_recount(self):
        rng=random.Random(1903)
        with tempfile.TemporaryDirectory() as d,PersistentSolver(Path(d)/'s.db') as s:
            s._request(dict(mode='source_init',id='graph',width=1,layers=[[i] for i in range(1,10)]))
            definitions=[];levels={}
            for height in range(4):
                for start in range(0,8,1<<height):
                    names=[]
                    for variant in range(16 if height==3 else 2):
                        name=f'n-{height}-{start}-{variant}'
                        body=dict(id=name,layout='graph',width=1,start=start,height=height,mask=15)
                        if height==0:body['clauses']=[] if variant==0 else [[start+1,-start-1]]
                        else:
                            body['left']=levels[height-1,start][variant%2]
                            body['right']=levels[height-1,start+(1<<(height-1))][(variant//2)%2]
                        definitions.append(body);names.append(name)
                    levels[height,start]=names
            self.assertEqual(len(definitions),44)
            s._request(dict(mode='source_define',nodes=definitions))
            live={body['id']:body for body in definitions}
            rejected=removed=duplicates=0
            for _ in range(180):
                if not live:break
                # Recompute the full graph independently of the incremental
                # implementation, then compare its zero-count deletion frontier.
                incoming=Counter(child for body in live.values() if body['height']
                                 for child in (body['left'],body['right']))
                name=rng.choice(list(live));body=live[name]
                if rng.randrange(4)==0:
                    result=s._request(dict(mode='source_define',nodes=[body,body]))
                    self.assertEqual(result['original_source_nodes'],0);duplicates+=1
                elif incoming[name]:
                    with self.assertRaisesRegex(ValueError,'referenced'):
                        s._request(dict(mode='source_drop',ids=[name]))
                    rejected+=1
                else:
                    self.assertEqual(s._request(dict(mode='source_drop',ids=[name]))['evicted'],1)
                    del live[name];removed+=1
                roots=[key for key,value in live.items() if value['height']==3]
                if roots:
                    self.assertTrue(s._request(dict(mode='source_query',root=rng.choice(roots),witness=True))['answer'])
            self.assertGreater(rejected,0);self.assertGreater(removed,0);self.assertGreater(duplicates,0)
            remaining=sorted(live,key=lambda key:live[key]['height'],reverse=True)
            self.assertEqual(s._request(dict(mode='source_drop',ids=remaining))['evicted'],len(remaining))
            # Rebuild the same names after complete deletion. Stale or inflated
            # reference counts would obstruct this second complete reclamation.
            s._request(dict(mode='source_define',nodes=definitions))
            for root in levels[3,0]:
                self.assertTrue(s._request(dict(mode='source_query',root=root,witness=False))['answer'])
            order=[body['id'] for body in sorted(definitions,key=lambda body:body['height'],reverse=True)]
            self.assertEqual(s._request(dict(mode='source_drop',ids=order))['evicted'],44)

    def test_named_join_uses_exact_sources_even_with_equal_relations(self):
        with tempfile.TemporaryDirectory() as d,PersistentSolver(Path(d)/'s.db') as s:
            s._request(dict(mode='source_init',id='links',width=1,layers=[[1],[2],[3]]))
            leaf=dict(id='empty',layout='links',width=1,start=0,height=0,mask=15,clauses=[])
            tautologies=[[1,-1],[1,-1]]
            other=dict(leaf,id='other',clauses=tautologies)
            right=dict(leaf,id='right',start=1)
            root=dict(id='root',layout='links',width=1,start=0,height=1,left='other',right='right',mask=15)
            s._request(dict(mode='source_define',nodes=[leaf,other,right,root]))
            # Both candidate left children have identical relations, but the
            # chosen name determines the exact original clause occurrences.
            with self.assertRaisesRegex(ValueError,'Original source clauses differ'):
                s._request(dict(mode='source_bind',root='root',width=1,layers=[[1],[2],[3]],clauses=[],witness=False))
            bound=s._request(dict(mode='source_bind',root='root',width=1,layers=[[1],[2],[3]],clauses=tautologies,witness=True))
            self.assertTrue(bound['verdict']['answer'])
            for changes in (dict(left='missing'),dict(right='missing'),dict(left=5),dict(right=None)):
                with self.assertRaises(ValueError):
                    s._request(dict(mode='source_define',nodes=[dict(root,id='bad',**changes)]))
            with self.assertRaisesRegex(ValueError,'identity changed'):
                s._request(dict(mode='source_define',nodes=[dict(other,clauses=[])]))
            self.assertTrue(s._request(dict(mode='source_query',root='root',witness=False))['answer'])

    def test_serialized_masks_must_match_even_when_sat_answer_matches(self):
        with tempfile.TemporaryDirectory() as d,PersistentSolver(Path(d)/'s.db') as s:
            s._request(dict(mode='source_init',id='masks',width=1,layers=[[1],[2],[3]]))
            left=dict(id='left',layout='masks',width=1,start=0,height=0,mask=12,clauses=[[1]])
            right=dict(left,id='right',start=1,mask=15,clauses=[])
            pad=dict(right,id='pad',start=2,mask=9)
            root=dict(id='root',layout='masks',width=1,start=0,height=1,left='left',right='right',mask=12)
            for body in (left,pad):
                with self.assertRaises(ValueError):
                    s._request(dict(mode='source_define',nodes=[dict(body,mask=15)]))
            s._request(dict(mode='source_define',nodes=[left,right,pad]))
            for mask in (15,0,-1,'12',None):
                with self.assertRaises(ValueError):
                    s._request(dict(mode='source_define',nodes=[dict(root,mask=mask)]))
            missing=dict(root);del missing['mask']
            with self.assertRaises(ValueError):s._request(dict(mode='source_define',nodes=[missing]))
            s._request(dict(mode='source_define',nodes=[root]))
            result=s._request(dict(mode='source_query',root='root',witness=True))
            self.assertTrue(result['answer']);self.assertEqual(result['witness'][0],1)

    def test_named_children_survive_until_last_registered_parent_is_removed(self):
        with tempfile.TemporaryDirectory() as d,PersistentSolver(Path(d)/'s.db') as s:
            s._request(dict(mode='source_init',id='lifetime',width=1,layers=[[1],[2],[3]]))
            left=dict(id='left',layout='lifetime',width=1,start=0,height=0,mask=15,clauses=[])
            right=dict(left,id='right',start=1)
            root=dict(id='root-0',layout='lifetime',width=1,start=0,height=1,left='left',right='right',mask=15)
            roots=[dict(root,id=f'root-{i}') for i in range(12)]
            s._request(dict(mode='source_define',nodes=[left,right]+roots))
            order=list(range(12));random.Random(1902).shuffle(order)
            for i in order:
                for child in ('left','right'):
                    with self.assertRaisesRegex(ValueError,'referenced'):
                        s._request(dict(mode='source_drop',ids=[child]))
                self.assertTrue(s._request(dict(mode='source_query',root=f'root-{i}',witness=False))['answer'])
                s._request(dict(mode='source_drop',ids=[f'root-{i}']))
            self.assertEqual(s._request(dict(mode='source_drop',ids=['left','right']))['evicted'],2)

    def test_native_paired_store_failed_eviction_batches_are_atomic(self):
        with tempfile.TemporaryDirectory() as d,PersistentSolver(Path(d)/'s.db') as s:
            s._request(dict(mode='source_init',id='paired',width=1,layers=[[1],[2],[3]]))
            leaves=[dict(id=f'leaf-{i}',layout='paired',width=1,start=i,height=0,mask=15,clauses=[])
                    for i in range(2)]
            root=dict(id='root',layout='paired',width=1,start=0,height=1,left='leaf-0',right='leaf-1',mask=15)
            s._request(dict(mode='source_define',nodes=leaves+[root]))
            for ids,error in ((['root','missing'],'Unknown evicted'),(['root','root'],'Unknown evicted'),
                              (['leaf-0'],'referenced')):
                with self.assertRaisesRegex(ValueError,error):
                    s._request(dict(mode='source_drop',ids=ids))
                self.assertTrue(s._request(dict(mode='source_query',root='root',witness=True))['answer'])
                # A failed parent-first batch must restore incoming counts as
                # well as both maps; otherwise this child could be removed.
                with self.assertRaisesRegex(ValueError,'referenced'):
                    s._request(dict(mode='source_drop',ids=['leaf-1']))
            self.assertEqual(s._request(dict(mode='source_drop',ids=['root','leaf-0','leaf-1']))['evicted'],3)
            with self.assertRaisesRegex(ValueError,'Unknown source root'):
                s._request(dict(mode='source_query',root='root',witness=False))

    def test_native_paired_store_reused_names_bind_new_original_clauses(self):
        with tempfile.TemporaryDirectory() as d,PersistentSolver(Path(d)/'s.db') as s:
            s._request(dict(mode='source_init',id='reuse',width=1,layers=[[1],[2],[3]]))
            first=dict(id='leaf',layout='reuse',width=1,start=0,height=0,mask=15,clauses=[])
            other=dict(first,id='other-leaf',clauses=[[1,-1],[1,-1]])
            last=dict(first,id='last',start=1)
            root=dict(id='root',layout='reuse',width=1,start=0,height=1,left='leaf',right='last',mask=15)
            other_root=dict(root,id='other-root',left='other-leaf')
            s._request(dict(mode='source_define',nodes=[first,other,last,root,other_root]))
            s._request(dict(mode='source_drop',ids=['root','leaf']))
            with self.assertRaisesRegex(ValueError,'referenced'):
                s._request(dict(mode='source_drop',ids=['last']))
            self.assertTrue(s._request(dict(mode='source_query',root='other-root',witness=True))['answer'])
            replacement=dict(first,clauses=[[],[]],mask=0)
            defined=s._request(dict(mode='source_define',nodes=[replacement,dict(root,mask=0)]))
            self.assertEqual(defined['original_clause_entries'],2)
            self.assertFalse(s._request(dict(mode='source_query',root='root',witness=True))['answer'])
            # Equal relation masks do not identify original clause arrays.
            with self.assertRaisesRegex(ValueError,'Original source clauses differ'):
                s._request(dict(mode='source_bind',root='other-root',width=1,layers=[[1],[2],[3]],clauses=[],witness=False))
            bound=s._request(dict(mode='source_bind',root='root',width=1,layers=[[1],[2],[3]],clauses=[[],[]],witness=False))
            self.assertFalse(bound['verdict']['answer'])

    def test_native_metadata_decode_failure_rolls_back_paired_insertion(self):
        with tempfile.TemporaryDirectory() as d,PersistentSolver(Path(d)/'s.db') as s:
            s._request(dict(mode='source_init',id='metadata',width=1,layers=[[1],[2]]))
            first=dict(id='root',layout='metadata',width=1,start=0,height=0,mask=15,clauses=[])
            for field in ('id','layout','width','start','height','clauses'):
                bad=dict(first,id='bad');del bad[field]
                with self.assertRaises(ValueError):
                    s._request(dict(mode='source_define',nodes=[first,bad]))
                with self.assertRaisesRegex(ValueError,'Unknown source root'):
                    s._request(dict(mode='source_query',root='root',witness=False))
            s._request(dict(mode='source_define',nodes=[first]))
            self.assertTrue(s._request(dict(mode='source_query',root='root',witness=False))['answer'])

    def test_indexed_native_joins_require_consecutive_intervals(self):
        with tempfile.TemporaryDirectory() as d,PersistentSolver(Path(d)/'s.db') as s:
            s._request(dict(mode='source_init',id='indexed',width=1,layers=[[101],[202],[303],[404]]))
            buckets=[[[202]],[[-202]],[]]
            masks=s._request(dict(mode='source_compile',edits=[dict(edge=i,clauses=b) for i,b in enumerate(buckets)]))['masks']
            leaves=[dict(id=f'leaf-{i}',layout='indexed',width=1,start=i,height=0,mask=mask,clauses=bucket)
                    for i,(mask,bucket) in enumerate(zip(masks+[9],buckets+[[]]))]
            defined=s._request(dict(mode='source_define',nodes=leaves))
            self.assertEqual([defined[k] for k in ('original_source_nodes','original_clause_entries','original_literal_entries')],[4,2,2])
            joined=dict(id='left',layout='indexed',width=1,start=0,height=1,
                        left='leaf-0',right='leaf-1',mask=compose(masks[0],masks[1],2))
            for changes,error in ((dict(right='leaf-0'),'consecutive'),(dict(start=1),'consecutive'),
                                  (dict(left='leaf-1',right='leaf-0'),'consecutive'),(dict(height=2),'Unbalanced'),
                                  (dict(width=2),'width'),(dict(layout='other'),'layout')):
                with self.assertRaisesRegex(ValueError,error):
                    s._request(dict(mode='source_define',nodes=[dict(joined,**changes)]))
            right=dict(id='right',layout='indexed',width=1,start=2,height=1,left='leaf-2',right='leaf-3',mask=masks[2])
            root=dict(id='root',layout='indexed',width=1,start=0,height=2,left='left',right='right',mask=0)
            s._request(dict(mode='source_define',nodes=[joined,right,root]))
            self.assertFalse(s._request(dict(mode='source_query',root='root',witness=True))['answer'])
            # Both local positive/negative units admit boundary pairs; the original
            # variable 202 cannot satisfy their conjunction on the shared block.
            self.assertNotEqual(masks[0],0);self.assertNotEqual(masks[1],0)
            duplicate=s._request(dict(mode='source_define',nodes=leaves+[joined,right,root]))
            self.assertEqual([duplicate[k] for k in ('original_source_nodes','original_clause_entries','original_literal_entries')],[0,0,0])

    def test_indexed_context_reset_and_failed_batch_leave_no_stale_nodes(self):
        with tempfile.TemporaryDirectory() as d,PersistentSolver(Path(d)/'s.db') as s:
            layout=dict(mode='source_init',id='old',width=1,layers=[[1],[2]])
            s._request(layout)
            leaf=dict(id='root',layout='old',width=1,start=0,height=0,mask=15,clauses=[])
            s._request(dict(mode='source_define',nodes=[leaf]))
            with self.assertRaisesRegex(ValueError,'identity changed'):
                s._request(dict(layout,layers=[[3],[4]]))
            self.assertTrue(s._request(dict(mode='source_query',root='root',witness=False))['answer'])
            s._request(dict(mode='source_init',id='new',width=2,layers=[[3,4],[5]]))
            with self.assertRaisesRegex(ValueError,'Unknown source root'):
                s._request(dict(mode='source_query',root='root',witness=False))
            with self.assertRaisesRegex(ValueError,'layout mismatch'):
                s._request(dict(mode='source_define',nodes=[leaf]))
            first=dict(id='root',layout='new',width=2,start=0,height=0,mask=65535,clauses=[])
            bad=dict(first,id='bad',mask=0)
            with self.assertRaisesRegex(ValueError,'mask'):
                s._request(dict(mode='source_define',nodes=[first,bad]))
            with self.assertRaisesRegex(ValueError,'Unknown source root'):
                s._request(dict(mode='source_query',root='root',witness=False))
            checked=s._request(dict(mode='source_define',nodes=[first]))
            self.assertEqual(checked['original_source_nodes'],1)
            self.assertTrue(s._request(dict(mode='source_query',root='root',witness=False))['answer'])

    def test_original_payload_counts_sparse_layout_edits_and_restart(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'s.db';large=2**90
            layers=[[],[large+2,large+1],[],[large+3]]
            with PersistentSolver(path) as s:
                first=s.source_cnf(2,[[large+1]],layers)
                counts=first['source_updates']
                self.assertEqual([counts[k] for k in ('original_source_nodes','original_clause_entries','original_literal_entries')],[7,1,1])
                # Move the unit to edge zero, then contradict it across edge one.
                moved=s.source_cnf(base=first['state'],replace={0:[[large+1]],1:[]})
                negative=s.source_cnf(base=moved['state'],replace={1:[[-large-1]]})
                self.assertFalse(negative['answer'])
                counts=negative['source_updates']
                self.assertEqual([counts[k] for k in ('original_source_nodes','original_clause_entries','original_literal_entries')],[3,1,1])
                deleted=s.source_cnf(base=negative['state'],replace={0:[]})
                self.assertTrue(deleted['answer'])
                unchanged=s.source_cnf(base=negative['state'])
                self.assertEqual([unchanged['source_updates'][k] for k in ('original_source_nodes','original_clause_entries','original_literal_entries')],[0,0,0])
            with PersistentSolver(path) as s:
                for state,answer in ((negative,False),(first,True),(deleted,True),(moved,True)):
                    self.assertEqual(s.source_cnf(base=state['state'],witness=True)['answer'],answer)

    def test_initial_binding_has_checked_counts_and_warm_edits_do_not_rescan(self):
        with tempfile.TemporaryDirectory() as d,PersistentSolver(Path(d)/'s.db') as s:
            for width in (1,2,4):
                clauses=[[10],[-30,40]];layers=[[10],[20],[30],[40]]
                q=1<<width
                first=s.source_cnf(width,clauses,layers,witness=True)
                metrics=first['source_updates']
                self.assertTrue(first['answer'])
                self.assertEqual(metrics['binding_visits'],7)
                self.assertEqual(metrics['binding_leaves'],4)
                self.assertEqual(metrics['binding_relation_comparisons'],4)
                self.assertEqual(metrics['binding_cell_bound'],4*q*q)
                self.assertEqual(metrics['binding_source_test_bound'],(4+2+3)*q*q)
                for result in (s.source_cnf(base=first['state']),s.source_cnf(base=first['state'],replace={0:[[]]})):
                    for field in ('binding_leaves','binding_relation_comparisons','binding_cell_bound','binding_source_test_bound'):
                        self.assertEqual(result['source_updates'][field],0)
                full=s.layered_cnf(width,clauses,layers)
                for field in ('binding_leaves','binding_relation_comparisons','binding_cell_bound','binding_source_test_bound'):
                    self.assertEqual(full['compilation'][field],metrics[field])

    def test_global_grouping_matches_every_complete_assignment(self):
        rng=random.Random(1901)
        with tempfile.TemporaryDirectory() as d,PersistentSolver(Path(d)/'s.db') as s:
            for width in (1,2,3):
                names=[(1<<80)+113*k for k in range(1,3*width+1)]
                rng.shuffle(names)
                layers=[names[i*width:(i+1)*width] for i in range(3)]
                positions={v:i for i,block in enumerate(layers) for v in block}
                for _ in range(20):
                    clauses=[]
                    for _ in range(rng.randrange(9)):
                        edge=rng.randrange(2);scope=layers[edge]+layers[edge+1]
                        clause=[rng.choice(scope)*rng.choice((-1,1)) for _ in range(rng.randrange(5))]
                        clauses.append(clause)
                        if rng.randrange(4)==0:clauses.append(list(clause))
                    rng.shuffle(clauses)
                    expected=[[],[]]
                    for clause in clauses:
                        edge=min(min((positions[abs(lit)] for lit in clause),default=0),1)
                        expected[edge].append(clause)
                    compiled=s._request(dict(mode='layered_compile',width=width,layers=layers,clauses=clauses))
                    self.assertEqual(compiled['buckets'],expected)
                    self.assertEqual(Counter(map(tuple,clauses)),Counter(tuple(c) for b in compiled['buckets'] for c in b))
                    satisfiable=False;states=1<<width
                    for bits in itertools.product((False,True),repeat=len(names)):
                        values=dict(zip(names,bits))
                        words=[sum(int(values[v])<<j for j,v in enumerate(block)) for block in layers]
                        original=all(any(values[abs(lit)]==(lit>0) for lit in c) for c in clauses)
                        grouped=all(bool(mask&(1<<(words[i]*states+words[i+1]))) for i,mask in enumerate(compiled['masks']))
                        self.assertEqual(grouped,original)
                        satisfiable |= original
                    result=s.source_cnf(width,clauses,layers,witness=True)
                    self.assertEqual(result['answer'],satisfiable)
                    if result['answer']:
                        values={v:bool(result['witness'][i]&(1<<j)) for i,block in enumerate(layers) for j,v in enumerate(block)}
                        self.assertTrue(all(any(values[abs(lit)]==(lit>0) for lit in c) for c in clauses))

    def test_nonempty_local_relations_can_have_no_consistent_global_path(self):
        layers=[[10],[20],[30]];clauses=[[10],[-10,20],[-20],[30]]
        with tempfile.TemporaryDirectory() as d,PersistentSolver(Path(d)/'s.db') as s:
            compiled=s._request(dict(mode='layered_compile',width=1,layers=layers,clauses=clauses))
            self.assertTrue(all(compiled['masks']))
            self.assertFalse(s.source_cnf(1,clauses,layers)['answer'])

    def test_grouping_preserves_repeated_empty_clauses_and_last_block_units(self):
        clauses=[[77],[],[9],[77],[],[9],[-77]]
        with tempfile.TemporaryDirectory() as d,PersistentSolver(Path(d)/'s.db') as s:
            compiled=s._request(dict(mode='layered_compile',width=2,layers=[[9],[],[77]],clauses=clauses))
            self.assertEqual(compiled['buckets'],[[[],[9],[],[9]],[[77],[77],[-77]]])
            self.assertEqual(compiled['masks'],[0,0])

    def test_grouping_large_partition_and_repeated_input_are_stack_safe(self):
        with tempfile.TemporaryDirectory() as d,PersistentSolver(Path(d)/'s.db') as s:
            layers=[[] for _ in range(65536)]+[[77]]
            compiled=s._request(dict(mode='layered_compile',width=1,layers=layers,clauses=[[77],[77]]))
            self.assertEqual(compiled['edges'],65536)
            self.assertEqual(compiled['buckets'][:-1],[[]]*65535)
            self.assertEqual(compiled['buckets'][-1],[[77],[77]])
            self.assertEqual(compiled['masks'][:-1],[15]*65535)
            self.assertEqual(compiled['masks'][-1],10)
            clauses=[[10]]*12000
            repeated=s._request(dict(mode='layered_compile',width=1,layers=[[10],[20]],clauses=clauses))
            self.assertEqual(repeated['buckets'],[clauses])
            self.assertEqual(repeated['masks'],[12])

    def test_native_translation_matches_every_boundary_assignment(self):
        # Sparse IDs and permuted slots prevent accidental index-based agreement.
        rng=random.Random(1897)
        with tempfile.TemporaryDirectory() as d,PersistentSolver(Path(d)/'s.db') as s:
            for width in (1,2,3,4):
                names=[(1<<80)+101*k for k in range(1,2*width+1)]
                rng.shuffle(names)
                layers=[names[:width],names[width:]]
                s._request(dict(mode='source_init',id=f'mapping-{width}',width=width,layers=layers))
                cases=[[],[[]],[[names[0]],[-names[0]]],[[names[-1]]]]
                cases += [[[rng.choice(names)*rng.choice((-1,1)) for _ in range(rng.randrange(5))]
                           for _ in range(rng.randrange(6))] for _ in range(24)]
                for clauses in cases:
                    expected=0;states=1<<width
                    for x,y in itertools.product(range(states),repeat=2):
                        values={v:bool(word&(1<<j)) for word,block in zip((x,y),layers)
                                for j,v in enumerate(block)}
                        if all(any(values[abs(lit)]==(lit>0) for lit in c) for c in clauses):
                            expected |= 1<<(x*states+y)
                    initial=s._request(dict(mode='layered_compile',width=width,layers=layers,clauses=clauses))
                    edited=s._request(dict(mode='source_compile',edits=[dict(edge=0,clauses=clauses)]))
                    self.assertEqual(initial['masks'],[expected])
                    self.assertEqual(edited['masks'],[expected])

    def test_short_empty_blocks_unused_variables_and_restart(self):
        layers=[[900,7],[],[51],[3000,2]]
        clauses=[[900],[-7],[51,2],[-3000]]
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'s.db'
            with PersistentSolver(path) as s:
                first=s.source_cnf(4,clauses,layers,witness=True)
                self.assertTrue(first['answer'])
                values={v:bool(first['witness'][i]&(1<<j)) for i,block in enumerate(layers) for j,v in enumerate(block)}
                self.assertTrue(all(any(values[abs(lit)]==(lit>0) for lit in c) for c in clauses))
                negative=s.source_cnf(base=first['state'],replace={1:[[51],[-51]]})
                self.assertFalse(negative['answer'])
                restored=s.source_cnf(base=negative['state'],replace={1:[]})
                self.assertTrue(restored['answer'])
            with PersistentSolver(path) as s:
                for version in (first,negative,restored):
                    self.assertEqual(s.source_cnf(base=version['state'])['answer'],version['answer'])
                self.assertTrue(s.source_cnf(4,[],[[],[]])['answer'])
                self.assertFalse(s.source_cnf(4,[[]],[[],[]])['answer'])

    def test_native_mapping_rejects_invalid_names_and_nonlocal_literals(self):
        with tempfile.TemporaryDirectory() as d,PersistentSolver(Path(d)/'s.db') as s:
            for layers in ([[1,1],[]],[[1],[1]],[[0],[3]],[[1,2,3],[4]]):
                with self.assertRaises(ValueError):
                    s._request(dict(mode='source_init',id='bad-map',width=2,layers=layers))
            s._request(dict(mode='source_init',id='valid-map',width=2,layers=[[9],[],[77]]))
            for clauses in ([[0]],[[88]],[[77]],[[9,77]]):
                with self.assertRaises(ValueError):
                    s._request(dict(mode='source_compile',edits=[dict(edge=0,clauses=clauses)]))
            with self.assertRaises(ValueError):
                s._request(dict(mode='layered_compile',width=2,layers=[[9],[],[77]],clauses=[[9,77]]))
            self.assertEqual(s._request(dict(mode='source_compile',edits=[dict(edge=0,clauses=[])]))['masks'],[65535])

    def test_translation_accumulation_handles_large_clause_and_bucket(self):
        with tempfile.TemporaryDirectory() as d,PersistentSolver(Path(d)/'s.db') as s:
            s._request(dict(mode='source_init',id='large-map',width=1,layers=[[10],[20]]))
            for clauses in ([[10]*30000+[-10]],[[10]]*12000):
                result=s._request(dict(mode='source_compile',edits=[dict(edge=0,clauses=clauses)]))
                self.assertEqual(result['masks'],[15 if len(clauses)==1 else 12])

    def test_random_edits_deletions_branches_and_restart_match_exhaustive_cnf(self):
        rng=random.Random(1820)
        for width in (1,2):
            layers=[list(range(i*width+1,(i+1)*width+1)) for i in range(4)]
            def bucket(edge):
                scope=layers[edge]+layers[edge+1]
                return [[rng.choice(scope)*rng.choice((-1,1)) for _ in range(rng.randrange(4))]
                        for _ in range(rng.randrange(5))]
            with tempfile.TemporaryDirectory() as d:
                path=Path(d)/'s.db';versions=[]
                with PersistentSolver(path,native_layer_cells=7*(1<<width)**2) as s:
                    first=s.source_cnf(width,[],layers)
                    versions.append((first['state'],[[],[],[]]))
                    for _ in range(60):
                        base,buckets=rng.choice(versions);buckets=list(buckets)
                        changes={i:bucket(i) for i in rng.sample(range(3),rng.randrange(1,4))}
                        for i,clauses in changes.items():buckets[i]=clauses
                        result=s.source_cnf(base=base,replace=changes,witness=True)
                        flat=[clause for group in buckets for clause in group]
                        self.assertEqual(result['answer'],sat(flat,4*width))
                        if result['answer']:
                            values={v:bool(result['witness'][i]&(1<<j)) for i,block in enumerate(layers) for j,v in enumerate(block)}
                            self.assertTrue(all(any(values[abs(lit)]==(lit>0) for lit in c) for c in flat))
                        self.assertEqual(result['source_updates']['binding_visits'],0)
                        versions.append((result['state'],buckets))
                with PersistentSolver(path,native_layer_cells=7*(1<<width)**2) as s:
                    for state,buckets in versions[::10]:
                        result=s.source_cnf(base=state)
                        self.assertEqual(result['answer'],sat([c for b in buckets for c in b],4*width))

    def test_flat_source_binding_and_nonconsecutive_variable_names(self):
        with tempfile.TemporaryDirectory() as d,PersistentSolver(Path(d)/'s.db') as s:
            r=s.source_cnf(2,[[100],[-42],[100,9999]],[[100],[9999],[42]],witness=True)
            self.assertTrue(r['answer']);self.assertEqual(r['witness'][0]&1,1);self.assertEqual(r['witness'][2]&1,0)
            r=s.source_cnf(base=r['state'],replace={1:[[42],[-42]]})
            self.assertFalse(r['answer'])
            self.assertTrue(s.source_cnf(base=r['state'],replace={1:[]})['answer'])

    def test_source_cannot_change_unedited_subtree_or_forge_leaf(self):
        with tempfile.TemporaryDirectory() as d,PersistentSolver(Path(d)/'s.db') as s:
            a=s.source_cnf(1,[],[[1],[2],[3],[4],[5]])
            b=s.source_cnf(base=a['state'],replace={3:[[]]})
            with self.assertRaisesRegex(ValueError,'unedited'):
                s._request(dict(mode='source_patch',base=a['root'],root=b['root'],
                    edits=[dict(edge=0,clauses=[])],witness=False))
            node=s.source_layers.read(a['root'])
            while node['height']:node=s.source_layers.read(node['left'])
            forged=dict(node,id='forged-source',mask=0)
            with self.assertRaisesRegex(ValueError,'mask'):
                s._request(dict(mode='source_define',nodes=[forged]))
            with self.assertRaisesRegex(ValueError,'Original source'):
                s._request(dict(mode='source_bind',root=a['root'],width=1,layers=[[1],[2],[3],[4],[5]],
                    clauses=[[]],witness=False))
            self.assertTrue(s.source_cnf(base=a['state'])['answer'])

    def test_locality_validation_and_failed_updates_preserve_base(self):
        with tempfile.TemporaryDirectory() as d,PersistentSolver(Path(d)/'s.db') as s:
            a=s.source_cnf(1,[],[[1],[2],[3]])
            for changes in ({0:[[3]]},{0:[[0]]},{2:[]},{0:[], '0':[]},{-1:[]}):
                with self.assertRaises(ValueError):s.source_cnf(base=a['state'],replace=changes)
                self.assertTrue(s.source_cnf(base=a['state'])['answer'])
            for blocks in ([[1],[1]],[[0],[1]],[[1,2],[3]]):
                with self.assertRaises(ValueError):s.source_cnf(1,[],blocks)
            self.assertTrue(s.source_cnf(base=a['state'])['answer'])
            b=s.source_cnf(1,[[]],[[10],[20]])
            self.assertFalse(b['answer'])
            self.assertTrue(s.source_cnf(base=a['state'])['answer'])

    def test_tight_cap_source_edits_have_local_evidence_and_measured_reservation(self):
        size=256;height=8;cells=4;cap=(2*size-1)*cells
        with tempfile.TemporaryDirectory() as d,PersistentSolver(Path(d)/'s.db',native_layer_cells=cap) as s:
            a=s.source_cnf(1,[],[[i+1] for i in range(size+1)])
            for i in range(40):
                edge=i%size
                r=s.source_cnf(base=a['state'],replace={edge:[[edge+1]]})
                self.assertTrue(r['answer']);self.assertIsNone(r['witness']);m=r['source_updates']
                self.assertEqual(m['native_definitions'],height+1)
                self.assertEqual(m['inserted_objects'],height+3)
                self.assertEqual(m['native_evictions'],height+1)
                self.assertEqual(m['patch_visits'],2*height+1)
                self.assertEqual(m['binding_visits'],0)
                self.assertEqual(m['layout_replays'],0)
                self.assertLess(m['node_reads'],100)
                self.assertEqual(m['native_cells'],cap)
                self.assertEqual(m['peak_native_cells'],cap+(height+1)*cells)
                a=r
            same=s.source_cnf(base=a['state']);m=same['source_updates']
            self.assertEqual(m['native_definitions'],0)
            self.assertEqual(m['reachability_updates'],0)
            self.assertEqual(m['inserted_objects'],0)

    def test_source_working_set_refusal_keeps_other_version(self):
        with tempfile.TemporaryDirectory() as d,PersistentSolver(Path(d)/'s.db',native_layer_cells=12) as s:
            a=s.source_cnf(1,[],[[1],[2],[3]])
            with self.assertRaises(BudgetExceeded):s.source_cnf(1,[],[[1],[2],[3],[4],[5]])
            self.assertTrue(s.source_cnf(base=a['state'])['answer'])

    def test_caller_mutation_cannot_change_saved_source_or_cached_replay(self):
        from solver.resources import stop_process
        with tempfile.TemporaryDirectory() as d,PersistentSolver(Path(d)/'s.db') as s:
            layers=[[1],[2],[3]];clauses=[[1]]
            a=s.source_cnf(1,clauses,layers)
            bucket=[[1],[-1]]
            b=s.source_cnf(base=a['state'],replace={0:bucket})
            layers[0][0]=99;clauses[0][0]=99;bucket[1][0]=1
            stop_process(s.process);s.process=None
            self.assertFalse(s.source_cnf(base=b['state'])['answer'])
            self.assertTrue(s.source_cnf(base=a['state'])['answer'])

    def test_old_engine_source_replays_clauses_instead_of_importing_answer(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'s.db'
            with PersistentSolver(path) as s:
                a=s.source_cnf(1,[],[[1],[2],[3]])
                b=s.source_cnf(base=a['state'],replace={1:[[]]})
                with s.db:
                    s.db.execute("UPDATE source_states SET engine='older-engine',answer=1-answer")
                before=[tuple(r) for r in s.db.execute('SELECT * FROM source_states ORDER BY id')]
            with PersistentSolver(path) as s:
                for prior,expected in ((a,True),(b,False)):
                    r=s.source_cnf(base=prior['state'])
                    self.assertEqual(r['answer'],expected)
                    self.assertTrue(r['revalidated_source'])
                    self.assertGreater(r['source_updates']['native_definitions'],0)
                    self.assertFalse(s.source_cnf(base=prior['state'])['revalidated_source'])
                self.assertEqual([tuple(r) for r in s.db.execute("SELECT * FROM source_states WHERE engine='older-engine' ORDER BY id")],before)
                self.assertEqual(s.db.execute('SELECT count(*) FROM source_states').fetchone()[0],4)
                self.assertTrue(s.source_cnf(base=b['state'],replace={1:[]})['answer'])


if __name__=='__main__':unittest.main()
