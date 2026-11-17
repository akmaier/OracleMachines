#!/usr/bin/env python3
"""Report total propagation and publication costs on exact historical prefixes."""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_terminal_first as study
from experiments.validate_cnf_unsat_support import bound
base=study.base


def run(out):
    report=base.load(out/'report.json');samples=[bound(e) for e in report['samples']];pairs=[]
    for cohort,cid in dict.fromkeys((r['cohort'],r['case']) for r in samples):
        pair={r['mode']:r for r in samples if r['cohort']==cohort and r['case']==cid};summary={}
        for mode,r in pair.items():
            child=sum(c['metrics'].get('propagation_literal_visits',0) for c in r['children']);screen=r['screen_counts'].get('propagation_literal_visits',0)
            summary[mode]=dict(new_nodes=r['new_nodes'],new_payload_units=r['new_payload_units'],expanded_nodes=r['expanded_nodes'],trace_publications=r['trace_publications'],premise_publications=int(r['premise_inserted']),
                screen_propagation_literal_visits=screen,child_propagation_literal_visits=child,total_propagation_literal_visits=child+screen,trace_check_literals=sum(c['metrics'].get('screen_trace_check_literals',0) for c in r['children']),
                posting_visits=r['screen_counts'].get('screen_posting_visits',0),core_reads=r['screen_counts'].get('screen_core_reads',0),plans=r['screen_counts'].get('screen_plans',0),retained_bytes=r['retained_bytes'],
                preparation_seconds=r['preparation_seconds'],screen_setup_seconds=r['screen_setup_seconds'],screen_seconds=r['screen_seconds'],child_seconds=sum(c['seconds'] for c in r['children']),cold_seconds=r['cold']['seconds'],complete_seconds=r['seconds'])
        pairs.append(dict(cohort=cohort,case=cid,costs=summary))
    result=dict(passed=True,report=study.binding(out/'report.json'),pairs=pairs,limitations=['Historical prefix correction, no fresh-input coverage or stable timing/peak-memory result. Setup and trace verification remain charged. A terminal native proof still consumes one row even when expanded_nodes is zero.', 'Nonterminal selection and proof deltas are unchanged; the checker independently reconstructs choices and compares both policies to previously preserved certificates.'])
    base.write(out/'cost-attribution.json',result);print(base.encode(pairs),flush=True)


if __name__=='__main__':run(Path(sys.argv[1]))
