#!/usr/bin/env python3
"""Preserve frozen history, incomplete harness evidence and frontier lineages."""
from pathlib import Path
from unittest.mock import patch
import sys,tempfile,time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_terminal_first as study
from experiments.cnf_snapshot_replay import SnapshotResidualSolver
from experiments.cnf_incremental_support import check_proposals
from experiments.validate_cnf_unsat_support import bound
base=study.base


def run(out):
    start=time.perf_counter();v=base.load(study.PARENT/'validation.json');manifests=dict(v['parent_manifests']);path=str(study.PARENT/'manifest.json');manifests[path]=dict(sha256=base.sha(path),artifacts_checked=len(base.load(path)['artifacts']));count=0
    for path,entry in manifests.items():
        assert base.sha(path)==entry['sha256'],path
        artifacts=base.load(path)['artifacts'];assert len(artifacts)==entry['artifacts_checked']
        for f,h in artifacts.items():assert base.sha(f)==h,f
        count+=len(artifacts)
    for f,h in v['source_fingerprints'].items():assert base.sha(f)==h,f
    assert (len(v['source_fingerprints']),count,len(manifests))==(443,4843,84)
    base.write(out/'parent-manifests.json',manifests);base.write(out/'preservation.json',dict(prior_sources_unchanged=443,prior_artifacts_unchanged=count,prior_manifests_unchanged=len(manifests),seconds=time.perf_counter()-start))
    p=base.load(out/'checkpoint.json');old=bound(p['parent_checkpoint']);changed=[k for k in old if p[k]!=old[k]];added=sorted(set(p)-set(old))
    assert set(changed)=={'parent_checkpoint','source_fingerprints'} and added==['terminal_first_decisions','terminal_first_study'];assert p['reference_union']==old['reference_union']
    report=base.load(out/'report.json');samples=[bound(e) for e in report['samples']];incomplete=Path('experiments/results/cnf-terminal-first');ip=base.load(incomplete/'protocol.json')
    for f,h in ip['source_fingerprints'].items():assert base.sha(f)==h,f
    partial=[]
    for cid in (6,68,135):
        for mode in study.MODES:
            path=incomplete/f'older-{cid}-{mode}'/'report.json';data=base.load(path);complete=next(r for r in samples if r['cohort']=='older' and r['case']==cid and r['mode']==mode)
            assert bound(data['delta'])==bound(complete['delta']) and bound(data['records'])==bound(complete['records']) and data['plan']==complete['plan'] and data['screen']==complete['screen']
            partial.append(study.binding(path))
    base.write(out/'incomplete-run.json',dict(protocol=study.binding(incomplete/'protocol.json'),samples=partial,semantic_parity=True,failure='The exclusive restore helper rejected reuse of initial/final temporary paths at the second cohort. The wrapper refreshes only paths successfully restored by that invocation, after readers have closed. Six complete earlier arms are retained unchanged.'))
    frontiers={}
    with tempfile.TemporaryDirectory() as td:
        path=Path(td)/'proofs';base.restore_archive(p['reference_union'],path);s=SnapshotResidualSolver(path)
        try:
            with patch.object(s,'_expand',side_effect=AssertionError('Frontier search')),patch.object(s,'_store',side_effect=AssertionError('Frontier publication')):
                for name in ('active_support_proposals','extended_support_proposals','causal_support_proposals','incremental_causal_proposals'):
                    bank=bound(p[name]);names={o['catalog'] for o in bank['origins']};catalogs=[(f,bound(p[f])) for f in study.FIELDS if f in names];assert set(n for n,_ in catalogs)==names;lineage=check_proposals(s,bank,catalogs);ready=0
                    for core in bank['cores']:
                        cnf,_,key=s._canonical(core['source']);node=s._read(key,cnf)
                        if node is not None:assert node['answer'] is False;ready+=1
                    frontiers[name]=dict(binding=p[name],catalogs=len(catalogs),lineage=lineage,retained=len(bank['cores']),ready=ready,pending=len(bank['cores'])-ready)
        finally:s.close()
    assert frontiers==v['union_frontiers'];result=dict(passed=True,frontiers=frontiers,changed_checkpoint_fields=changed,added_checkpoint_fields=added,reference_archive_reused=True,seconds=time.perf_counter()-start);base.write(out/'frontier-check.json',result);print(base.encode(dict(prior_sources=443,prior_artifacts=count,prior_manifests=len(manifests),unchanged_frontiers=True,reference_archive_reused=True)),flush=True)


if __name__=='__main__':run(Path(sys.argv[1]))
