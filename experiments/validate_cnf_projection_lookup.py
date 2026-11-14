#!/usr/bin/env python3
"""Cold membership, search and proof replay for the projection proposal index."""
from collections import Counter
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import time
import zlib
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))

from experiments.compare_cnf_projection_lookup import (BASE, restore_checkpoint, read_archive,
    sha, unpack, routes_for, full, BudgetedInventory, encode_json)
from experiments.cnf_projection_lookup import KernelIndex, search, signature
from experiments.cnf_projection_bridge import verify, record_key, verify_positive
from experiments.cnf_pattern_inventory import FORMAT, encode
from experiments.cnf_implied_subsumption import indexed_certificate


def validate(out):
    start=time.perf_counter();r=json.loads((out/'report.json').read_text())
    result=dict(report_sha256=sha(out/'report.json'))
    with tempfile.TemporaryDirectory() as td,patch.object(BudgetedInventory,'_discover',side_effect=AssertionError('fresh recognition')):
        tmp=Path(td);tick=time.perf_counter();restored,*evidence=restore_checkpoint(out/'report.json',tmp/'history',tmp)
        assert restored==r;result['restore_seconds']=time.perf_counter()-tick
        before=sha(tmp/'history');h=BudgetedInventory(tmp/'history',**r['options']);h.set_admission_budget(0)
        index=None
        try:
            d=r['index'];assert sha(d['path'])==d['sha256'];unpack(d['path'],tmp/'index',d['database_sha256'])
            tick=time.perf_counter();index=KernelIndex(tmp/'index',h.config);seen=set();counts=Counter()
            for ident,sig,clauses,payload in index.db.execute('SELECT id,kernel,clauses,payload FROM targets ORDER BY id'):
                key=zlib.decompress(payload).decode();assert hashlib.sha256(key.encode()).digest()==ident
                fmt,config,depth,cnf=json.loads(key);assert fmt==FORMAT and config==h.config and clauses==len(cnf)
                # Independent length-ordered subset scan, without anchor postings.
                cert=indexed_certificate(cnf,counts);core=[cnf[i] for i in cert['kept']]
                support=len({abs(l) for c in cnf for l in c})
                assert signature(depth,support,core,counts)==sig
                assert h.db.execute('SELECT 1 FROM cnf_patterns_v1 WHERE id=?',(key,)).fetchone()
                assert ident not in seen;seen.add(ident)
            expected={hashlib.sha256(key.encode()).digest() for key, in h.db.execute('SELECT id FROM cnf_patterns_v1')
                      if json.loads(key)[1]==h.config}
            assert seen==expected and len(seen)==r['index_build']['entries']
            result.update(index_entries=len(seen),index_complete_for_snapshot=True,
                independent_index_check_seconds=time.perf_counter()-tick,index_check_counts=dict(counts))
            sources=read_archive(r['sources']);parent=json.loads(BASE.read_text());selected=read_archive(parent['next_selection'])
            assert sources==[x['source'] for x in selected['navigation']['ranked_sources']]+[read_archive(parent['bridges'])[0]['source']]
            reference=None
            for arm in r['arms']:
                rows=read_archive(arm['results']);assert len(rows)==len(sources)
                logical=[]
                for key,row in zip(sources,rows,strict=True):
                    assert hashlib.sha256(key.encode()).hexdigest()==row['source_sha256']
                    assert row['counts'].get('projection_variables',0)<=64 and row['counts'].get('target_candidate_entries',0)<=64
                    for record in row['records']:
                        assert record['source']==key;verify(h,record,Counter())
                    logical.append([record_key(x) for x in row['records']])
                if reference is None:reference=logical
                else:assert logical==reference
            tick=time.perf_counter();replayed=[[record_key(x) for x in search(h,key,index,Counter())] for key in sources]
            assert replayed==reference
            result.update(cold_search_seconds=time.perf_counter()-tick,sources=len(sources),
                matched_all_modes_and_repeats=True,discovered_bridges=sum(map(len,reference)),
                frontier_sources_with_bridge=sum(bool(x) for x in reference[:-1]),known_control_has_bridge=bool(reference[-1]))
            bridges=read_archive(r['bridges']);roots=[h._canonical(c['source'],h.config['max_depth'])[2] for c in r['cases']]
            tick=time.perf_counter();routes=routes_for(h,evidence,bridges);closed,_,_=full(h,roots,routes)
            assert closed==[r['final_closed'],r['without_growth_closed']]
            result['global_coverage_seconds']=time.perf_counter()-tick
            claimed=[k for k,b in zip(roots,closed[0],strict=True) if b]
            verify_positive(h,read_archive(r['expanded_certificate']),claimed,evidence,bridges,Counter())
            assert not h.admitted
        finally:
            if index:index.close()
            h.close()
        assert sha(tmp/'history')==before
    result.update(passed=True,seconds=time.perf_counter()-start,authority_unchanged=True,
                  covered=sum(r['final_closed']),gains=r['gains'])
    (out/'reconstruction.json').write_text(encode_json(result))
    print(json.dumps({k:result[k] for k in ('passed','sources','discovered_bridges','frontier_sources_with_bridge','covered','seconds')}),flush=True)


if __name__=='__main__':validate(Path(sys.argv[1]))
