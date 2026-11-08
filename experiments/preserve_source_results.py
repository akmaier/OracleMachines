#!/usr/bin/env python3
"""Back up the live archive, revalidate old inputs, and retain source versions."""
import argparse
import hashlib
import json
from pathlib import Path
import sqlite3
import subprocess
import sys
import time

ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from solver.persistent import PersistentSolver,DEFAULT_CACHE


def quote(name):return '"'+name.replace('"','""')+'"'


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cache',type=Path,default=DEFAULT_CACHE)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    if args.output.exists():raise ValueError('Preserve the previous report; choose a new output')
    backup=args.cache.parent/'backups'/('before-source-updates-'+str(time.time_ns())+'.sqlite3')
    backup.parent.mkdir(parents=True,exist_ok=True)
    with sqlite3.connect(args.cache) as old,sqlite3.connect(backup) as saved:old.backup(saved)
    # sqlite3 context managers commit/rollback but do not close connections.
    old.close();saved.close()
    artifacts={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in
        subprocess.check_output(['git','ls-files','experiments/results'],cwd=ROOT,text=True).splitlines()}
    report=dict(backup=str(backup.relative_to(ROOT)),source_commit=subprocess.check_output(
        ['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),previous_artifacts=artifacts)
    clauses=[[x,-x-1] for x in range(1,9)]+[[-x,x+1] for x in range(1,9)]
    layers=[[x] for x in range(1,10)];versions=[]
    with PersistentSolver(args.cache) as service:
        report['before']=service.stats()
        report['revalidation']=service.revalidate()
        report['audit']=service.audit()
        previous_sources=[r[0] for r in service.db.execute(
            'SELECT DISTINCT id FROM source_states WHERE engine!=? ORDER BY id',(service.engine_id,))]
        report['previous_source_versions']=[]
        for state in previous_sources:
            checked=service.source_cnf(base=state)
            report['previous_source_versions'].append(dict(state=state,answer=checked['answer'],
                revalidated_source=checked['revalidated_source'],
                native_definitions=checked['source_updates']['native_definitions']))
        first=service.source_cnf(1,clauses,layers)
        versions.append(dict(kind='initial',state=first['state'],expected=True))
        edit=service.source_cnf(base=first['state'],replace={3:[[4],[-5]]})
        versions.append(dict(kind='edit',state=edit['state'],expected=True))
        negative=service.source_cnf(base=edit['state'],replace={4:[[]]})
        versions.append(dict(kind='negative',state=negative['state'],expected=False))
        deletion=service.source_cnf(base=negative['state'],replace={4:[]})
        versions.append(dict(kind='deletion',state=deletion['state'],expected=True))
        branch=service.source_cnf(base=first['state'],replace={0:[[-1],[2]]})
        versions.append(dict(kind='old_branch',state=branch['state'],expected=True))
        for row,result in zip(versions,[first,edit,negative,deletion,branch]):
            assert result['answer']==row['expected'],row
        report['after']=service.stats()
    with PersistentSolver(args.cache) as service:
        for row in versions:
            result=service.source_cnf(base=row['state'],witness=True)
            assert result['answer']==row['expected'],row
            row.update(restarted_answer=result['answer'],witness=result['witness'])
        report['source_versions']=versions
        service.db.execute('ATTACH DATABASE ? AS previous',(str(backup),))
        tables=[r[0] for r in service.db.execute("SELECT name FROM previous.sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")]
        preserved={}
        for table in tables:
            name=quote(table)
            count=service.db.execute('SELECT count(*) FROM previous.'+name).fetchone()[0]
            missing=service.db.execute('SELECT count(*) FROM (SELECT * FROM previous.'+name+' EXCEPT SELECT * FROM main.'+name+')').fetchone()[0]
            preserved[table]=dict(previous_rows=count,missing_or_changed=missing)
            assert missing==0,(table,missing)
        report['previous_rows']=preserved
        report['storage']=service.archive_usage()
    for path,digest in artifacts.items():assert hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==digest,path
    report['previous_artifacts_unchanged']=True
    args.output.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k not in ('previous_artifacts','source_versions','storage')}))


if __name__=='__main__':main()
