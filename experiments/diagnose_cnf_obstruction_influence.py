#!/usr/bin/env python3
"""Check already-acquired probe influence on saved renaming obstructions."""
from collections import Counter
import gzip
import hashlib
import json
from pathlib import Path
import sqlite3
import sys
import tempfile
import time

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments.cnf_residual_dag import restrict
from experiments.cnf_simplification import check_simplification
from experiments.cnf_polarity_horn import check_polarity
from experiments.cnf_pattern_inventory import encode


def main(directory):
    target=directory/'influence.json'
    if target.exists():raise FileExistsError(target)
    report_path=directory/'report.json';report=json.loads(report_path.read_text())
    changes_path=directory/'mechanisms.json';changes=json.loads(changes_path.read_text())['changes'];rows=[];counts=Counter()
    archive=next(a for a in report['archives'] if a['mode']=='baseline')
    raw=gzip.decompress(Path(archive['path']).read_bytes());assert hashlib.sha256(raw).hexdigest()==archive['database_sha256']
    with tempfile.TemporaryDirectory() as tmp:
        path=Path(tmp)/'a.db';path.write_bytes(raw);db=sqlite3.connect(f'file:{path}?mode=ro',uri=True)
        nodes={(n['depth'],encode(n['cnf'])):n for payload, in db.execute('SELECT payload FROM cnf_patterns_v1') for n in [json.loads(payload)]};db.close()
    started=time.perf_counter()
    for change in changes:
        for pair in change['matched_first_splits']:
            source=pair['cnf'];node=nodes[pair['depth'],encode(source)];obstruction=pair['certificate'];check_polarity(source,obstruction,counts)
            original=node['profile']['probing'].get('attempts',[])
            for variable in sorted(set(pair['winning']['baseline']+pair['winning']['obstruction'])):
                row=dict(case=change['case'],change=change['change'],variable=variable,
                    outside_obstruction_support=variable not in pair['obstruction_support'],branches=[])
                for value in (False,True):
                    attempt=next((a for a in original if a['variable']==variable and a['value']==value),None)
                    if attempt is None:
                        row['branches'].append(dict(value=value,outcome='not_preprobed'));continue
                    # Original-pass units use parent names (no normalization).
                    branch=restrict(source,{variable:value},counts)
                    _,units=check_simplification(branch,attempt['certificate'],counts,pure=False)
                    fixed={variable:value,**units};removed=[];direct=[]
                    for direction in ('forward','backward'):
                        for index,(_,cid,i,j) in enumerate(obstruction[direction]):
                            clause=source[cid]
                            def damaged(assignment):
                                return (any(assignment.get(abs(l))==(l>0) for l in clause if abs(l) in assignment)
                                        or abs(clause[i]) in assignment or abs(clause[j]) in assignment)
                            if damaged({variable:value}):direct.append([direction,index])
                            if damaged(fixed):removed.append([direction,index])
                    row['branches'].append(dict(value=value,outcome='checked_original_trace',certificate=attempt['certificate'],
                        fixed=sorted(fixed.items()),directly_damaged_edges=direct,closure_damaged_edges=removed,
                        fixed_obstruction_variables=sorted(set(fixed)&set(pair['obstruction_support']))))
                rows.append(row)
    output=dict(report_sha256=hashlib.sha256(report_path.read_bytes()).hexdigest(),
        changes_sha256=hashlib.sha256(changes_path.read_bytes()).hexdigest(),
        script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        diagnostic_seconds=time.perf_counter()-started,counts=dict(counts),rows=rows,
        limitations=['Only already-persisted original-pass probes are reused; no new propagation/search/discovery',
          'Every reused unit certificate is independently checked against its restricted original source, retaining parent variable names',
          'Missing traces are unmeasured, not evidence of no influence; learned-continuation traces are not substituted silently',
          'Damaging this saved path does not establish renamability or structural closure; other obstructions may survive',
          'This diagnostic changes no conditioning choices and establishes no coverage or runtime improvement',
          'Timing excludes loading/decompression/database indexing and result serialization'])
    target.write_text(json.dumps(output,indent=2)+'\n')
    print(json.dumps([dict(case=r['case'],variable=r['variable'],outside=r['outside_obstruction_support'],
        branches=[(b['outcome'],len(b.get('directly_damaged_edges',[])),len(b.get('closure_damaged_edges',[]))) for b in r['branches']]) for r in rows]),flush=True)


if __name__=='__main__':main(Path(sys.argv[1]))
