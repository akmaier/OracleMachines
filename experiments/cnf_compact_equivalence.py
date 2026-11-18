"""Version-two equivalence evidence without duplicated source/child formulas.

The full native source key remains the exact identity. Its canonical source and
checked substitution uniquely reconstruct the native negative dependency.
Version-one rows remain readable and are never implicitly rewritten or deleted.
"""
import json,time
from experiments.cnf_binary_equivalence import (
    BinaryEquivalenceSolver,EquivalenceStore,check_substitution,
    FORMAT as LEGACY_FORMAT,TABLE as LEGACY_TABLE)
from experiments.cnf_targeted_backbone import AccountedTargetedBackboneSolver
from experiments.cnf_residual_dag import FORMAT as NATIVE_FORMAT

FORMAT='binary-equivalence-negative-v2'
TABLE='cnf_binary_equivalence_v2'


def source_from_key(s,key):
    prefix=NATIVE_FORMAT+':'
    if type(key) is not str or not key.startswith(prefix):raise ValueError('Invalid compact source key')
    s.counts['equiv_compact_key_parse_bytes']+=len(key.encode())
    try:source=json.loads(key[len(prefix):])
    except (ValueError,TypeError) as e:raise ValueError('Invalid source-key JSON') from e
    if type(source) is not list or any(type(c) is not list for c in source):raise ValueError('Invalid source-key clauses')
    cnf,_,actual=s._canonical(source)
    if key!=actual or source!=[list(c) for c in cnf]:raise ValueError('Noncanonical compact source key')
    return cnf


def dependency(s,key,node):
    """Check compact evidence and reconstruct a native-only dependency."""
    if (type(node) is not dict or set(node)!={'format','answer','evidence'}
            or node['format']!=FORMAT or node['answer'] is not False):raise ValueError('Invalid compact equivalence node')
    cnf=source_from_key(s,key);target,_=check_substitution(cnf,node['evidence'],s.counts)
    expected,_,child=s._canonical(target)
    result=s._read(child,expected,purpose='certificate')
    if result is None or result['answer'] is not False:raise ValueError('Missing checked native UNSAT quotient')
    s.counts['equiv_compact_nodes_checked']+=1
    return cnf,child


class CompactEquivalenceStore:
    def __init__(self,solver,*,create=False):
        self.solver=solver;self.checked={};self.legacy=EquivalenceStore(solver)
        if create:
            solver.db.execute(f'CREATE TABLE IF NOT EXISTS {TABLE} (id TEXT PRIMARY KEY,payload TEXT NOT NULL)');solver.db.commit()
        self.tables={r[0] for r in solver.db.execute('SELECT name FROM sqlite_master WHERE type=? AND name IN (?,?)',('table',TABLE,LEGACY_TABLE))}

    def verify(self,key,node):
        if type(node) is dict and node.get('format')==LEGACY_FORMAT:return self.legacy.verify(key,node)
        dependency(self.solver,key,node);return node

    def read(self,key):
        s=self.solver
        if key in self.checked:s.counts['equiv_compact_memory_hits']+=1;return self.checked[key]
        if TABLE in self.tables:
            s.counts['equiv_compact_database_lookups']+=1
            row=s.db.execute(f'SELECT payload FROM {TABLE} WHERE id=?',(key,)).fetchone()
            if row is not None:
                s.counts['equiv_compact_read_bytes']+=len(row[0].encode())
                node=json.loads(row[0])
                # A v2 row cannot smuggle a v1 payload into the new namespace.
                dependency(s,key,node);self.checked[key]=node;return node
        if LEGACY_TABLE in self.tables:
            node=self.legacy.read(key)
            if node is not None:self.checked[key]=node
            return node
        return None

    def publish(self,key,cnf,evidence,child):
        s=self.solver;node=dict(format=FORMAT,answer=False,evidence=evidence)
        expected,derived=dependency(s,key,node)
        if cnf!=expected or child!=derived:raise ValueError('Publication source or dependency mismatch')
        payload=json.dumps(node,sort_keys=True,separators=(',',':'))
        s.counts['equiv_compact_serialized_bytes']+=len(payload.encode())
        with s.db:cursor=s.db.execute(f'INSERT OR IGNORE INTO {TABLE} VALUES (?,?)',(key,payload))
        if cursor.rowcount:
            s.counts['equiv_compact_inserted_nodes']+=1;s.counts['equiv_compact_inserted_bytes']+=len(key)+len(payload)
            self.checked[key]=node
        else:
            self.checked.pop(key,None);node=self.read(key)
        return node


class CompactBinaryEquivalenceSolver(BinaryEquivalenceSolver):
    def __init__(self,*args,**kwargs):
        AccountedTargetedBackboneSolver.__init__(self,*args,**kwargs)
        self.equivalences=CompactEquivalenceStore(self,create=True)

    def solve(self,source):
        began=time.perf_counter();result=super().solve(source)
        if result['authority']==LEGACY_FORMAT:
            result['authority']=self.equivalences.checked[result['root']]['format']
        result['seconds']=time.perf_counter()-began
        return result
