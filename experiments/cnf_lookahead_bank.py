"""Optional checked probe persistence for bounded cofactor lookahead.

Only explicit scouting writes the bank. Ordinary acquisition may reuse an entry
but otherwise follows the frozen planner. Probe evidence depends on the exact
canonical CNF and full policy, not remaining conditioning depth; every hit is
rechecked before use. Pattern formats and old archives remain unchanged.
"""
import json
from experiments.cnf_complete_admission import CompleteAdmissionInventory
from experiments.cnf_pattern_inventory import encode,classify
from experiments.cnf_residual_dag import normalize,components

TABLE='cnf_lookahead_probes_v1'
FORMAT='checked-lookahead-probes-v1'


class LookaheadInventory(CompleteAdmissionInventory):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        self.db.execute(f'CREATE TABLE IF NOT EXISTS {TABLE} (id TEXT PRIMARY KEY,payload TEXT NOT NULL)')
        self.db.commit();self._scouting=False;self.reuse_probe_bank=True

    def _bank_key(self,cnf):
        key=encode([FORMAT,self.config,cnf])
        self.counts['lookahead_bank_key_bytes']+=len(key.encode())
        return key

    def check_bank_row(self,key,payload):
        try:
            identity=json.loads(key);result=json.loads(payload)
            if (type(identity) is not list or len(identity)!=3 or identity[0]!=FORMAT
                    or encode(identity[1])!=encode(self.config)):
                raise ValueError('Foreign lookahead policy')
            cnf,_=normalize(identity[2],self.counts)
            if encode(cnf)!=encode(identity[2]) or self._bank_key(cnf)!=key:
                raise ValueError('Noncanonical lookahead source')
            self._check_probes(cnf,result)
        except (TypeError,KeyError,IndexError,AttributeError) as exc:
            raise ValueError('Malformed lookahead proof') from exc
        self.counts['lookahead_bank_verified']+=1
        return result

    def _discover_probes(self,cnf):
        key=self._bank_key(cnf)
        row=None
        if self.reuse_probe_bank or self._scouting:
            row=self.db.execute(f'SELECT payload FROM {TABLE} WHERE id=?',(key,)).fetchone()
            self.counts['lookahead_bank_lookups']+=1
        if row is not None:
            self.counts['lookahead_bank_read_bytes']+=len(row[0].encode())
            result=self.check_bank_row(key,row[0]);self.counts['lookahead_bank_hits']+=1
            return result
        result=super()._discover_probes(cnf)
        if self._scouting:
            payload=encode(result);self.check_bank_row(key,payload)
            with self.db:self.db.execute(f'INSERT INTO {TABLE} VALUES (?,?)',(key,payload))
            self.counts['lookahead_bank_inserted']+=1
            self.counts['lookahead_bank_written_bytes']+=len(key.encode())+len(payload.encode())
        return result

    def scout(self,source,depth):
        """One admitted profile; no recursive acquisition or inferred closure bit."""
        if type(depth) is not int or not 0<=depth<=self.config['max_depth']:
            raise ValueError('Invalid lookahead depth')
        cnf,_,key=self._canonical(source,depth)
        existing=self._load(key)
        if existing is not None:
            self.counts['lookahead_saved_profiles']+=1
            if existing['summary']['closed']:
                return dict(source_key=key,probe_status='already_covered',target_variables=0,
                    recognized_components=0,unresolved_components=0,max_unresolved_variables=0,unresolved_literals=0)
            profile=existing['profile']
        else:
            self._admit(key,'lookahead')
            previous=self._scouting;self._scouting=True
            try:profile=self._profile(cnf)
            finally:self._scouting=previous
        target=cnf
        if self._uses_probe(profile):target,_=self._check_probes(cnf,profile['probing'])
        elif self._uses_simplification(profile,components(cnf,self.counts)):
            target,_=self._simplified(cnf,profile)
        target,_=normalize(target,self.counts)
        unresolved=[];recognized=0
        for group in components(target,self.counts):
            p=classify(group,self.config['parity_width'],self.counts)
            if any(v=='recognized' for v in p['outcomes'].values()):recognized+=1
            else:unresolved.append(group)
        return dict(source_key=key,probe_status=profile['probing']['status'],
            target_variables=len({abs(l) for c in target for l in c}),
            recognized_components=recognized,unresolved_components=len(unresolved),
            max_unresolved_variables=max((len({abs(l) for c in g for l in c}) for g in unresolved),default=0),
            unresolved_literals=sum(sum(map(len,g)) for g in unresolved))


def scout_candidates(h,ranked):
    """Rank both polarities by one checked profile each; return all observations."""
    from experiments.cnf_trace_split import verify
    from collections import Counter
    result=[]
    for row in ranked:
        targets,_=verify(h,row['record'],Counter());depth=h._load(row['record']['source'])['depth']
        observations=[h.scout(target,depth) for target in targets]
        score=[sum(x['unresolved_components'] for x in observations),
            max(x['max_unresolved_variables'] for x in observations),
            sum(x['unresolved_literals'] for x in observations),*row['rank']]
        result.append(dict(record=row['record'],old_rank=row['rank'],score=score,observations=observations))
    return sorted(result,key=lambda x:(x['score'],encode(x['record'])))
