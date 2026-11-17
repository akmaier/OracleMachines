#!/usr/bin/env python3
"""Separate bounded probing, trace reuse, remaining search and retained storage."""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_assumption_guard as study
from experiments.validate_cnf_unsat_support import bound
base = study.base


def run(out):
    report = base.load(out / 'report.json'); p = bound(report['protocol'])
    samples = [bound(e) for e in report['samples']]
    old = [bound(e) for e in bound(p['prior_study'])['samples']]
    cases = []
    for cid in dict.fromkeys(r['case'] for r in samples):
        arms = {}
        for r in (r for r in samples if r['case'] == cid):
            premise = {} if r['premise'] is None else r['premise']['metrics']
            arms[r['mode']] = dict(
                expanded_nodes=r['expanded_nodes'], new_nodes=r['new_nodes'], native_bytes=r['new_payload_units'],
                retained_bytes=r['retained_bytes'], selected=None if r['choice'] is None else r['choice'].get('clause'),
                premise_probes=r['probe_counts'].get('assumption_premise_probes', 0),
                probe_propagation_visits=r['probe_counts'].get('propagation_literal_visits', 0),
                premise_propagation_visits=premise.get('propagation_literal_visits', 0),
                child_propagation_visits=r['child']['metrics'].get('propagation_literal_visits', 0),
                total_propagation_visits=r['probe_counts'].get('propagation_literal_visits', 0) + premise.get('propagation_literal_visits', 0) + r['child']['metrics'].get('propagation_literal_visits', 0),
                trace_publications=premise.get('screen_trace_publications', 0), child_expansions=r['child']['metrics'].get('expanded_nodes', 0),
                preparation_seconds=r['preparation_seconds'], selection_seconds=r['selection_seconds'],
                premise_seconds=r['premise_seconds'], child_seconds=r['child_seconds'],
                composition_seconds=r['composition_seconds'], cold_seconds=r['cold']['seconds'], complete_seconds=r['seconds'])
        native = next(r for r in samples if r['case'] == cid and r['mode'] == 'native-guard')
        trace = next(r for r in samples if r['case'] == cid and r['mode'] == 'trace-guard')
        same_delta = dict(bound(native['delta'])) == dict(bound(trace['delta']))
        same_records = bound(native['records']) == bound(trace['records'])
        assert same_delta and same_records
        prior = {r['mode']: dict(rows=r['new_nodes'], native_bytes=r['new_payload_units'], retained_bytes=r['retained_bytes']) for r in old if r['case'] == cid}
        cases.append(dict(case=cid, arms=arms, direct_trace_same_payloads=same_delta, direct_trace_same_records=same_records,
                          prior_partitions=prior, posthoc_best=min(arms, key=lambda m: (arms[m]['new_nodes'], arms[m]['native_bytes'], m))))
    totals = {mode: {field: sum(r['arms'][mode][field] for r in cases)
                    for field in ('expanded_nodes', 'new_nodes', 'native_bytes', 'retained_bytes', 'total_propagation_visits')}
              for mode in p['modes']}
    result = dict(passed=True, report=study.binding(out / 'report.json'), cases=cases, totals=totals,
                  limitations=['Historical selected queries, not excluded-input coverage. Candidate origins require separately charged prior discovery. Direct and retained-trace guards use exactly the same probing policy.',
                               'Totals are sums of independent exact-prefix arms, not a streamed policy. Posthoc baseline fallback is not an implemented selector. Trace publication still acquires/checks/stores a row. One sample per arm proves no stable runtime or peak-memory gain.'])
    base.write(out / 'cost-attribution.json', result)
    print(base.encode(totals), flush=True)


if __name__ == '__main__': run(Path(sys.argv[1]))
