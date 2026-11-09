#!/usr/bin/env python3
"""Check matched semantic plans, count shared proofs and retain bottleneck data."""
from collections import Counter
import copy
import cProfile
import hashlib
import json
from pathlib import Path
import pstats
import sys
import tempfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from experiments.cnf_pattern_inventory import encode
from experiments.cnf_probe_closure_reuse import expand_references
from experiments.cnf_probe_closure_compact import CompactProbeClosureInventory
from experiments.analyze_cnf_conditioning import load_nodes
from experiments.analyze_cnf_probe_equivalence import selected


def plan(node, nodes):
    """Ignore proof order/reason choice and versioned IDs, not logical content."""
    node = copy.deepcopy(node)
    p = node['profile']['probing']
    if p['status'] in ('learned', 'learning_clear'):
        p['continuation'] = expand_references(p['continuation'], p['attempts'])

    def visit(value):
        if isinstance(value, list): return [visit(v) for v in value]
        if not isinstance(value, dict): return value
        if set(value) == {'units', 'conflict', 'pure_rounds'}:
            return dict(units=sorted(lit for lit, _ in value['units']),
                        conflict=value['conflict'] is not None, pure_rounds=value['pure_rounds'])
        return {k: ([nodes[v]['depth'], nodes[v]['cnf']] if k == 'key' and isinstance(v, str) and v in nodes
                    else visit(v)) for k, v in value.items()}
    return visit(node)


def analyze(directory):
    report = json.loads((directory/'report.json').read_text())
    rows = {(r['mode'], r['case']): r for r in report['records']}
    all_nodes = {a['mode']: load_nodes(directory, a) for a in report['archives'] if a['mode'] != 'solver_only'}
    indexed = {mode: {encode([n['depth'], n['cnf']]): (k, n) for k, n in nodes.items()}
               for mode, nodes in all_nodes.items()}
    assert set(indexed['baseline']) == set(indexed['compact'])
    assert set(indexed['reuse']) == set(indexed['compact'])
    differing_proofs = 0
    for identity, (k, n) in indexed['compact'].items():
        vk, verbose = indexed['reuse'][identity]
        assert plan(n, all_nodes['compact']) == plan(verbose, all_nodes['reuse'])
        assert n['profile'] == verbose['profile']
        bk, b = indexed['baseline'][identity]
        assert plan(n, all_nodes['compact']) == plan(b, all_nodes['baseline'])
        p, bp = n['profile']['probing'], b['profile']['probing']
        if 'continuation' in p:
            differing_proofs += expand_references(p['continuation'], p['attempts']) != bp['continuation']
    for i in range(len(report['cases'])):
        a, b = rows['baseline', i]['discovery'], rows['compact', i]['discovery']
        assert a['summary'] == b['summary'] and a['dag'] == b['dag']
    stats = {}; misses = []; leaves = set()
    for mode, nodes in all_nodes.items():
        sizes = Counter(); continuations = Counter(); learning = Counter(); refs = attempts = full_bytes = ref_bytes = 0
        for k, n in nodes.items():
            sizes[n['kind']] += len(k.encode()) + len(encode(n).encode())
            p = n['profile']['probing']; learning[p['status']] += 1
            if 'continuation' not in p: continue
            continuations[p['continuation']['status']] += 1
            for a in p['continuation']['attempts']:
                attempts += 1
                if 'reuse' in a['certificate']:
                    refs += 1
                    full_bytes += len(encode(p['attempts'][a['certificate']['reuse']]['certificate']).encode())
                    ref_bytes += len(encode(a['certificate']).encode())
        stats[mode] = dict(nodes=len(nodes), logical_bytes_by_kind=dict(sizes), statuses=dict(learning),
            continuation_statuses=dict(continuations), continuation_probes=attempts, references=refs,
            replaced_certificate_bytes=full_bytes, reference_bytes=ref_bytes)
    current = all_nodes['compact']; hashes = {hashlib.sha256(k.encode()).hexdigest(): k for k in current}
    for i, case in enumerate(report['cases']):
        r = rows['compact', i]
        if r['discovery']['summary']['closed']: continue
        path = selected(current, hashes[r['discovery']['root_hash']])
        leaves.update(k for k in path if current[k]['kind'] == 'unresolved')
        misses.append(dict(case=i, group=case['group'], label=case.get('label'), answer=r['answer'],
                           summary=r['discovery']['summary']))
    worst = max((r for r in report['records'] if r['mode'] == 'compact' and not r['discovery']['summary']['closed']),
                key=lambda r: r['discovery']['seconds'])['case']
    with tempfile.TemporaryDirectory() as tmp:
        h = CompactProbeClosureInventory(Path(tmp)/'profile.db', max_depth=2, probe_limit=4, learn_limit=4)
        profiler = cProfile.Profile(); profiler.enable()
        result = h.inspect(report['cases'][worst]['source']); profiler.disable(); h.close()
        functions = [dict(file=f, line=line, name=name, primitive_calls=pr, calls=ca,
                          own_seconds=own, cumulative_seconds=cu)
                     for (f, line, name), (pr, ca, own, cu, _) in pstats.Stats(profiler).stats.items()]
    return dict(report_sha256=hashlib.sha256((directory/'report.json').read_bytes()).hexdigest(),
        source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(), nodes=stats,
        matched_semantic_nodes=len(indexed['compact']), changed_continuation_proofs=differing_proofs,
        matched_source_plans=len(report['cases']), misses=misses, selected_unresolved_nodes=len(leaves),
        selected_leaf_statuses=dict(Counter(current[k]['profile']['probing']['status'] for k in leaves)),
        selected_unresolved_literals=sum(current[k]['profile']['shape']['literals'] for k in leaves),
        profile=dict(case=worst, instrumented_seconds=result['seconds'], metrics=result['metrics'],
                     functions=sorted(functions, key=lambda f: -f['own_seconds'])[:40]),
        limitations=['Semantic-plan comparison ignores unit order/reason choice only after independent archive checking',
                     'Reference byte saving excludes versioned key overhead and full database accounting',
                     'Supporting discovery optimization: no new coverage is claimed',
                     'Inactive batch avoids replay; active batches and new choices still require full probing',
                     'Separate diagnostic profile is not a primary benchmark timing'])


if __name__ == '__main__':
    directory = Path(sys.argv[1]); out = directory/'mechanisms.json'
    if out.exists(): raise ValueError('Preserve earlier analysis')
    out.write_text(json.dumps(analyze(directory), indent=2)+'\n')
