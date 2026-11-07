"""Renaming-normalized, variable-disjoint conjuncts with checked recomposition.

Canonicalization uses first occurrence, not full Boolean equivalence or graph
isomorphism. A new connecting constraint merges components and invalidates the
independent positive decomposition. An archived UNSAT conjunct remains usable
under additional constraints only after Lean checks its current embedding.
"""
import hashlib
import time

from solver.incremental import parse_postfix
from solver.knowledge_store import KnowledgeStore


def key(bits):
    return hashlib.sha256(bits.encode()).hexdigest()


def conjunction(parts):
    # Right-associated conjunction with a true terminator, matching Lean.
    return "".join(parts) + "0010" + "11" * len(parts)


def analyze(bits, deadline):
    nodes, root = parse_postfix(bits, deadline)
    starts = []
    for i, node in enumerate(nodes):
        starts.append(i if node[0] in ("var", "false") else starts[node[1]])
    terms, stack = [], [(root, "")]
    while stack:
        deadline.check()
        i, path = stack.pop()
        node = nodes[i]
        if node[0] == "and":
            stack.extend([(node[2], path + "1"), (node[1], path + "0")])
        else:
            terms.append(dict(index=i, path=path, support=[nodes[j][1] for j in range(starts[i], i+1) if nodes[j][0] == "var"]))
    def encoded(i, rename=None):
        tokens = []
        for j in range(starts[i], i+1):
            if j % 256 == 0:
                deadline.check()
            node = nodes[j]
            if node[0] == "var":
                variable = node[1] if rename is None else rename[node[1]]
                tokens.append("01" + "1" * variable + "0")
            else:
                tokens.append({"false": "00", "not": "10", "and": "11"}[node[0]])
        return "".join(tokens)
    parent = {}
    def find(v):
        parent.setdefault(v, v)
        while parent[v] != v:
            parent[v] = parent[parent[v]]
            v = parent[v]
        return v
    for term in terms:
        support = term["support"]
        if support:
            first = find(support[0])
            for v in support[1:]:
                parent[find(v)] = first
    groups = {}
    for term in terms:
        token = find(term["support"][0]) if term["support"] else None
        groups.setdefault(token, []).append(term)
        term["global_bits"] = encoded(term["index"])
    components = []
    for group in groups.values():
        mapping = {}
        for term in group:
            for variable in term["support"]:
                if variable not in mapping:
                    mapping[variable] = len(mapping)
        parts = [encoded(term["index"], mapping) for term in group]
        canonical = conjunction(parts)
        components.append(dict(key=key(canonical), bits=canonical, parts=parts,
                               variables=list(mapping), paths=[t["path"] for t in group],
                               global_parts=[t["global_bits"] for t in group]))
    return components, {t["global_bits"]: t["path"] for t in terms}, len(nodes)


