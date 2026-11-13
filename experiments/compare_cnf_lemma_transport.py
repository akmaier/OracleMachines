#!/usr/bin/env python3
"""Retain and compare parent-lemma transport with learning from leaf traces.

The history is read-only. These independently checked augmentations are saved
as portable evidence; neither is silently installed as a structural route.
"""
from collections import Counter
import argparse
import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import time
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from experiments.cnf_lemma_transport import FORMAT, check_certificate
from experiments.cnf_exhaustion_certificate import make_certificate, check_certificate as check_exhaustion
from experiments.cnf_probe_equivalence import discover_equivalence_probes, check_equivalence_probes
from experiments.cnf_probe_learning import learning_batch, augment
from experiments.cnf_pattern_inventory import encode
from experiments.compare_cnf_trace_reuse import read_archive, archive_json
from experiments.compare_cnf_probe_continuation import sha
from experiments.continue_cnf_reuse_frontier import restore_checkpoint
from experiments.cnf_coupled_pivots import BudgetedInventory
from experiments.cnf_trace_learning import checked_augmentation, verify_learning
from experiments.cnf_trace_reuse import read_attempt
from experiments.cnf_trace_split import verify as verify_split

PARENT = Path('experiments/results/cnf-reuse-frontier/report.json')
FILES = ['experiments/cnf_lemma_transport.py', 'experiments/compare_cnf_lemma_transport.py',
    'solver/test_cnf_lemma_transport.py', 'experiments/cnf_probe_learning.py',
    'experiments/cnf_probe_equivalence.py', 'experiments/cnf_additive_elimination.py',
    'experiments/cnf_binary_paths.py', 'experiments/cnf_exhaustion_certificate.py']


def pack(h, base, split, value, target, counts):
    """Extract only the dependencies of this path from the checked inventory."""
    if base['source'] != split['source'] or type(value) is not bool:
        raise ValueError('Mismatched transport source or branch')
    node, _ = checked_augmentation(h, base, counts); verify_learning(h, base, counts)
    verify_split(h, split, counts)
    certificate = dict(format=FORMAT, source=copy.deepcopy(node['cnf']),
        attempts=[read_attempt(h, base['source'], ref, counts) for ref in base['references']],
        lemmas=[dict(attempt=c['reference'], unit=c['unit'], clause=c['clause']) for c in base['clauses']], steps=[])
    edge = split['edges'][int(value)]
    certificate['steps'].append(dict(kind='condition',
        attempt=read_attempt(h, split['source'], split['references'][int(value)], counts),
        names=edge['names'], target=h._load(edge['key'])['cnf']))
    key = edge['key']; seen = set()
    while key != target:
        if key in seen: raise ValueError('Cyclic retained path')
        seen.add(key); node = h._load(key)
        if node['kind'] == 'eliminate' and node.get('additive_elimination', {}).get('variable') is not None:
            step = dict(kind='eliminate', certificate=node['additive_elimination'],
                pair_limit=h.config['elimination_pair_limit'], clause_growth_limit=h.config['clause_growth_limit'])
        elif node['kind'] == 'binary_paths':
            step = dict(kind='binary_paths', certificate=node['binary_paths'], root_limit=h.config['binary_path_root_limit'])
        else:
            raise ValueError('This extractor does not certify that path kind')
        edge = node['edge']; step.update(names=edge['names'], target=h._load(edge['key'])['cnf'])
        certificate['steps'].append(step); key = edge['key']
    check_certificate(certificate, expected_source=h._load(base['source'])['cnf'],
        expected_target=h._load(target)['cnf'], counts=counts)
    return copy.deepcopy(certificate)


def local_certificate(cnf, attempts, counts):
    batch = learning_batch(cnf, attempts, 16, counts); selected = []; indices = {}; lemmas = []
    for item in batch:
        index = item['attempt']
        if index not in indices:
            indices[index] = len(selected); selected.append(attempts[index])
        lemmas.append(dict(attempt=indices[index], unit=item['unit'], clause=item['clause']))
    return dict(format=FORMAT, source=cnf, attempts=selected, lemmas=lemmas, steps=[])


def acquire(certificate, cnf):
    counts = Counter(); start = time.perf_counter()
    result = check_certificate(certificate, expected_target=cnf, counts=counts)
    checking = time.perf_counter() - start
    expanded = augment(cnf, [dict(clause=c) for c in result['additions']])
    start = time.perf_counter(); probing = discover_equivalence_probes(expanded, 64, counts)
    discovery = time.perf_counter() - start
    start = time.perf_counter(); target, fixed = check_equivalence_probes(expanded, probing, 64, counts)
    verification = time.perf_counter() - start
    # Keep a changed inference state explicit even when it yields no rewrite.
    exhaustion = make_certificate(expanded, probing['attempts']) if probing['status'] == 'clear' else None
    return dict(transport=result, expanded=[list(c) for c in expanded], probing=probing,
        target=[list(c) for c in target], fixed=fixed, exhaustion=exhaustion,
        proof_check_seconds=checking, discovery_seconds=discovery, probe_check_seconds=verification,
        counts=dict(counts))


