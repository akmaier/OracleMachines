import OracleMachines.Encoding

/-!
# SAT, UNSAT, and malformed inputs

UNSAT means unsatisfiability, not SAT without a size cap. Complexity-class
membership is not formalized here. Malformed strings are outside EncodedSAT,
but are not members of the valid-formula language EncodedUNSAT either.
-/

namespace OracleMachines.SAT

def EncodedUNSAT (bits : Word) : Prop :=
  ∃ f, decode bits = some f ∧ ¬ Satisfiable f

def ValidEncoding (bits : Word) : Prop := ∃ f, decode bits = some f

/-- Partial decision: malformed inputs have no SAT/UNSAT verdict. -/
def decideEncoded (bits : Word) : Option Bool := (decode bits).map solve

theorem decision_invalid_iff (bits : Word) :
    decideEncoded bits = none ↔ decode bits = none := by
  cases h : decode bits <;> simp [decideEncoded, h]

theorem decision_sat_iff (bits : Word) :
    decideEncoded bits = some true ↔ EncodedSAT bits := by
  cases h : decode bits <;> simp [decideEncoded, EncodedSAT, h, solve_correct]

theorem decision_unsat_iff (bits : Word) :
    decideEncoded bits = some false ↔ EncodedUNSAT bits := by
  cases h : decode bits <;> simp [decideEncoded, EncodedUNSAT, h, solve_false_iff]

theorem sat_unsat_disjoint (bits : Word) : ¬ (EncodedSAT bits ∧ EncodedUNSAT bits) := by
  cases h : decode bits <;> simp [EncodedSAT, EncodedUNSAT, h]

theorem not_sat_iff_invalid_or_unsat (bits : Word) :
    ¬ EncodedSAT bits ↔ decode bits = none ∨ EncodedUNSAT bits := by
  cases h : decode bits <;> simp [EncodedSAT, EncodedUNSAT, h]

theorem valid_not_sat_iff_unsat (bits : Word) (valid : ValidEncoding bits) :
    ¬ EncodedSAT bits ↔ EncodedUNSAT bits := by
  rcases valid with ⟨f, h⟩
  simp [EncodedSAT, EncodedUNSAT, h]

theorem total_false_iff_invalid_or_unsat (bits : Word) :
    solveEncoded bits = false ↔ decode bits = none ∨ EncodedUNSAT bits := by
  rw [← not_sat_iff_invalid_or_unsat, ← solveEncoded_correct]
  cases solveEncoded bits <;> simp

theorem encode_unsatisfiable (f : Formula) : EncodedUNSAT (encode f) ↔ ¬ Satisfiable f := by
  simp [EncodedUNSAT, decode_encode]

end OracleMachines.SAT
