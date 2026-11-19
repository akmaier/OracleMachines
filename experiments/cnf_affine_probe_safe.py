"""Snapshot finite CNF iterables before the frozen multi-pass affine kernel."""
import time
from experiments.cnf_affine_probe import AffineProbeSolver


class InputSafeAffineProbeSolver(AffineProbeSolver):
    def solve(self,source):
        began=time.perf_counter()
        source=tuple(tuple(clause) for clause in source)
        literals=sum(map(len,source))
        try:result=super().solve(source)
        finally:
            self.counts['affine_input_snapshot_clauses']+=len(source)
            self.counts['affine_input_snapshot_literals']+=literals
        result['metrics']=dict(self.counts);result['seconds']=time.perf_counter()-began
        return result
