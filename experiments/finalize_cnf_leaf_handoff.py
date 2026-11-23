#!/usr/bin/env python3
"""Seal missing-leaf handoff, preserved regressions and a causal origin-policy diagnostic."""
from collections import Counter
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import hashlib
import time
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_leaf_handoff as study
base = study.base


def origin_followup(out, p, reference):
    """Diagnostic only: extract from actual earlier recomposed proof payloads."""
    from experiments.cnf_snapshot_replay import SnapshotResidualSolver
    from experiments.cnf_carried_origins import extract
    from experiments.cnf_conditional_unit_support import extract as original_extract
    from experiments.cnf_residual_dag import restrict, propagate
    from experiments.cnf_learned_conditional import check_cover, COVER_FORMAT
    from experiments.cnf_clause_deletion_guard import clause_set
    queries = study.bound(reference['queries'])
    cases = {x['index']: x for x in study.bound(p['cases'])}
    prefix = study.read_zip(p['prefix']); delta = study.read_zip(reference['delta'])
    findings = []
    with tempfile.TemporaryDirectory() as directory:
        database = Path(directory) / 'trial'
        study.restore(prefix, database, delta)
        solver = SnapshotResidualSolver(database)
        try:
            for origin_case, target_case in ((15, 19), (15, 20), (19, 20)):
                origin_index, origin = next((i, q) for i, q in enumerate(queries) if q['case'] == origin_case and q['template'] == 3)
                target_index, target = next((i, q) for i, q in enumerate(queries) if q['case'] == target_case and q['template'] == 3)
                assert origin_index < target_index and origin['status'] == 'unsat'
                assert origin['assignment'] == target['assignment']
                source = restrict(cases[origin_case]['source'], dict(origin['assignment']))
                raw_target = restrict(cases[target_case]['source'], dict(target['assignment']))
                before = Counter(solver.counts); began = time.perf_counter()
                bundle, counts = extract(solver, source)
                seconds = time.perf_counter() - began
                native_counts = dict(solver.counts - before)
                other, _ = original_extract(solver, source)
                assert bundle == other and bundle['origin'] == origin['root']
                cover = dict(format=COVER_FORMAT, tree=bundle['tree'], templates=[e['template'] for e in bundle['entries']])
                c = Counter(); check_cover(cover, c)
                members = clause_set(raw_target, c)
                intact = [clause_set(t['clauses'], c) <= members for t in cover['templates']]
                current = target['partial']
                cnf, names, root = solver._canonical(raw_target)
                _, trace, conflict = propagate(cnf, c)
                assert target['screen'] == dict(root=root, trace=trace, conflict=conflict)
                assert conflict is None
                fixed = {names[abs(lit)-1]: lit > 0 for lit, _ in trace}
                def residual_work(context):
                    raw = restrict(raw_target, context, c)
                    return dict(context=sorted(context.items()), source_sha256=hashlib.sha256(base.encode(raw).encode()).hexdigest(), clauses=len(raw),
                        literals=sum(map(len, raw)), variables=len({abs(l) for cl in raw for l in cl}))
                candidate_missing = []
                for i, (entry, intact_leaf) in enumerate(zip(bundle['entries'], intact)):
                    if intact_leaf: continue
                    branch = dict(entry['path_assignment'])
                    if any(v in fixed and fixed[v] != bit for v, bit in branch.items()): continue
                    candidate_missing.append(dict(leaf=i, **residual_work({**fixed, **branch})))
                current_missing = [dict(leaf=e['leaf'], **residual_work(dict(e['context'])))
                    for e in current['leaves'] if e['route'] == 'native']
                findings.append(dict(origin_query=origin_index, target_query=target_index,
                    origin_case=origin_case, target_case=target_case, guard=origin['assignment'],
                    origin_root=origin['root'], target_root=target['root'], bundle=bundle,
                    intact=intact, candidate_missing_residuals=candidate_missing, current_missing_residuals=current_missing, extraction_seconds=seconds, extraction_counts=counts,
                    native_counts=native_counts, check_counts=dict(c),
                    current_intact=current['intact'], current_leaves=current['leaves'],
                    missing=len(intact)-sum(intact), current_missing=len(current['intact'])-sum(current['intact'])))
        finally: solver.close()
    base.write(out / 'origin-followup.json', dict(queries=reference['queries'], cases=p['cases'], findings=findings,
        limitations=['Posthoc bounded extraction from the actual preceding negative recomposition proof, not from a different policy or a future answer. All examined origin queries strictly precede their targets and use the same supplied guard.',
            'The timed policy does not admit these origins. Support survival is not a solved target or a total-cost saving; missing leaves, path checking, admission, discovery, retention and cold replay still need evaluation.',
            'Extraction timings include stateful reader warm-up in diagnostic pair order and are excluded from comparative means. Both extractors agree exactly; no new native record is published.']))


