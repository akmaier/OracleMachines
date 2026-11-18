#!/usr/bin/env python3
"""Retain untimed whole-source mechanism checks of all three policies."""
from collections import Counter
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_binary_backbone as study
from experiments.cnf_binary_clause_cover import BinaryClauseCoverSolver
from experiments.cnf_binary_backbone import BinaryBackboneSolver,FrequencyBinaryBackboneSolver
base=study.base


def diagnose(out):
    cases=base.load(study.PARENT/'cases.json')['cases'];totals={};records=[]
    policies={'cover':BinaryClauseCoverSolver,'first':BinaryBackboneSolver,'frequency':FrequencyBinaryBackboneSolver}
    for mode,cls in policies.items():
        total=Counter()
        for case in cases:
            s=cls()
            try:
                r=s.solve(case['source']);m=r['metrics']
                metrics=dict(nodes=r['archive_nodes'],payload=r['archive_payload_bytes'],expanded=m.get('expanded_nodes',0),propagation=m.get('propagation_literal_visits',0),
                    selected=m.get('binary_backbone_selections',0),compiled=m.get('binary_backbone_compiled_children',0))
                total.update(metrics);records.append(dict(mode=mode,case=case['case'],family=case['family'],answer=r['answer'],root=r['root'],metrics=metrics,counters=m))
            finally:s.close()
        totals[mode]=dict(total)
    for case in cases:assert len({r['answer'] for r in records if r['case']==case['case']})==1
    base.write(out/'diagnosis.json',dict(source_catalog=study.binding(study.PARENT/'cases.json'),totals=totals,records=records,
        limitations=['Each mechanism check starts from a separate empty in-memory archive. It is neither historical exact-prefix replay nor the prepared production path.',
            'No mechanism timings are reported. The first-path storage regression is retained alongside the frequency gate.',
            'Production and cold-replay archives, not these untimed counters alone, establish persistence and resource comparisons.']))


if __name__=='__main__':diagnose(Path(sys.argv[1]))
