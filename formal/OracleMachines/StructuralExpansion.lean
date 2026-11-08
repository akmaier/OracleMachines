import OracleMachines.AffineGrowth

/-! Semantic conditions for expansion without general elimination. These are
conditional theorems, not an executable recognizer or a machine-cost bound.
Native dispatch does not yet use these special cases. -/
namespace OracleMachines.StructuralExpansion

variable {X Y : Type}

def forward (relation : X → Y → Prop) (boundary : X → Prop) (next : Y) : Prop :=
  ∃ old, boundary old ∧ relation old next

theorem forward_empty (relation : X → Y → Prop) (next : Y) :
    ¬ forward relation (fun _ => False) next := by
  rintro ⟨_,impossible,_⟩
  exact impossible

/-- Totality preserves existence, but says nothing about the cost or shape of
the complete successor boundary. -/
theorem total_preserves_nonempty (relation : X → Y → Prop) (boundary : X → Prop)
    (total : ∀ old, ∃ next, relation old next) :
    (∃ next, forward relation boundary next) ↔ ∃ old, boundary old := by
  constructor
  · rintro ⟨_,old,member,_⟩
    exact ⟨old,member⟩
  · rintro ⟨old,member⟩
    obtain ⟨next,related⟩ := total old
    exact ⟨next,old,member,related⟩

/-- A singleton boundary stays a singleton under every total function, including
noninjective functions. No search over old assignments is needed semantically. -/
theorem functional_singleton (function : X → Y) (point : X) (next : Y) :
    forward (fun old new => new = function old) (fun old => old = point) next ↔
      next = function point := by
  constructor
  · rintro ⟨old,rfl,related⟩
    exact related
  · intro related
    exact ⟨point,rfl,related⟩

/-- For arbitrary boundaries, a bijection transports the exact predicate by
its inverse. The representation and evaluation cost of that inverse is extra. -/
theorem bijective_transport (function : X ≃ Y) (boundary : X → Prop) (next : Y) :
    forward (fun old new => new = function old) boundary next ↔
      boundary (function.symm next) := by
  constructor
  · rintro ⟨old,member,rfl⟩
    simpa using member
  · intro member
    exact ⟨function.symm next,member,(function.apply_symm_apply next).symm⟩

/-- Source-linked specialization: the batch must first be proved to encode the
claimed total function, and the whole old history must have the stated boundary.
Neither premise can be replaced by a similar-looking feature vector. -/
theorem affine_point_append {b : Nat} (history : Affine.History b)
    (rows : List (Affine.Row (b+b))) (point : Fin b → Affine.F)
    (function : (Fin b → Affine.F) → (Fin b → Affine.F))
    (point_exact : ∀ old, history.Holds old ↔ old = point)
    (batch_exact : ∀ old next, Affine.Holds rows (Fin.append old next) ↔ next = function old)
    (next : Fin b → Affine.F) :
    (Affine.History.append history rows).Holds next ↔ next = function point := by
  change (∃ old, history.Holds old ∧ Affine.Holds rows (Fin.append old next)) ↔ _
  simp only [point_exact,batch_exact]
  exact functional_singleton function point next

end OracleMachines.StructuralExpansion
