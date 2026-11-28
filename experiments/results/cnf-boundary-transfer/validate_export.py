"""Reproduce fresh proof export, exact state charging, storage and cold checks."""
from collections import Counter
from pathlib import Path
import gzip,importlib.util,json,sys
sys.path.insert(0,str(Path(__file__).resolve().parents[3]))
from experiments import compare_cnf_boundary_transfer as s


def validate(out):
    spec=importlib.util.spec_from_file_location('root_export',out/'export_root_exclusions.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    report=s.load(out/'root-export.json');policy=s.bound(report['policy']);assert report['script']['sha256']==policy['script']['sha256']==s.sha(out/'export_root_exclusions.py')
    assert Path(report['script']['path']).resolve()==Path(policy['script']['path']).resolve()==(out/'export_root_exclusions.py').resolve()
    assert policy['parent_comparisons']==s.binding(out/'comparisons.json')
    audit=s.load(out/'export-audit.json');module.audit(out);assert s.load(out/'export-audit.json')==audit and audit['passed']
    rows=s.source_rows(s.load(out/'protocol.json'));prior=s.load(out/'boundary-0/report.json')['cases'];evidences=s.load(out/'root-export/discovery.json');old_evidence=s.load(out/'boundary-0/discovery.json');assert evidences==old_evidence
    total=Counter();proofs=[];negative=[]
    for row,case,old,ev in zip(rows,report['cases'],prior,evidences):
        assert row['id']==case['id']==old['id'];counts=Counter();proof,evidence,diag=module.discover(row['source'],counts)
        stored=s.load(out/'root-export'/(row['id']+'.json'));proofs.append(stored)
        assert proof==stored and evidence==ev and diag==case['diagnostic'] and dict(counts)==case['discovery_counts']
        assert diag['boundary']==old['diagnostic'] and diag['total_states']<=20000
        got=module.check(row['source'],proof,counts);s.e.check_evidence(row['source'],ev,counts);total.update(counts)
        assert json.loads(s.encode(got))==case['result'] and dict(counts)==case['counts']
        if case['status']=='unsat':
            assert old['status']=='unresolved' and diag['boundary']['prefix']['reason']=='radius-exhausted'
            assert diag['total_states']==2*diag['replay']['expanded'];negative.append(row['id'])
            assert s.load(out/'references'/(row['id']+'-portfolio.json'))['result']['answer'] is False
            assert s.load(out/'references'/(row['id']+'-z3.json'))['result']['answer'] is False
    assert dict(total)==report['counts']
    for key,repeats in (('warm_counts',1),('cold_counts',2)):
        counts=Counter()
        for _ in range(repeats):
            for row,ev,proof in zip(rows,evidences,proofs):module.check(row['source'],proof,counts);s.e.check_evidence(row['source'],ev,counts)
        assert dict(counts)==report[key]
    assert json.loads(gzip.decompress((out/'root-export/combined.json.gz').read_bytes()))==dict(proofs=proofs,evidence=evidences)
    assert report['proof_bytes']==sum((out/'root-export'/(row['id']+'.json')).stat().st_size for row in rows)
    assert report['evidence_bytes']==(out/'root-export/discovery.json').stat().st_size
    assert report['combined_gzip_bytes']==(out/'root-export/combined.json.gz').stat().st_size
    assert negative==['t004','t005','t006','t007','t026','t027']
    result=dict(passed=True,negative_exports=negative,already_certified_by_portfolio=negative,extra_states=sum(c['diagnostic']['replay']['expanded'] for c in report['cases'] if c['diagnostic']['replay']),total_states=sum(c['diagnostic']['total_states'] for c in report['cases']),coverage=dict(Counter(c['status'] for c in report['cases'])),reproduced_counts_and_replays=True,semantic_audit=s.binding(out/'export-audit.json'),report=s.binding(out/'root-export.json'),script=s.binding(__file__))
    s.write(out/'export-validation.json',result);print(s.encode(result))


if __name__=='__main__':validate(Path(sys.argv[1]))
