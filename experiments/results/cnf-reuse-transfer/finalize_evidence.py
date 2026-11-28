"""Bind verified external-transfer results, lineage and reviewed manuscript."""
from pathlib import Path
import gzip, re, subprocess, sys
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from experiments import compare_cnf_reuse_transfer as s
out=Path('experiments/results/cnf-reuse-transfer')
p=s.load(out/'protocol.json'); v=s.load(out/'validation.json'); a=s.load(out/'analysis.json')
assert v['passed'] and len(a['outcomes'])==16 and len(a['survival'])==16
for file,h in p['source_fingerprints'].items(): assert s.sha(file)==h,file
sem=s.load(out/'semantic-audit.json')
assert sem['passed'] and sem==s.load(out/'semantic-audit-reproduced.json')==s.load(out/'preflight-semantic-audit.json')
assert sem['counts']['checked_outcomes']==15520 and sem['counts']['targets']==7760
for mode in s.POLICIES: assert s.load(out/('replay-'+mode+'.json'))['passed']
for name,count in [('full-tests.log',2697),('focused-tests.log',8)]:
    assert re.search(r'Ran '+str(count)+r' tests in .*\n\nOK',(out/name).read_text()),name
paper='paper/bounded_domain_sat_and_amortized_reasoning.tex'
old=subprocess.check_output(['git','show','628bb9fb:'+paper],text=True)
pattern=r'\\begin\{proof\}.*?\\end\{proof\}'
proofs=re.findall(pattern,old,re.S)
assert len(proofs)==92 and proofs==re.findall(pattern,Path(paper).read_text(),re.S)
for name in ('latex-reviewed.log','latex-final.log'):
    assert not re.search(r'Warning|Overfull|Underfull|^!',(out/name).read_text(),re.M),name
pages=int(sys.argv[1]); inspected=list(map(int,sys.argv[2:]))
s.write(out/'supplemental-checks.json',dict(passed=True,full_tests=2697,focused_tests=8,
    old_proofs_unchanged=92,added_proofs=0,semantic_audit=s.binding(out/'semantic-audit.json'),
    independent_outcome_checks=15520,independent_edited_targets=7760,
    fresh_worker_replays={m:s.binding(out/('replay-'+m+'.json')) for m in s.POLICIES},
    target_overlaps=s.binding(out/'target-overlaps.json'),manuscript_pages=pages,
    visually_inspected_pages=inspected,clean_final_latex_passes=2))
documents=['research/frozen-external-reuse-transfer.md','research/sat-pattern-discovery.md',
    'research/structural-reuse-priorities.md','research/implementation-gaps.md',paper]
s.write(out/'decision.json',dict(decision='Retain unfiltered finite external-parent transfer evidence with parent acquisition charged, all fresh-only/reuse-only/unknown cases and independent target certificates. Keep original distributions and selection limits explicit; no production-default or complexity change.',
    coverage=a['coverage'],strata=a['strata'],union_counts=a['union_counts'],reuse_only=a['reuse_only'],fresh_only=a['fresh_only'],
    documents={f:s.sha(f) for f in documents},supplemental_checks=s.binding(out/'supplemental-checks.json'),
    limitations=p['limitations'],next_target='Diagnose fresh/reuse coverage differences and proof cost; develop and separately test compact supports or a justified dispatch/admission policy, preserving structural-recognition and unrestricted-expansion obligations.'))
cp=s.load(out/'checkpoint.json');cp['reuse_transfer']['decision']=s.binding(out/'decision.json')
s.write(out/'checkpoint.json',cp);v['checkpoint']=s.binding(out/'checkpoint.json');s.write(out/'validation.json',v)
s.write(out/'checks.json',dict(passed=True,full_tests=2697,focused_tests=8,old_proof_blocks_unchanged=92,
    added_proof_blocks=0,prior_sources=1381,final_sources=1384,prior_manifests=254,prior_artifacts=84935,
    checkpoint=s.binding(out/'checkpoint.json')))
for file in out.rglob('*.log'):
    raw=file.read_bytes();archive=Path(str(file)+'.raw.gz')
    if not archive.exists():archive.write_bytes(gzip.compress(raw,mtime=0))
    normalized='\n'.join(line.rstrip() for line in raw.decode().splitlines()).rstrip()
    file.write_text(normalized+'\n' if normalized else '')
files=sorted(f for f in out.rglob('*') if f.is_file() and f.name!='manifest.json' and '__pycache__' not in f.parts)
s.write(out/'manifest.json',dict(artifacts={str(f):s.sha(f) for f in files}))
print(s.encode(dict(sealed=True,artifacts=len(files),next_manifests=255,next_artifacts=84935+len(files))))
