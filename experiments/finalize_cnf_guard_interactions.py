#!/usr/bin/env python3
"""Seal local guard composition, its regressions and the next live test."""
from pathlib import Path
import re
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from experiments import study_cnf_guard_interactions as study

base = study.base
old = study.old


def finalize(out):
    validation = base.load(out / 'validation.json')
    checkpoint = base.load(out / 'checkpoint.json')
    analysis = old.bound(checkpoint['guard_interactions']['analysis'])
    assert validation['passed']
    assert validation['checkpoint'] == old.binding(out / 'checkpoint.json')
    assert tuple(validation[k] for k in (
        'contexts_checked', 'hints_checked', 'selected_checked', 'closures_checked'
    )) == (648, 6100, 116, 61)
    assert (len(validation['parent_manifests']), validation['prior_artifacts_unchanged']) == (165, 15566)
    for path, entry in validation['parent_manifests'].items():
        assert base.sha(path) == entry['sha256']
        for filename, digest in base.load(path)['artifacts'].items():
            assert base.sha(filename) == digest, filename
    sources = {
        **validation['source_fingerprints'],
        'experiments/finalize_cnf_guard_interactions.py': base.sha(__file__),
    }
    assert len(sources) == 960
    for filename, digest in sources.items():
        assert base.sha(filename) == digest, filename

    # Describe the useful closure tiers, separately from path-set differences.
    contexts = {}
    cores = set()
    for binding in analysis['study']['targets']:
        report = old.bound(binding)
        for row in old.bound(report['records']):
            contexts[(report['target'], row['event'])] = row
            if row['hints']:
                cores.add(row['root'])
    closures = analysis['closure_study']['records']
    opposite = whole = 0
    for closure in closures:
        row = contexts[(closure['target'], closure['event'])]
        units = set(row['analysis']['explicit_units'])
        has_opposite = any(-literal in units for literal in units)
        assert not (has_opposite and closure['needs_binary_guard'])
        opposite += has_opposite
        whole += row['whole']
    binary = sum(row['needs_binary_guard'] for row in closures)
    breakdown = dict(
        unique_hint_cores=len(cores), direct_opposite_unit_closures=opposite,
        unit_plus_original_extra=len(closures) - opposite - binary,
        needs_binary_guard=binary, full_source_closures=whole,
        subset_closures=len(closures) - whole,
    )
    assert breakdown == dict(
        unique_hint_cores=616, direct_opposite_unit_closures=40,
        unit_plus_original_extra=1, needs_binary_guard=20,
        full_source_closures=36, subset_closures=25,
    )
    analysis['structure_breakdown'] = breakdown
    base.write(out / 'analysis.json', analysis)

    paper = 'paper/bounded_domain_sat_and_amortized_reasoning.tex'
    baseline = 'f8ac2d15'
    before = subprocess.check_output(['git', 'show', baseline + ':' + paper], text=True)
    proof_pattern = r'\\begin\{proof\}.*?\\end\{proof\}'
    proofs = re.findall(proof_pattern, before, re.S)
    assert len(proofs) == 64
    assert proofs == re.findall(proof_pattern, Path(paper).read_text(), re.S)
    full = (out / 'full-tests.log').read_text()
    focused = (out / 'focused-tests.log').read_text()
    assert re.search(r'Ran 1749 tests in .*\n\nOK', full)
    assert re.search(r'Ran 105 tests in .*\n\nOK', focused)
    warnings = {key: text.count('ResourceWarning: unclosed database')
                for key, text in (('full', full), ('focused', focused))}
    assert warnings['focused'] == 0
    latex = (out / 'latex-final.log').read_text()
    assert not re.search(r'Warning|Overfull|Underfull|^!', latex, re.M)
    pages = int(re.search(r'\((\d+) pages,', latex)[1])

    changes = {}
    for name in ('selected_pairs', 'closure_pairs'):
        paired = analysis[name]
        assert paired['compile']['unresolved'] == paired['fresh']['unresolved'] == 0
        changes[name] = {key: paired['compile'][key] / paired['fresh'][key] - 1
                         for key in ('seconds', 'nodes', 'payload_bytes')}
    decision = dict(
        status='offline diagnostic; no default change or new completed whole query',
        result='Source-bound guard consequences compose into 61 native local refutations. Twenty need binary guards; three roots were absent after the preceding shared query budget. Both acquisition controls complete with individual budgets.',
        structure_breakdown=breakdown, acquisition_changes=changes,
        limitation='One alternating cold pair per local object, with provisioned support. Discovery, recognition, hint persistence, original acquisition and historical audits are additional. Isolated exclusions regress; no end-to-end gain is established.',
        next_target='Test a selective live local-contradiction gate: opposite units, then units plus original binary clauses, then supported binary guards. Check only active short guards, find a contradiction by SCC and compile its two paths. Keep source support containment and native recomposition; compare whole-query cost and completion against ordinary and guided policies, including misses and cold replay.',
        secondary_target='Share repeated exact core bodies in the separate hint bank; 6100 hints reference 616 cores. No new storage scheme or memory reduction is implemented here.',
        scope='Wider guards, automatic origin discovery, general transport, fresh unlabelled evaluation and uniformly efficient arbitrary-CNF closure remain open. Guard graph components need not be independent source components.',
    )
    base.write(out / 'decision.json', decision)
    base.write(out / 'next-target.json', dict(
        decision=decision, summary=analysis['summary'],
        satisfiable_combined_graphs=analysis['satisfiable_combined_graphs'],
        limitations=analysis['limitations'],
    ))
    checkpoint['source_fingerprints'] = sources
    checkpoint['guard_interactions'].update(
        analysis=old.binding(out / 'analysis.json'),
        decision=old.binding(out / 'decision.json'),
        next_target=old.binding(out / 'next-target.json'),
    )
    base.write(out / 'checkpoint.json', checkpoint)
    validation.update(source_fingerprints=sources, checkpoint=old.binding(out / 'checkpoint.json'))
    base.write(out / 'validation.json', validation)
    base.write(out / 'checks.json', dict(
        passed=True, baseline_commit=baseline, prior_sources=954, final_sources=len(sources),
        prior_artifacts=15566, prior_manifests=165, full_tests=1749, focused_tests=105,
        warnings=warnings, manuscript_pages=pages, paper_sha256=base.sha(paper),
        proof_blocks_unchanged=64, source_fingerprints=sources,
        final_union_tables=validation['preserved_tables'],
        final_checkpoint=old.binding(out / 'checkpoint.json'),
        limitations=validation['limitations'],
    ))
    files = sorted(path for path in out.rglob('*') if path.is_file() and path.name != 'manifest.json')
    base.write(out / 'manifest.json', dict(artifacts={str(path): base.sha(path) for path in files}))
    print(base.encode(dict(
        passed=True, sources=len(sources), artifacts=len(files), next_artifacts=15566 + len(files),
        next_manifests=166, pages=pages, warnings=warnings, structure_breakdown=breakdown,
        tables=validation['preserved_tables'], acquisition_changes=changes,
    )), flush=True)


if __name__ == '__main__':
    finalize(Path(sys.argv[1]))
