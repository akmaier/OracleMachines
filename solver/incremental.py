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
    def __init__(self, executable=DEFAULT_INCREMENTAL, max_nodes=200000, max_bytes=64 * 1024**2,
                 store=None, max_replay_clauses=20000):
        self.executable, self.max_nodes, self.max_bytes = Path(executable), max_nodes, max_bytes
        self.process = None
        self.atoms, self.gates, self.next_var = {}, {}, 2
        self.queries = 0
        self.store, self.max_replay_clauses = store, max_replay_clauses
        self.loaded = False
        self.records, self.clauses = [], set()
        self.replay = []
        self.restored_nodes = self.restored_clauses = 0

    def close(self):
        stop_process(self.process)
        self.process = None
        self.atoms, self.gates, self.next_var = {}, {}, 2
        self.queries = 0
        self.loaded = False
        self.records, self.clauses, self.replay = [], set(), []
        self.restored_nodes = self.restored_clauses = 0

    @staticmethod
    def node_commands(record):
        if record[1] == "atom":
            v = record[0]
            return [f"ADD {v} -{v} 0"]
        v, _, a, b = record
        return [f"ADD {-v} {a} 0", f"ADD {-v} {b} 0", f"ADD {v} {-a} {-b} 0"]

    def load(self, deadline):
        if self.loaded:
            return
        state = self.store.restore(deadline) if self.store else {"nodes": [], "clauses": []}
        if len(state["nodes"]) + 2 > self.max_nodes:
            state = {"nodes": [], "clauses": []}  # archive is retained, active replay is bounded
        for record in state["nodes"]:
            deadline.check()
            if (not isinstance(record, list) or len(record) not in (3, 4)
                    or record[0] != self.next_var):
                raise ValueError("Invalid saved circuit node order")
            v = record[0]
            if record[1] == "atom" and len(record) == 3 and type(record[2]) is int and 0 <= record[2] < 8*1024**2:
                if record[2] in self.atoms:
                    raise ValueError("Duplicate saved circuit variable")
                self.atoms[record[2]] = v
            elif record[1] == "and" and len(record) == 4 and all(type(x) is int and 0 < abs(x) < v for x in record[2:]):
                self.gates[tuple(record[2:])] = v
            else:
                raise ValueError("Invalid saved circuit node")
            self.records.append(record)
            self.replay.extend(self.node_commands(record))
            self.next_var += 1
        for clause in state["clauses"]:
            if (not isinstance(clause, list) or not 1 <= len(clause) <= 64
                    or any(type(x) is not int or not 0 < abs(x) < self.next_var for x in clause)):
                raise ValueError("Invalid saved learned clause")
            self.clauses.add(tuple(sorted(set(clause))))
        # Short clauses get priority; no archived object is deleted by this cap.
        replayed = sorted(self.clauses, key=lambda c: (len(c), c))[:self.max_replay_clauses]
        self.replay += ["ADD " + " ".join(map(str, clause)) + " 0" for clause in replayed]
        self.restored_nodes, self.restored_clauses = len(self.records), len(replayed)
        if self.store:
            self.store.start(dict(nodes=self.records, clauses=[list(c) for c in sorted(self.clauses)]))
        self.loaded = True

    def propose(self, bits, deadline):
        try:
            self.load(deadline)
            nodes, root = parse_postfix(bits, deadline)
            if self.next_var + len(nodes) > self.max_nodes:
                self.close()  # Only ephemeral solver state; the durable archive is untouched.
                self.loaded = True  # start a fresh bounded branch, not the same oversized replay
                if self.store:
                    self.store.start({"nodes": [], "clauses": []})
            if len(nodes) + 2 > self.max_nodes:
                raise BudgetExceeded("Incremental circuit exceeds its node budget")
            if self.process is None:
                self.process = subprocess.Popen([str(self.executable)], stdin=subprocess.PIPE,
                                                stdout=subprocess.PIPE)
                additions = ["ADD -1 0"] + self.replay
                self.replay = []
            else:
                additions = []
            values, used = [], set()
            new_records = []
            replay_count = len(additions)
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
                        new_records.append([self.next_var, "atom", original])
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
                            new_records.append([gate, "and", left, right])
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
            response["new_definition_clauses"] = len(additions) - 1 - replay_count
            response["shared_nodes"] = self.next_var - 1
            exported = response.pop("learned_export", [])
            new_clauses = []
            for clause in exported:
                if (not isinstance(clause, list) or not 1 <= len(clause) <= 64
                        or any(type(x) is not int or not 0 < abs(x) < self.next_var for x in clause)):
                    raise ValueError("Invalid learned clause export")
                clause = tuple(sorted(set(clause)))
                if clause not in self.clauses:
                    self.clauses.add(clause)
                    new_clauses.append(list(clause))
            self.records.extend(new_records)
            deadline.check()
            raw, packed = self.store.append(new_records, new_clauses) if self.store else (0, 0)
            response.update(restored_nodes=self.restored_nodes, restored_clauses=self.restored_clauses,
                            archived_new_clauses=len(new_clauses), archived_clauses=len(self.clauses),
                            delta_raw_bytes=raw, delta_compressed_bytes=packed)
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
