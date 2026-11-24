#!/usr/bin/env python3
"""Seal delayed binary preparation, both controls and preserved proof authority."""
from collections import Counter
from pathlib import Path
import re
import subprocess
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_probe_binary_lazy as study
base = study.base


def finalize(out):
    p = base.load(out/'protocol.json')
    v = base.load(out/'validation.json')
    cp = base.load(out/'checkpoint.json')
    assert v['passed'] and v['query_audits'] == 1728
    assert v['census_events'] == 353 and v['census_verdicts']['binary-unsat'] == 19
    assert v['previous_partition_records'] == 342
    assert (len(v['parent_manifests']), v['prior_artifacts_unchanged']) == (159, 14390)
    for path, entry in v['parent_manifests'].items():
        assert base.sha(path) == entry['sha256']
        for f, h in base.load(path)['artifacts'].items(): assert base.sha(f) == h, f
    sources = {**v['source_fingerprints'],
        'experiments/profile_cnf_probe_binary_lazy.py': base.sha('experiments/profile_cnf_probe_binary_lazy.py'),
        'experiments/inspect_cnf_stopped_origins.py': base.sha('experiments/inspect_cnf_stopped_origins.py'),
        'experiments/finalize_cnf_probe_binary_lazy.py': base.sha(__file__)}
    assert len(sources) == 926
    for f, h in sources.items(): assert base.sha(f) == h, f
    head = 'd15f57ed'
    paper = 'paper/bounded_domain_sat_and_amortized_reasoning.tex'
    old = subprocess.check_output(['git', 'show', head+':'+paper], text=True)
    pattern = r'\\begin\{proof\}.*?\\end\{proof\}'
    proofs = re.findall(pattern, old, re.S)
    assert len(proofs) == 64 and proofs == re.findall(pattern, Path(paper).read_text(), re.S)
    full, focused = [(out/f).read_text() for f in ('full-tests.log', 'focused-tests.log')]
    assert re.search(r'Ran 1697 tests in .*\n\nOK', full)
    assert re.search(r'Ran 86 tests in .*\n\nOK', focused)
    warnings = {k: len(re.findall('ResourceWarning: unclosed database', text))
        for k, text in (('full', full), ('focused', focused))}
    assert warnings['focused'] == 0
    latex = (out/'latex-final.log').read_text()
    assert not re.search(r'Warning|Overfull|Underfull|^!', latex, re.M)
    pages = int(re.search(r'\((\d+) pages,', latex)[1])
    analysis = base.load(out/'analysis.json')['summary']
    coverage, pairs, frontiers, comparisons, queries = {}, [], {}, {}, {}
    cost_keys = ('mean_solve_seconds', 'mean_complete_worker_seconds', 'mean_peak_rss_bytes',
        'native_payload', 'native_nodes', 'checked_python_bytes', 'database_bytes', 'compressed_bytes')
    for split in study.SPLITS:
        cases = study.bound(p['cases'][split])
        coverage[split], queries[split], sets = {}, {}, {}
        roots = {c['root'] for c in cases}
        assert len(roots) == 48
        for mode in study.MODES:
            rows = [base.load(out/f'{split}-{mode}-{i}/queries.json') for i in range(4)]
            completed = {c['root'] for c,r in zip(cases,rows[0]) if r['result'] is not None}
            sets[mode] = completed
            coverage[split][mode] = dict(completed_distinct_roots=len(completed), distinct_roots=48,
                statuses=dict(Counter(r['status'] for r in rows[0])))
            queries[split][mode] = [dict(case=c['case'], family=c['family'], root=c['root'], status=r['status'],
                mean_solve_seconds=sum(rr[i]['solve_seconds'] for rr in rows)/4, metrics=r['metrics'])
                for i,(c,r) in enumerate(zip(cases,rows[0]))]
        assert sets['lazy'] == sets['closure']
        frontiers[split] = dict(gained_roots=sorted(sets['lazy']-sets['current']),
            lost_roots=sorted(sets['current']-sets['lazy']), unresolved_roots=sorted(roots-sets['lazy']))
        comparisons[split] = {}
        for control in ('current', 'closure'):
            x, y = analysis[split][control], analysis[split]['lazy']
            comparisons[split][control] = {k: y[k]/x[k]-1 for k in cost_keys}
            comparisons[split][control]['expanded_nodes'] = y['counters']['expanded_nodes']/x['counters']['expanded_nodes']-1
            for repeat in range(4):
                a = base.load(out/f'{split}-{control}-{repeat}/report.json')['summary']
                b = base.load(out/f'{split}-lazy-{repeat}/report.json')['summary']
                pairs.append(dict(split=split, control=control, repeat=repeat,
                    solve_change=b['solve_seconds']/a['solve_seconds']-1,
                    worker_change=b['complete_worker_seconds']/a['complete_worker_seconds']-1))
    assert not any(r['known_in_parent'] for r in p['novelty']['holdout'])
    profile = base.load(out/'profiling.json')
    assert len(profile['records']) == 3
    for r in profile['records']:
        assert base.sha(r['profile']['path']) == r['profile']['sha256']
        row = base.load(out/f"holdout-{r['mode']}-0/queries.json")[r['case']]
        assert (row['status'], row['metrics']) == (r['result']['status'], r['result']['metrics'])
    origins = base.load(out/'stopped-origins.json')
    assert len(origins['pairs']) == 24 and origins['selected']['target_case'] == 64
    assert origins['profile'] == study.binding(out/'profiling.json')
    assert origins['queries'] == study.binding(out/'holdout-lazy-0/queries.json')
    decision = base.load(out/'decision.json')
    frontier = dict(protocol=study.binding(out/'protocol.json'), analysis=study.binding(out/'analysis.json'),
        profiling=study.binding(out/'profiling.json'), stopped_origins=study.binding(out/'stopped-origins.json'), coverage=coverage, frontiers=frontiers,
        comparisons=comparisons, pairs=pairs, queries=queries, decision=decision,
        archive_reader=cp['reference_union_reader'], limitations=p['limitations']+v['limitations']+profile['limitations']+[
            'Naive/lazy certificate identity does not imply improved coverage over handoff-only or lower total cost. Both controls and all regressions remain explicit.',
            'All 64 preceding proof environments are unchanged. The full suite retains pre-existing SQLite ResourceWarnings.'])
    base.write(out/'next-target.json', frontier)
    cp['source_fingerprints'] = sources
    cp['probe_binary_lazy'].update(next_target=study.binding(out/'next-target.json'),
        profile=study.binding(out/'profiling.json'), stopped_origins=study.binding(out/'stopped-origins.json'), decision=decision)
    base.write(out/'checkpoint.json', cp)
    v.update(source_fingerprints=sources, checkpoint=study.binding(out/'checkpoint.json'))
    base.write(out/'validation.json', v)
    base.write(out/'checks.json', dict(passed=True, baseline_commit=head, prior_sources=918, final_sources=len(sources),
        prior_artifacts=14390, prior_manifests=159, full_tests=1697, focused_tests=86, warnings=warnings,
        manuscript_pages=pages, paper_sha256=base.sha(paper), proof_blocks_unchanged=64,
        source_fingerprints=sources, final_union_tables=v['preserved_tables'],
        final_checkpoint=study.binding(out/'checkpoint.json'), limitations=frontier['limitations']))
    files = sorted(f for f in out.rglob('*') if f.is_file() and f.name != 'manifest.json')
    base.write(out/'manifest.json', dict(artifacts={str(f):base.sha(f) for f in files}))
    print(base.encode(dict(passed=True, artifacts=len(files), next_artifacts=14390+len(files),
        next_manifests=160, sources=len(sources), pages=pages, warnings=warnings,
        tables=v['preserved_tables'], coverage=coverage, comparisons=comparisons)), flush=True)


if __name__ == '__main__': finalize(Path(sys.argv[1]))
