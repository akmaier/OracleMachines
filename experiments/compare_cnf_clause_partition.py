#!/usr/bin/env python3
"""Price first-false partitions on the three preserved multi-clause misses."""
from collections import Counter
from pathlib import Path
from unittest.mock import patch
import shutil,sys,tempfile,time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_premise_guard as previous
from experiments.cnf_clause_partition import branch_sources,publish_premise,make_record,check_record,PartitionBank
from experiments.cnf_guard_chain import make_record as chain_record,GuardChainBank
from experiments.cnf_premise_guard import PremiseGuardSelector
from experiments.cnf_snapshot_replay import SnapshotResidualSolver
from experiments.validate_cnf_unsat_support import bound
base=previous.base;binding=previous.binding;rows=previous.rows;ResidualSolver=previous.ResidualSolver
PARENT=Path('experiments/results/cnf-premise-guard');FIELDS=previous.FIELDS;OLD_FIELDS=previous.OLD_FIELDS
FILES=('experiments/cnf_clause_partition.py','solver/test_cnf_clause_partition.py','experiments/compare_cnf_clause_partition.py','experiments/validate_cnf_clause_partition.py')


def prefixes(initial,final,records):
    available=dict(initial);result={};by_hash={base.key_sha(k):k for k in final};assert len(by_hash)==len(final) and initial.items()<=final.items()
    for row in records:
        result[row['case']]=dict(available)
        for h in row['new_ids']:
            key=by_hash[h];assert key not in available;available[key]=final[key]
    assert available==final;return result


def prepare(s,p,row):
    bank,extensions,indices,prepared,cofactors=previous.setup(s,p);selector=previous.ordinary.AlternativeGuardSelector(p['alternative_budget'])
    target,normal,counts=previous.prepare(s,row['chain']['source'],p,bank,extensions,cofactors,selector)
    assert normal==row['ordinary'] and normal['guard'] is not None and not normal['target_known'] and normal['cofactor'] is None
    near=PremiseGuardSelector(prepared['cores']);choice,guard,child=near.select(s,target);assert choice is None and guard is None and child==target
    return target,normal['guard'],indices,prepared,dict(counts),dict(near.counts)


def audit_records(path,records,prepared,catalogs,indices):
    start=time.perf_counter();native=previous.ordinary.audit_portfolio(path,[],prepared,catalogs,indices);s=SnapshotResidualSolver(path)
    try:
        answers=[check_record(s,r)['answer'] for r in records];bank=PartitionBank(s,records)
        assert [bank.lookup(r['source'])['answer'] for r in records]==answers
    finally:s.close()
    return dict(native=native,partition_answers=answers,seconds=time.perf_counter()-start)


def plans(diagnosis):
    result=[]
    for row in diagnosis['cases']:
        result.append(dict(case=row['case'],mode='baseline',core=None,missing=None))
        for example in row['minima']['ready']['examples']:
            for order in ('forward','reverse'):
                missing=example['missing_clauses'];missing=missing if order=='forward' else list(reversed(missing))
                result.append(dict(case=row['case'],mode=f"core-{example['core']}-{order}",core=example['core'],missing=missing))
    return result