def finalize(out):
    p = base.load(out / 'protocol.json'); v = base.load(out / 'validation.json')
    cp = base.load(out / 'checkpoint.json'); analysis = base.load(out / 'analysis.json')
    assert v['passed'] and v['query_audits'] == 1656 and v['previous_partition_records'] == 342
    assert (len(v['parent_manifests']), v['prior_artifacts_unchanged']) == (149, 13184)
    prior_tables = base.load(study.PARENT / 'validation.json')['preserved_tables']
    for table, size in prior_tables.items():
        assert v['preserved_tables'][table] == size + v['new_records'].get(table, 0)
    for path, entry in v['parent_manifests'].items():
        assert base.sha(path) == entry['sha256']
        for f, h in base.load(path)['artifacts'].items(): assert base.sha(f) == h, f
    sources = {**v['source_fingerprints'],
        'experiments/profile_cnf_leaf_handoff.py': base.sha('experiments/profile_cnf_leaf_handoff.py'),
        'experiments/finalize_cnf_leaf_handoff.py': base.sha(__file__)}
    assert len(sources) == 851
    for f, h in sources.items(): assert base.sha(f) == h, f
    head = '4fcf1ac6'; paper = 'paper/bounded_domain_sat_and_amortized_reasoning.tex'
    before = subprocess.check_output(['git', 'show', head + ':' + paper], text=True)
    pattern = r'\\begin\{proof\}.*?\\end\{proof\}'
    proofs = re.findall(pattern, before, re.S)
    assert len(proofs) == 64 and proofs == re.findall(pattern, Path(paper).read_text(), re.S)
    full, focused = [(out / name).read_text() for name in ('full-tests.log', 'focused-tests.log')]
    assert re.search(r'Ran 1602 tests in .*\n\nOK', full)
    assert re.search(r'Ran 93 tests in .*\n\nOK', focused)
    warnings = {k: len(re.findall('ResourceWarning: unclosed database', text)) for k, text in (('full', full), ('focused', focused))}
    assert warnings['focused'] == 0
    sites = Counter(re.sub(r'0x[0-9a-f]+', 'ADDR', line.lstrip('.')) for line in full.splitlines() if 'ResourceWarning: unclosed database' in line)
    latex = (out / 'latex-final.log').read_text()
    assert not re.search(r'Warning|Overfull|Underfull|^!', latex, re.M)
    pages = int(re.search(r'\((\d+) pages,', latex)[1])
    for binding in [cp['reference_union']] + [b for b in cp['leaf_handoff'].values() if isinstance(b, dict) and 'sha256' in b]:
        assert base.sha(binding['path']) == binding['sha256']
    work = analysis['work']['handoff']
    assert work['partial_attempts'] == 4 and work['partial_native_leaves'] == 5
    assert work['partial_support_leaves'] == 6 and work['learned_cover_hits'] == 2
    faster = 0
    for repeat in range(4):
        reports = {mode: base.load(out / f'{mode}-{repeat}/report.json') for mode in study.MODES}
        faster += reports['handoff']['summary']['preparation_and_queries'] < reports['carried']['summary']['preparation_and_queries']
        assert study.read_zip(reports['carried']['delta']) == study.read_zip(reports['handoff']['delta'])
    assert faster == 2
    assert len(v['extraction_audits']) == 8
    assert not v['new_records']
    assert cp['reference_union'] == study.bound(p['parent'])['reference_union']
    assert work['prepared_partial_leaf_reuses'] == 6 and work['prepared_partial_frame_reuses'] == 1
    profile = base.load(out / 'profiling.json')
    profiled = study.bound(profile['report']); reference = base.load(out / 'handoff-0/report.json')
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
    assert sum(old_calls.values()) == 89 and sum(new_calls.values()) == 84
    assert {k: old_calls[k] - new_calls[k] for k in old_calls} == {(7, 4): 1, (15, 3): 1, (19, 3): 1, (20, 3): 2}
    def restrictions(data):
        return {(q['case'], q['template']): sum(r['calls'] for r in q['functions'] if r['function'] == 'restrict_scan' and r['file'].endswith('cnf_residual_dag.py')) for q in data['queries']}
    old_restrict, new_restrict = restrictions(previous_profile), restrictions(profile)
    assert old_restrict == new_restrict
    assert (new_restrict[(7, 4)], new_restrict[(15, 3)]) == (15, 25)
    assert work['learned_extract_origin_untouched_representatives'] == 2647
    assert work['learned_extract_origin_index_literals'] == 1593
    assert work['learned_extract_origin_scanned_literals'] == 480
    assert work['learned_extract_origin_copied_map_slots'] == 5740
    previous_work = analysis['work']['carried']
    assert work['leaf_handoff_reuses'] == 5
    assert previous_work['normalization_literal_visits'] - work['normalization_literal_visits'] == 3133
    assert previous_work['key_serialized_bytes'] - work['key_serialized_bytes'] == 13573
    origin_followup(out, p, reference)
    diagnostic = base.load(out / 'origin-followup.json')
    assert [(r['missing'], r['current_missing']) for r in diagnostic['findings']] == [(1, 1), (2, 2), (2, 2)]
    assert [r['literals'] for r in diagnostic['findings'][1]['candidate_missing_residuals']] == [683, 673]
    assert [r['literals'] for r in diagnostic['findings'][1]['current_missing_residuals']] == [693, 673]
    for i in (0, 2):
        row = diagnostic['findings'][i]
        assert [r['source_sha256'] for r in row['candidate_missing_residuals']] == [r['source_sha256'] for r in row['current_missing_residuals']]
    rows = study.bound(reference['queries'])
    frontier = dict(protocol=study.binding(out / 'protocol.json'), prefix=p['prefix'],
        query_log=reference['queries'], hints=reference['hints'], profile=study.binding(out / 'profiling.json'),
        normalization_calls={str(k): v for k, v in new_calls.items()},
        restriction_calls=dict(before={str(k): v for k, v in old_restrict.items()}, after={str(k): v for k, v in new_restrict.items()}),
        origin_followup=study.binding(out / 'origin-followup.json'),
        cases=[c for c in study.bound(p['cases']) if c['index'] in {x[0] for x in targets}],
        partial_queries=[dict(query_index=i, **r) for i, r in enumerate(rows) if r.get('partial')],
        costs=[r for r in analysis['queries'] if (r['case'], r['template']) in targets],
        next_question='Can an earlier recomposed proof contribute a finer surviving subbranch inside a failed support? Case 15 to 20 retains an extra split but still has two missing leaves; one residual shrinks only 693 to 683 literals. Test bounded causal admission and total avoided native work before promoting it. Case 19 to 20 does not improve the missing residuals; preserve that counterexample.',
        limitations=['The timed stream still registers no origins from recomposed outcomes; the prospective diagnostic is not a measured online policy. All three origin alternatives preserve missing-leaf counts; newly recomposed case 19 supplies no smaller missing residual to case 20.',
            'Diagnostic profiles preserve proof bytes and routes but add overhead; cumulative times overlap.',
            'Five fewer normalizations save deterministic work, but preparation/query mean regresses 2.29% and complete-worker mean 2.58%, each with two wins and two losses. Keep optional.',
            'Recent construction pilots have not established a durable total-cost gain. The specific finer-subbranch hypothesis is small and unproven; do not replace it with blanket new-origin admission or another generic normalization cache.',
            'No production default, proof format, formal Lean refinement, automatic guard correspondence or unrestricted bound changes.'])
    base.write(out / 'next-target.json', frontier)
    cp['source_fingerprints'] = sources
    cp['leaf_handoff']['next_target'] = study.binding(out / 'next-target.json')
    cp['leaf_handoff']['profile'] = study.binding(out / 'profiling.json')
    base.write(out / 'checkpoint.json', cp)
    v.update(source_fingerprints=sources, checkpoint=study.binding(out / 'checkpoint.json'))
    base.write(out / 'validation.json', v)
    checks = dict(passed=True, baseline_commit=head, prior_sources=845, final_sources=851,
        prior_artifacts=13184, prior_manifests=149, full_tests=1602, focused_tests=93,
        warnings=warnings, warning_sites=dict(sites), manuscript_pages=pages, paper_sha256=base.sha(paper),
        proof_blocks_unchanged=64, source_fingerprints=sources, final_union_tables=v['preserved_tables'],
        final_checkpoint=study.binding(out / 'checkpoint.json'),
        limitations=p['limitations'] + analysis['limitations'] + v['limitations'] + frontier['limitations'] + [
            'Identical proof payloads, hints, expansion counts and native checks are preserved. Fewer normalizations do not establish total-cost improvement; selected endpoint object bytes are not a peak-RAM guarantee.',
            'Full-suite SQLite resource warnings remain; focused tests have none. Existing 64 manuscript proofs are unchanged.'])
    base.write(out / 'checks.json', checks)
    files = sorted(f for f in out.rglob('*') if f.is_file() and f.name != 'manifest.json')
    base.write(out / 'manifest.json', dict(artifacts={str(f): base.sha(f) for f in files}))
    print(base.encode(dict(passed=True, artifacts=len(files), next_artifacts=13184+len(files),
        next_manifests=150, sources=851, pages=pages, warnings=warnings, tables=v['preserved_tables'])), flush=True)


if __name__ == '__main__': finalize(Path(sys.argv[1]))
