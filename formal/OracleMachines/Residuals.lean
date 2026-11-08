import OracleMachines.SAT

/-!
# Exact conditioning and branching for residual reuse

These semantic lemmas justify a variable split for arbitrary formulas. They do
not verify the Python candidate, its CNF parser, cache, or cost bounds, and do not
bound the number of distinct residuals. Component joining is treated separately
in `Components.lean`.
-/
namespace OracleMachines.SAT

def Formula.condition (f : Formula) (index : Nat) (value : Bool) : Formula :=
  match f with
  | .falsum => .falsum
  | .var i => if i = index then (if value then .neg .falsum else .falsum) else .var i
  | .neg g => .neg (g.condition index value)
  | .conj g h => .conj (g.condition index value) (h.condition index value)

theorem condition_eval (f : Formula) (index : Nat) (value : Bool) (v : Nat → Bool) :
    (f.condition index value).eval v =
      f.eval (fun i => if i = index then value else v i) := by
  induction f with
  | falsum => rfl
  | var i =>
    by_cases h : i = index
    · cases value <;> simp [Formula.condition, Formula.eval, h]
    · simp [Formula.condition, Formula.eval, h]
  | neg g ih => simp [Formula.condition, Formula.eval, ih]
  | conj g h ihg ihh => simp [Formula.condition, Formula.eval, ihg, ihh]

theorem satisfiable_condition (f : Formula) (index : Nat) (value : Bool) :
    Satisfiable (f.condition index value) ↔
      ∃ v, v index = value ∧ f.eval v = true := by
  constructor
  · rintro ⟨v, hv⟩
    refine ⟨fun i => if i = index then value else v i, by simp, ?_⟩
    exact (condition_eval f index value v).symm.trans hv
  · rintro ⟨v, hi, hv⟩
    refine ⟨v, ?_⟩
    rw [condition_eval]
    have agreement : (fun i => if i = index then value else v i) = v := by
      funext i
      by_cases h : i = index
      · subst i; simp [hi]
      · simp [h]
    simpa [agreement] using hv

theorem satisfiable_split (f : Formula) (index : Nat) :
    Satisfiable f ↔ Satisfiable (f.condition index false) ∨
      Satisfiable (f.condition index true) := by
  constructor
  · rintro ⟨v, hv⟩
    cases hi : v index with
    | false => exact Or.inl ((satisfiable_condition f index false).mpr ⟨v, hi, hv⟩)
    | true => exact Or.inr ((satisfiable_condition f index true).mpr ⟨v, hi, hv⟩)
  · intro h
    rcases h with h | h
    · obtain ⟨v, _, hv⟩ := (satisfiable_condition f index false).mp h
      exact ⟨v, hv⟩
    · obtain ⟨v, _, hv⟩ := (satisfiable_condition f index true).mp h
      exact ⟨v, hv⟩

theorem unsatisfiable_split (f : Formula) (index : Nat)
    (low : ¬ Satisfiable (f.condition index false))
    (high : ¬ Satisfiable (f.condition index true)) : ¬ Satisfiable f := by
  intro h
  exact ((satisfiable_split f index).mp h).elim low high

end OracleMachines.SAT
