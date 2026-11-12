import OracleMachines.VariableElimination

/-! Conditional size bounds for an elimination-only chain. These lemmas do not
prove that an admissible pivot exists, refine the Python runtime, or bound the
full branching inventory. Normalization is an explicit premise. -/
namespace OracleMachines.ClauseBoundElimination
open OracleMachines.Fragments

/-- Normalized non-tautological clauses mention each variable at most once. -/
def NormalizedOver (support : Finset Nat) (c : Clause) : Prop :=
  (c.map Prod.fst).Nodup ∧ ∀ l ∈ c, l.1 ∈ support

def literalCount (cnf : List Clause) : Nat := (cnf.map List.length).sum

theorem clause_width_bound (support : Finset Nat) (c : Clause)
    (normalized : NormalizedOver support c) : c.length ≤ support.card := by
  have sub : (c.map Prod.fst).toFinset ⊆ support := by
    intro x hx
    obtain ⟨l, member, rfl⟩ := List.mem_map.mp (List.mem_toFinset.mp hx)
    exact normalized.2 l member
  calc
    c.length = (c.map Prod.fst).toFinset.card := by
      simpa using (List.toFinset_card_of_nodup normalized.1).symm
    _ ≤ support.card := Finset.card_le_card sub

theorem literal_count_le (cnf : List Clause) (n : Nat)
    (width : ∀ c ∈ cnf, c.length ≤ n) : literalCount cnf ≤ cnf.length * n := by
  induction cnf with
  | nil => simp [literalCount]
  | cons c rest ih =>
    have hc := width c (by simp)
    have hr := ih (fun d hd => width d (by simp [hd]))
    simpa [literalCount, Nat.add_mul, Nat.add_comm] using Nat.add_le_add hc hr

/-- Clause-count preservation suffices for a polynomial per-CNF bound even
when literal count grows on individual steps. -/
theorem bounded_cnf_size (cnf : List Clause) (support : Finset Nat) (m : Nat)
    (clauses : cnf.length ≤ m) (normalized : ∀ c ∈ cnf, NormalizedOver support c) :
    literalCount cnf ≤ m * support.card := by
  exact (literal_count_le cnf support.card (fun c hc => clause_width_bound support c (normalized c hc))).trans
    (Nat.mul_le_mul_right support.card clauses)

/-- Abstract chain length: every accepted step strictly decreases support. -/
inductive DecreasingChain : Nat → Nat → Prop
  | stop (n : Nat) : DecreasingChain n 0
  | step {n next steps : Nat} : next < n → DecreasingChain next steps →
      DecreasingChain n (steps + 1)

theorem chain_length_bound {n steps : Nat} (h : DecreasingChain n steps) : steps ≤ n := by
  induction h with
  | stop n => omega
  | step decreases tail ih => omega

/-- Sum of the CNF literal payloads on one accepted chain, excluding profiles,
other alternatives, source keys, metadata, integer encoding and unrelated roots. -/
theorem chain_payload_bound (states : List (List Clause)) (support : Finset Nat) (m : Nat)
    (state_count : states.length ≤ support.card + 1)
    (clauses : ∀ cnf ∈ states, cnf.length ≤ m)
    (normalized : ∀ cnf ∈ states, ∀ c ∈ cnf, NormalizedOver support c) :
    (states.map literalCount).sum ≤ (support.card + 1) * (m * support.card) := by
  have bound : (states.map literalCount).sum ≤ states.length * (m * support.card) := by
    induction states with
    | nil => simp
    | cons cnf rest ih =>
      have first := bounded_cnf_size cnf support m (clauses cnf (by simp))
        (normalized cnf (by simp))
      have tail := ih (by simpa using Nat.le_trans (Nat.le_succ rest.length) state_count)
        (fun d hd => clauses d (by simp [hd]))
        (fun d hd => normalized d (by simp [hd]))
      simpa [Nat.add_mul, Nat.add_comm] using Nat.add_le_add first tail
  exact bound.trans (Nat.mul_le_mul_right (m * support.card) state_count)

end OracleMachines.ClauseBoundElimination
