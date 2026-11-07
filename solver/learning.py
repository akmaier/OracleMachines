"""A bounded online perceptron proposing SAT witnesses, never verdicts.

Five shared integer weights generalize across variable identities. Features are
positive/negative syntactic occurrences under negation. They are not sufficient
to solve general SAT; every prediction must be checked by the Lean evaluator.
"""
import json
from solver.incremental import parse_postfix

LIMIT = 10000
COUNTER_LIMIT = 2**63 - 1


def features(bits, deadline):
    nodes, root = parse_postfix(bits, deadline)
    counts, stack, visited = {}, [(root, False)], 0
    while stack:
        if visited % 256 == 0:
            deadline.check()
        visited += 1
        index, inverted = stack.pop()
        node = nodes[index]
        if node[0] == "var":
            pair = counts.setdefault(node[1], [0, 0])
            pair[int(inverted)] += 1
        elif node[0] == "not":
            stack.append((node[1], not inverted))
        elif node[0] == "and":
            stack.extend([(node[1], inverted), (node[2], inverted)])
    return {i: (1, min(p, 32), min(n, 32), int(p > n), int(n > p))
            for i, (p, n) in counts.items()}


class Predictor:
    def __init__(self, state=None):
        state = state or {"weights": [0] * 5, "examples": 0, "updates": 0}
        weights = state.get("weights")
        if (not isinstance(weights, list) or len(weights) != 5
                or any(type(w) is not int or abs(w) > LIMIT for w in weights)
                or any(type(state.get(k)) is not int or not 0 <= state[k] <= COUNTER_LIMIT
                       for k in ("examples", "updates"))):
            raise ValueError("Invalid predictor state")
        self.state = dict(state, weights=list(weights))

    def predict(self, observed):
        word = ["0"] * (max(observed) + 1 if observed else 0)
        for i, vector in observed.items():
            word[i] = "1" if sum(w * x for w, x in zip(self.state["weights"], vector)) > 0 else "0"
        return "".join(word)

    def update(self, observed, witness, deadline):
        weights = self.state["weights"]
        for count, (i, vector) in enumerate(observed.items()):
            if count % 256 == 0:
                deadline.check()
            label = int(i < len(witness) and witness[i] == "1")
            predicted = int(sum(w * x for w, x in zip(weights, vector)) > 0)
            if label != predicted:
                for j, value in enumerate(vector):
                    weights[j] = max(-LIMIT, min(LIMIT, weights[j] + (label - predicted) * value))
                self.state["updates"] = min(COUNTER_LIMIT, self.state["updates"] + 1)
            self.state["examples"] = min(COUNTER_LIMIT, self.state["examples"] + 1)

    def dump(self):
        return json.dumps(self.state, sort_keys=True, separators=(",", ":"))
