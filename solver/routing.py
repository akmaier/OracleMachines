"""Measured two-route selection; no universal speedup or regret claim.

Only the chosen route runs. Each input-size bucket first samples both routes,
then uses measured mean complete-query time, with periodic exploration. Failed
queries are charged. The selection and durable observation costs are explicit
ledger phases. Historical observations are retained.
"""
import time


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

    def __init__(self, db, namespace):
        self.db, self.namespace = db, namespace

    def choose(self, bits):
        bucket = len(bits).bit_length()
        rows = self.db.execute('SELECT route,count,total_ns FROM route_totals WHERE engine=? AND bucket=?',
                               (self.namespace, bucket)).fetchall()
        totals = {r[0]: (r[1], r[2]) for r in rows}
        count = sum(v[0] for v in totals.values())
        for route in self.routes:
            if route not in totals:
                return dict(bucket=bucket, route=route, reason='initial_sample', observations=count)
        if count % 8 == 7:
            route = self.routes[(count // 8) % 2]
            reason = 'periodic_sample'
        else:
            route = min(self.routes, key=lambda r: totals[r][1] / totals[r][0])
            reason = 'measured_mean'
        return dict(bucket=bucket, route=route, reason=reason, observations=count)

    def observe(self, decision, elapsed_ns, success):
        with self.db:
            values = (self.namespace, decision['bucket'], decision['route'])
            self.db.execute('INSERT INTO route_observations VALUES (?,?,?,?,?,?)',
                            (*values, elapsed_ns, int(success), time.time_ns()))
            self.db.execute('''INSERT INTO route_totals VALUES (?,?,?,1,?)
                ON CONFLICT(engine,bucket,route) DO UPDATE SET
                count=count+1,total_ns=total_ns+excluded.total_ns''', (*values, elapsed_ns))
