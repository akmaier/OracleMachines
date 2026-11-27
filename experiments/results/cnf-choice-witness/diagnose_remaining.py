"""Classify extracted interactions without turning discovery failure into UNSAT."""
from collections import Counter
from pathlib import Path
from unittest.mock import patch
import json
from experiments import cnf_choice_witness as e


def run(out):
    load=lambda p:json.loads(Path(p).read_text())
    rows=load('experiments/results/cnf-external-cutsets/panel.json')
    report=load(out/'choice-0/report.json');categories=Counter();records=[]
    for row,case in zip(rows,report['cases']):
        assert row['id']==case['id'];attempt=case['diagnostic']['choice']['attempts'][0]
        category=('strict-choice-class' if attempt['strict_choice_class'] else
                  'complete-nonclique-choices' if not attempt['unclassified_clauses'] else
                  'partial-choices-with-unclassified-clauses')
        categories[category]+=1
        records.append(dict(id=row['id'],category=category,first_attempt=attempt,status=case['status']))
    edited=rows[36];original=rows[20];proof=load(out/'choice-0/e036.json')['proof']
    got=e.check(edited['source'],proof)
    restored_conflict=edited['source']+[original['source'][0]]
    assert e.check(restored_conflict,proof)['answer']
    original_assignment_satisfies=all(any(got['model'][abs(v)]==(v>0) for v in c) for c in original['source'])
    assert not original_assignment_satisfies
    counterfactual=dict(witness_true_variables=[v for v,b in got['model'].items() if b],
                        restored_deleted_exclusion_still_satisfied=True,
                        original_unedited_formula_rejects_witness=True,
                        scope='This same full witness works after restoring the deleted first exclusion, so the literal edit alone suffices for this SAT witness. Rejection by the original formula is not an independent UNSAT proof.')
    rejected=[]; original_check=e.check
    def inspect_check(source,candidate,counts=None):
        values=dict(zip(candidate['names'],candidate['values']))
        violated=[i for i,c in enumerate(source) if not any(values[abs(v)]==(v>0) for v in c)]
        if violated:rejected.append(dict(candidate=candidate,violated_clause_indices=violated))
        return original_check(source,candidate,counts)
    with patch.object(e,'check',inspect_check):
        candidate,diagnostic=e.discover(rows[7]['source'])
    assert candidate is None and rejected
    result=dict(first_attempt_categories=dict(categories),external=records,edited_witness_diagnostic=counterfactual,
                remaining_random=dict(id=rows[7]['id'],source=rows[7]['source'],rejected_candidates=rejected,diagnostic=diagnostic,scope='These are rejected assignments, not SAT certificates. Full source checks reject each before publication.'),
                scope='Categories depend on the fixed greedy extraction and are not canonical semantic SAT classes. Strict choices, fully represented nonclique conflicts and unclassified clauses have different obligations. These classifications do not replace complete source witness checks.')
    (out/'gap-diagnostics.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(dict(categories=dict(categories),true_variables=len(counterfactual['witness_true_variables']),remaining_rejected_clauses=[len(r['violated_clause_indices']) for r in rejected])))


if __name__=='__main__':
    import sys
    run(Path(sys.argv[1]))
