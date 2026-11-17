#!/usr/bin/env python3
"""Price local discovery, distinguish publications, and inspect remaining proofs."""
from collections import Counter
from pathlib import Path
import sys, tempfile
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_local_guard as study
from experiments.validate_cnf_unsat_support import bound
base = study.base


def run(out):
    report = base.load(out / 'report.json'); p = bound(report['protocol'])
    historical = [bound(e) for e in bound(report['historical'])['samples']]
    hcases = []
    for cid in p['historical_cases']:
        arms = {}
        for r in (r for r in historical if r['case'] == cid):
            arms[r['mode']] = dict(rows=r['new_nodes'], native_bytes=r['new_payload_units'], retained_bytes=r['retained_bytes'],
                choice=None if r['local_choice'] is None else r['local_choice'].get('clause'), **r['summary'],
                selection_seconds=r['selection_seconds'], premise_seconds=r['premise_seconds'], child_seconds=r['child_seconds'],
                cold_seconds=r['cold']['seconds'], complete_seconds=r['seconds'])
        hcases.append(dict(case=cid, arms=arms))
    history_totals = {mode: {k: sum(r['arms'][mode][k] for r in hcases) for k in ('rows', 'native_bytes', 'retained_bytes', 'expanded_nodes', 'trace_publications', 'propagation_literal_visits')} for mode in study.MODES}
    trials = [(e, bound(e)) for e in report['samples']]; rows_by_mode = {}; details = {}
    with tempfile.TemporaryDirectory() as td:
        for entry, data in trials:
            if entry['repeat']: continue
            mode = entry['mode']; queries = bound(data['queries']); rows_by_mode[mode] = queries
            path = Path(td) / mode; base.restore_archive(data['archive'], path); s = study.native.ResidualSolver(path)
            try: archive = study.native.rows(s)
            finally: s.close()
            by_hash = {base.key_sha(k): (k, v) for k, v in archive.items()}; details[mode] = {}
            stream_ids = {h for r in queries for h in r['new_ids']}
            available = {k for k in archive if base.key_sha(k) not in stream_ids}
            for r in queries:
                node = base.load_json(archive[r['child']['root']]); proof = node.get('proof', {})
                kinds = Counter(); sizes = Counter()
                for h in r['new_ids']:
                    k, v = by_hash[h]; n = base.load_json(v); kind = n.get('proof', {}).get('kind', 'model')
                    kinds[kind] += 1; sizes[kind] += len(k) + len(v)
                child_info = dict(root=r['child']['root'], kind=proof.get('kind', 'model'), answer=node['answer'],
                                  new_root=base.key_sha(r['child']['root']) in r['new_ids'], unit_steps=len(proof.get('trace', [])))
                if proof.get('child') is not None:
                    c = base.load_json(archive[proof['child']])
                    child_info.update(next_root=proof['child'], next_kind=c.get('proof', {}).get('kind', 'model'),
                                      next_new=base.key_sha(proof['child']) in r['new_ids'])
                frontier = []; stack = [r['child']['root']]; seen = set()
                while stack:
                    key = stack.pop()
                    if key in seen: continue
                    seen.add(key); n = base.load_json(archive[key])
                    if key in available:
                        frontier.append(dict(root=key, kind=n.get('proof', {}).get('kind', 'model'),
                                             clauses=len(n['cnf']), literals=sum(map(len, n['cnf']))))
                    else:
                        pr = n.get('proof', {})
                        stack.extend(pr[field] for field in ('child', 'low', 'high') if field in pr)
                child_info['known_dependency_roots'] = frontier
                details[mode][r['case']] = dict(case=r['case'], answer=r['record']['answer'], rows=r['new_nodes'],
                    native_bytes=sum(len(x) + len(y) for h in r['new_ids'] for x, y in [by_hash[h]]),
                    ordinary_rows=len(r['ordinary_ids']), near_rows=len(r['near_ids']), engine_rows=r['new_nodes'] - len(r['ordinary_ids']) - len(r['near_ids']),
                    choice=None if r['local_choice'] is None else {k: v for k, v in r['local_choice'].items() if k != 'screen'},
                    expanded_nodes=sum(c['metrics'].get('expanded_nodes', 0) for c in (r['child'], r['premise']) if c is not None),
                    child_expansions=r['child']['metrics'].get('expanded_nodes', 0), probe_counts=r['probe_counts'],
                    proof_kinds=dict(kinds), proof_bytes=dict(sizes), child=child_info)
                available.update(by_hash[h][0] for h in r['new_ids'])
    changes = []
    for case in sorted(details['baseline']):
        b = details['baseline'][case]; local = details['local'][case]
        if local['choice'] is not None or b['rows'] != local['rows'] or b['native_bytes'] != local['native_bytes']:
            changes.append(dict(case=case, baseline=b, local=local))
    pairs = []
    for repeat in range(len(p['orders'])):
        pair = {e['mode']: d['summary'] for e, d in trials if e['repeat'] == repeat}
        b, local = pair['baseline'], pair['local']
        pairs.append(dict(repeat=repeat, order=p['orders'][repeat], baseline_complete_seconds=b['complete_worker_seconds'],
                          local_complete_seconds=local['complete_worker_seconds'], local_minus_baseline_seconds=local['complete_worker_seconds'] - b['complete_worker_seconds']))
    summary = report['summary']; b, local = summary['baseline'], summary['local']
    percentages = {k: 100 * (local[k] - b[k]) / b[k] for k in ('new_nodes', 'new_payload_units', 'propagation_literal_visits', 'mean_query_seconds', 'mean_complete_worker_seconds', 'mean_peak_rss_bytes')}
    bbytes = sum(b['sidecar_bytes']) / len(b['sidecar_bytes']); lbytes = sum(local['sidecar_bytes']) / len(local['sidecar_bytes'])
    percentages['mean_sidecar_bytes'] = 100 * (lbytes - bbytes) / bbytes
    remaining = sorted((r for r in details['local'].values() if r['child_expansions']), key=lambda r: (-r['child_expansions'], r['case']))
    result = dict(passed=True, report=study.binding(out / 'report.json'), historical=hcases, historical_totals=history_totals,
                  fresh_summary=summary, fresh_changes=changes, remaining_child_work=remaining, paired_times=pairs, fresh_percent_change=percentages,
                  limitations=['Fresh query contributions come from matched streams whose prefixes can diverge; they are not isolated per-query causal savings. Historical arms use equal exact prefixes.',
                               'Expanded-node reductions must be compared with explicit trace publications and all new rows. Child proof shapes explain materialization but do not establish that every wrapper can be removed safely.',
                               'Two reversed-order pairs are a small timing sample. Process peak RSS is not a live-state complexity bound. Retained diagnostic sidecars, native rows and compressed files measure different storage obligations.'])
    base.write(out / 'cost-attribution.json', result)
    print(base.encode(dict(historical=history_totals, fresh_percent_change=percentages,
                          remaining=[dict(case=r['case'], expansions=r['child_expansions'], rows=r['rows'], child_kind=r['child']['kind'], unit_steps=r['child']['unit_steps'], next_kind=r['child'].get('next_kind')) for r in remaining],
                          changes=[dict(case=r['case'], rows=[r['baseline']['rows'], r['local']['rows']], native_bytes=[r['baseline']['native_bytes'], r['local']['native_bytes']], choice=r['local']['choice']) for r in changes])), flush=True)


if __name__ == '__main__': run(Path(sys.argv[1]))
