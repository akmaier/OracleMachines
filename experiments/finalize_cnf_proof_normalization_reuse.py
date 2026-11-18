#!/usr/bin/env python3
"""Seal targeted normalization reuse, exact proof checks and preserved histories."""
from pathlib import Path
from collections import Counter
import re,subprocess,sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_proof_normalization_reuse as study
base=study.base
POSTHOC=('experiments/validate_cnf_proof_normalization_reuse.py','experiments/profile_cnf_proof_normalization_reuse.py','experiments/finalize_cnf_proof_normalization_reuse.py')


def finalize(out):
    p=base.load(out/'protocol.json');parent=study.bound(p['parent']);v=base.load(out/'validation.json')
    for ledger in (parent['source_fingerprints'],p['source_fingerprints']):
        for f,h in ledger.items():assert base.sha(f)==h,f
    assert len(parent['source_fingerprints'])==625
    for path,entry in v['parent_manifests'].items():
        assert base.sha(path)==entry['sha256'];artifacts=base.load(path)['artifacts'];assert len(artifacts)==entry['artifacts_checked']
        for f,h in artifacts.items():assert base.sha(f)==h,f
    assert len(v['parent_manifests'])==116 and v['prior_artifacts_unchanged']==7947
    sources=dict(p['source_fingerprints']);sources.update({f:base.sha(f) for f in POSTHOC});assert len(sources)==632
    checkpoint=base.load(out/'checkpoint.json');assert checkpoint['reference_union']==parent['reference_union']
    checkpoint['source_fingerprints']=sources;base.write(out/'checkpoint.json',checkpoint)
    v['source_fingerprints']=sources;v['checkpoint']=study.binding(out/'checkpoint.json');base.write(out/'validation.json',v)
    assert sorted(v['preserved_tables'].values())==[22,26,34,42,53,28886]
    assert v['reference_union_unchanged'] and v['new_native']==v['new_extensions']==0
    assert (v['query_audits'],v['truth_tables'],v['choice_audits'],v['known_hit_audits'],v['exact_query_comparisons'])==(624,104,144,84,416)
    assert (v['old_composed_records'],v['old_pilot_records'])==(5650,444)
    assert (v['canonical_fixedpoints'],v['representation_mutations'])==(28886,4961)
    assert len(v['committed_prefix_audits'])==104
    summaries=base.load(out/'report.json')['summary'];a=summaries['batch32'];b=summaries['memo128'];single=summaries['memo32']
    for arm in (b,single):
        for k in ('native_digest','extension_digest','database_bytes','compressed_bytes','native_payload','extension_payload','cache_digest'):
            assert arm[k]==a[k]
        assert arm['sqlite_settings']==a['sqlite_settings']==dict(journal_mode='delete',synchronous=2)
        assert arm['counters']['batch_committed_records']==605 and arm['counters']['batch_committed_payload']==651784
        assert arm['batch_peak_records']<=arm['batch_rows'] and arm['batch_peak_payload']<=arm['batch_payload_limit']
    assert single['counters']['batch_commits']==104 and b['counters']['batch_commits']==104
    assert (b['batch_peak_records'],b['batch_peak_payload'],b['batch_peak_python_bytes'])==(27,39747,17086)
    for arm,hits,units in ((b,262,25478),(single,178,14546)):
        assert arm['counters']['proof_memo_hits']==hits
        assert a['counters']['normalization_literal_visits']==arm['counters']['normalization_literal_visits']+units
        assert arm['proof_memo_peak_bytes']<=arm['proof_memo_capacity']
    diagnosis=base.load(out/'diagnosis.json')
    assert diagnosis['outputs_counters_and_payloads_identical'] and diagnosis['queries']==104
    assert diagnosis['source']['sha256']==sources['experiments/inspect_cnf_residual_normalization.py']
    assert diagnosis['sites']['_negative_child']['exact_repeats']==311
    assert diagnosis['repeat_edges']['_visit -> _negative_child']==270
    assert diagnosis['sites']['_visit']['ordered_clean_calls']==501
    profile=base.load(out/'profile.json')
    assert all(p['outputs_and_counters_identical'] for p in profile['profiles'].values())
    assert profile['profile_source']['sha256']==sources['experiments/profile_cnf_proof_normalization_reuse.py']
    for mode in ('memo128','memo32'):
        observed=profile['memory_observations'][mode]
        assert observed['admission_checks']==546
        assert observed['peak_actual_object_bytes']<=observed['peak_charged_bytes']==summaries[mode]['proof_memo_peak_bytes']
    paper='paper/bounded_domain_sat_and_amortized_reasoning.tex';commit=subprocess.check_output(['git','rev-parse','fbd9b04'],text=True).strip()
    old=subprocess.check_output(['git','show',commit+':'+paper],text=True);pattern=r'\\begin\{proof\}.*?\\end\{proof\}'
    proofs=re.findall(pattern,old,re.S);assert len(proofs)==64 and proofs==re.findall(pattern,Path(paper).read_text(),re.S)
    logs={name:(out/name).read_text() for name in ('full-tests.log','focused-tests.log','latex-final.log')}
    assert re.search(r'Ran 1292 tests in .*\n\nOK',logs['full-tests.log'])
    assert re.search(r'Ran 123 tests in .*\n\nOK',logs['focused-tests.log'])
    warnings={k:len(re.findall('ResourceWarning: unclosed database',x)) for k,x in logs.items() if k!='latex-final.log'}
    assert warnings=={'full-tests.log':44,'focused-tests.log':0}
    def warning_sites(text):
        return Counter(re.sub(r'0x[0-9a-f]+','ADDR',line.lstrip('.')) for line in text.splitlines() if 'ResourceWarning: unclosed database' in line)
    current_warning_sites=warning_sites(logs['full-tests.log'])
    parent_warning_sites=warning_sites((study.PARENT/'full-tests.log').read_text())
    # ResourceWarnings are emitted where GC happens, not necessarily where a
    # connection was created. Preserve the changed distribution instead of
    # pretending the parent's exact counts/sites are reproduced.
    repo=str(Path.cwd())+'/'
    for site in current_warning_sites:
        filename=site.split(':',1)[0]
        if filename.startswith(repo):assert filename[len(repo):] in parent['source_fingerprints']
        else:assert any(old.split(':',1)[0]==filename for old in parent_warning_sites)
    warning_delta=dict(added=dict(current_warning_sites-parent_warning_sites),removed=dict(parent_warning_sites-current_warning_sites))

    latex=logs['latex-final.log'];pages=int(re.search(r'\((\d+) pages,',latex)[1]);assert not re.search(r'Warning|Overfull|Underfull|^!',latex,re.M)
    checks=dict(passed=True,baseline_commit=commit,prior_sources=625,final_sources=len(sources),prior_artifacts=7947,prior_manifests=116,
        source_fingerprints=sources,full_tests=1292,focused_tests=123,warnings=warnings,warning_sites=dict(current_warning_sites),warning_emission_files_preexisting=True,warning_distribution_delta=warning_delta,proof_blocks_unchanged=64,manuscript_pages=pages,paper_sha256=base.sha(paper),
        limitations=['All 104 inputs replay the preceding study; two run orders do not establish representative arbitrary-SAT performance.',
            '128-KiB query deltas improve in both orders, but complete deltas are mixed. 32-KiB query and complete deltas are mixed. Keep all regressions; no robust end-to-end speedup claim.',
            'Warm queries have no memo producers or consumers and cold readers/archives are identical; their timing variations are not reuse benefits.',
            'Memo charges bound retained objects after operations, excluding transient allocations, allocator overhead and full-solver memory. Persistent storage is unchanged.',
            'Producers normalize, copy and size their inputs; consumer hits still validate and hash raw literals, then perform the original key and checked-UNSAT tests.',
            'The full suite emits 44 unclosed-SQLite ResourceWarnings versus 43 in the parent, at unchanged source/stdlib files; the GC emission distribution changes. Focused tests emit none. This checkpoint does not fix that existing suite issue.',
            'No new persisted mathematical answers, production-default change, Lean theorem or unrestricted-SAT resource bound.'])
    base.write(out/'checks.json',checks)
    files=sorted(f for f in out.rglob('*') if f.is_file() and f.name!='manifest.json')
    base.write(out/'manifest.json',dict(artifacts={str(f):base.sha(f) for f in files}))
    print(base.encode(dict(passed=True,artifacts=len(files),next_artifacts=7947+len(files),next_manifests=117,final_sources=len(sources),pages=pages)),flush=True)


if __name__=='__main__':finalize(Path(sys.argv[1]))