def run(out, parent_path=PARENT):
    pipeline = time.perf_counter(); out.mkdir(exist_ok=False)
    parent = json.loads(parent_path.read_text()); diagnostics = read_archive(parent['diagnostics'])
    target = diagnostics['after']['leaves'][0]['source']; counts = Counter()
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td); path = tmp/'history'; started = time.perf_counter()
        restored, rewrites, learning, blocks, splits = restore_checkpoint(parent_path, path, tmp)
        assert restored == parent
        restore_seconds = time.perf_counter() - started; digest = sha(path); history_bytes = path.stat().st_size
        h = BudgetedInventory(path, **parent['options']); h.set_admission_budget(0)
        # This run studies the latest retained split's false branch, not a
        # search over the entire inventory for a favourable transport example.
        split = splits[-1]; bases = [base for base in learning if base['source'] == split['source']]
        if len(bases) != 1: raise ValueError('Ambiguous retained parent batch')
        base = bases[0]; started = time.perf_counter()
        with patch.object(h, '_discover', side_effect=AssertionError('new recognition')):
            portable = pack(h, base, split, False, target, counts)
            cnf = copy.deepcopy(h._load(target)['cnf'])
        packing = time.perf_counter() - started
        assert not h.admitted; h.close(); assert sha(path) == digest
    source = base['source']
    bound = dict(source_key=source, target_key=target, certificate=portable)
    # Existing exact-source exhaustion evidence supplies the local alternative.
    obstruction_path = parent_path.parent/'obstruction.json'; obstruction = json.loads(obstruction_path.read_text())
    if obstruction['report_sha256'] != sha(parent_path): raise ValueError('Changed source evidence')
    entries = read_archive(obstruction['certificates'])
    entry = next(row for row in entries if row['source'] == target)
    started = time.perf_counter(); check_exhaustion(entry['certificate'], expected_cnf=cnf, counts=counts)
    local = local_certificate(cnf, entry['certificate']['attempts'], counts)
    local_preparation = time.perf_counter() - started
    arms = {name: acquire(cert, cnf) for name, cert in (('transport', portable), ('local', local))}
    # Four extra clauses in this example, not evidence that local learning
    # subsumes transported lemmas for other formulas or inference policies.
    a = {tuple(c) for c in arms['transport']['transport']['additions']}
    b = {tuple(c) for c in arms['local']['transport']['additions']}
    report = dict(format='parent-lemma-transport-comparison-v1',
        parent=dict(path=str(parent_path), sha256=sha(parent_path)),
        source_commit=subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip(),
        fingerprints={p: sha(p) for p in FILES},
        evidence_counts=dict(splits=len(splits), learning=len(learning), blocks=len(blocks)),
        source_sha256=sha_text(source), target_sha256=sha_text(target),
        provenance=dict(base_sha256=sha_text(encode(base)), split_sha256=sha_text(encode(split)), value=False),
        transport=archive_json(out/'transport.json.gz', bound),
        local=archive_json(out/'local.json.gz', local),
        arms={name: archive_json(out/f'{name}-acquisition.json.gz', value) for name, value in arms.items()},
        source_exhaustion=dict(path=str(obstruction_path), sha256=sha(obstruction_path)),
        restore_seconds=restore_seconds, packing_seconds=packing, local_preparation_seconds=local_preparation,
        export_counts=dict(counts), history_bytes=history_bytes, history_sha256=digest,
        history_bytes_unchanged=True, new_recognition_states=0, final_closed=parent['final_closed'],
        comparison=dict(shared=sorted(a & b), transport_only=sorted(a-b), local_only=sorted(b-a)),
        limitations=[
            'One adaptive development leaf, no independent holdout or general coverage/runtime claim.',
            'Source proofs and all conditioning, elimination and renaming steps are checked; a transported fact alone is not a coverage plan.',
            'The local arm starts with already acquired leaf traces. All ancestral acquisition remains in the parent reports.',
            'Both arms add entailed clauses and use the same 64-variable cap, above this leaf support; different candidate counts are reported.',
            'Single local timings exclude process startup and do not establish a runtime advantage; peak RAM is not measured.',
            'The working history is unchanged; new evidence is retained in the listed sidecar archives, not in an automatic solver route.',
            'Neither exhaustion nor failure of common/equivalence tests decides SAT/UNSAT or bounds arbitrary algorithms.'])
    pilot = []
    for name in ('transport', 'fresh'):
        p = Path(f'/tmp/cnf-transport-{name}.json')
        if p.exists(): pilot.append(dict(name=name, data=json.loads(p.read_text())))
    if pilot:
        report['pilot'] = archive_json(out/'pilot.json.gz', dict(
            scope='Pre-checker exploratory ordering; retained for reproducibility, not the checked comparison.', arms=pilot))
    report['pipeline_seconds'] = time.perf_counter()-pipeline
    (out/'report.json').write_text(encode(report)+'\n')
    print(json.dumps(dict(additions={k: len(v['transport']['additions']) for k,v in arms.items()},
        status={k:v['probing']['status'] for k,v in arms.items()}, restore_seconds=restore_seconds,
        packing_seconds=packing, pipeline_seconds=report['pipeline_seconds'])), flush=True)


