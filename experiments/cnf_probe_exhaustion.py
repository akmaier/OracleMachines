"""Certify an obstruction to single-assumption unit refutation.

In a normalized CNF with no clauses shorter than two, a variable absent from
every binary clause cannot create a unit or empty clause under either value.
Consequently unit propagation cannot start. This does NOT decide satisfiability.
"""
from collections import Counter
import argparse
import json
from pathlib import Path
import sys
import tempfile
import time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments.continue_cnf_probes import restore_report
from experiments.cnf_coupled_pivots import BudgetedInventory
from experiments.cnf_probe_continuation import TABLE
from experiments.cnf_probe_window import TABLE as WINDOW_TABLE
from experiments.cnf_residual_dag import restrict
from experiments.cnf_simplification import check_simplification
from experiments.compare_cnf_probe_continuation import sha, sha_key


def no_unit_triggers(cnf, variables, counts):
    """Check a sufficient structural certificate for both assignment polarities."""
    support = set(); binary = set()
    for clause in cnf:
        counts['exhaustion_source_literal_visits'] += len(clause)
        if (len(clause) < 2 or any(type(l) is not int or not l for l in clause)
                or len({abs(l) for l in clause}) != len(clause)):
            raise ValueError('Expected normalized clauses of width at least two')
        support.update(abs(l) for l in clause)
        if len(clause) == 2: binary.update(abs(l) for l in clause)
    if any(type(v) is not int or v <= 0 for v in variables):
        raise ValueError('Invalid variable')
    selected = set(variables)
    if not selected <= support or selected & binary:
        raise ValueError('Variable may trigger a unit clause')
    counts['structurally_excluded_probe_variables'] += len(selected)
    return True


def check_clear_attempts(cnf, attempts, counts):
    """Replay only top-level source traces, regardless of the profile's wrapper.

    In particular, learning_clear contains a nested continuation on an augmented
    formula. It is not evidence of unit closure on the unaugmented source.
    """
    support = {abs(l) for c in cnf for l in c}
    for attempt in attempts:
        if (set(attempt) != {'variable','value','certificate'} or
                type(attempt['variable']) is not int or attempt['variable'] not in support or
                type(attempt['value']) is not bool or attempt['certificate']['conflict'] is not None):
            raise ValueError('Expected a clear source-bound assumption trace')
        branch = restrict(cnf,{attempt['variable']:attempt['value']},counts)
        check_simplification(branch,attempt['certificate'],counts,pure=False)
        counts['exhaustion_checked_attempts'] += 1


def certify_exhaustion(cnf, attempts, counts):
    """Only verified source traces and the no-trigger lemma justify exhaustion.

    Trial routing, prefix offsets and discovery-policy status are unnecessary
    premises for this particular property. Missing binary-variable evidence is
    rejected, including when a ranking cap previously omitted that variable.
    """
    check_clear_attempts(cnf,attempts,counts)
    attempted = {(a['variable'],a['value']) for a in attempts}
    covered = {v for v,_ in attempted}
    binary = {abs(l) for c in cnf if len(c)==2 for l in c}
    if attempted != {(v,b) for v in covered for b in (False,True)} or not binary <= covered:
        raise ValueError('Missing clear evidence for both values of every binary variable')
    support = {abs(l) for c in cnf for l in c}; outside = sorted(support-covered)
    no_unit_triggers(cnf,outside,counts)
    return sorted(binary),outside


def diagnose(report_path, out):
    pipeline_started = started = time.perf_counter(); r = json.loads(report_path.read_text())
    opportunity_path = report_path.parent/'continuation-opportunity.json'
    assert sha(opportunity_path) == r['opportunity_sha256']
    opportunity = json.loads(opportunity_path.read_text())
    targets = {row['source_sha256']:row for row in opportunity['rows']
        if row['status'] == 'clear' and not row['remaining_ranked_candidates'] and row['open_selected_cases']}
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp); history = tmp/'history'; restored = restore_report(report_path,history,tmp)
        restoration = time.perf_counter()-started; before = sha(history)
        started = time.perf_counter(); h = BudgetedInventory(history,**restored['options']); h.set_admission_budget(0)
        windows = [json.loads(p) for p, in h.db.execute(f'SELECT payload FROM {WINDOW_TABLE} ORDER BY id')]
        continuations = [json.loads(p) for p, in h.db.execute(f'SELECT payload FROM {TABLE} ORDER BY id')]
        rows = []; counts = Counter()
        for base in windows:
            source = base['source']; identity = sha_key(source)
            if identity not in targets: continue
            node = h._load(source); assert node['kind'] == 'unresolved'
            original = node['profile']['probing']
            blocks = [base] + sorted((rec for rec in continuations if rec['source']==source),key=lambda rec:rec['offset'])
            assert all(rec['probing']['status'] == 'clear' and rec['edge'] is None for rec in blocks)
            # For this property, independently check all source assumption facts
            # and complete variable coverage; do not load unrelated trial routes.
            attempts = original.get('attempts',[]) + [a for rec in blocks for a in rec['probing']['attempts']]
            binary,outside = certify_exhaustion(node['cnf'],attempts,counts)
            support = {abs(l) for c in node['cnf'] for l in c}
            assert outside == targets[identity]['outside_ranked_pool']
            rows.append(dict(source=source,source_sha256=identity,open_selected_cases=targets[identity]['open_selected_cases'],
                variables=len(support),clauses=len(node['cnf']),minimum_clause_width=min(map(len,node['cnf'])),
                original_probe_status=original['status'],
                checked_binary_variables=sorted(binary),structurally_excluded_variables=outside,
                offsets=[rec.get('offset',0) for rec in blocks],checked_attempts=len(attempts),
                conclusion='No assignment of one source variable yields a unit-propagation refutation. SAT/UNSAT remains unresolved here.'))
        assert {row['source_sha256'] for row in rows} == set(targets) and not h.admitted
        diagnosis_seconds = time.perf_counter()-started; h.close(); assert sha(history) == before
    result = dict(report_sha256=sha(report_path),script_sha256=sha(Path(__file__)),rows=rows,counts=dict(counts),
        restore_seconds=restoration,diagnosis_seconds=diagnosis_seconds,total_seconds=time.perf_counter()-pipeline_started,
        new_probe_discovery=False,history_bytes_unchanged=True,
        scope='Exact single-assumption unit-propagation obstruction on these checked residuals; no SAT answer, lower bound for arbitrary algorithms, or exclusion of stronger lookahead.')
    out.write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
    print(json.dumps(dict(certified_sources=len(rows),outside_variables=sum(len(row['structurally_excluded_variables']) for row in rows))),flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(); parser.add_argument('report',type=Path); parser.add_argument('output',type=Path)
    args = parser.parse_args(); diagnose(args.report,args.output)
