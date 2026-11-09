# Terminal signed-subsumption pilot

Nine selected prior queries, unchanged depth-two/four-probe/four-clause budgets.
The baseline is `ActivityLearningInventory`; the candidate adds a checked signed
subset search only at exhausted unresolved leaves and follows a reduced core
only when the existing basic classifier recognizes a family.

Sources **977, 1044, 1053 and 1365** become structurally closed. Sources 907, 1179
and 1363 remain open with one leaf each (72, 13 and 29 literals). Sources 956 and
1024 remain closed. There are no lost closures in this selected pilot. Closure
means that every selected leaf has a recognized family, not that the source is
satisfiable. Independent solver answers agree in all modes.

| Measurement | Activity baseline | Signed subsumption |
| --- | ---: | ---: |
| Operation seconds | 4.28813 | 3.53358 |
| SQLite bytes | 13,623,296 | 11,644,928 |
| Pattern nodes | 1,377 | 1,161 |
| Cold replay seconds | 1.84654 | 1.55978 |

These are single sequential samples on deliberately selected opportunities,
including the unchanged solver. They do not establish a broad runtime advantage.
All three archives replay byte-identically, including every alternative, nine
source bindings and 195 solver residuals in each mode. Warm reuse inserts nothing.
The report records counters, initialization, allocation scope and code hashes.
The full matched corpus and balanced timing controls are a separate study.

Reproduce from the repository root, choosing a new destination:

```sh
python3 experiments/compare_cnf_signed_subsumption.py --pilot --output /tmp/new-signed-pilot
```
