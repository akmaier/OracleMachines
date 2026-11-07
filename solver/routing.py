"""Failure-aware routing over a recent window; historical evidence is retained.

Scores charge elapsed time and a query-budget penalty for every failed request,
per completed answer. An observed route with no successes has no finite score.
Periodic exploration can retry it. This policy supplies no regret guarantee.
"""
import time
import hashlib
import json
from solver.incremental import parse_postfix
from solver.resources import Deadline, BudgetExceeded


class Router:
    routes = ('checked', 'interfaces')

    @staticmethod
    def create(db):
        db.execute('''CREATE TABLE IF NOT EXISTS route_observations (
            engine TEXT NOT NULL, bucket INTEGER NOT NULL, route TEXT NOT NULL,
            elapsed_ns INTEGER NOT NULL, success INTEGER NOT NULL,
            created_ns INTEGER NOT NULL)''')
        db.execute('''CREATE INDEX IF NOT EXISTS route_by_bucket
            ON route_observations(engine,bucket,route)''')
        db.execute('''CREATE TABLE IF NOT EXISTS route_totals (
            engine TEXT NOT NULL, bucket INTEGER NOT NULL, route TEXT NOT NULL,
            count INTEGER NOT NULL, total_ns INTEGER NOT NULL,
            PRIMARY KEY(engine,bucket,route))''')

    def __init__(self, db, namespace, engine=None):
        self.db, self.namespace = db, namespace
        self.engine=engine or namespace

    def profile(self,bits,deadline,max_interface):
        local=Deadline(min(0.1,deadline.remaining()*0.1)) if deadline else Deadline(0.1)
        try:
            nodes,root=parse_postfix(bits,local)
            supports=[];starts=[];variables=set()
            for i,node in enumerate(nodes):
                local.check()
                if node[0]=='var':scope={node[1]};variables.add(node[1]);start=i
                elif node[0]=='false':scope=set();start=i
                elif node[0]=='not':scope=supports[node[1]];start=starts[node[1]]
                else:
                    a,b=supports[node[1]],supports[node[2]]
                    scope=None if a is None or b is None else a|b
                    start=starts[node[1]]
                supports.append(scope if scope is None or len(scope)<=max_interface+1 else None)
                starts.append(start)
            terms=[];stack=[root]
            while stack:
                local.check();i=stack.pop()
                if nodes[i][0]=='and':stack.extend(nodes[i][1:])
                else:terms.append(i)
            neighbors={v:set() for v in variables};reused=0
            for i in terms:
                scope=supports[i]
                if scope is None:return dict(complete=True,reject=True,reason='leaf_width',variables=len(variables),terms=len(terms))
                for v in scope:neighbors[v].update(scope-{v})
            for i in terms[:8]:
                local.check();parts=[]
                for n in nodes[starts[i]:i+1]:
                    parts.append('01'+'1'*n[1]+'0' if n[0]=='var' else {'false':'00','not':'10','and':'11'}[n[0]])
                definition=dict(kind='leaf',bits=''.join(parts),scope=sorted(supports[i]))
                token=hashlib.sha256(json.dumps(definition,sort_keys=True,separators=(',',':')).encode()).hexdigest()
                reused+=self.db.execute('SELECT 1 FROM interface_nodes WHERE engine=? AND id=?',(self.engine,token)).fetchone() is not None
            degrees=[len(n) for n in neighbors.values()]
            minimum=min(degrees,default=0)
            return dict(complete=True,reject=minimum>max_interface,reason='initial_degree' if minimum>max_interface else 'candidate',
                variables=len(variables),terms=len(terms),minimum_degree=minimum,
                density_bucket=min(15,sum(degrees)//max(1,len(degrees))),reusable_sample=reused,
                sampled_terms=min(8,len(terms)))
        except BudgetExceeded:
            if deadline:deadline.check()
            return dict(complete=False,reject=True,reason='profile_budget')

    def choose(self, bits, deadline=None, max_interface=3):
        failure_budget_ns=int((deadline.remaining() if deadline else 30)*1e9)
        profile=self.profile(bits,deadline,max_interface)
        feature_key=[len(bits).bit_length(),profile.get('variables',0).bit_length(),
                     profile.get('density_bucket',0),profile.get('reusable_sample',0)//3,
                     profile.get('reject',False)]
        bucket=int.from_bytes(hashlib.sha256(json.dumps(feature_key).encode()).digest()[:7],'big')
        rows = self.db.execute('SELECT route,count,total_ns FROM route_totals WHERE engine=? AND bucket=?',
                               (self.namespace, bucket)).fetchall()
        totals = {r[0]: (r[1], r[2]) for r in rows}
        count = sum(v[0] for v in totals.values())
        scores={};recent={}
        for route in self.routes:
            observations=self.db.execute('''SELECT elapsed_ns,success FROM route_observations
                WHERE engine=? AND bucket=? AND route=? ORDER BY rowid DESC LIMIT 32''',
                (self.namespace,bucket,route)).fetchall()
            completed=sum(r[1] for r in observations)
            cost=sum(r[0]+(0 if r[1] else failure_budget_ns) for r in observations)
            scores[route]=cost/completed if completed else None
            recent[route]=dict(attempts=len(observations),completed=completed)
        if profile['reject']:
            return dict(bucket=bucket,route='checked',reason='structural_guard',observations=count,features=profile)
        for route in self.routes:
            if route not in totals:
                return dict(bucket=bucket, route=route, reason='initial_sample', observations=count,features=profile)
        if count % 8 == 7:
            route = self.routes[(count // 8) % 2]
            reason = 'periodic_sample'
        else:
            route = min(self.routes, key=lambda r: float('inf') if scores[r] is None else scores[r])
            reason = 'completion_cost'
        return dict(bucket=bucket, route=route, reason=reason, observations=count,features=profile,
                    scores_ns=scores,recent=recent,failure_budget_ns=failure_budget_ns)

    def observe(self, decision, elapsed_ns, success):
        with self.db:
            values = (self.namespace, decision['bucket'], decision['route'])
            self.db.execute('INSERT INTO route_observations VALUES (?,?,?,?,?,?)',
                            (*values, elapsed_ns, int(success), time.time_ns()))
            self.db.execute('''INSERT INTO route_totals VALUES (?,?,?,1,?)
                ON CONFLICT(engine,bucket,route) DO UPDATE SET
                count=count+1,total_ns=total_ns+excluded.total_ns''', (*values, elapsed_ns))
