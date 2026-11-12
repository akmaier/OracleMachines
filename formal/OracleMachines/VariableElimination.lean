import OracleMachines.ProofFragments

/-! Exact Davis-Putnam projection and constructive Boolean model extension.
This semantic theorem does not refine the Python normalization, bounded search,
certificate parser, persistence, or its cost model. -/
namespace OracleMachines.VariableElimination
open OracleMachines.Fragments

def Models (v : Valuation) (cnf : List Clause) : Prop :=
  ∀ c ∈ cnf, Holds v c

def Avoids (x : Nat) (cnf : List Clause) : Prop :=
  ∀ c ∈ cnf, ∀ l ∈ c, l.1 ≠ x

def source (x : Nat) (rest positive negative : List Clause) : List Clause :=
  rest ++ positive.map (fun c => (x, true) :: c) ++
    negative.map (fun c => (x, false) :: c)

def projected (rest positive negative : List Clause) : List Clause :=
  rest ++ positive.flatMap (fun p => negative.map (fun n => p ++ n))

theorem holds_append (v : Valuation) (a b : Clause) :
    Holds v (a ++ b) ↔ Holds v a ∨ Holds v b := by
  simp only [Holds, List.mem_append]
  aesop

theorem holds_update (v : Valuation) (x : Nat) (b : Bool) (c : Clause)
    (avoids : ∀ l ∈ c, l.1 ≠ x) :
    Holds (Function.update v x b) c ↔ Holds v c := by
  constructor
  · rintro ⟨l, hl, hv⟩
    exact ⟨l, hl, by simpa [Function.update, avoids l hl] using hv⟩
  · rintro ⟨l, hl, hv⟩
    exact ⟨l, hl, by simpa [Function.update, avoids l hl] using hv⟩

theorem projected_models (v : Valuation) (rest positive negative : List Clause) :
    Models v (projected rest positive negative) ↔
      Models v rest ∧ ∀ p ∈ positive, ∀ n ∈ negative, Holds v p ∨ Holds v n := by
  simp only [Models, projected, List.mem_append, List.mem_flatMap, List.mem_map]
  constructor
  · intro h
    refine ⟨fun c hc => h c (Or.inl hc), ?_⟩
    intro p hp n hn
    exact (holds_append v p n).mp (h (p ++ n) (Or.inr ⟨p, hp, n, hn, rfl⟩))
  · rintro ⟨rest_ok, pairs⟩ c hc
    rcases hc with hc | ⟨p, hp, n, hn, rfl⟩
    · exact rest_ok c hc
    · exact (holds_append v p n).mpr (pairs p hp n hn)

theorem source_models (v : Valuation) (x : Nat) (b : Bool)
    (rest positive negative : List Clause)
    (hr : Avoids x rest) (hp : Avoids x positive) (hn : Avoids x negative) :
    Models (Function.update v x b) (source x rest positive negative) ↔
      Models v rest ∧ (∀ p ∈ positive, b = true ∨ Holds v p) ∧
        (∀ n ∈ negative, b = false ∨ Holds v n) := by
  have r : Models (Function.update v x b) rest ↔ Models v rest := by
    exact forall₂_congr (fun c hc => holds_update v x b c (hr c hc))
  have pos : ∀ p ∈ positive,
      Holds (Function.update v x b) ((x, true) :: p) ↔ b = true ∨ Holds v p := by
    intro p h
    have tail := holds_update v x b p (hp p h)
    simpa [Holds, List.mem_cons, exists_or, Function.update] using
      or_congr (Iff.rfl : b = true ↔ b = true) tail
  have neg : ∀ n ∈ negative,
      Holds (Function.update v x b) ((x, false) :: n) ↔ b = false ∨ Holds v n := by
    intro n h
    have tail := holds_update v x b n (hn n h)
    simpa [Holds, List.mem_cons, exists_or, Function.update] using
      or_congr (Iff.rfl : b = false ↔ b = false) tail
  simp only [source, Models, List.forall_mem_append, List.forall_mem_map]
  change ((Models (Function.update v x b) rest ∧ _) ∧ _) ↔ _
  rw [r, forall₂_congr pos, forall₂_congr neg]
  tauto

/-- Full opposing-pair resolution preserves exactly existential quantification
of x. Tails and retained clauses must be independent of x. -/
theorem projection_exact (v : Valuation) (x : Nat) (rest positive negative : List Clause)
    (hr : Avoids x rest) (hp : Avoids x positive) (hn : Avoids x negative) :
    Models v (projected rest positive negative) ↔
      ∃ b : Bool, Models (Function.update v x b) (source x rest positive negative) := by
  classical
  rw [projected_models]
  constructor
  · rintro ⟨rest_ok, pairs⟩
    by_cases all_positive : ∀ p ∈ positive, Holds v p
    · refine ⟨false, (source_models v x false rest positive negative hr hp hn).mpr ?_⟩
      exact ⟨rest_ok, fun p h => Or.inr (all_positive p h), fun _ _ => Or.inl rfl⟩
    · push_neg at all_positive
      obtain ⟨p, member, false_tail⟩ := all_positive
      refine ⟨true, (source_models v x true rest positive negative hr hp hn).mpr ?_⟩
      exact ⟨rest_ok, fun _ _ => Or.inl rfl,
        fun n h => Or.inr ((pairs p member n h).resolve_left false_tail)⟩
  · rintro ⟨b, model⟩
    obtain ⟨rest_ok, pos, neg⟩ := (source_models v x b rest positive negative hr hp hn).mp model
    refine ⟨rest_ok, ?_⟩
    intro p hp' n hn'
    cases b with
    | false => exact Or.inl ((pos p hp').resolve_left Bool.false_ne_true)
    | true => exact Or.inr ((neg n hn').resolve_left (by decide))

end OracleMachines.VariableElimination
