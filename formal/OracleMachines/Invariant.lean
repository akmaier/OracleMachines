import OracleMachines.Expansion

/-!
# Obligations for replacing the table with another representation

The state type can represent a compressed or learned model. The induction step
requires exact answers on every newly covered input and preservation on every
previously covered input. Sample accuracy is not one of its hypotheses.
-/

namespace OracleMachines

def expandState {State : Type*} (initial : State) (step : Nat → State → State) : Nat → State
  | 0 => initial
  | n + 1 => step (n + 1) (expandState initial step n)

theorem expansion_invariant {State : Type*} (initial : State) (step : Nat → State → State)
    (answer : State → Word → Bool) (truth : Word → Bool)
    (base : answer initial [] = truth [])
    (preserve : ∀ n x, x.length ≤ n →
      answer (step (n + 1) (expandState initial step n)) x =
        answer (expandState initial step n) x)
    (extend : ∀ n x, x.length = n + 1 →
      answer (step (n + 1) (expandState initial step n)) x = truth x)
    (n : Nat) (x : Word) (hx : x.length ≤ n) :
    answer (expandState initial step n) x = truth x := by
  induction n with
  | zero =>
    have hnil : x = [] := List.length_eq_zero_iff.mp (by omega)
    simpa [expandState, hnil] using base
  | succ n ih =>
    by_cases hold : x.length ≤ n
    · exact (preserve n x hold).trans (ih hold)
    · exact extend n x (by omega)

/-- Coverage suffices for a correct answer after finitely many stages. The
cost and computability of `cover`, `step`, and `answer` are separate obligations. -/
theorem answer_at_cover {State : Type*} (initial : State) (step : Nat → State → State)
    (answer : State → Word → Bool) (truth : Word → Bool)
    (exact : ∀ n x, x.length ≤ n → answer (expandState initial step n) x = truth x)
    (cover : Word → Nat) (covers : ∀ x, x.length ≤ cover x) (x : Word) :
    answer (expandState initial step (cover x)) x = truth x :=
  exact (cover x) x (covers x)

end OracleMachines
