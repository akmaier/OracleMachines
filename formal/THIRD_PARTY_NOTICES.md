# Lean standard-library adaptation

`OracleMachines/IncrementalProof.lean` adapts the private `toCNF.go` traversal
from Lean 4.24.0 `Std/Sat/AIG/CNF.lean` as `collectDefinitions` so that all nodes
of a shared circuit can be compiled. Copyright 2024 Lean FRO, LLC; author Henrik
Böving. This adapted traversal is licensed under Apache License 2.0, reproduced
in [LICENSE-APACHE-2.0](LICENSE-APACHE-2.0), rather than the project MIT license.
The surrounding new development remains under the project's license.