class ComponentSolver:
    def __init__(self, db, engine):
        self.db, self.engine = db, engine
        self.store = KnowledgeStore(db, engine)

    def entry(self, component_key):
        row = self.db.execute("SELECT object_id FROM component_entries WHERE engine=? AND key=?",
                              (self.engine, component_key)).fetchone()
        if row is None:
            return None
        value = self.store.get(row[0], "component_result")
        if key(value["bits"]) != component_key or type(value.get("answer")) is not bool:
            raise ValueError("Invalid component result identity")
        return value

    def retain_structure(self, bits, components, deadline):
        root, totals = None, [0, 0]
        before = self.store.inserted_objects
        with self.db:
            for component in components:
                deadline.check()
                terms = [self.store.put("component_term", term)[0] for term in component["parts"]]
                shape = self.store.put("component_shape", terms)[0]
                mapping = self.store.put("component_map", component["variables"])[0]
                root, raw, packed = self.store.put("component_prefix", [root, shape, mapping])
                totals[0] += raw
                totals[1] += packed
            self.db.execute("INSERT OR IGNORE INTO component_roots VALUES (?,?,?,?)",
                            (self.engine, key(bits), root, len(components)))
        after = self.store.inserted_objects
        return dict(new_structure_objects=after-before, prefix_reference_raw_bytes=totals[0],
                    prefix_reference_compressed_bytes=totals[1])

    @staticmethod
    def certificate(entry, paths, variables):
        return dict(format="component", bits=entry["bits"], paths=paths,
                    variables=variables, proof=entry["certificate"])

    def prior_negative(self, current_terms, deadline):
        for row in self.db.execute("SELECT key,instance FROM component_negatives WHERE engine=? ORDER BY created_ns DESC LIMIT 4", (self.engine,)):
            deadline.check()
            instance = self.store.get(row["instance"], "component_negative_instance")
            if all(term in current_terms for term in instance["parts"]):
                entry = self.entry(row["key"])
                if entry is None or entry["answer"]:
                    raise ValueError("Invalid negative component reference")
                yield self.certificate(entry, [current_terms[t] for t in instance["parts"]], instance["variables"])

    def solve(self, service, bits):
        deadline = service._deadline
        if deadline is None:
            # Administrative direct calls still get a bounded structural attempt.
            from solver.resources import Deadline
            deadline = Deadline(service.query_timeout)
        with service._phase("component_analysis"):
            components, current_terms, nodes = analyze(bits, deadline)
        if sum(len(c["paths"]) for c in components) > 4096:
            return None
        with service._phase("component_storage"):
            metadata = self.retain_structure(bits, components, deadline)
        metadata.update(components=len(components), distinct_shapes=len({c["key"] for c in components}),
                        largest_component_variables=max(len(c["variables"]) for c in components),
                        global_variables=len({v for c in components for v in c["variables"]}),
                        input_nodes=nodes, hits=0, acquisitions=0, canonical_bytes=sum(len(c["bits"]) for c in components),
                        negative_subsumption=False)
        parse_work = 0
        for certificate in self.prior_negative(current_terms, deadline):
            check = service._request(dict(mode="verify_certificate", bits=bits, certificate=certificate))
            parse_work += check["parse_work"]
            if not check["valid"]:
                raise ValueError("Saved component refutation rejected")
            metadata.update(hits=1, negative_subsumption=True)
            return self.result(False, None, certificate, parse_work, metadata)
        assignment = {}
        for component in components:
            deadline.check()
            with service._phase("component_lookup"):
                entry = self.entry(component["key"])
            if entry is None:
                # Component wrappers accept the legacy base proof formats. A full
                # shared-graph certificate is checked through its own root path.
                compatible = getattr(service.incremental, "certificate_format", None) != "incremental_lrat"
                acquired = service._fast_live(component["bits"], allow_components=False,
                                              allow_interfaces=False, allow_incremental=compatible)
                parse_work += acquired["parse_work"]
                entry = dict(bits=component["bits"], answer=acquired["answer"], witness=acquired["witness"],
                             certificate=acquired.get("certificate"))
                with service._phase("component_storage"), self.db:
                    token = self.store.put("component_result", entry)[0]
                    self.db.execute("INSERT OR IGNORE INTO component_entries VALUES (?,?,?,?)",
                                    (self.engine, component["key"], token, time.time_ns()))
                metadata["acquisitions"] += 1
            else:
                metadata["hits"] += 1
            if entry["answer"]:
                witness = entry["witness"]
                if not isinstance(witness, str) or any(c not in "01" for c in witness):
                    raise ValueError("Invalid component witness")
                for local, variable in enumerate(component["variables"]):
                    value = witness[local] if local < len(witness) else "0"
                    if variable in assignment and assignment[variable] != value:
                        raise ValueError("Overlapping private component assignments")
                    assignment[variable] = value
            else:
                certificate = self.certificate(entry, component["paths"], component["variables"])
                checked = service._request(dict(mode="verify_certificate", bits=bits, certificate=certificate))
                parse_work += checked["parse_work"]
                if not checked["valid"]:
                    raise ValueError("Component UNSAT certificate rejected")
                with service._phase("component_storage"), self.db:
                    instance = self.store.put("component_negative_instance",
                                              dict(parts=component["global_parts"], variables=component["variables"]))[0]
                    self.db.execute("INSERT OR IGNORE INTO component_negatives VALUES (?,?,?,?)",
                                    (self.engine, component["key"], instance, time.time_ns()))
                return self.result(False, None, certificate, parse_work, metadata)
        witness = "".join(assignment.get(i, "0") for i in range(max(assignment, default=-1)+1))
        checked = service._request(dict(mode="verify_witness", bits=bits, witness=witness))
        parse_work += checked["parse_work"]
        if not checked["valid"]:
            raise ValueError("Recomposed component witness rejected")
        return self.result(True, witness, None, parse_work, metadata)

    @staticmethod
    def result(answer, witness, certificate, parse_work, metadata):
        return dict(answer=answer, witness=witness, certificate=certificate,
                    backend="components", reuse_kind="witness" if answer else "refutation",
                    core_work=None, counted_work=None, counted_complete=False, nodes=None,
                    parse_work=parse_work, components=metadata)
