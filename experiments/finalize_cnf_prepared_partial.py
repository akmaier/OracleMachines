#!/usr/bin/env python3
"""Seal shared partial preparation and bind the remaining cold extraction cost."""
from collections import Counter
from pathlib import Path
import re
import subprocess
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_prepared_partial as study
base = study.base


def finalize(out):
    p = base.load(out / 'protocol.json'); v = base.load(out / 'validation.json')
    cp = base.load(out / 'checkpoint.json'); analysis = base.load(out / 'analysis.json')
    assert v['passed'] and v['query_audits'] == 1656 and v['previous_partition_records'] == 342
    assert (len(v['parent_manifests']), v['prior_artifacts_unchanged']) == (147, 13006)
    prior_tables = base.load(study.PARENT / 'validation.json')['preserved_tables']
    for table, size in prior_tables.items():
        assert v['preserved_tables'][table] == size + v['new_records'].get(table, 0)
    for path, entry in v['parent_manifests'].items():
        assert base.sha(path) == entry['sha256']
        for f, h in base.load(path)['artifacts'].items(): assert base.sha(f) == h, f
    sources = {**v['source_fingerprints'],
        'experiments/profile_cnf_prepared_partial.py': base.sha('experiments/profile_cnf_prepared_partial.py'),
        'experiments/finalize_cnf_prepared_partial.py': base.sha(__file__)}
    assert len(sources) == 839
    for f, h in sources.items(): assert base.sha(f) == h, f
    head = '5d4dc5e7'; paper = 'paper/bounded_domain_sat_and_amortized_reasoning.tex'
    before = subprocess.check_output(['git', 'show', head + ':' + paper], text=True)
    pattern = r'\\begin\{proof\}.*?\\end\{proof\}'
    proofs = re.findall(pattern, before, re.S)
    assert len(proofs) == 64 and proofs == re.findall(pattern, Path(paper).read_text(), re.S)
    full, focused = [(out / name).read_text() for name in ('full-tests.log', 'focused-tests.log')]
    assert re.search(r'Ran 1579 tests in .*\n\nOK', full)
    assert re.search(r'Ran 90 tests in .*\n\nOK', focused)
    warnings = {k: len(re.findall('ResourceWarning: unclosed database', text)) for k, text in (('full', full), ('focused', focused))}
    assert warnings['focused'] == 0
    sites = Counter(re.sub(r'0x[0-9a-f]+', 'ADDR', line.lstrip('.')) for line in full.splitlines() if 'ResourceWarning: unclosed database' in line)
    latex = (out / 'latex-final.log').read_text()
    assert not re.search(r'Warning|Overfull|Underfull|^!', latex, re.M)
    pages = int(re.search(r'\((\d+) pages,', latex)[1])
    for binding in [cp['reference_union']] + [b for b in cp['prepared_partial'].values() if isinstance(b, dict) and 'sha256' in b]:
        assert base.sha(binding['path']) == binding['sha256']
    work = analysis['work']['prepared']
    assert work['partial_attempts'] == 4 and work['partial_native_leaves'] == 5
    assert work['partial_support_leaves'] == 6 and work['learned_cover_hits'] == 2
    faster = 0
    for repeat in range(4):
        reports = {mode: base.load(out / f'{mode}-{repeat}/report.json') for mode in study.MODES}
        faster += reports['prepared']['summary']['preparation_and_queries'] < reports['partial']['summary']['preparation_and_queries']
        assert study.read_zip(reports['prepared']['delta']) == study.read_zip(reports['partial']['delta'])
    assert faster == 3
    assert not v['new_records']
    assert cp['reference_union'] == study.bound(p['parent'])['reference_union']
    assert work['prepared_partial_leaf_reuses'] == 6 and work['prepared_partial_frame_reuses'] == 1
    profile = base.load(out / 'profiling.json')
    profiled = study.bound(profile['report']); reference = base.load(out / 'prepared-0/report.json')
    assert study.read_zip(profiled['delta']) == study.read_zip(reference['delta'])
    for a, b in zip(study.bound(profiled['queries']), study.bound(reference['queries'])):
        for field in ('root', 'status', 'route', 'expanded_nodes', 'new_ids', 'partial'):
            assert a.get(field) == b.get(field)
    targets = {(7, 4), (15, 3), (19, 3), (20, 3)}
    assert {(q['case'], q['template']) for q in profile['queries']} == targets
    for q in profile['queries']:
        assert base.sha(q['profile']['path']) == q['profile']['sha256']
    previous_profile = base.load(study.PARENT / 'profiling.json')
    def normalizations(data):
        return {(q['case'], q['template']): sum(r['calls'] for r in q['functions'] if r['function'] == 'normalize' and r['file'].endswith('cnf_residual_dag.py')) for q in data['queries']}
    old_calls, new_calls = normalizations(previous_profile), normalizations(profile)
    assert sum(old_calls.values()) == 96 and sum(new_calls.values()) == 89
    assert all(new_calls[k] < old_calls[k] for k in old_calls)
    rows = study.bound(reference['queries'])
    frontier = dict(protocol=study.binding(out / 'protocol.json'), prefix=p['prefix'],
        query_log=reference['queries'], hints=reference['hints'], profile=study.binding(out / 'profiling.json'),
        normalization_calls=dict(before={str(k): v for k, v in old_calls.items()}, after={str(k): v for k, v in new_calls.items()}),
        cases=[c for c in study.bound(p['cases']) if c['index'] in {x[0] for x in targets}],
        partial_queries=[dict(query_index=i, **r) for i, r in enumerate(rows) if r.get('partial')],
        costs=[r for r in analysis['queries'] if (r['case'], r['template']) in targets],
        next_question='Can conditional-cover extraction carry original reason-clause provenance through checked unit/split/component transitions instead of rescanning the full source at every proof node, with explicit source-coordinate and representative bindings?' ,
        limitations=['The current live stream registers no new origins from recomposed outcomes. All four partial attempts use earlier registered three-leaf covers, not the posthoc four-leaf examples from the preceding policy.',
            'Diagnostic profiling preserves proof bytes and routes but adds overhead; cumulative times overlap.',
            'The prepared composer now counts its root canonicalization. Prior literal/key counters omitted that work; wall time included it. The direct profiler-call comparison avoids mixing that counter correction with saved work.',
            'Three of four preparation/query pairs improve, one regresses; the mean difference from native baseline is only 0.06%. No robust general end-to-end speedup is inferred.',
            'No production default, proof format, formal Lean refinement, automatic guard correspondence or unrestricted bound changes.'])
    base.write(out / 'next-target.json', frontier)
    cp['source_fingerprints'] = sources
    cp['prepared_partial']['next_target'] = study.binding(out / 'next-target.json')
    cp['prepared_partial']['profile'] = study.binding(out / 'profiling.json')
    base.write(out / 'checkpoint.json', cp)
    v.update(source_fingerprints=sources, checkpoint=study.binding(out / 'checkpoint.json'))
    base.write(out / 'validation.json', v)
    checks = dict(passed=True, baseline_commit=head, prior_sources=833, final_sources=839,
        prior_artifacts=13006, prior_manifests=147, full_tests=1579, focused_tests=90,
        warnings=warnings, warning_sites=dict(sites), manuscript_pages=pages, paper_sha256=base.sha(paper),
        proof_blocks_unchanged=64, source_fingerprints=sources, final_union_tables=v['preserved_tables'],
        final_checkpoint=study.binding(out / 'checkpoint.json'),
        limitations=p['limitations'] + analysis['limitations'] + v['limitations'] + frontier['limitations'] + [
            'Identical native proofs, dispatches, origins and hints isolate a caller-side preparation saving. Small timing means are local and variable; selected retained Python state omits temporary allocations.',
            'Full-suite SQLite resource warnings remain; focused tests have none. Existing 64 manuscript proofs are unchanged.'])
    base.write(out / 'checks.json', checks)
    files = sorted(f for f in out.rglob('*') if f.is_file() and f.name != 'manifest.json')
    base.write(out / 'manifest.json', dict(artifacts={str(f): base.sha(f) for f in files}))
    print(base.encode(dict(passed=True, artifacts=len(files), next_artifacts=13006+len(files),
        next_manifests=148, sources=839, pages=pages, warnings=warnings, tables=v['preserved_tables'])), flush=True)


if __name__ == '__main__': finalize(Path(sys.argv[1]))
