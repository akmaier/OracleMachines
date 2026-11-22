#!/usr/bin/env python3
"""Seal the bounded-target study after tests, replay and manuscript checks."""
from collections import Counter
from pathlib import Path
import re,subprocess,sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_ranked_binary_targets as study
base=study.base


def finalize(out):
    p=base.load(out/'protocol.json');v=base.load(out/'validation.json');cp=base.load(out/'checkpoint.json')
    assert v['passed'] and v['query_audits']==96
    assert (len(v['parent_manifests']),v['prior_artifacts_unchanged'])==(128,9192)
    for path,entry in v['parent_manifests'].items():
        assert base.sha(path)==entry['sha256']
        for f,h in base.load(path)['artifacts'].items():assert base.sha(f)==h,f
    diagnostic='experiments/diagnose_cnf_ranked_binary_targets.py'
    sources={**v['source_fingerprints'],diagnostic:base.sha(diagnostic),__file__.removeprefix(str(Path.cwd())+'/'):base.sha(__file__)}
    assert len(sources)==703
    for f,h in sources.items():assert base.sha(f)==h,f
    # The pre-target whole-cover body is copied exactly, not retuned together
    # with the target-selection change.
    old=Path('experiments/cnf_targeted_backbone.py').read_text();new=Path('experiments/cnf_ranked_binary_targets.py').read_text()
    assert old[old.index('    # Preserve'):old.index('    # The model excludes')]==new[new.index('    # Preserve'):new.index('    # Use the binary model')]
    paper='paper/bounded_domain_sat_and_amortized_reasoning.tex';head='f8be02b'
    before=subprocess.check_output(['git','show',head+':'+paper],text=True);pattern=r'\\begin\{proof\}.*?\\end\{proof\}'
    proofs=re.findall(pattern,before,re.S);assert len(proofs)==64 and proofs==re.findall(pattern,Path(paper).read_text(),re.S)
    full=(out/'full-tests.log').read_text();focused=(out/'focused-tests.log').read_text()
    assert re.search(r'Ran 1394 tests in .*\n\nOK',full) and re.search(r'Ran 76 tests in .*\n\nOK',focused)
    warnings={k:len(re.findall('ResourceWarning: unclosed database',s)) for k,s in (('full',full),('focused',focused))}
    assert warnings['focused']==0
    sites=Counter(re.sub(r'0x[0-9a-f]+','ADDR',line.lstrip('.')) for line in full.splitlines() if 'ResourceWarning: unclosed database' in line)
    latex=(out/'latex-final.log').read_text();assert not re.search(r'Warning|Overfull|Underfull|^!',latex,re.M)
    pages=int(re.search(r'\((\d+) pages,',latex)[1])
    for b in (cp['reference_union'],cp['ranked_binary_targets']['partitions'],cp['ranked_binary_targets']['analysis']):assert base.sha(b['path'])==b['sha256']
    target=base.load(out/'next-target.json')
    assert target['preceding_reused_node_available_under_binary1'] and target['reader_counts'].get('expanded_nodes',0)==0
    assert [target['dependency_census'][m][2]['expansions'] for m in study.MODES]==[10,35,33]
    for entry in target['input_reports'].values():study.bound(entry)
    cp['source_fingerprints']=sources;cp['ranked_binary_targets']['next_target']=study.binding(out/'next-target.json')
    base.write(out/'checkpoint.json',cp)
    v.update(source_fingerprints=sources,checkpoint=study.binding(out/'checkpoint.json'));base.write(out/'validation.json',v)
    checks=dict(passed=True,baseline_commit=head,prior_sources=696,final_sources=703,prior_artifacts=9192,prior_manifests=128,
        full_tests=1394,focused_tests=76,warnings=warnings,warning_sites=dict(sites),whole_cover_body_unchanged=True,
        manuscript_pages=pages,paper_sha256=base.sha(paper),proof_blocks_unchanged=64,source_fingerprints=sources,
        final_union_tables=v['preserved_tables'],final_checkpoint=study.binding(out/'checkpoint.json'),
        limitations=p['limitations']+v['limitations']+target['limitations']+[
            'Full-suite unclosed SQLite warning sites can be collection sites, not allocation sites. Focused tests emit none.',
            'This checkpoint inherits all previous record payloads and preserves alternative proofs in trial deltas. Both native readers recheck the cumulative union; older unrelated audits remain manifest-bound.',
            'No independent external SAT benchmark or machine-checked refinement theorem was added.'])
    base.write(out/'checks.json',checks)
    files=sorted(f for f in out.rglob('*') if f.is_file() and f.name!='manifest.json')
    base.write(out/'manifest.json',dict(artifacts={str(f):base.sha(f) for f in files}))
    print(base.encode(dict(passed=True,artifacts=len(files),next_artifacts=9192+len(files),next_manifests=129,final_sources=703,pages=pages,warnings=warnings,tables=v['preserved_tables'])),flush=True)


if __name__=='__main__':finalize(Path(sys.argv[1]))
