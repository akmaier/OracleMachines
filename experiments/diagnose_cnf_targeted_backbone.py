#!/usr/bin/env python3
"""Check the saved missed opportunities and untimed whole-source mechanisms."""
from collections import Counter
from pathlib import Path
import sys,tempfile
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_targeted_backbone as study
from experiments.cnf_targeted_backbone import TargetedBackboneSolver,inspect_targeted_backbone
from experiments.cnf_binary_backbone import FrequencyBinaryBackboneSolver,check_path
base=study.base


def diagnose(out):
    cases=base.load(study.PARENT/'cases.json')['cases'];totals={};records=[]
    policies={'frequency':FrequencyBinaryBackboneSolver,'targeted':TargetedBackboneSolver}
    for mode,cls in policies.items():
        total=Counter()
        for case in cases:
            s=cls()
            try:
                r=s.solve(case['source']);m=r['metrics']
                metrics=dict(nodes=r['archive_nodes'],payload=r['archive_payload_bytes'],expanded=m.get('expanded_nodes',0),propagation=m.get('propagation_literal_visits',0),
                    selected=m.get('binary_backbone_selections',0),compiled=m.get('binary_backbone_compiled_children',0),target_calls=m.get('binary_target_calls',0),target_roots=m.get('binary_target_reach_roots',0),target_hits=m.get('binary_target_reach_hits',0),target_misses=m.get('binary_target_misses',0))
                total.update(metrics);records.append(dict(mode=mode,case=case['case'],family=case['family'],answer=r['answer'],root=r['root'],metrics=metrics,counters=m))
            finally:s.close()
        totals[mode]=dict(total)
    for case in cases:assert len({r['answer'] for r in records if r['case']==case['case']})==1
    missed=base.load(study.PARENT/'attribution.json')['frontier']['missed'];checked=[]
    saved=base.load(study.PARENT/'frequency-0/report.json')
    with tempfile.TemporaryDirectory() as td:
        path=Path(td)/'archive';base.restore_archive(saved['archive'],path);solver=study.native.ResidualSolver(path)
        try:rows={base.key_sha(k):base.load_json(v) for k,v in study.native.rows(solver).items()}
        finally:solver.close()
    for item in missed:
        cnf=tuple(tuple(c) for c in rows[item['root_sha256']]['cnf']);counts=Counter()
        proof,cover,partials=inspect_targeted_backbone(cnf,counts)
        assert proof is None and cover is None and partials
        evidence=partials[0];assert abs(evidence['literal'])==item['default_variable']
        assert -evidence['literal'] in item['forced_literals'];check_path(cnf,evidence,counts)
        checked.append(dict(**item,evidence=evidence,counts=dict(counts)))
    assert len(checked)==14 and sum(r['native_kind']=='split' for r in checked)==6
    base.write(out/'diagnosis.json',dict(source_catalog=study.binding(study.PARENT/'cases.json'),totals=totals,records=records,saved_opportunities=checked,
        limitations=['Each mechanism check starts from a separate empty in-memory archive. It is neither historical exact-prefix replay nor the prepared production path.',
            'No mechanism timings are reported. Recognition of saved stored nodes is not a count of avoided expansions; whole-source acquisition is measured separately.',
            'Production and cold-replay archives, not these untimed counters alone, establish persistence and resource comparisons.']))


if __name__=='__main__':diagnose(Path(sys.argv[1]))