def sha_text(value):
    import hashlib
    return hashlib.sha256(value.encode()).hexdigest()


def validate(report_path, *, history=False):
    start = time.perf_counter(); r = json.loads(report_path.read_text())
    for p, digest in r['fingerprints'].items():
        if sha(p) != digest: raise ValueError('Changed transport implementation')
    if sha(r['parent']['path']) != r['parent']['sha256']: raise ValueError('Changed parent')
    parent_report = json.loads(Path(r['parent']['path']).read_text())
    if r['final_closed'] != parent_report['final_closed'] or r['new_recognition_states'] != 0:
        raise ValueError('Changed coverage claim')
    bound = read_archive(r['transport']); portable = bound['certificate']; local = read_archive(r['local'])
    source = json.loads(bound['source_key'])[-1]; target = json.loads(bound['target_key'])[-1]
    if sha_text(bound['source_key']) != r['source_sha256'] or sha_text(bound['target_key']) != r['target_sha256']:
        raise ValueError('Changed formula identity')
    if sha(r['source_exhaustion']['path']) != r['source_exhaustion']['sha256']:
        raise ValueError('Changed local evidence')
    obstruction = json.loads(Path(r['source_exhaustion']['path']).read_text())
    if obstruction['report_sha256'] != r['parent']['sha256']: raise ValueError('Mismatched local history')
    entry = next(row for row in read_archive(obstruction['certificates']) if row['source'] == bound['target_key'])
    check_exhaustion(entry['certificate'], expected_cnf=target)
    if encode(local_certificate(target, entry['certificate']['attempts'], Counter())) != encode(local):
        raise ValueError('Different local learning batch')
    results = []; counts = Counter()
    for name, cert in [('transport', portable), ('local', local)]:
        result = check_certificate(cert, expected_source=source if name=='transport' else target,
            expected_target=target, counts=counts)
        arm = read_archive(r['arms'][name]); expanded = augment(target, [dict(clause=c) for c in result['additions']])
        if encode(result) != encode(arm['transport']) or encode(expanded) != encode(arm['expanded']):
            raise ValueError('Changed augmentation')
        with patch('experiments.cnf_probe_equivalence.discover_equivalence_probes', side_effect=AssertionError('new search')):
            leaf, fixed = check_equivalence_probes(expanded, arm['probing'], 64, counts)
            if encode(leaf) != encode(arm['target']) or encode(fixed) != encode(arm['fixed']): raise ValueError('Changed inference')
            exhaustion = check_exhaustion(arm['exhaustion'], expected_cnf=expanded, counts=counts)
        results.append(dict(arm=name, additions=len(result['additions']), status=arm['probing']['status'], exhaustion=exhaustion))
    ancestry = None
    if history:
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td); path = tmp/'history'
            parent, rewrites, learning, blocks, splits = restore_checkpoint(Path(r['parent']['path']), path, tmp)
            before = sha(path); h = BudgetedInventory(path, **parent['options']); h.set_admission_budget(0)
            base = next(b for b in learning if sha_text(encode(b)) == r['provenance']['base_sha256'])
            split = next(s for s in splits if sha_text(encode(s)) == r['provenance']['split_sha256'])
            with patch.object(h, '_discover', side_effect=AssertionError('new recognition')):
                repacked = pack(h, base, split, r['provenance']['value'], bound['target_key'], Counter())
            if encode(repacked) != encode(portable): raise ValueError('Changed retained transport path')
            assert not h.admitted; h.close(); assert sha(path) == before == r['history_sha256']
            ancestry = dict(history_bytes=path.stat().st_size, unchanged=True,
                splits=len(splits), learning=len(learning), blocks=len(blocks))
    return dict(report_sha256=sha(report_path), results=results, counts=dict(counts),
        history=ancestry, seconds=time.perf_counter()-start, new_discovery=False)


if __name__ == '__main__':
    p = argparse.ArgumentParser(); sub = p.add_subparsers(dest='command', required=True)
    q = sub.add_parser('run'); q.add_argument('output', type=Path); q.add_argument('--parent', type=Path, default=PARENT)
    q = sub.add_parser('validate'); q.add_argument('report', type=Path); q.add_argument('--history', action='store_true')
    a = p.parse_args()
    if a.command == 'run': run(a.output, a.parent)
    else: print(json.dumps(validate(a.report, history=a.history), sort_keys=True))
