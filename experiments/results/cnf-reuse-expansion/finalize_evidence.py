"""Bind verified measurements, tests and manuscript to the next checkpoint."""
from pathlib import Path
import gzip, re, subprocess, sys
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from experiments import compare_cnf_reuse_expansion as s

out = Path(__file__).resolve().parent
root = out.parents[2]
out = out.relative_to(root)
p = s.load(out / 'protocol.json'); v = s.load(out / 'validation.json'); a = s.load(out / 'analysis.json')
assert v['passed'] and a['baseline_matches_parent'] and a['increasing_budget_preserves_derivation_prefix']
assert a['coverage']['reuse2000'] == {'unresolved': 13, 'unsat': 3}
for file, h in p['source_fingerprints'].items(): assert s.sha(file) == h, file
audit = s.load(out / 'semantic-audit.json'); assert audit['passed'] and audit == s.load(out / 'semantic-audit-reproduced.json')
assert audit['counts']['checked_outcomes'] == 47328 and audit['counts']['edited_targets'] == 7888
census = s.load(out / 'support-census.json'); assert census['passed'] and len(census['records']) == 16
for mode in s.POLICIES: assert s.load(out / ('replay-' + mode + '.json'))['passed']
for name, count in [('full-tests.log', 2689), ('focused-tests.log', 10)]:
    assert re.search(r'Ran ' + str(count) + r' tests in .*\n\nOK', (out / name).read_text())
paper = 'paper/bounded_domain_sat_and_amortized_reasoning.tex'
old = subprocess.check_output(['git', 'show', 'ef6722d1:' + paper], text=True)
pattern = r'\\begin\{proof\}.*?\\end\{proof\}'
proofs = re.findall(pattern, old, re.S)
assert len(proofs) == 92 and proofs == re.findall(pattern, Path(paper).read_text(), re.S)
for name in ('latex-reviewed.log', 'latex-final.log'):
    text = (out / name).read_text(); assert not re.search(r'Warning|Overfull|Underfull|^!', text, re.M)
pages = int(sys.argv[1]); inspected = list(map(int, sys.argv[2:]))
supplemental = dict(passed=True, full_tests=2689, focused_tests=10, old_proofs_unchanged=92, added_proofs=0,
    semantic_audit=s.binding(out / 'semantic-audit.json'), independent_outcome_checks=47328,
    independent_edited_targets=7888, budget_prefix_checks=31552,
    fresh_worker_replays={m: s.binding(out / ('replay-' + m + '.json')) for m in s.POLICIES},
    baseline_matches_parent=True, complete_derivation_prefixes_preserved=True,
    support_census=s.binding(out / 'support-census.json'),
    manuscript_pages=pages, visually_inspected_pages=inspected, clean_final_latex_passes=2,
    initial_reproduction_directory_error_preserved=True,
    validation_note='A first semantic reproduction finished its assertions but could not write into a missing output directory. The error is retained; creating that directory was the only correction. No frozen scientific source or policy changed.')
s.write(out / 'supplemental-checks.json', supplemental)
documents = ['research/reuse-expansion-budget.md', 'research/sat-pattern-discovery.md',
    'research/structural-reuse-priorities.md', 'research/implementation-gaps.md', paper]
s.write(out / 'decision.json', dict(decision='Retain the fixed-budget coverage and cost comparison, including fresh-search ablation, unknown targets and complete checked proof prefixes. Preserve old coverage separately; no production defaults or general complexity claim.',
    coverage=a['coverage'], union_counts=a['union_counts'], gains_over_reuse2000=a['gains_over_reuse2000'],
    documents={f: s.sha(f) for f in documents}, supplemental_checks=s.binding(out / 'supplemental-checks.json'),
    limitations=p['limitations'], next_target='Fresh frozen external transfer and alternative premise supports; diagnose the seven fresh-search misses and the wide recorded proof supports to choose compact interaction or proof-retention investigations.'))
cp = s.load(out / 'checkpoint.json'); cp['reuse_expansion']['decision'] = s.binding(out / 'decision.json')
s.write(out / 'checkpoint.json', cp); v['checkpoint'] = s.binding(out / 'checkpoint.json'); s.write(out / 'validation.json', v)
s.write(out / 'checks.json', dict(passed=True, full_tests=2689, focused_tests=10, old_proof_blocks_unchanged=92,
    added_proof_blocks=0, prior_sources=1377, final_sources=1381, prior_manifests=253,
    prior_artifacts=84766, checkpoint=s.binding(out / 'checkpoint.json')))
for file in out.rglob('*.log'):
    raw = file.read_bytes(); archive = Path(str(file) + '.raw.gz')
    if not archive.exists(): archive.write_bytes(gzip.compress(raw, mtime=0))
    normalized = '\n'.join(line.rstrip() for line in raw.decode().splitlines()).rstrip()
    file.write_text(normalized + '\n' if normalized else '')
files = sorted(f for f in out.rglob('*') if f.is_file() and f.name != 'manifest.json' and '__pycache__' not in f.parts)
s.write(out / 'manifest.json', dict(artifacts={str(f): s.sha(f) for f in files}))
print(s.encode(dict(sealed=True, artifacts=len(files), next_manifests=254, next_artifacts=84766 + len(files))))
