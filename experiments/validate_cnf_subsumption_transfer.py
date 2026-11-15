#!/usr/bin/env python3
"""Cold replay, matched-cost summary and explicit admission-accounting audit."""
from collections import Counter
import gzip
import json
from pathlib import Path
import sys
import tempfile
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import experiments.compare_cnf_subsumption_transfer as study
from experiments.cnf_coverage_union import inventory
from experiments.cnf_subsumption_transfer import CoreIndex, check_transfer, minimal
from experiments.cnf_pattern_inventory import encode
from experiments.cnf_residual_dag import normalize


def admission_audit(protocol, bank, mode, expected, path):
    """Observe persisted states outside BudgetedInventory._discover admissions.

    Fused conditioning can call _discover_profile and _record_node directly.
    Preserve that historical policy; do not silently reinterpret its cap as a
    bound on every discovered or stored state. This diagnostic is not a timing.
    """
    class ObservedInventory(study.BudgetedInventory):
        def _record_node(self, key, node):
            if key not in self.admitted:
                self.outside.append(study.key_sha(key))
            return super()._record_node(key, node)

    h = ObservedInventory(path, **protocol['options'])
    index = CoreIndex({bank['id']: bank['source']}) if mode == 'subsumption' else None
    rows = []
    try:
        for case, saved in zip(protocol['cases'], expected, strict=True):
            source = case['source']; h.set_admission_budget(protocol['state_limit'])
            h.outside = []; h.counts = Counter(); h.prepared.counts = Counter()
            root = None; closed = False; capped = False; route = 'ordinary'
            before = h.db.execute('SELECT count(*) FROM cnf_patterns_v1').fetchone()[0]
            if mode == 'exact' and normalize(source)[0] == normalize(bank['source'])[0]:
                route = 'exact'; closed = True
            if mode == 'subsumption':
                cert = index.lookup(source)
                if cert is not None:
                    check_transfer(source, bank['source'], bank['id'], cert)
                    route = 'subsumption'; closed = True
            if not closed:
                root, closed, capped = study.ordinary(h, source)
            stored = h.db.execute('SELECT count(*) FROM cnf_patterns_v1').fetchone()[0]-before
            assert (root, closed, capped, route, len(h.admitted), stored, h.counts.get('probe_attempts', 0)) == (
                saved['root'], saved['closed'], saved['capped'], saved['route'], saved['entered_states'],
                saved['stored_states'], saved['probe_attempts'])
            rows.append(dict(case=saved['case'], recorded_without_admission=len(h.outside),
                             source_sha256=h.outside, admissions=len(h.admitted), stored=stored))
    finally:
        h.close()
    return dict(recorded_without_admission=sum(x['recorded_without_admission'] for x in rows),
        cases=[x for x in rows if x['recorded_without_admission']],
        max_admissions=max(x['admissions'] for x in rows),
        max_stored_per_query=max(x['stored'] for x in rows),
        total_admissions=sum(x['admissions'] for x in rows), total_stored=sum(x['stored'] for x in rows))


