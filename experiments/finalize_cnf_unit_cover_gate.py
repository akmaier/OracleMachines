#!/usr/bin/env python3
"""Seal unit gating and bind the remaining partially broken conditional covers."""
from collections import Counter
from copy import deepcopy
from pathlib import Path
import re, subprocess, sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_unit_cover_gate as study
from experiments.cnf_learned_conditional import check_cover
from experiments.cnf_clause_deletion_guard import clause_set
from experiments.cnf_residual_dag import restrict
base = study.base


def finalize(out):
    p = base.load(out / 'protocol.json'); v = base.load(out / 'validation.json')
    cp = base.load(out / 'checkpoint.json'); analysis = base.load(out / 'analysis.json')
    assert v['passed'] and v['query_audits'] == 2208 and v['previous_partition_records'] == 342
    assert (len(v['parent_manifests']), v['prior_artifacts_unchanged']) == (145, 12813)
    prior_tables = base.load(study.PARENT / 'validation.json')['preserved_tables']
    for table, size in prior_tables.items():
        assert v['preserved_tables'][table] == size + v['new_records'].get(table, 0)
    for path, entry in v['parent_manifests'].items():
        assert base.sha(path) == entry['sha256']
        for f, h in base.load(path)['artifacts'].items(): assert base.sha(f) == h, f
    sources = {**v['source_fingerprints'], __file__.removeprefix(str(Path.cwd()) + '/'): base.sha(__file__)}
    assert len(sources) == 827
    for f, h in sources.items(): assert base.sha(f) == h, f
    head = '73dd4e67'; paper = 'paper/bounded_domain_sat_and_amortized_reasoning.tex'
    before = subprocess.check_output(['git', 'show', head + ':' + paper], text=True)
    pattern = r'\\begin\{proof\}.*?\\end\{proof\}'
    proofs = re.findall(pattern, before, re.S)
    assert len(proofs) == 64 and proofs == re.findall(pattern, Path(paper).read_text(), re.S)
    full, focused = [(out / name).read_text() for name in ('full-tests.log', 'focused-tests.log')]
    assert re.search(r'Ran 1559 tests in .*\n\nOK', full)
    assert re.search(r'Ran 70 tests in .*\n\nOK', focused)
    warnings = {k: len(re.findall('ResourceWarning: unclosed database', text)) for k, text in (('full', full), ('focused', focused))}
    assert warnings['focused'] == 0
    sites = Counter(re.sub(r'0x[0-9a-f]+', 'ADDR', line.lstrip('.')) for line in full.splitlines() if 'ResourceWarning: unclosed database' in line)
    latex = (out / 'latex-final.log').read_text()
    assert not re.search(r'Warning|Overfull|Underfull|^!', latex, re.M)
    pages = int(re.search(r'\((\d+) pages,', latex)[1])
    for binding in [cp['reference_union']] + [b for b in cp['unit_cover_gate'].values() if isinstance(b, dict) and 'sha256' in b]:
        assert base.sha(binding['path']) == binding['sha256']
    assert analysis['work']['unit-gated']['unit_gate_conflicts'] == 3
    assert analysis['work']['unit-gated']['learned_cover_hits'] == 2
    assert analysis['work']['unit-gated']['unit_gate_screens'] == 9
    assert analysis['work']['gate-only'].get('learned_extractions', 0) == 0
    for repeat in range(4):
        reports = {mode: base.load(out / f'{mode}-{repeat}/report.json') for mode in study.MODES}
        assert study.read_zip(reports['baseline']['delta']) == study.read_zip(reports['gate-only']['delta'])
        assert reports['baseline']['summary']['preparation_and_queries'] < reports['unit-gated']['summary']['preparation_and_queries'] < reports['learned']['summary']['preparation_and_queries']

    # Diagnostic partial matches: origin proofs must precede each target. These
    # final hints are inspected posthoc, never supplied to the timed workers.
    hints = base.load(out / 'unit-gated-0/hints.json')
    rows = base.load(out / 'unit-gated-0/queries.json'); cases = study.bound(p['cases'])
    matches = []
    for index, row in enumerate(rows):
        if (row['case'], row['template']) not in ((19, 3), (20, 3)): continue
        target = restrict(cases[row['case']]['source'], dict(row['assignment']))
        members = clause_set(target, Counter())
        for entry in hints['learned']:
            origins = [(j, r) for j, r in enumerate(rows[:index]) if r['root'] == entry['origin'] and r['route'] in ('native', 'unit-fallback') and r['expanded_nodes'] >= 3]
            if entry['cover'] is None or not origins or entry['guard'] != sorted(row['assignment']): continue
            check_cover(entry['cover'])
            j, origin = origins[-1]
            leaves = [dict(index=i, assumptions=t['assumptions'],
                missing=[list(cl) for cl in sorted(clause_set(t['clauses'], Counter()) - members)])
                for i, t in enumerate(entry['cover']['templates'])]
            matches.append(dict(target_case=row['case'], target_template=row['template'], query_index=index,
                source=cases[row['case']]['source'], assignment=row['assignment'], target_root=row['root'],
                origin_case=origin['case'], origin_template=origin['template'], origin_query_index=j,
                origin=entry['origin'], names=entry['names'], cover=deepcopy(entry['cover']), leaves=leaves,
                intact_leaves=sum(not leaf['missing'] for leaf in leaves)))
    expected = {(19, 4): (2, 3), (19, 15): (3, 4), (20, 4): (1, 3), (20, 15): (2, 4), (20, 19): (3, 4)}
    assert {(m['target_case'], m['origin_case']): (m['intact_leaves'], len(m['leaves'])) for m in matches} == expected
    assert all(len(leaf['missing']) <= 1 for m in matches for leaf in m['leaves'])
    frontier = dict(protocol=study.binding(out / 'protocol.json'), prefix=p['prefix'],
        query_log=study.binding(out / 'unit-gated-0/queries.json'), hints=study.binding(out / 'unit-gated-0/hints.json'),
        matches=matches, costs=[r for r in analysis['queries'] if (r['case'], r['template']) in ((19, 3), (20, 3), (7, 4))],
        next_question='Can intact checked branches be retained while native acquisition handles only failed leaves, with exact partition recomposition and full SAT witness lifting?',
        limitations=['Posthoc matching of eventually retained covers from strictly earlier origins. Extraction and matching were not free; these are opportunities, not measured partial-cover solver hits.',
            'Replay only earlier queries to reconstruct live pools/bank. Final hints and the final union must not seed a chronological experiment.',
            'A missing support clause invalidates that leaf certificate. A negative root needs all reachable branches; a positive leaf needs a full-target witness. Preserve the SAT control.'])
    base.write(out / 'next-target.json', frontier)
    cp['source_fingerprints'] = sources
    cp['unit_cover_gate']['next_target'] = study.binding(out / 'next-target.json')
    base.write(out / 'checkpoint.json', cp)
    v.update(source_fingerprints=sources, checkpoint=study.binding(out / 'checkpoint.json'))
    base.write(out / 'validation.json', v)
    checks = dict(passed=True, baseline_commit=head, prior_sources=822, final_sources=827,
        prior_artifacts=12813, prior_manifests=145, full_tests=1559, focused_tests=70,
        warnings=warnings, warning_sites=dict(sites), manuscript_pages=pages, paper_sha256=base.sha(paper),
        proof_blocks_unchanged=64, source_fingerprints=sources, final_union_tables=v['preserved_tables'],
        final_checkpoint=study.binding(out / 'checkpoint.json'),
        limitations=p['limitations'] + analysis['limitations'] + v['limitations'] + frontier['limitations'] + [
            'The gate fixes the expensive unit-conflict route, but gated learning still regresses against baseline. No default solver change or new whole-input class.',
            'Full-suite SQLite resource warnings remain; focused tests have none. Existing 64 manuscript proofs are unchanged. No new Lean refinement theorem.'])
    base.write(out / 'checks.json', checks)
    files = sorted(f for f in out.rglob('*') if f.is_file() and f.name != 'manifest.json')
    base.write(out / 'manifest.json', dict(artifacts={str(f): base.sha(f) for f in files}))
    print(base.encode(dict(passed=True, artifacts=len(files), next_artifacts=12813+len(files),
        next_manifests=146, sources=827, pages=pages, warnings=warnings, tables=v['preserved_tables'])), flush=True)


if __name__ == '__main__': finalize(Path(sys.argv[1]))
