"""Exact binary-core discovery reuse for the optional compact quotient API.

A discovery entry is not a SAT certificate. Every selected tree is transported
back to current source clauses and checked before substitution; persisted cache
outcomes (including misses) are recomputed once on first use after restart.
Native/extension certificate formats and recursive search remain unchanged.
"""
from collections import Counter
import json,time
from experiments.cnf_binary_equivalence import discover,check_substitution
from experiments.cnf_compact_equivalence import CompactBinaryEquivalenceSolver,FORMAT
from experiments.cnf_residual_dag import FORMAT as NATIVE_FORMAT,holds

FORMAT_CACHE='binary-core-discovery-v1'
TABLE='cnf_binary_core_discovery_v1'


def encode(value):return json.dumps(value,sort_keys=True,separators=(',',':'))


def core_key(core):return FORMAT_CACHE+':'+encode(core)


def compute(core,counts):
    # The unchanged recognizer ignores all wide-clause literals: one wide clause
    # supplies only its mixed-source gate. Binary clause indices are now local.
    return discover(core+((1,2,3),),counts)


def parse_key(key):
    prefix=FORMAT_CACHE+':'
    if type(key) is not str or not key.startswith(prefix):raise ValueError('Invalid binary-core key')
    try:raw=json.loads(key[len(prefix):])
    except (ValueError,TypeError) as e:raise ValueError('Invalid binary-core JSON') from e
    if type(raw) is not list or not raw:raise ValueError('Missing binary core')
    for c in raw:
        if (type(c) is not list or len(c)!=2 or any(type(l) is not int or not l for l in c)
                or c!=sorted(c) or abs(c[0])==abs(c[1])):raise ValueError('Invalid binary clause')
    core=tuple(tuple(c) for c in raw)
    if core!=tuple(sorted(set(core))) or key!=core_key(core):raise ValueError('Noncanonical binary core')
    return core


def transport(evidence,ids,counts):
    if evidence is None:return None
    counts['equiv_cache_transport_edges']+=len(evidence['forward'])+len(evidence['backward'])
    return dict(representative=evidence['representative'],**{
        name:[[a,b,ids[cid]] for a,b,cid in evidence[name]] for name in ('forward','backward')})


class BinaryCoreCache:
    def __init__(self,solver,*,persistent=True,create=False):
        self.solver=solver;self.persistent=persistent;self.checked={}
        if persistent and create:
            solver.db.execute(f'CREATE TABLE IF NOT EXISTS {TABLE} (id TEXT PRIMARY KEY,payload TEXT NOT NULL)');solver.db.commit()
        self.exists=bool(persistent and solver.db.execute('SELECT 1 FROM sqlite_master WHERE name=?',(TABLE,)).fetchone())

    def verify(self,key,payload):
        """Recompute cold entries, so even null outcomes retain exact policy semantics."""
        counts=self.solver.counts;counts['equiv_cache_validation_bytes']+=len(key.encode())+len(payload.encode())
        core=parse_key(key);local=Counter();expected=compute(core,local)
        counts.update({'equiv_cache_validation_'+k:v for k,v in local.items()})
        if payload!=encode(expected):raise ValueError('Binary-core discovery outcome mismatch')
        counts['equiv_cache_validated_entries']+=1
        return expected

    def find(self,cnf):
        s=self.solver;c=s.counts;c['equiv_cache_calls']+=1;ids=[];wide=False
        for cid,clause in enumerate(cnf):
            c['equiv_cache_source_clause_scans']+=1
            if len(clause)<2:return None
            if len(clause)==2:ids.append(cid)
            else:wide=True
        if not ids or not wide:return None
        core=tuple(cnf[cid] for cid in ids);key=core_key(core)
        c['equiv_cache_key_literal_units']+=2*len(core);c['equiv_cache_key_bytes']+=len(key.encode())
        if key in self.checked:
            c['equiv_cache_memory_hits']+=1;evidence=self.checked[key]
        else:
            row=None
            if self.exists:
                c['equiv_cache_database_lookups']+=1
                row=s.db.execute(f'SELECT payload FROM {TABLE} WHERE id=?',(key,)).fetchone()
            if row is not None:
                evidence=self.verify(key,row[0]);c['equiv_cache_cold_hits']+=1
            else:
                c['equiv_cache_misses']+=1;evidence=compute(core,c)
                if self.persistent:
                    payload=encode(evidence);c['equiv_cache_serialized_bytes']+=len(payload.encode())
                    with s.db:cursor=s.db.execute(f'INSERT OR IGNORE INTO {TABLE} VALUES (?,?)',(key,payload))
                    if cursor.rowcount:
                        c['equiv_cache_inserted_entries']+=1;c['equiv_cache_inserted_bytes']+=len(key.encode())+len(payload.encode())
                    else:
                        # Respect a retained row if another publisher won the insert.
                        retained=s.db.execute(f'SELECT payload FROM {TABLE} WHERE id=?',(key,)).fetchone()[0]
                        evidence=self.verify(key,retained)
            self.checked[key]=evidence
        if evidence is None:c['equiv_cache_null_outcomes']+=1
        else:c['equiv_cache_selected_blocks']+=1
        return transport(evidence,ids,c)


class CachedBinaryEquivalenceSolver(CompactBinaryEquivalenceSolver):
    def __init__(self,*args,persistent_cache=True,**kwargs):
        super().__init__(*args,**kwargs)
        self.binary_cores=BinaryCoreCache(self,persistent=persistent_cache,create=True)

    def solve(self,source):
        # Same acquisition/recomposition as BinaryEquivalenceSolver.solve; only
        # discovery is routed through exact core reuse. No global monkeypatch.
        began=time.perf_counter();self.counts=Counter();cnf,names,root=self._canonical(source)
        native=self._read(root,cnf) if self.reuse else None;authority='native';model=None
        if native is not None:
            if native['answer']:model=dict(enumerate(native['model'],1))
        elif self.reuse and self.equivalences.read(root) is not None:
            authority=self.equivalences.checked[root]['format']
        else:
            evidence=self.binary_cores.find(cnf) if self.leaves else None
            if evidence is None:model,_=self._visit(cnf)
            else:
                target,mapping=check_substitution(cnf,evidence,self.counts)
                child_model,child=self._visit(target)
                if child_model is None:
                    self.equivalences.publish(root,cnf,evidence,child);authority=FORMAT
                else:
                    model={v:False for v in range(1,len(names)+1)};model.update(child_model)
                    for variable,signed in mapping.items():model[variable]=model[abs(signed)] if signed>0 else not model[abs(signed)]
                    if not holds(cnf,model):raise ValueError('Invalid equivalence model lift')
                    self.counts['equiv_positive_lifts']+=1;self.counts['equiv_lift_variables']+=len(mapping)
                    self._store(root,dict(format=NATIVE_FORMAT,cnf=[list(c) for c in cnf],answer=True,model=[model[v] for v in range(1,len(names)+1)]))
        external=None if model is None else {old:model.get(i,False) for i,old in enumerate(names,1)}
        if external is not None and not holds(source,external):raise ValueError('Invalid source witness')
        self.counts['source_witness_literal_payload']+=sum(map(len,source)) if external is not None else 0
        nodes,payload=self.archive_storage()
        return dict(answer=external is not None,model=external,root=root,authority=authority,metrics=dict(self.counts),
            seconds=time.perf_counter()-began,archive_nodes=nodes,archive_payload_bytes=payload)