def validate(out):
    began = time.perf_counter(); r = study.load(out/'report.json')
    for path, digest in r['fingerprints'].items():
        assert study.sha(path) == digest
    assert study.sha(r['protocol']['path']) == r['protocol']['sha256']
    protocol = study.load(r['protocol']['path']); bank = study.unpack(r['bank'])
    assert protocol['cases'] == study.new_cases(bank['source'])
    parent = study.load(r['parent']['path']); assert study.sha(r['parent']['path']) == r['parent']['sha256']
    parent_bundle = study.unpack(parent['bundle'])
    old_inputs = {study.source_id(c) for c in parent_bundle['claim']['sources']}
    old_nodes = {study.source_id(json.loads(k)[-1]) for k, _ in parent_bundle['rows']['cnf_patterns_v1']}
    assert all(study.source_id(c['source']) not in old_inputs | old_nodes for c in protocol['cases'])
    samples = []; costs = {}; audits = {}
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td); bank_check = study.verify_bank(bank, tmp/'bank')
        for i, sample in enumerate(r['samples']):
            assert study.sha(sample['path']) == sample['sha256']
            data = study.load(sample['path']); entry = data['archive']
            assert study.sha(entry['path']) == entry['sha256']
            path = tmp/f'cold-{i}'; path.write_bytes(gzip.decompress(Path(entry['path']).read_bytes()))
            assert study.sha(path) == entry['database_sha256']
            cold = study.cold_replay(path, protocol, bank, sample['mode'], data['records'])
            assert study.sha(path) == entry['database_sha256']
            samples.append(dict(mode=sample['mode'], repeat=sample['repeat'], **cold))
        for mode in study.MODES:
            arms = [study.load(s['path']) for s in r['samples'] if s['mode'] == mode]
            first = arms[0]
            costs[mode] = dict(covered=sum(x['closed'] for x in first['records']),
                hits=sum(x['route']!='ordinary' for x in first['records']),
                admissions=sum(x['entered_states'] for x in first['records']),
                stored=sum(x['stored_states'] for x in first['records']),
                probes=sum(x['probe_attempts'] for x in first['records']),
                mean_preparation_seconds=sum(a['preparation_seconds'] for a in arms)/2,
                mean_query_seconds=sum(a['query_seconds'] for a in arms)/2,
                mean_prepared_query_seconds=sum(a['query_seconds']+a['preparation_seconds'] for a in arms)/2,
                database_bytes=first['database_bytes'], database_growth=first['database_growth'],
                mean_archive_bytes=sum(a['archive']['compressed_bytes'] for a in arms)/2,
                groups={g:dict(**{k:v for k,v in first['groups'][g].items() if k!='operation_seconds'},
                    mean_operation_seconds=sum(a['groups'][g]['operation_seconds'] for a in arms)/2)
                    for g in first['groups']},
                remaining=[dict(case=x['case'], group=x['group'], capped=x['capped'],
                                source_sha256=x['source_sha256']) for x in first['records'] if not x['closed']])
            audits[mode] = admission_audit(protocol, bank, mode, first['records'], tmp/f'audit-{mode}')
    normalized, _, names = minimal(bank['source'], Counter())
    baseline = costs['empty']; improved = costs['subsumption']
    reductions = dict(admissions=baseline['admissions']-improved['admissions'],
        probes=baseline['probes']-improved['probes'], stored=baseline['stored']-improved['stored'],
        database_bytes=baseline['database_bytes']-improved['database_bytes'],
        observed_query_fraction=1-improved['mean_query_seconds']/baseline['mean_query_seconds'],
        observed_prepared_query_fraction=1-improved['mean_prepared_query_seconds']/baseline['mean_prepared_query_seconds'])
    result = dict(passed=True, report_sha256=study.sha(out/'report.json'), source_sha256=study.sha(__file__),
        cases=len(protocol['cases']), bank=bank_check, cold_samples=samples, costs=costs,
        template_minimum=dict(variables=len(names), clauses=len(normalized), literals=sum(map(len,normalized))),
        reductions=reductions, admission_audit=audits, seconds=time.perf_counter()-began,
        accounting_correction='The frozen protocol calls the allowance 32 states. It limits BudgetedInventory._discover admissions, not every recognizer state: fused conditioning records additional nodes via _discover_profile. Both admissions and actual stored rows are reported. No total 32-state bound is claimed.',
        limitations=['Novelty is relative to the 1497 historical inputs and selected proof rows in the prepared union; this is not a search of every previous trial.',
            'The first twelve motif variants are deliberately derived from the chosen template. Their hits are applicability evidence, not an unbiased coverage estimate.',
            'Only two timing repetitions and one fixed stream order; small aggregate time differences are not statistically established speedups.',
            'Original acquisition and producer extraction are not included in warm query time. Prepared-query totals charge template verification and index setup.',
            'Successful transfer avoids populating the ordinary planner with some earlier states, so later fallback can lose incidental warm reuse.',
            'All capped cases remain unknown structural coverage. Positive proof replay does not produce SAT/UNSAT decisions.'])
    (out/'reconstruction.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print(json.dumps(dict(passed=True, costs={m:{k:v for k,v in c.items() if k not in ('groups','remaining')} for m,c in costs.items()},
                         reductions=reductions, admission_outside={m:a['recorded_without_admission'] for m,a in audits.items()})))


if __name__ == '__main__':
    validate(Path(sys.argv[1]))
