#!/usr/bin/env python3
"""Seal the frozen larger stream, its preserved failures and separate witness recovery."""
from pathlib import Path
from collections import Counter
import re,subprocess,sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_larger_mixtures as study
base=study.base
POSTHOC=('experiments/validate_cnf_larger_mixtures.py','experiments/profile_cnf_larger_mixtures.py',
         'experiments/cnf_checked_model_reuse.py','experiments/resume_cnf_larger_mixtures.py',
         'solver/test_cnf_checked_model_reuse.py','experiments/finalize_cnf_larger_mixtures.py')


def finalize(out):
    p=base.load(out/'protocol.json');parent=study.bound(p['parent']);v=base.load(out/'validation.json');recovery=base.load(out/'recovery.json')
    assert len(parent['source_fingerprints'])==638
    for ledger in (parent['source_fingerprints'],p['source_fingerprints'],recovery['source_fingerprints']):
        for f,h in ledger.items():assert base.sha(f)==h,f
    for f,entry in v['parent_manifests'].items():
        assert base.sha(f)==entry['sha256'];items=base.load(f)['artifacts'];assert len(items)==entry['artifacts_checked']
        for path,h in items.items():assert base.sha(path)==h,path
    assert len(v['parent_manifests'])==118 and v['prior_artifacts_unchanged']==8032 and v['passed']
    assert (v['query_audits'],v['exact_comparisons'],v['distinct_roots'],v['known_parent_queries'])==(648,540,72,0)
    assert v['statuses']==dict(sat=70,unsat=36,unresolved=2)
    assert (v['old_composed_records'],v['old_pilot_records'])==(5650,444)
    assert v['new_records']==dict(cnf_residual_v1=2254,cnf_binary_equivalence_v2=0,cnf_binary_equivalence_v3=0)
    assert recovery['final_union_native']==31141 and recovery['new_nodes']==1 and recovery['new_payload']==7895
    assert recovery['result']['status']=='sat' and not recovery['result']['metrics'].get('expanded_nodes',0)
    for checked in recovery['verified'].values():assert checked==dict(nodes=2260,source_roots=dict(sat=48,unsat=24))
    assert recovery['parent_checkpoint']==study.binding(out/'pre-recovery-checkpoint.json')
    # The validator's checkpoint is preserved under its pre-recovery name. Its
    # original hash still matches; point the audit there and bind the final union separately.
    assert v['checkpoint']['sha256']==base.sha(out/'pre-recovery-checkpoint.json')
    v['checkpoint']=study.binding(out/'pre-recovery-checkpoint.json')
    sources=dict(p['source_fingerprints']);sources.update({f:base.sha(f) for f in POSTHOC});assert len(sources)==647
    checkpoint=base.load(out/'checkpoint.json');assert checkpoint['reference_union']==recovery['reference_union']
    checkpoint['source_fingerprints']=sources;base.write(out/'checkpoint.json',checkpoint)
    v['source_fingerprints']=sources;v['final_checkpoint']=study.binding(out/'checkpoint.json');base.write(out/'validation.json',v)
    for archive in (checkpoint['reference_union'],recovery['archive'],base.load(out/'discovery.json')['archive']):assert base.sha(archive['path'])==archive['sha256']
    summaries=base.load(out/'report.json')['summary'];control=summaries['batch32']
    for arm in summaries.values():
        for k in ('native_digest','extension_digest','database_bytes','compressed_bytes','native_payload','extension_payload','statuses','checked_python_bytes'):
            assert arm[k]==control[k]
    assert (control['native_nodes'],control['extension_nodes'],control['native_payload'])==(2259,0,12128848)
    assert (control['database_bytes'],control['checked_python_bytes'])==(22851584,53930391)
    profile=base.load(out/'profile.json');assert profile['source']['sha256']==sources['experiments/profile_cnf_larger_mixtures.py']
    assert all(x['outputs_and_counters_identical'] for x in profile['profiles'].values())
    inventory=base.load(out/'discovery.json');assert inventory['closed_queries']==18 and inventory['verified_nodes']==624
    assert inventory['storage']['nodes']==624 and inventory['storage']['sources']==108
    opportunity=base.load(out/'reuse-opportunities.json');assert (opportunity['eligible'],opportunity['base_sat'])==(21,23)
    paper='paper/bounded_domain_sat_and_amortized_reasoning.tex';commit=subprocess.check_output(['git','rev-parse','a012109'],text=True).strip()
    old=subprocess.check_output(['git','show',commit+':'+paper],text=True);pattern=r'\\begin\{proof\}.*?\\end\{proof\}'
    proofs=re.findall(pattern,old,re.S);assert len(proofs)==64 and proofs==re.findall(pattern,Path(paper).read_text(),re.S)
    full=(out/'full-tests.log').read_text();focused=(out/'focused-tests.log').read_text();latex=(out/'latex-final.log').read_text()
    assert re.search(r'Ran 1311 tests in .*\n\nOK',full) and re.search(r'Ran 142 tests in .*\n\nOK',focused)
    warnings={k:len(re.findall('ResourceWarning: unclosed database',s)) for k,s in (('full',full),('focused',focused))}
    assert warnings==dict(full=44,focused=0)
    def sites(text):return Counter(re.sub(r'0x[0-9a-f]+','ADDR',line.lstrip('.')) for line in text.splitlines() if 'ResourceWarning: unclosed database' in line)
    current=sites(full);previous=sites((study.PARENT/'full-tests.log').read_text());repo=str(Path.cwd())+'/'
    for site in current:
        filename=site.split(':',1)[0]
        if filename.startswith(repo):assert filename[len(repo):] in parent['source_fingerprints']
        else:assert any(old.split(':',1)[0]==filename for old in previous)
    assert not re.search(r'Warning|Overfull|Underfull|^!',latex,re.M);pages=int(re.search(r'\((\d+) pages,',latex)[1])
    checks=dict(passed=True,baseline_commit=commit,prior_sources=638,final_sources=647,prior_artifacts=8032,prior_manifests=118,
        source_fingerprints=sources,full_tests=1311,focused_tests=142,warnings=warnings,warning_sites=dict(current),
        proof_blocks_unchanged=64,manuscript_pages=pages,paper_sha256=base.sha(paper),final_union_native=31141,
        final_checkpoint=study.binding(out/'checkpoint.json'),
        limitations=['Designed larger stream, not representative arbitrary SAT; two run orders and all regressions are preserved.',
        'Two initial budget stops remain unknown at their occurrence. A later repeat and separate supplied-candidate witness recovery complete this finite catalog only.',
        'The expansion cap excludes other work and does not cap stored nodes, runtime or memory. Complete worker RSS includes benchmark state.',
        'Bounded inventory closure is structural recognition, not SAT. All root syntax vectors coincide; only 18/108 family decompositions close.',
        'Related donor selection is supplied. Automatic candidate retrieval, negative proof reuse across edits, and unrestricted resource bounds remain open.',
        'Failed inventory audit omitted default decompose=True from its expected configuration; source/log/union retained. No timed solver run was altered.',
        '44 unclosed-SQLite ResourceWarnings remain at unchanged files; focused tests emit none.'])
    base.write(out/'checks.json',checks)
    files=sorted(f for f in out.rglob('*') if f.is_file() and f.name!='manifest.json')
    base.write(out/'manifest.json',dict(artifacts={str(f):base.sha(f) for f in files}))
    print(base.encode(dict(passed=True,artifacts=len(files),next_artifacts=8032+len(files),next_manifests=119,final_sources=647,pages=pages)),flush=True)


if __name__=='__main__':finalize(Path(sys.argv[1]))
