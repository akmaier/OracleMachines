#!/usr/bin/env python3
"""Account for actual path sharing, direct-only overlap and changed coverage."""
from collections import Counter
import gzip
import hashlib
import json
from pathlib import Path
import sqlite3
import sys
import tempfile

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments.cnf_pattern_inventory import encode


def main(directory):
    target=directory/'mechanisms.json'
    if target.exists():raise FileExistsError(target)
    path=directory/'report.json';report=json.loads(path.read_text());rows=[];by_mode=[]
    for archive in report['archives']:
        counts=Counter();raw=gzip.decompress(Path(archive['path']).read_bytes())
        assert hashlib.sha256(raw).hexdigest()==archive['database_sha256'] and archive['audit']['bytes_unchanged']
        with tempfile.TemporaryDirectory() as tmp:
            dbpath=Path(tmp)/'a.db';dbpath.write_bytes(raw);db=sqlite3.connect(f'file:{dbpath}?mode=ro',uri=True)
            for key,payload in db.execute('SELECT id,payload FROM cnf_patterns_v1'):
                node=json.loads(payload);cert=node.get('binary_paths')
                if cert is None:continue
                counts['proposal_nodes']+=1;counts['all_proposal_bytes']+=len(encode(cert).encode())
                if not cert['removed']:continue
                binary=[set(c) for c in node['cnf'] if len(c)==2];expanded=[];roots=[]
                for step in cert['proof']:
                    if len(step)==1:roots.append(step[0]);expanded.append([])
                    else:
                        parent,lit,cid=step;roots.append(roots[parent]);expanded.append(expanded[parent]+[[lit,cid]])
                flat=[];local=Counter()
                for cid,end in cert['removed']:
                    target_clause=set(node['cnf'][cid])
                    local['direct_possible' if any(c<=target_clause for c in binary) else 'transitive_only']+=1
                    local['removed_literals']+=len(target_clause)
                    local['independent_path_nodes']+=len(expanded[end])+1
                    flat.append([cid,roots[end],expanded[end]])
                local.update(rewrite_nodes=1,removed_clauses=len(cert['removed']),shared_proof_nodes=len(cert['proof']),
                             shared_certificate_bytes=len(encode(cert).encode()),independent_certificate_bytes=len(encode(flat).encode()))
                counts.update(local)
                rows.append(dict(mode=archive['mode'],key_sha256=hashlib.sha256(key.encode()).hexdigest(),
                                 shape=node['profile']['shape'],depth=node['depth'],closed=node['summary']['closed'],**local))
            db.close()
        by_mode.append(dict(mode=archive['mode'],**counts))
    records={(r['mode'],r['case']):r for r in report['records']};changes=[]
    for i in range(len(report['cases'])):
        a,b=(records[m,i] for m in ('baseline','binary_paths'))
        if a['discovery']['summary']['closed']!=b['discovery']['summary']['closed']:
            changes.append(dict(case=i,source=report['cases'][i],answer=a['answer'],
                change='gain' if b['discovery']['summary']['closed'] else 'loss',
                baseline=a['discovery']['summary'],binary_paths=b['discovery']['summary']))
    output=dict(report_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
        script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),counts=by_mode,changes=changes,rows=rows,
        limitations=['Counts every persisted reduction, including failed alternatives; not distinct original-source gains',
          'Direct possible means a retained original binary clause already subsumes that removed wide clause',
          'Independent encoding is [wide_clause_id, root_literal, [[next_literal, binary_clause_id], ...]] per witness',
          'The shared format may use more bytes despite fewer repeated path nodes; both are measured',
          'Full parent sources, reduced children and versioned keys remain stored, beyond this proof-only comparison',
          'This read-only diagnostic uses complete cold-checked archives and makes no acquisition timing claim'])
    target.write_text(json.dumps(output,indent=2)+'\n');print(json.dumps(dict(counts=by_mode,changes=[(r['case'],r['change']) for r in changes])),flush=True)


if __name__=='__main__':main(Path(sys.argv[1]))
