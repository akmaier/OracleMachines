import OracleMachines.ClauseBoundElimination

/-! Conditional size bounds with a fixed per-step additive clause allowance.
Reachability is abstract: it does not guarantee a next pivot or refine Python. -/
namespace OracleMachines.AdditiveElimination
open OracleMachines.Fragments OracleMachines.ClauseBoundElimination

/-- A prefix of support-decreasing steps, each adding at most d clauses. -/
inductive GrowthReach (d n₀ m₀ : Nat) : Nat → Nat → Nat → Prop
  | start : GrowthReach d n₀ m₀ n₀ m₀ 0
  | step {n m k nextN nextM : Nat} : GrowthReach d n₀ m₀ n m k →
      nextN < n → nextM ≤ m + d → GrowthReach d n₀ m₀ nextN nextM (k + 1)

theorem support_and_steps {d n₀ m₀ n m k : Nat}
    (h : GrowthReach d n₀ m₀ n m k) : n + k ≤ n₀ := by
  induction h with
  | start => omega
  | step previous decreases growth ih => omega

theorem prefix_clause_bound {d n₀ m₀ n m k : Nat}
    (h : GrowthReach d n₀ m₀ n m k) : m ≤ m₀ + d * k := by
  induction h with
  | start => simp
  | step previous decreases growth ih =>
    calc
      _ ≤ _ + d := growth
      _ ≤ (m₀ + d * _) + d := Nat.add_le_add_right ih d
      _ = m₀ + d * (_ + 1) := by simp [Nat.mul_add, Nat.add_assoc]

theorem global_clause_bound {d n₀ m₀ n m k : Nat}
    (h : GrowthReach d n₀ m₀ n m k) : m ≤ m₀ + d * n₀ := by
  have steps : k ≤ n₀ := by have := support_and_steps h; omega
  exact (prefix_clause_bound h).trans
    (Nat.add_le_add_left (Nat.mul_le_mul_left d steps) m₀)

theorem state_literal_bound {d n₀ m₀ n m k : Nat}
    (h : GrowthReach d n₀ m₀ n m k) (cnf : List Clause) (support : Finset Nat)
    (size : cnf.length ≤ m) (vars : support.card ≤ n)
    (normalized : ∀ c ∈ cnf, NormalizedOver support c) :
    literalCount cnf ≤ (m₀ + d * n₀) * n₀ := by
  have count := bounded_cnf_size cnf support (m₀ + d * n₀)
    (size.trans (global_clause_bound h)) normalized
  have ns : n ≤ n₀ := by have := support_and_steps h; omega
  exact count.trans (Nat.mul_le_mul_left _ (vars.trans ns))

/-- Formula payload only. The list-size and normalization obligations are
explicit; branches, metadata, keys and identifier encoding are excluded. -/
theorem additive_chain_payload (states : List (List Clause)) (support : Finset Nat)
    (d m₀ : Nat) (state_count : states.length ≤ support.card + 1)
    (reachable : ∀ cnf ∈ states, ∃ n k, GrowthReach d support.card m₀ n cnf.length k)
    (normalized : ∀ cnf ∈ states, ∀ c ∈ cnf, NormalizedOver support c) :
    (states.map literalCount).sum ≤
      (support.card + 1) * ((m₀ + d * support.card) * support.card) := by
  apply chain_payload_bound states support (m₀ + d * support.card) state_count
  · intro cnf hc
    obtain ⟨n, k, h⟩ := reachable cnf hc
    exact global_clause_bound h
  · exact normalized

end OracleMachines.AdditiveElimination
