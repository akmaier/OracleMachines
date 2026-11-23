#!/usr/bin/env python3
"""Seal exact conditional transfers, their regressions and the unit-gate target."""
from collections import Counter
from pathlib import Path
import json, re, subprocess, sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_learned_conditional as study
base = study.base


def finalize(out):
    p = base.load(out / 'protocol.json'); v = base.load(out / 'validation.json')
    cp = base.load(out / 'checkpoint.json'); analysis = base.load(out / 'analysis.json')
    assert v['passed'] and v['query_audits'] == 912 and v['previous_partition_records'] == 342
    assert v['new_records'] == {'cnf_residual_v1': 12}
    assert (len(v['parent_manifests']), v['prior_artifacts_unchanged']) == (144, 12751)
    for path, entry in v['parent_manifests'].items():
        assert base.sha(path) == entry['sha256']
        for f, h in base.load(path)['artifacts'].items(): assert base.sha(f) == h, f
    sources = {**v['source_fingerprints'], __file__.removeprefix(str(Path.cwd()) + '/'): base.sha(__file__)}
    assert len(sources) == 822
    for f, h in sources.items(): assert base.sha(f) == h, f
    head = '1d59c585'; paper = 'paper/bounded_domain_sat_and_amortized_reasoning.tex'
    before = subprocess.check_output(['git', 'show', head + ':' + paper], text=True)
    pattern = r'\\begin\{proof\}.*?\\end\{proof\}'
    proofs = re.findall(pattern, before, re.S)
    assert len(proofs) == 64 and proofs == re.findall(pattern, Path(paper).read_text(), re.S)
    full, focused = [(out / name).read_text() for name in ('full-tests.log', 'focused-tests.log')]
    assert re.search(r'Ran 1550 tests in .*\n\nOK', full)
    assert re.search(r'Ran 42 tests in .*\n\nOK', focused)
    warnings = {k: len(re.findall('ResourceWarning: unclosed database', text)) for k, text in (('full', full), ('focused', focused))}
    assert warnings['focused'] == 0
    sites = Counter(re.sub(r'0x[0-9a-f]+', 'ADDR', line.lstrip('.')) for line in full.splitlines() if 'ResourceWarning: unclosed database' in line)
    latex = (out / 'latex-final.log').read_text()
    assert not re.search(r'Warning|Overfull|Underfull|^!', latex, re.M)
    pages = int(re.search(r'\((\d+) pages,', latex)[1])
    for binding in [cp['reference_union']] + [b for b in cp['learned_conditional'].values() if isinstance(b, dict) and 'sha256' in b]:
        assert base.sha(binding['path']) == binding['sha256']
    assert analysis['work']['baseline']['expanded_nodes'] == 43
    assert analysis['work']['learned']['expanded_nodes'] == 33
    assert analysis['work']['learned']['learned_cover_hits'] == 3
    report = base.load(out / 'report.json')
    for repeat in range(4):
        old = base.load(out / f'baseline-{repeat}/report.json')['summary']
        new = base.load(out / f'learned-{repeat}/report.json')['summary']
        assert new['preparation_and_queries'] > old['preparation_and_queries']
    selected = {(6, 3), (7, 4), (9, 5), (16, 3), (16, 4)}
    cases = study.bound(p['cases'])
    comparisons = [r for r in analysis['queries'] if (r['case'], r['template']) in selected]
    targets = [dict(**r, source=cases[r['case']]['source']) for r in comparisons]
    baseline = base.load(out / 'baseline-0/report.json'); learned = base.load(out / 'learned-0/report.json')
    oldrows, rows = study.bound(baseline['queries']), study.bound(learned['queries'])
    index = next(i for i, r in enumerate(rows) if (r['case'], r['template']) == (6, 3))
    key = rows[index]['root']; assert key == oldrows[index]['root']
    before_proof = json.loads(dict(study.read_zip(baseline['delta'])['cnf_residual_v1'])[key])['proof']
    after_proof = json.loads(dict(study.read_zip(learned['delta'])['cnf_residual_v1'])[key])['proof']
    assert before_proof['kind'] == 'units' and before_proof.get('conflict') is not None
    assert after_proof['kind'] == 'split'
    frontier = dict(protocol=study.binding(out / 'protocol.json'), prefix=p['prefix'],
        prior_query_count=index, query_log=learned['queries'], preparation_delta=learned['preparation_delta'],
        targets=targets, cheap_baseline_proof=before_proof, larger_cover_proof=after_proof,
        next_question='Can a checked full-target unit gate avoid unnecessary cover work while sharing its prefix with fallback and charging every failed screen?',
        limitations=['Replay only queries preceding the selected target to rebuild solver pools and the deferred bank. Final hints and the union include later knowledge and cannot seed a chronological comparison.',
            'The actual unit-gate improvement is not implemented or measured here. Case 7/guard 4 is SAT and must remain a miss/control. Cases 16/guards 3 and 4 retain useful later transfers.'])
    base.write(out / 'next-target.json', frontier)
    cp['source_fingerprints'] = sources
    cp['learned_conditional']['next_target'] = study.binding(out / 'next-target.json')
    base.write(out / 'checkpoint.json', cp)
    v.update(source_fingerprints=sources, checkpoint=study.binding(out / 'checkpoint.json'))
    base.write(out / 'validation.json', v)
    checks = dict(passed=True, baseline_commit=head, prior_sources=816, final_sources=822,
        prior_artifacts=12751, prior_manifests=144, full_tests=1550, focused_tests=42,
        warnings=warnings, warning_sites=dict(sites), manuscript_pages=pages, paper_sha256=base.sha(paper),
        proof_blocks_unchanged=64, source_fingerprints=sources, final_union_tables=v['preserved_tables'],
        final_checkpoint=study.binding(out / 'checkpoint.json'),
        limitations=p['limitations'] + analysis['limitations'] + v['limitations'] + [
            'Three exact chronological cover transfers do not improve overall query time or retained memory. The route stays experimental; all regressions are retained.',
            'Full-suite SQLite resource warnings remain; focused tests have none. No new Lean refinement theorem.'])
    base.write(out / 'checks.json', checks)
    files = sorted(f for f in out.rglob('*') if f.is_file() and f.name != 'manifest.json')
    base.write(out / 'manifest.json', dict(artifacts={str(f): base.sha(f) for f in files}))
    print(base.encode(dict(passed=True, artifacts=len(files), next_artifacts=12751+len(files),
                          next_manifests=145, sources=822, pages=pages, warnings=warnings,
                          tables=v['preserved_tables'])), flush=True)


if __name__ == '__main__': finalize(Path(sys.argv[1]))
