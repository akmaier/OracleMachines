#!/usr/bin/env python3
"""Seal exact origin carry, local savings, total regressions and the next cost target."""
from collections import Counter
from pathlib import Path
import re
import subprocess
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_carried_origins as study
base = study.base


def finalize(out):
    p = base.load(out / 'protocol.json'); v = base.load(out / 'validation.json')
    cp = base.load(out / 'checkpoint.json'); analysis = base.load(out / 'analysis.json')
    assert v['passed'] and v['query_audits'] == 1656 and v['previous_partition_records'] == 342
    assert (len(v['parent_manifests']), v['prior_artifacts_unchanged']) == (148, 13095)
    prior_tables = base.load(study.PARENT / 'validation.json')['preserved_tables']
    for table, size in prior_tables.items():
        assert v['preserved_tables'][table] == size + v['new_records'].get(table, 0)
    for path, entry in v['parent_manifests'].items():
        assert base.sha(path) == entry['sha256']
        for f, h in base.load(path)['artifacts'].items(): assert base.sha(f) == h, f
    sources = {**v['source_fingerprints'],
        'experiments/profile_cnf_carried_origins.py': base.sha('experiments/profile_cnf_carried_origins.py'),
        'experiments/finalize_cnf_carried_origins.py': base.sha(__file__)}
    assert len(sources) == 845
    for f, h in sources.items(): assert base.sha(f) == h, f
    head = '1a9b0c2a'; paper = 'paper/bounded_domain_sat_and_amortized_reasoning.tex'
    before = subprocess.check_output(['git', 'show', head + ':' + paper], text=True)
    pattern = r'\\begin\{proof\}.*?\\end\{proof\}'
    proofs = re.findall(pattern, before, re.S)
    assert len(proofs) == 64 and proofs == re.findall(pattern, Path(paper).read_text(), re.S)
    full, focused = [(out / name).read_text() for name in ('full-tests.log', 'focused-tests.log')]
    assert re.search(r'Ran 1590 tests in .*\n\nOK', full)
    assert re.search(r'Ran 111 tests in .*\n\nOK', focused)
    warnings = {k: len(re.findall('ResourceWarning: unclosed database', text)) for k, text in (('full', full), ('focused', focused))}
    assert warnings['focused'] == 0
    sites = Counter(re.sub(r'0x[0-9a-f]+', 'ADDR', line.lstrip('.')) for line in full.splitlines() if 'ResourceWarning: unclosed database' in line)
    latex = (out / 'latex-final.log').read_text()
    assert not re.search(r'Warning|Overfull|Underfull|^!', latex, re.M)
    pages = int(re.search(r'\((\d+) pages,', latex)[1])
    for binding in [cp['reference_union']] + [b for b in cp['carried_origins'].values() if isinstance(b, dict) and 'sha256' in b]:
        assert base.sha(binding['path']) == binding['sha256']
    work = analysis['work']['carried']
    assert work['partial_attempts'] == 4 and work['partial_native_leaves'] == 5
    assert work['partial_support_leaves'] == 6 and work['learned_cover_hits'] == 2
    faster = 0
    for repeat in range(4):
        reports = {mode: base.load(out / f'{mode}-{repeat}/report.json') for mode in study.MODES}
        faster += reports['carried']['summary']['preparation_and_queries'] < reports['prepared']['summary']['preparation_and_queries']
        assert study.read_zip(reports['prepared']['delta']) == study.read_zip(reports['carried']['delta'])
    assert faster == 2
    assert len(v['extraction_audits']) == 8
    assert not v['new_records']
    assert cp['reference_union'] == study.bound(p['parent'])['reference_union']
    assert work['prepared_partial_leaf_reuses'] == 6 and work['prepared_partial_frame_reuses'] == 1
    profile = base.load(out / 'profiling.json')
    profiled = study.bound(profile['report']); reference = base.load(out / 'carried-0/report.json')
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
    assert old_calls == new_calls and sum(new_calls.values()) == 89
    def restrictions(data):
        return {(q['case'], q['template']): sum(r['calls'] for r in q['functions'] if r['function'] == 'restrict_scan' and r['file'].endswith('cnf_residual_dag.py')) for q in data['queries']}
    old_restrict, new_restrict = restrictions(previous_profile), restrictions(profile)
    assert (old_restrict[(7, 4)], old_restrict[(15, 3)]) == (1996, 2048)
    assert (new_restrict[(7, 4)], new_restrict[(15, 3)]) == (15, 25)
    assert work['learned_extract_origin_untouched_representatives'] == 2647
    assert work['learned_extract_origin_index_literals'] == 1593
    assert work['learned_extract_origin_scanned_literals'] == 480
    assert work['learned_extract_origin_copied_map_slots'] == 5740
    phase_pairs = []
    for repeat in range(4):
        values = {}
        for mode in ('prepared', 'carried'):
            qs = base.load(out / f'{mode}-{repeat}/queries.json')
            values[mode] = sum(q['counts'].get('unit_gate_cover_seconds', 0) for q in qs)
        assert values['carried'] < values['prepared']
        phase_pairs.append(dict(repeat=repeat, **values))
    rows = study.bound(reference['queries'])
    frontier = dict(protocol=study.binding(out / 'protocol.json'), prefix=p['prefix'],
        query_log=reference['queries'], hints=reference['hints'], profile=study.binding(out / 'profiling.json'),
        normalization_calls={str(k): v for k, v in new_calls.items()},
        restriction_calls=dict(before={str(k): v for k, v in old_restrict.items()}, after={str(k): v for k, v in new_restrict.items()}),
        cover_phase_pairs=phase_pairs,
        cases=[c for c in study.bound(p['cases']) if c['index'] in {x[0] for x in targets}],
        partial_queries=[dict(query_index=i, **r) for i, r in enumerate(rows) if r.get('partial')],
        costs=[r for r in analysis['queries'] if (r['case'], r['template']) in targets],
        next_question='Can the five missing-leaf acquisitions consume the canonical formula/name/key triple already held by the partial traversal, avoiding repeated caller preparation without weakening native certificate or source checks?'  ,
        limitations=['The current live stream registers no new origins from recomposed outcomes. All four partial attempts use earlier registered three-leaf covers, not the posthoc four-leaf examples from the preceding policy.',
            'Diagnostic profiling preserves proof bytes and routes but adds overhead; cumulative times overlap.',
            'The prepared composer now counts its root canonicalization. Prior literal/key counters omitted that work; wall time included it. The direct profiler-call comparison avoids mixing that counter correction with saved work.',
            'Cover-phase time improves in every pair, but preparation/query mean regresses 1.79% with two faster and two slower trials. Complete-worker mean regresses 6.32%; retain the negative result.',
            'The existing general canonicalization cache already regressed; inspect its evidence before trying another cache. Favor explicit call-local preparation transport with unchanged proof checking.',
            'No production default, proof format, formal Lean refinement, automatic guard correspondence or unrestricted bound changes.'])
    base.write(out / 'next-target.json', frontier)
    cp['source_fingerprints'] = sources
    cp['carried_origins']['next_target'] = study.binding(out / 'next-target.json')
    cp['carried_origins']['profile'] = study.binding(out / 'profiling.json')
    base.write(out / 'checkpoint.json', cp)
    v.update(source_fingerprints=sources, checkpoint=study.binding(out / 'checkpoint.json'))
    base.write(out / 'validation.json', v)
    checks = dict(passed=True, baseline_commit=head, prior_sources=839, final_sources=845,
        prior_artifacts=13095, prior_manifests=148, full_tests=1590, focused_tests=111,
        warnings=warnings, warning_sites=dict(sites), manuscript_pages=pages, paper_sha256=base.sha(paper),
        proof_blocks_unchanged=64, source_fingerprints=sources, final_union_tables=v['preserved_tables'],
        final_checkpoint=study.binding(out / 'checkpoint.json'),
        limitations=p['limitations'] + analysis['limitations'] + v['limitations'] + frontier['limitations'] + [
            'Exact minimum original representatives and native proofs are preserved. Local origin-work savings do not establish a total-cost gain; copied maps and indexing add transient state.',
            'Full-suite SQLite resource warnings remain; focused tests have none. Existing 64 manuscript proofs are unchanged.'])
    base.write(out / 'checks.json', checks)
    files = sorted(f for f in out.rglob('*') if f.is_file() and f.name != 'manifest.json')
    base.write(out / 'manifest.json', dict(artifacts={str(f): base.sha(f) for f in files}))
    print(base.encode(dict(passed=True, artifacts=len(files), next_artifacts=13095+len(files),
        next_manifests=149, sources=845, pages=pages, warnings=warnings, tables=v['preserved_tables'])), flush=True)


if __name__ == '__main__': finalize(Path(sys.argv[1]))
