"""Post-hoc small-cap comparison; never changes the frozen timed policy."""
from pathlib import Path
from experiments import cnf_boundary_repair as e
from experiments.compare_cnf_boundary_repair import load,write


def main(out):
    for source in load(out/'semantic-audit.json')['fresh_inputs']:
        initial=e.proposal(source)
        for cap in range(2,25):
            baseline=e.previous_search.search(source,initial,len(initial['names']),node_limit=cap)
            candidate=e.repair(source,node_limit=cap,prefix_limit=cap//2)
            if baseline['witness'] and candidate['witness'] is None:
                assert e.previous.check(source,baseline['witness'])['answer'];e.check_evidence(source,candidate['evidence'])
                write(out/'budget-regression.json',dict(source=source,seed=initial,node_limit=cap,prefix_limit=cap//2,baseline=baseline,boundary=candidate,scope='Post-hoc illustrative small-cap regression. Does not test or alter the frozen 10000/20000 policy; demonstrates lack of general restart-budget dominance.'))
                print(cap,len(initial['names']),len(source));return
    raise AssertionError('No regression in searched small panel')


if __name__=='__main__':main(Path('experiments/results/cnf-boundary-repair'))
