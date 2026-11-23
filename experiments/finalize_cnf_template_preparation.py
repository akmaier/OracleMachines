#!/usr/bin/env python3
"""Seal the construction result and the next conditional-support experiment."""
from collections import Counter
from copy import deepcopy
from pathlib import Path
import re, subprocess, sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_template_preparation as study
base = study.base


def finalize(out):
    p = base.load(out / 'protocol.json')
    v = base.load(out / 'validation.json')
    cp = base.load(out / 'checkpoint.json')
    assert v['passed'] and v['query_audits'] == 1026 and v['new_records'] == 0
    assert v['previous_partition_records'] == 342
    assert (len(v['parent_manifests']), v['prior_artifacts_unchanged']) == (143, 12684)
    for path, entry in v['parent_manifests'].items():
        assert base.sha(path) == entry['sha256']
        for f, h in base.load(path)['artifacts'].items():
            assert base.sha(f) == h, f
    sources = {**v['source_fingerprints'], __file__.removeprefix(str(Path.cwd()) + '/'): base.sha(__file__)}
    assert len(sources) == 816
    for f, h in sources.items():
        assert base.sha(f) == h, f
    head = '207f9578'
    paper = 'paper/bounded_domain_sat_and_amortized_reasoning.tex'
    before = subprocess.check_output(['git', 'show', head + ':' + paper], text=True)
    pattern = r'\\begin\{proof\}.*?\\end\{proof\}'
    proofs = re.findall(pattern, before, re.S)
    assert len(proofs) == 64 and proofs == re.findall(pattern, Path(paper).read_text(), re.S)
    full, focused = [(out / name).read_text() for name in ('full-tests.log', 'focused-tests.log')]
    assert re.search(r'Ran 1539 tests in .*\n\nOK', full)
    assert re.search(r'Ran 31 tests in .*\n\nOK', focused)
    warnings = {k: len(re.findall('ResourceWarning: unclosed database', text))
                for k, text in (('full', full), ('focused', focused))}
    assert warnings['focused'] == 0
    sites = Counter(re.sub(r'0x[0-9a-f]+', 'ADDR', line.lstrip('.')) for line in full.splitlines()
                    if 'ResourceWarning: unclosed database' in line)
    latex = (out / 'latex-final.log').read_text()
    assert not re.search(r'Warning|Overfull|Underfull|^!', latex, re.M)
    pages = int(re.search(r'\((\d+) pages,', latex)[1])
    assert cp['reference_union'] == v['archive_reused'] == study.bound(p['parent'])['reference_union']
    assert base.sha(cp['reference_union']['path']) == cp['reference_union']['sha256']
    for binding in cp['template_preparation'].values():
        if isinstance(binding, dict) and 'sha256' in binding:
            study.bound(binding)
    analysis = base.load(out / 'analysis.json')
    assert analysis['identical_proof_bytes'] and analysis['identical_chronology']
    assert analysis['work']['repeated']['templates_checked'] == 173
    assert analysis['work']['shared']['templates_checked'] == 102
    assert analysis['work']['shared']['verified_nodes'] == analysis['work']['repeated']['verified_nodes'] == 164
    report = base.load(out / 'report.json')
    for sample in report['samples']:
        data = study.bound(sample)
        for field in ('queries', 'hints', 'delta', 'preparation_delta'):
            assert base.sha(data[field]['path']) == data[field]['sha256']

    # Bind a resumable, chronological frontier, without seeding any target answer.
    selected = {(4, 3), (4, 4), (15, 3), (16, 3), (16, 4)}
    control = (7, 4)
    rows = [base.load(out / f'shared-{i}/queries.json') for i in range(4)]
    cases = study.bound(p['cases'])
    available = {t: [k for k, _ in study.read_zip(base.load(out / 'shared-0/report.json')['preparation_delta'])[t]]
                 for t in study.TABLES}
    targets = []
    for index, row in enumerate(rows[0]):
        coordinate = (row['case'], row['template'])
        if coordinate in selected or coordinate == control:
            assert row['route'] == 'native'
            assert row['status'] == ('sat' if coordinate == control else 'unsat')
            targets.append(dict(case=row['case'], template=row['template'],
                                role='positive-control' if coordinate == control else 'candidate',
                                source=cases[row['case']]['source'], assignment=row['assignment'],
                                root=row['root'], expanded_nodes=row['expanded_nodes'],
                                prior_delta_ids=deepcopy(available),
                                query_mean_seconds=sum(rs[index]['seconds'] for rs in rows) / 4,
                                observed_new_ids=row['new_ids']))
        for table, ids in row['new_ids'].items():
            available[table].extend(ids)
    native_seconds = analysis['routes']['shared']['native']['mean_seconds']
    target_seconds = sum(t['query_mean_seconds'] for t in targets if t['role'] == 'candidate')
    frontier = dict(protocol=study.binding(out / 'protocol.json'), prefix=p['prefix'],
                    preparation_delta=base.load(out / 'shared-0/report.json')['preparation_delta'],
                    chronological_delta=base.load(out / 'shared-0/report.json')['delta'],
                    query_log=study.binding(out / 'shared-0/queries.json'),
                    targets=targets, native_seconds=native_seconds, candidate_seconds=target_seconds,
                    fraction_of_native_time=target_seconds / native_seconds,
                    candidate_expansions=sum(t['expanded_nodes'] for t in targets if t['role'] == 'candidate'),
                    next_question='Do source-bound conditional supports learned on case 4 survive cases 15/16 and improve on the existing negative pool, with all branch guards and maps retained?',
                    limitations=['Observed target answers and later additions are diagnostic only. Restore the historical prefix plus listed prior IDs, never the complete union, for chronological transfer tests.',
                                 'Guard selection and correspondence remain supplied. No transfer gain is established by this cost ranking. Retain positive control case 7/guard 4.'])
    assert len(targets) == 6 and frontier['candidate_expansions'] == 22
    base.write(out / 'next-target.json', frontier)
    cp['source_fingerprints'] = sources
    cp['template_preparation']['next_target'] = study.binding(out / 'next-target.json')
    base.write(out / 'checkpoint.json', cp)
    v.update(source_fingerprints=sources, checkpoint=study.binding(out / 'checkpoint.json'))
    base.write(out / 'validation.json', v)
    checks = dict(passed=True, baseline_commit=head, prior_sources=810, final_sources=816,
                  prior_artifacts=12684, prior_manifests=143, full_tests=1539, focused_tests=31,
                  warnings=warnings, warning_sites=dict(sites), manuscript_pages=pages,
                  paper_sha256=base.sha(paper), proof_blocks_unchanged=64,
                  source_fingerprints=sources, final_union_tables=v['preserved_tables'],
                  final_checkpoint=study.binding(out / 'checkpoint.json'),
                  limitations=p['limitations'] + analysis['limitations'] + v['limitations'] + [
                      'Full-suite unclosed SQLite warnings are preserved; reported collection sites need not be allocation sites. Focused tests have no warnings.',
                      'Matched construction saving with unchanged proofs. Four pairs do not establish general performance or an end-to-end gain. No new Lean theorem.'])
    base.write(out / 'checks.json', checks)
    files = sorted(f for f in out.rglob('*') if f.is_file() and f.name != 'manifest.json')
    base.write(out / 'manifest.json', dict(artifacts={str(f): base.sha(f) for f in files}))
    print(base.encode(dict(passed=True, artifacts=len(files), next_artifacts=12684 + len(files),
                          next_manifests=144, sources=816, pages=pages, warnings=warnings,
                          candidate_fraction=frontier['fraction_of_native_time'])), flush=True)


if __name__ == '__main__':
    finalize(Path(sys.argv[1]))
