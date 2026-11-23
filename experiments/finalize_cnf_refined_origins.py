#!/usr/bin/env python3
"""Seal a failed finer-cover admission policy and its causal cost evidence."""
from collections import Counter
from pathlib import Path
import re
import subprocess
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_refined_origins as study
base = study.base


def finalize(out):
    p = base.load(out / 'protocol.json'); v = base.load(out / 'validation.json')
    cp = base.load(out / 'checkpoint.json'); analysis = base.load(out / 'analysis.json')
    assert v['passed'] and v['query_audits'] == 1656 and v['previous_partition_records'] == 342
    assert (len(v['parent_manifests']), v['prior_artifacts_unchanged']) == (150, 13273)
    before_tables = base.load(study.PARENT / 'validation.json')['preserved_tables']
    for table, size in before_tables.items():
        assert v['preserved_tables'][table] == size + v['new_records'].get(table, 0)
    for path, entry in v['parent_manifests'].items():
        assert base.sha(path) == entry['sha256']
        for f, h in base.load(path)['artifacts'].items(): assert base.sha(f) == h, f
    sources = {**v['source_fingerprints'],
        'experiments/profile_cnf_refined_origins.py': base.sha('experiments/profile_cnf_refined_origins.py'),
        'experiments/finalize_cnf_refined_origins.py': base.sha(__file__)}
    assert len(sources) == 857
    for f, h in sources.items(): assert base.sha(f) == h, f
    head = '5f22a953'; paper = 'paper/bounded_domain_sat_and_amortized_reasoning.tex'
    before = subprocess.check_output(['git', 'show', head + ':' + paper], text=True)
    pattern = r'\\begin\{proof\}.*?\\end\{proof\}'
    proofs = re.findall(pattern, before, re.S)
    assert len(proofs) == 64 and proofs == re.findall(pattern, Path(paper).read_text(), re.S)
    full, focused = [(out / name).read_text() for name in ('full-tests.log', 'focused-tests.log')]
    assert re.search(r'Ran 1611 tests in .*\n\nOK', full)
    assert re.search(r'Ran 102 tests in .*\n\nOK', focused)
    warnings = {k: len(re.findall('ResourceWarning: unclosed database', text)) for k, text in (('full', full), ('focused', focused))}
    assert warnings['focused'] == 0
    sites = Counter(re.sub(r'0x[0-9a-f]+', 'ADDR', line.lstrip('.')) for line in full.splitlines() if 'ResourceWarning: unclosed database' in line)
    latex = (out / 'latex-final.log').read_text()
    assert not re.search(r'Warning|Overfull|Underfull|^!', latex, re.M)
    pages = int(re.search(r'\((\d+) pages,', latex)[1])
    for binding in [cp['reference_union']] + [b for b in cp['refined_origins'].values() if isinstance(b, dict) and 'sha256' in b]:
        assert base.sha(binding['path']) == binding['sha256']
    work = analysis['work']['refined']; old = analysis['work']['handoff']
    assert work['partial_attempts'] == old['partial_attempts'] == 4
    assert work['partial_native_leaves'] == old['partial_native_leaves'] == 5
    assert work['partial_support_leaves'] == 8 and old['partial_support_leaves'] == 6
    assert work['partial_split_publications'] == 8 and old['partial_split_publications'] == 6
    assert work['refined_admissions'] == 2 and work['refined_small_skips'] == 1
    assert work['refined_positive_or_missing_skips'] == 1
    assert work['learned_extractions'] == 3 and old['learned_extractions'] == 2
    assert work['verified_nodes'] == 199 and old['verified_nodes'] == 197
    means = analysis['means']; pairs = []
    for repeat in range(4):
        a, b = [base.load(out / f'{mode}-{repeat}/report.json')['summary'] for mode in ('handoff', 'refined')]
        assert a['expanded_nodes'] == b['expanded_nodes'] == 32
        assert (a['hint_bytes'], b['hint_bytes']) == (42031, 61318)
        assert (a['new_payload_bytes'], b['new_payload_bytes']) == (1508442, 1525496)
        pairs.append(dict(repeat=repeat, preparation_query_change=b['preparation_and_queries']/a['preparation_and_queries']-1,
            complete_worker_change=b['complete_worker_seconds']/a['complete_worker_seconds']-1))
    assert sum(r['preparation_query_change'] < 0 for r in pairs) == 1
    assert sum(r['complete_worker_change'] < 0 for r in pairs) == 2
    assert means['refined']['preparation_and_queries'] > means['handoff']['preparation_and_queries']
    assert len(v['extraction_audits']) == 12
    profile = base.load(out / 'profiling.json')
    profiled = study.bound(profile['report']); reference = base.load(out / 'refined-0/report.json')
    assert study.read_zip(profiled['delta']) == study.read_zip(reference['delta'])
    for a, b in zip(study.bound(profiled['queries']), study.bound(reference['queries'])):
        for field in ('root', 'status', 'route', 'expanded_nodes', 'new_ids', 'partial', 'learned', 'screen'):
            assert a.get(field) == b.get(field)
    targets = {(7, 4), (15, 3), (19, 3), (20, 3)}
    assert {(q['case'], q['template']) for q in profile['queries']} == targets
    for q in profile['queries']: assert base.sha(q['profile']['path']) == q['profile']['sha256']
    rows = study.bound(reference['queries']); originals = study.bound(base.load(out / 'handoff-0/report.json')['queries'])
    origin = next(r for r in rows if (r['case'], r['template']) == (15, 3))
    for case in (19, 20):
        row = next(r for r in rows if (r['case'], r['template']) == (case, 3))
        assert row['partial']['origin'] == origin['root']
    frontier = dict(protocol=study.binding(out / 'protocol.json'), prefix=p['prefix'],
        query_log=reference['queries'], hints=reference['hints'], profile=study.binding(out / 'profiling.json'),
        pairs=pairs, decisions='Reject this admission heuristic as a default: no avoided native acquisition, larger proofs and hints, and a preparation/query regression in three pairs.',
        cases=[c for c in study.bound(p['cases']) if c['index'] in {x[0] for x in targets}],
        queries=[dict(query_index=i, previous=originals[i], refined=r) for i, r in enumerate(rows) if r.get('partial')],
        costs=[r for r in analysis['queries'] if (r['case'], r['template']) in targets],
        next_question='Return to discovery on unlabelled whole CNFs. Freeze fresh seeds for the existing larger-mixture generators, run the current solver and existing automatic guard recognizers under matched budgets without supplied assignments or final archived answers, then target the largest unresolved shared-variable interaction. Preserve base/edit/repeat cases and explicit unknowns.',
        relevant_sources=['experiments/cnf_larger_mixtures.py', 'experiments/compare_cnf_affine_probe_safe.py',
            'experiments/cnf_pattern_inventory.py', 'experiments/cnf_ranked_binary_targets.py',
            'experiments/cnf_local_guard.py', 'experiments/cnf_alternative_guard.py'],
        limitations=['All 138 conditional queries per worker were already solved. The finer cover adds no whole-CNF coverage or unrestricted tractability guarantee.',
            'More intact leaves and a smaller residual did not avoid native dispatches. Future ranking must account for the remaining computations and construction costs, not intact-leaf counts alone.',
            'Complete-worker mean is 0.65% lower with mixed pairs, while preparation/query is 2.39% worse and retained state grows. This is not a consistent end-to-end advantage.',
            'The two-dispatch admission threshold and candidate order are exposed-workload heuristics; no claim of optimal acquisition or admission policy.',
            'Diagnostic profiling occurs after timed workers and adds overhead; cumulative times overlap. Cold audit timings are separate from comparative means.',
            'No production default, proof format, formal Lean refinement, automatic guard correspondence or unrestricted bound changes.'])
    base.write(out / 'next-target.json', frontier)
    cp['source_fingerprints'] = sources
    cp['refined_origins']['next_target'] = study.binding(out / 'next-target.json')
    cp['refined_origins']['profile'] = study.binding(out / 'profiling.json')
    base.write(out / 'checkpoint.json', cp)
    v.update(source_fingerprints=sources, checkpoint=study.binding(out / 'checkpoint.json'))
    base.write(out / 'validation.json', v)
    checks = dict(passed=True, baseline_commit=head, prior_sources=851, final_sources=857,
        prior_artifacts=13273, prior_manifests=150, full_tests=1611, focused_tests=102,
        warnings=warnings, warning_sites=dict(sites), manuscript_pages=pages, paper_sha256=base.sha(paper),
        proof_blocks_unchanged=64, source_fingerprints=sources, final_union_tables=v['preserved_tables'],
        final_checkpoint=study.binding(out / 'checkpoint.json'),
        limitations=p['limitations'] + analysis['limitations'] + v['limitations'] + frontier['limitations'] + [
            'Full-suite SQLite resource warnings remain; focused tests have none. Existing 64 manuscript proofs are unchanged.',
            'The preserved development failure was an incorrect test assumption: a two-variable contradiction is closed by native binary reasoning in one expansion; the multi-dispatch admission fixture uses three variables.'])
    base.write(out / 'checks.json', checks)
    files = sorted(f for f in out.rglob('*') if f.is_file() and f.name != 'manifest.json')
    base.write(out / 'manifest.json', dict(artifacts={str(f): base.sha(f) for f in files}))
    print(base.encode(dict(passed=True, artifacts=len(files), next_artifacts=13273+len(files),
        next_manifests=151, sources=857, pages=pages, warnings=warnings, tables=v['preserved_tables'])), flush=True)


if __name__ == '__main__': finalize(Path(sys.argv[1]))
