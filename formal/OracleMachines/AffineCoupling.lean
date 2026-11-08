import OracleMachines.AffineCosts

/-!
# Exact affine projection in the presence of leftover constraints

The leftover predicate may be arbitrary, but must depend only on variables
outside the eliminated set. This composes the existing executable affine
projection theorem with a coupling predicate. It does not refine the Python
CNF extractor, sparse certificate checker, encoding budget or persistence.
-/
namespace OracleMachines.Affine

def InvariantOutside {n : Nat} (hidden : List (Fin n)) (remainder : (Fin n → F) → Prop) : Prop :=
  ∀ v w, AgreesOutside hidden v w → (remainder v ↔ remainder w)

/-- Every feasible boundary has an original witness satisfying the same
leftover constraints, and every original witness projects back. -/
theorem project_with_remainder_exact {n : Nat} (hidden : List (Fin n))
    (rows : List (Row n)) (remainder : (Fin n → F) → Prop)
    (invariant : InvariantOutside hidden remainder) (v : Fin n → F) :
    (Holds (project hidden rows) v ∧ remainder v) ↔
      ∃ w, AgreesOutside hidden v w ∧ Holds rows w ∧ remainder w := by
  constructor
  · rintro ⟨projected, rest⟩
    obtain ⟨w, agrees, original⟩ := (project_exact hidden rows v).mp projected
    exact ⟨w, agrees, original, (invariant v w agrees).mp rest⟩
  · rintro ⟨w, agrees, original, rest⟩
    exact ⟨(project_exact hidden rows v).mpr ⟨w, agrees, original⟩,
      (invariant v w agrees).mpr rest⟩

theorem project_with_remainder_sat {n : Nat} (hidden : List (Fin n))
    (rows : List (Row n)) (remainder : (Fin n → F) → Prop)
    (invariant : InvariantOutside hidden remainder) :
    (∃ v, Holds (project hidden rows) v ∧ remainder v) ↔
      ∃ w, Holds rows w ∧ remainder w := by
  constructor
  · rintro ⟨v, hv⟩
    obtain ⟨w, _, original, rest⟩ :=
      (project_with_remainder_exact hidden rows remainder invariant v).mp hv
    exact ⟨w, original, rest⟩
  · rintro ⟨w, original, rest⟩
    refine ⟨w, (project_with_remainder_exact hidden rows remainder invariant w).mpr ?_⟩
    exact ⟨w, fun _ _ => rfl, original, rest⟩

theorem project_with_remainder_unsat {n : Nat} (hidden : List (Fin n))
    (rows : List (Row n)) (remainder : (Fin n → F) → Prop)
    (invariant : InvariantOutside hidden remainder) :
    (¬ ∃ v, Holds (project hidden rows) v ∧ remainder v) ↔
      ¬ ∃ w, Holds rows w ∧ remainder w :=
  not_congr (project_with_remainder_sat hidden rows remainder invariant)

end OracleMachines.Affine
