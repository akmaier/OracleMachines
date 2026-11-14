from collections import Counter
import copy
import json
import unittest
from unittest.mock import patch

from experiments.cnf_coupled_pivots import BudgetedInventory
from experiments.cnf_expanded_coverage import expand
from experiments.cnf_selected_routes import verify_selected_plan
from experiments.cnf_pattern_inventory import encode
from experiments.cnf_positive_bundle import (collect_bundle,replay_bundle,capture_reads,
    ReadCapture,TABLES)
import solver.test_cnf_selected_routes as fixtures

EMPTY=[[],[],[],[],[]]


def tiny_bundle():
    options=dict(max_depth=0); sources=[[[1],[3]]]
    h=BudgetedInventory(**options)
    h.prepared._edge(sources[0],0);h.set_admission_budget(8)
    root=h._edge(sources[0],0)['key']
    old=dict(roots=[root],steps=[dict(source=root,rule=dict(kind='base'))])
    routes=verify_selected_plan(h,old,[root],EMPTY,Counter())
    proof=expand(h,old,[root],routes,Counter())
    h.checked.clear();h.prepared.checked.clear()
    bundle,counts=collect_bundle(h,proof,sources,options,EMPTY,Counter())
    h.close()
    return bundle,sources,options,counts


class PositiveBundleTests(unittest.TestCase):
    def test_standalone_retained_replay_and_value_snapshot(self):
        bundle,sources,options,counts=tiny_bundle()
        self.assertGreater(counts['lookup_calls'],0)
        sources_before=copy.deepcopy(sources);options_before=copy.deepcopy(options)
        sources[0].append([999]);options['max_depth']=1
        with patch.object(BudgetedInventory,'_discover',side_effect=AssertionError('discovery')):
            result=replay_bundle(json.loads(encode(bundle)),sources_before,options_before)
        self.assertEqual(result['roots'],1)
        self.assertEqual(result['steps'],len(bundle['proof']['steps']))
        self.assertEqual(result['historical']['unique_nodes'],0)
        self.assertEqual(result['capture_counts']['missing_lookups'] if 'missing_lookups' in result['capture_counts'] else 0,0)

    def test_missing_every_graph_record_and_omitted_branch_rejected(self):
        bundle,sources,options,_=tiny_bundle()
        for index in range(len(bundle['rows']['cnf_patterns_v1'])):
            bad=copy.deepcopy(bundle);bad['rows']['cnf_patterns_v1'].pop(index)
            with self.assertRaises(ValueError):replay_bundle(bad,sources,options)
        bad=copy.deepcopy(bundle)
        next(s for s in bad['proof']['steps'] if s['rule']['kind']=='components')['children'].pop()
        with self.assertRaises(ValueError):replay_bundle(bad,sources,options)

    def test_requested_claim_scope_schema_and_duplicate_id_are_checked(self):
        bundle,sources,options,_=tiny_bundle()
        for bad_sources,bad_options in (([],options),([[[2],[4]]],options),(sources,dict(max_depth=1))):
            with self.assertRaises(ValueError):replay_bundle(bundle,bad_sources,bad_options)
        for mutation in (
                lambda b:b.update(scope='complete-discovery-catalog'),
                lambda b:b['rows'].update({'outside_table':[]}),
                lambda b:b['rows']['cnf_patterns_v1'].append(b['rows']['cnf_patterns_v1'][0]),
                lambda b:b['evidence'].pop(),
                lambda b:b.update(source_archive='/unavailable/history')):
            bad=copy.deepcopy(bundle);mutation(bad)
            with self.assertRaises(ValueError):replay_bundle(bad,sources,options)

    def test_recomputed_envelope_does_not_authorize_corrupt_payload(self):
        bundle,sources,options,_=tiny_bundle()
        root=bundle['proof']['roots'][0]
        for changed in ('cnf','reference'):
            bad=copy.deepcopy(bundle)
            row=next(r for r in bad['rows']['cnf_patterns_v1'] if r[0]==root)
            node=json.loads(row[1])
            if changed=='cnf':node['cnf']=[[1]]
            else:node['reference']=root
            row[1]=encode(node)
            with self.assertRaises(ValueError):replay_bundle(bad,sources,options)

    def test_unused_record_cannot_be_mistaken_for_verified_inventory(self):
        bundle,sources,options,_=tiny_bundle()
        bad=copy.deepcopy(bundle)
        bad['rows']['cnf_growth_trials_v1'].append(['unrelated','{}'])
        with self.assertRaisesRegex(ValueError,'unused rows'):replay_bundle(bad,sources,options)

    def test_external_trace_records_are_captured_and_required(self):
        helper=fixtures.SelectedRoutesTests()
        options=dict(max_depth=0,probe_limit=4,learn_limit=4,clause_growth_limit=2)
        h=BudgetedInventory(**options)
        try:
            for table in TABLES:h.db.execute(f'CREATE TABLE IF NOT EXISTS {table}(id TEXT PRIMARY KEY,payload TEXT NOT NULL)')
            root,old,evidence=helper.split(h)
            routes=verify_selected_plan(h,old,[root],evidence,Counter())
            proof=expand(h,old,[root],routes,Counter())
            sources=[json.loads(root)[3]]
            h.checked.clear();h.prepared.checked.clear()
            bundle,_=collect_bundle(h,proof,sources,options,evidence,Counter())
        finally:h.close()
        result=replay_bundle(bundle,sources,options)
        self.assertGreater(result['historical']['unique_nodes'],0)
        self.assertEqual(result['counts']['positive_external_steps'],1)
        self.assertEqual(result['capture_counts'].get('missing_lookups',0),0)
        bad=copy.deepcopy(bundle);bad['evidence'][3]=[]
        with self.assertRaises(ValueError):replay_bundle(bad,sources,options)

    def test_capture_rejects_writes_scans_and_prefilled_history_and_restores_views(self):
        h=BudgetedInventory(max_depth=0);h.set_admission_budget(8)
        try:
            root=h._edge(((1,),),0)['key'];connection=h.db
            with self.assertRaisesRegex(ValueError,'fresh historical'):
                collect_bundle(h,{},[[(1,)]],dict(max_depth=0),EMPTY,Counter())
            for sql,args in (('DELETE FROM cnf_patterns_v1',()),
                             ('SELECT id,payload FROM cnf_patterns_v1',()),
                             ('SELECT payload FROM secret WHERE id=?',('x',)),
                             ('SELECT payload FROM cnf_patterns_v1 WHERE id=?',(False,))):
                with self.assertRaises(ValueError),capture_reads(h) as capture:
                    capture.execute(sql,args)
                self.assertIs(h.db,connection);self.assertIs(h.prepared.db,connection)
            capture=ReadCapture(connection)
            cursor=capture.execute('SELECT payload FROM cnf_patterns_v1 WHERE id=?',(root,))
            self.assertIsNotNone(cursor.fetchone());self.assertIsNone(cursor.fetchone())
            row=json.loads(capture.rows['cnf_patterns_v1'][root]);row['summary']={}
            connection.execute('UPDATE cnf_patterns_v1 SET payload=? WHERE id=?',(encode(row),root))
            with self.assertRaisesRegex(ValueError,'Changed row'):
                capture.execute('SELECT payload FROM cnf_patterns_v1 WHERE id=?',(root,))
        finally:h.close()


if __name__=='__main__':unittest.main()
