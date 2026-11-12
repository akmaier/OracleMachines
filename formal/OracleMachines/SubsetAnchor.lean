import OracleMachines.SubsumedElimination

/-! Necessary-literal filtering preserves the first matching retained clause.
This abstracts the candidate filter, not the Python index or its resource costs. -/
namespace OracleMachines.SubsetAnchor

/-- Any chosen member of a subsuming clause must occur in its target. -/
theorem anchor_required {α : Type} (small large : List α) (anchor : α)
    (member : anchor ∈ small) (sub : ∀ l ∈ small, l ∈ large) : anchor ∈ large :=
  sub anchor member

/-- Empty clauses are unconditional candidates; nonempty clauses have an anchor. -/
theorem candidate_complete {α : Type} (small large : List α) (anchor : α)
    (member : small ≠ [] → anchor ∈ small) (sub : ∀ l ∈ small, l ∈ large) :
    small = [] ∨ anchor ∈ large := by
  by_cases empty : small = []
  · exact Or.inl empty
  · exact Or.inr (anchor_required small large anchor (member empty) sub)

/-- Removing only impossible candidates keeps the exact first matching witness. -/
theorem first_match_preserved {α : Type} (order : List α) (possible test : α → Bool)
    (complete : ∀ x ∈ order, test x = true → possible x = true) :
    (order.filter possible).find? test = order.find? test := by
  induction order with
  | nil => rfl
  | cons x xs ih =>
    have rest : ∀ y ∈ xs, test y = true → possible y = true := by
      intro y hy ht
      exact complete y (List.mem_cons_of_mem x hy) ht
    have tail := ih rest
    have head : test x = true → possible x = true :=
      complete x (List.mem_cons_self)
    cases hp : possible x <;> cases ht : test x <;>
      simp_all [List.filter, List.find?]

end OracleMachines.SubsetAnchor