def run(out):
    out.mkdir(exist_ok=False);start=time.perf_counter();historical=base.load(PARENT/'protocol.json');authority=bound(historical['parent']);trial=base.load(PARENT/'premise-first-0/report.json');records=bound(trial['queries']);diagnosis=base.load(PARENT/'remaining-gaps.json')
    sources=dict(base.load(PARENT/'validation.json')['source_fingerprints'])
    for f,h in sources.items():assert base.sha(f)==h,f
    sources.update({f:base.sha(f) for f in FILES});schedule=plans(diagnosis)
    p=dict(parent=binding(PARENT/'checkpoint.json'),historical_protocol=binding(PARENT/'protocol.json'),historical_trial=binding(PARENT/'premise-first-0/report.json'),diagnosis=binding(PARENT/'remaining-gaps.json'),source_fingerprints=sources,plans=schedule,
        limitations=['Three historical cases, baseline plus forward/reverse orders for all nearest ready cores reported by the prior diagnosis. Eleven single-sample arms, exact persistent pre-query prefixes and cold live caches. No fresh coverage, minimum-cost selection or stable runtime claim.',
            'All arms repeat ordinary preparation and the failed one-clause selector. Partition arms first check or derive the strengthened negative premise, then solve disjoint first-false branches sequentially, sharing the same native archive and stopping at the first SAT child.',
            'Discovery is inherited from the separately charged prior probe, not an efficient plan oracle. Trying both orders is diagnostic acquisition; a best observed arm is not a deployed selector.',
            'Open, preparation, premise, branch construction/solving, composition, warm-bank setup/lookup, serialization and full cold native/sidecar/lineage replay are reported. Prefix reconstruction and full-row snapshot/export overhead remain in aggregate study time. No peak RSS or downstream stream effects measured.',
            'Native proof formats stay unchanged. Partition conclusions require the bound sidecars and PartitionBank; the native source root need not exist.'])
    base.write(out/'protocol.json',p);samples=[]
    bindings=dict(legacy=historical['support_index'],causal=historical['causal_index']);indices={n:bound(e) for n,e in bindings.items()};prepared=previous.ordinary.compose(indices,bindings);cores=prepared['cores'];catalogs=[(n,bound(authority[n])) for n in OLD_FIELDS]
    with tempfile.TemporaryDirectory() as td:
        tmp=Path(td)
        def read(entry,name):
            path=tmp/name;base.restore_archive(entry,path);s=ResidualSolver(path)
            try:return rows(s)
            finally:s.close()
        initial=read(authority['reference_union'],'initial');final=read(trial['archive'],'final');tick=time.perf_counter();saved_prefixes=prefixes(initial,final,records);prefix_seconds=time.perf_counter()-tick
        for plan in schedule:
            cid=plan['case'];before=saved_prefixes[cid];old=next(r for r in records if r['case']==cid);dest=out/f"{cid}-{plan['mode']}";dest.mkdir();path=tmp/'arm';shutil.copyfile(tmp/'initial',path);tick=time.perf_counter();s=previous.ordinary.AccountedResidualSolver(path)
            with s.db:s.db.executemany('INSERT INTO cnf_residual_v1 VALUES (?,?)',[(k,v) for k,v in before.items() if k not in initial])
            open_seconds=time.perf_counter()-tick
            try:
                tick=time.perf_counter();target,guard,_,_,normal_counts,near_counts=prepare(s,historical,old);preparation_seconds=time.perf_counter()-tick;assert rows(s)==before
                premise_counts=Counter();old_counts=Counter(s.counts);premise_seconds=0.;inserted=False;branch_counts=Counter();children=[];branches=[]
                if plan['core'] is not None:
                    tick=time.perf_counter()
                    with patch.object(s,'_expand',side_effect=AssertionError('Premise search')):inserted,root=publish_premise(s,target,cores[plan['core']],plan['missing'],premise_counts)
                    premise_seconds=time.perf_counter()-tick
                premise_solver_counts=dict(s.counts-old_counts);tick=time.perf_counter()
                branches=[(target,{},target)] if plan['core'] is None else branch_sources(target,plan['missing'],branch_counts)[1]
                construction_seconds=time.perf_counter()-tick;branch_reports=[]
                for i,(_,_,child_source) in enumerate(branches):
                    tick=time.perf_counter();child=s.solve(child_source);children.append(child)
                    branch_reports.append(dict(index=i,root=child['root'],answer=child['answer'],metrics=child['metrics'],seconds=time.perf_counter()-tick))
                    if child['answer']:break
                tick=time.perf_counter()
                record=chain_record(s,old['chain']['source'],[guard],children[0]) if plan['core'] is None else make_record(s,old['chain']['source'],[guard],plan['missing'],root,children)
                composition_seconds=time.perf_counter()-tick;assert record['answer']==old['chain']['answer'];after=rows(s);assert before.items()<=after.items();delta=[(k,v) for k,v in after.items() if k not in before]
                if plan['core'] is None:assert set(map(base.key_sha,dict(delta)))==set(old['new_ids']) and all(final[k]==v for k,v in delta)
                with patch.object(s,'_expand',side_effect=AssertionError('Warm search')),patch.object(s,'_store',side_effect=AssertionError('Warm publication')):
                    tick=time.perf_counter();bank=(GuardChainBank if plan['core'] is None else PartitionBank)(s,[record]);warm_setup_seconds=time.perf_counter()-tick
                    tick=time.perf_counter();warm=bank.lookup(old['chain']['source']);warm_seconds=time.perf_counter()-tick
                assert warm['answer']==record['answer'] and rows(s)==after
            finally:s.close()
            tick=time.perf_counter();base.write(dest/'delta.json',delta);base.write(dest/'records.json',[record]);serialization_seconds=time.perf_counter()-tick
            cold=previous.prior.audit_chain(path,[record],prepared,catalogs,indices) if plan['core'] is None else audit_records(path,[record],prepared,catalogs,indices)
            result=dict(plan=plan,prefix_nodes=len(before),prefix_digest=base.key_sha(base.encode(sorted(before.items()))),delta=binding(dest/'delta.json'),records=binding(dest/'records.json'),
                new_nodes=len(delta),new_payload_units=sum(len(k)+len(v) for k,v in delta),retained_bytes=(dest/'delta.json').stat().st_size+(dest/'records.json').stat().st_size,
                expanded_nodes=sum(c['metrics'].get('expanded_nodes',0) for c in children),premise_inserted=inserted,answer=record['answer'],branch_reports=branch_reports,
                normal_counts=normal_counts,near_counts=near_counts,premise_counts=dict(premise_counts),premise_solver_counts=premise_solver_counts,branch_counts=dict(branch_counts),
                open_seconds=open_seconds,preparation_seconds=preparation_seconds,premise_seconds=premise_seconds,construction_seconds=construction_seconds,composition_seconds=composition_seconds,
                warm_setup_seconds=warm_setup_seconds,warm_seconds=warm_seconds,serialization_seconds=serialization_seconds,cold=cold,row_digest=base.key_sha(base.encode(sorted(after.items()))))
            base.write(dest/'report.json',result);samples.append(binding(dest/'report.json'));print(base.encode(dict(plan=plan,expansions=result['expanded_nodes'],new_nodes=len(delta),payload=result['new_payload_units'])),flush=True)
    base.write(out/'report.json',dict(protocol=binding(out/'protocol.json'),samples=samples,prefix_seconds=prefix_seconds,seconds=time.perf_counter()-start))


if __name__=='__main__':run(Path(sys.argv[1]))
