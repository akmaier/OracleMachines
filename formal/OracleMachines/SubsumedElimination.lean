import OracleMachines.VariableElimination

/-! A retained subclause can replace a resolvent without changing projection.
These are semantic list lemmas, not a refinement of the Python indexed checker,
its normalization, scheduling, or resource counters. -/
namespace OracleMachines.VariableElimination
open OracleMachines.Fragments

/-- A satisfying literal of a subclause also satisfies its superclause. -/
theorem holds_of_subclause (v : Valuation) (small large : Clause)
    (sub : ∀ l ∈ small, l ∈ large) (h : Holds v small) : Holds v large := by
  obtain ⟨l, member, satisfied⟩ := h
  exact ⟨l, sub l member, satisfied⟩

/-- Omitted clauses are redundant only because their subsumers remain retained. -/
theorem redundant_clauses (v : Valuation) (rest kept omitted : List Clause)
    (covered : ∀ c ∈ omitted, ∃ r ∈ rest, ∀ l ∈ r, l ∈ c) :
    Models v (rest ++ kept ++ omitted) ↔ Models v (rest ++ kept) := by
  simp only [Models, List.forall_mem_append]
  constructor
  · exact fun h => h.1
  · rintro ⟨hr, hk⟩
    refine ⟨⟨hr, hk⟩, ?_⟩
    intro c hc
    obtain ⟨r, member, sub⟩ := covered c hc
    exact holds_of_subclause v r c sub (hr r member)

/-- Every opposing pair is kept or covered by a subclause in the unaffected
source. This does not permit a deleted pivot clause to justify omission. -/
theorem subsumed_projection_exact (v : Valuation) (x : Nat)
    (rest positive negative kept : List Clause)
    (hr : Avoids x rest) (hp : Avoids x positive) (hn : Avoids x negative)
    (sound : ∀ c ∈ kept, ∃ p ∈ positive, ∃ n ∈ negative, c = p ++ n)
    (covered : ∀ p ∈ positive, ∀ n ∈ negative,
      p ++ n ∈ kept ∨ ∃ r ∈ rest, ∀ l ∈ r, l ∈ p ++ n) :
    Models v (rest ++ kept) ↔
      ∃ b : Bool, Models (Function.update v x b) (source x rest positive negative) := by
  rw [← projection_exact v x rest positive negative hr hp hn, projected_models]
  simp only [Models, List.forall_mem_append]
  change (Models v rest ∧ Models v kept) ↔ _
  constructor
  · rintro ⟨rest_ok, kept_ok⟩
    refine ⟨rest_ok, ?_⟩
    intro p pm n nm
    apply (holds_append v p n).mp
    rcases covered p pm n nm with member | ⟨r, member, sub⟩
    · exact kept_ok (p ++ n) member
    · exact holds_of_subclause v r (p ++ n) sub (rest_ok r member)
  · rintro ⟨rest_ok, pairs⟩
    refine ⟨rest_ok, ?_⟩
    intro c member
    obtain ⟨p, pm, n, nm, rfl⟩ := sound c member
    exact (holds_append v p n).mpr (pairs p pm n nm)

end OracleMachines.VariableElimination
