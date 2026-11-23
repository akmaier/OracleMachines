#!/usr/bin/env python3
"""Seal partial-cover evidence and the measured next construction bottleneck."""
from collections import Counter
from pathlib import Path
import re
import subprocess
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_partial_cover as study
base = study.base


def finalize(out):
    p = base.load(out / 'protocol.json'); v = base.load(out / 'validation.json')
    cp = base.load(out / 'checkpoint.json'); analysis = base.load(out / 'analysis.json')
    assert v['passed'] and v['query_audits'] == 1656 and v['previous_partition_records'] == 342
    assert (len(v['parent_manifests']), v['prior_artifacts_unchanged']) == (146, 12914)
    prior_tables = base.load(study.PARENT / 'validation.json')['preserved_tables']
    for table, size in prior_tables.items():
        assert v['preserved_tables'][table] == size + v['new_records'].get(table, 0)
    for path, entry in v['parent_manifests'].items():
        assert base.sha(path) == entry['sha256']
        for f, h in base.load(path)['artifacts'].items(): assert base.sha(f) == h, f
    sources = {**v['source_fingerprints'],
        'experiments/profile_cnf_partial_cover.py': base.sha('experiments/profile_cnf_partial_cover.py'),
        'experiments/finalize_cnf_partial_cover.py': base.sha(__file__)}
    assert len(sources) == 833
    for f, h in sources.items(): assert base.sha(f) == h, f
    head = '30053303'; paper = 'paper/bounded_domain_sat_and_amortized_reasoning.tex'
    before = subprocess.check_output(['git', 'show', head + ':' + paper], text=True)
    pattern = r'\\begin\{proof\}.*?\\end\{proof\}'
    proofs = re.findall(pattern, before, re.S)
    assert len(proofs) == 64 and proofs == re.findall(pattern, Path(paper).read_text(), re.S)
    full, focused = [(out / name).read_text() for name in ('full-tests.log', 'focused-tests.log')]
    assert re.search(r'Ran 1571 tests in .*\n\nOK', full)
    assert re.search(r'Ran 82 tests in .*\n\nOK', focused)
    warnings = {k: len(re.findall('ResourceWarning: unclosed database', text)) for k, text in (('full', full), ('focused', focused))}
    assert warnings['focused'] == 0
    sites = Counter(re.sub(r'0x[0-9a-f]+', 'ADDR', line.lstrip('.')) for line in full.splitlines() if 'ResourceWarning: unclosed database' in line)
    latex = (out / 'latex-final.log').read_text()
    assert not re.search(r'Warning|Overfull|Underfull|^!', latex, re.M)
    pages = int(re.search(r'\((\d+) pages,', latex)[1])
    for binding in [cp['reference_union']] + [b for b in cp['partial_cover'].values() if isinstance(b, dict) and 'sha256' in b]:
        assert base.sha(binding['path']) == binding['sha256']
    work = analysis['work']['partial']
    assert work['partial_attempts'] == 4 and work['partial_native_leaves'] == 5
    assert work['partial_support_leaves'] == 6 and work['learned_cover_hits'] == 2
    for repeat in range(4):
        reports = {mode: base.load(out / f'{mode}-{repeat}/report.json') for mode in study.MODES}
        assert reports['baseline']['summary']['preparation_and_queries'] < reports['partial']['summary']['preparation_and_queries'] < reports['unit-gated']['summary']['preparation_and_queries']
    profile = base.load(out / 'profiling.json')
    profiled = study.bound(profile['report']); reference = base.load(out / 'partial-0/report.json')
    assert study.read_zip(profiled['delta']) == study.read_zip(reference['delta'])
    for a, b in zip(study.bound(profiled['queries']), study.bound(reference['queries'])):
        for field in ('root', 'status', 'route', 'expanded_nodes', 'new_ids', 'partial'):
            assert a.get(field) == b.get(field)
    targets = {(7, 4), (15, 3), (19, 3), (20, 3)}
    assert {(q['case'], q['template']) for q in profile['queries']} == targets
    for q in profile['queries']:
        assert base.sha(q['profile']['path']) == q['profile']['sha256']
    rows = study.bound(reference['queries'])
    frontier = dict(protocol=study.binding(out / 'protocol.json'), prefix=p['prefix'],
        query_log=reference['queries'], hints=reference['hints'], profile=study.binding(out / 'profiling.json'),
        cases=[c for c in study.bound(p['cases']) if c['index'] in {x[0] for x in targets}],
        partial_queries=[dict(query_index=i, **r) for i, r in enumerate(rows) if r.get('partial')],
        costs=[r for r in analysis['queries'] if (r['case'], r['template']) in targets],
        next_question='Can immutable conditioned residuals, source-name maps and support membership be shared through partial traversal and leaf publication, retaining independent native verification and cold extraction costs?',
        limitations=['The current live stream registers no new origins from recomposed outcomes. All four partial attempts use earlier registered three-leaf covers, not the posthoc four-leaf examples from the preceding policy.',
            'Diagnostic profiling preserves proof bytes and routes but adds overhead; cumulative times overlap.',
            'One root canonicalization before the composer counter reset is omitted from aggregate literal/key counters, although wall time includes it. Carry this preparation explicitly in the next implementation.',
            'No production default, proof format, formal Lean refinement, automatic guard correspondence or unrestricted bound changes.'])
    base.write(out / 'next-target.json', frontier)
    cp['source_fingerprints'] = sources
    cp['partial_cover']['next_target'] = study.binding(out / 'next-target.json')
    cp['partial_cover']['profile'] = study.binding(out / 'profiling.json')
    base.write(out / 'checkpoint.json', cp)
    v.update(source_fingerprints=sources, checkpoint=study.binding(out / 'checkpoint.json'))
    base.write(out / 'validation.json', v)
    checks = dict(passed=True, baseline_commit=head, prior_sources=827, final_sources=833,
        prior_artifacts=12914, prior_manifests=146, full_tests=1571, focused_tests=82,
        warnings=warnings, warning_sites=dict(sites), manuscript_pages=pages, paper_sha256=base.sha(paper),
        proof_blocks_unchanged=64, source_fingerprints=sources, final_union_tables=v['preserved_tables'],
        final_checkpoint=study.binding(out / 'checkpoint.json'),
        limitations=p['limitations'] + analysis['limitations'] + v['limitations'] + frontier['limitations'] + [
            'Preparation/query time improves over complete covers but still loses to baseline. Complete-worker time does not improve.',
            'Full-suite SQLite resource warnings remain; focused tests have none. Existing 64 manuscript proofs are unchanged.'])
    base.write(out / 'checks.json', checks)
    files = sorted(f for f in out.rglob('*') if f.is_file() and f.name != 'manifest.json')
    base.write(out / 'manifest.json', dict(artifacts={str(f): base.sha(f) for f in files}))
    print(base.encode(dict(passed=True, artifacts=len(files), next_artifacts=12914+len(files),
        next_manifests=147, sources=833, pages=pages, warnings=warnings, tables=v['preserved_tables'])), flush=True)


if __name__ == '__main__': finalize(Path(sys.argv[1]))
