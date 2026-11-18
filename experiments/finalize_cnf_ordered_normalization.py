#!/usr/bin/env python3
"""Seal checked ordered normalization, exact proof checks and preserved histories."""
from pathlib import Path
from collections import Counter
import re,subprocess,sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_ordered_normalization as study
base=study.base
POSTHOC=('experiments/validate_cnf_ordered_normalization.py','experiments/profile_cnf_ordered_normalization.py','experiments/finalize_cnf_ordered_normalization.py')


def finalize(out):
    p=base.load(out/'protocol.json');parent=study.bound(p['parent']);v=base.load(out/'validation.json')
    for ledger in (parent['source_fingerprints'],p['source_fingerprints']):
        for f,h in ledger.items():assert base.sha(f)==h,f
    assert len(parent['source_fingerprints'])==632
    for path,entry in v['parent_manifests'].items():
        assert base.sha(path)==entry['sha256'];artifacts=base.load(path)['artifacts'];assert len(artifacts)==entry['artifacts_checked']
        for f,h in artifacts.items():assert base.sha(f)==h,f
    assert len(v['parent_manifests'])==117 and v['prior_artifacts_unchanged']==7990
    sources=dict(p['source_fingerprints']);sources.update({f:base.sha(f) for f in POSTHOC});assert len(sources)==638
    checkpoint=base.load(out/'checkpoint.json');assert checkpoint['reference_union']==parent['reference_union']
    checkpoint['source_fingerprints']=sources;base.write(out/'checkpoint.json',checkpoint)
    v['source_fingerprints']=sources;v['checkpoint']=study.binding(out/'checkpoint.json');base.write(out/'validation.json',v)
    assert sorted(v['preserved_tables'].values())==[22,26,34,42,53,28886]
    assert v['reference_union_unchanged'] and v['new_native']==v['new_extensions']==0
    assert (v['query_audits'],v['truth_tables'],v['choice_audits'],v['known_hit_audits'],v['exact_query_comparisons'])==(624,104,144,84,416)
    assert (v['old_composed_records'],v['old_pilot_records'])==(5650,444)
    assert (v['canonical_fixedpoints'],v['representation_mutations'])==(28886,4961)
    assert len(v['committed_prefix_audits'])==104
    summaries=base.load(out/'report.json')['summary'];a=summaries['batch32'];b=summaries['ordered'];single=summaries['memo128']
    for arm in (b,single):
        for k in ('native_digest','extension_digest','database_bytes','compressed_bytes','native_payload','extension_payload','cache_digest'):
            assert arm[k]==a[k]
        assert arm['sqlite_settings']==a['sqlite_settings']==dict(journal_mode='delete',synchronous=2)
        assert arm['counters']['batch_committed_records']==605 and arm['counters']['batch_committed_payload']==651784
        assert arm['batch_peak_records']<=arm['batch_rows'] and arm['batch_peak_payload']<=arm['batch_payload_limit']
    assert single['counters']['batch_commits']==104 and b['counters']['batch_commits']==104
    assert (b['batch_peak_records'],b['batch_peak_payload'],b['batch_peak_python_bytes'])==(27,39747,17086)
    assert a['counters']=={k:v for k,v in b['counters'].items() if not k.startswith('ordered_')}
    counts=b['counters']
    assert (counts['ordered_calls'],counts['ordered_fast_clauses'],counts['ordered_fallback_clauses'])==(1163,47059,2774)
    assert counts['ordered_initial_sorts_avoided']+counts['ordered_mapped_sorts_avoided']==96099
    assert b['proof_memo_capacity']==b['proof_memo_peak_bytes']==0
    assert single['counters']['proof_memo_hits']==262 and single['proof_memo_peak_bytes']==131020
    assert v['ordered_normalization_mutations']==4961
    profile=base.load(out/'profile.json')
    assert all(p['outputs_and_counters_identical'] for p in profile['profiles'].values())
    assert profile['profile_source']['sha256']==sources['experiments/profile_cnf_ordered_normalization.py']
    def sort_calls(mode):
        return sum(f['total_calls'] for f in profile['profiles'][mode]['functions'] if 'builtins.sorted' in f['function'])
    assert sort_calls('batch32')-sort_calls('ordered')==96099
    paper='paper/bounded_domain_sat_and_amortized_reasoning.tex';commit=subprocess.check_output(['git','rev-parse','9b83b1d'],text=True).strip()
    old=subprocess.check_output(['git','show',commit+':'+paper],text=True);pattern=r'\\begin\{proof\}.*?\\end\{proof\}'
    proofs=re.findall(pattern,old,re.S);assert len(proofs)==64 and proofs==re.findall(pattern,Path(paper).read_text(),re.S)
    logs={name:(out/name).read_text() for name in ('full-tests.log','focused-tests.log','latex-final.log')}
    assert re.search(r'Ran 1300 tests in .*\n\nOK',logs['full-tests.log'])
    assert re.search(r'Ran 131 tests in .*\n\nOK',logs['focused-tests.log'])
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
    checks=dict(passed=True,baseline_commit=commit,prior_sources=632,final_sources=len(sources),prior_artifacts=7990,prior_manifests=117,
        source_fingerprints=sources,full_tests=1300,focused_tests=131,warnings=warnings,warning_sites=dict(current_warning_sites),warning_emission_files_preexisting=True,warning_distribution_delta=warning_delta,proof_blocks_unchanged=64,manuscript_pages=pages,paper_sha256=base.sha(paper),
        limitations=['All 104 inputs replay the preceding study; two run orders do not establish representative arbitrary-SAT performance.',
            'Ordered improves paired query/complete times against batching, but remains slower than the memo on queries and regresses on warm queries. No robust general-SAT speedup claim.',
            'Cold readers/archives are identical; their timing variations are not ordered-normalization benefits.',
            'Ordered adds no retained memo, but transient snapshots, global clause sets, allocator overhead and full-solver memory remain. Persistent storage is unchanged.',
            'Every literal is validated. Global deduplication/sorting, name maps, exact keys and every original proof rule remain.',
            'The full suite emits 44 unclosed-SQLite ResourceWarnings, at unchanged source/stdlib files. Focused tests emit none. This checkpoint does not fix that existing suite issue.',
            'No new persisted mathematical answers, production-default change, Lean theorem or unrestricted-SAT resource bound.'])
    base.write(out/'checks.json',checks)
    files=sorted(f for f in out.rglob('*') if f.is_file() and f.name!='manifest.json')
    base.write(out/'manifest.json',dict(artifacts={str(f):base.sha(f) for f in files}))
    print(base.encode(dict(passed=True,artifacts=len(files),next_artifacts=7990+len(files),next_manifests=118,final_sources=len(sources),pages=pages)),flush=True)


if __name__=='__main__':finalize(Path(sys.argv[1]))
