"""Shared Tseitin definitions and live CDCL state, used only for proposals.

SAT models are independently checked on the original formula. UNSAT proposals
need the standalone LRAT path: this module is not an incremental proof checker.
"""
import json
from pathlib import Path
import subprocess

from solver.resources import BudgetExceeded, exchange, stop_process

DEFAULT_INCREMENTAL = Path(__file__).resolve().parents[1] / "formal/.lake/build/bin/oracleIncremental"


def parse_postfix(bits, deadline):
    nodes, stack, position = [], [], 0
    while position < len(bits):
        if len(nodes) % 256 == 0:
            deadline.check()
        instruction = bits[position:position + 2]
        position += 2
        if instruction == "00":
            node = ("false",)
        elif instruction == "01":
            end = bits.find("0", position)
            if end < 0:
                raise ValueError("Invalid variable index")
            node = ("var", end - position)
            position = end + 1
        elif instruction == "10" and stack:
            node = ("not", stack.pop())
        elif instruction == "11" and len(stack) >= 2:
            right, left = stack.pop(), stack.pop()
            node = ("and", left, right)
        else:
            raise ValueError("Invalid formula encoding")
        nodes.append(node)
        stack.append(len(nodes) - 1)
    if len(stack) != 1:
        raise ValueError("Invalid formula encoding")
    return nodes, stack[0]


class Incremental:
    def __init__(self, executable=DEFAULT_INCREMENTAL, max_nodes=200000, max_bytes=64 * 1024**2):
        self.executable, self.max_nodes, self.max_bytes = Path(executable), max_nodes, max_bytes
        self.process = None
        self.atoms, self.gates, self.next_var = {}, {}, 2
        self.queries = 0

    def close(self):
        stop_process(self.process)
        self.process = None
        self.atoms, self.gates, self.next_var = {}, {}, 2
        self.queries = 0

    def propose(self, bits, deadline):
        try:
            nodes, root = parse_postfix(bits, deadline)
            if self.next_var + len(nodes) > self.max_nodes:
                self.close()  # Only ephemeral solver state; the durable archive is untouched.
            if len(nodes) + 2 > self.max_nodes:
                raise BudgetExceeded("Incremental circuit exceeds its node budget")
            if self.process is None:
                self.process = subprocess.Popen([str(self.executable)], stdin=subprocess.PIPE,
                                                stdout=subprocess.PIPE)
                additions = ["ADD -1 0"]  # variable 1 is the false constant
            else:
                additions = []
            values, used = [], set()
            for index, node in enumerate(nodes):
                if index % 256 == 0:
                    deadline.check()
                if node[0] == "false":
                    literal = 1
                elif node[0] == "var":
                    original = node[1]
                    used.add(original)
                    if original not in self.atoms:
                        self.atoms[original] = self.next_var
                        # Introduce even a variable only used as a root assumption.
                        additions.append(f"ADD {self.next_var} -{self.next_var} 0")
                        self.next_var += 1
                    literal = self.atoms[original]
                elif node[0] == "not":
                    literal = -values[node[1]]
                else:
                    left, right = sorted((values[node[1]], values[node[2]]))
                    if left == 1 or right == 1 or left == -right:
                        literal = 1
                    elif left == -1:
                        literal = right
                    elif right == -1 or left == right:
                        literal = left
                    else:
                        pair = left, right
                        if pair not in self.gates:
                            gate = self.next_var
                            self.next_var += 1
                            self.gates[pair] = gate
                            additions += [f"ADD {-gate} {left} 0", f"ADD {-gate} {right} 0",
                                          f"ADD {gate} {-left} {-right} 0"]
                        literal = self.gates[pair]
                values.append(literal)
            ordered = sorted(used)
            ids = [self.atoms[i] for i in ordered]
            additions.append("SOLVE " + str(values[root]) + " " + " ".join(map(str, ids)) + " 0")
            payload = ("\n".join(additions) + "\n").encode()
            response = json.loads(exchange(self.process, payload, deadline, self.max_bytes))
            self.queries += 1
            response["new_definition_clauses"] = len(additions) - 1
            response["shared_nodes"] = self.next_var - 1
            if response["verdict"] == 10:
                model = response["values"]
                if len(model) != len(ids) or any(abs(v) != i for v, i in zip(model, ids)):
                    raise ValueError("Malformed incremental model")
                witness = ["0"] * (max(ordered) + 1 if ordered else 0)
                for original, value in zip(ordered, model):
                    witness[original] = "1" if value > 0 else "0"
                response["witness"] = "".join(witness)
            return response
        except BaseException:
            self.close()
            raise
