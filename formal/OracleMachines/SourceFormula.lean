import OracleMachines.SourcePatch

/-! The complete original formula represented by buckets and accepted edits.
These flattening functions occur only in specifications; native warm decisions
continue to read cached summaries. -/
namespace OracleMachines.SourceFormula
open OracleMachines.Layered OracleMachines.SourceNodes OracleMachines.SourcePatch

abbrev Buckets := Nat → Option Clauses

/-- Ordered flattening of one complete balanced interval. Absent buckets and
padding contribute no clauses. This is not run by the native checker. -/
def flatten (start : Nat) : Nat → Buckets → List (Array Int)
  | 0, source => (source start).getD #[] |>.toList
  | height+1, source => flatten start height source ++ flatten (start+2^height) height source

theorem flatten_congr (start height : Nat) (a b : Buckets)
    (same : ∀ edge, start ≤ edge → edge < start+2^height → a edge = b edge) :
    flatten start height a = flatten start height b := by
  induction height generalizing start with
  | zero => simp only [flatten,same start (by omega) (by simp)]
  | succ height ih =>
    simp only [flatten]
    have power : 2^(height+1) = 2^height+2^height := by simp [pow_succ]; omega
    congr 1
    · apply ih
      intro edge lower upper
      exact same edge lower (by rw [power]; omega)
    · apply ih
      intro edge lower upper
      exact same edge (by omega) (by rw [power]; omega)

theorem flatten_source {layers : Array (Array Nat)} {width start height : Nat}
    (source : OriginalTree layers width start height) :
    flatten start height (bucket source) = source.clauses := by
  induction source with
  | leaf => simp [flatten,bucket,OriginalTree.clauses]
  | pad => simp [flatten,bucket,OriginalTree.clauses]
  | @branch start height left right il ir =>
    simp only [flatten,OriginalTree.clauses]
    have hl : flatten start height (bucket (.branch left right)) = flatten start height (bucket left) := by
      apply flatten_congr
      intro edge _ upper
      simp [bucket,upper]
    have hr : flatten (start+2^height) height (bucket (.branch left right)) =
        flatten (start+2^height) height (bucket right) := by
      apply flatten_congr
      intro edge lower _
      simp [bucket,Nat.not_lt.mpr lower]
    rw [hl,hr,il,ir]

theorem bucket_present {layers : Array (Array Nat)} {width start height : Nat}
    (source : OriginalTree layers width start height) (edge : Nat) :
    (∃ clauses, bucket source edge = some clauses) ↔ start ≤ edge ∧ edge < start+2^height := by
  induction source with
  | leaf => simp only [bucket]; split <;> simp_all; omega
  | pad => simp only [bucket]; split <;> simp_all; omega
  | @branch start height left right il ir =>
    have power : 2^(height+1) = 2^height+2^height := by simp [pow_succ]; omega
    simp only [bucket]
    split
    · rw [il,power]; omega
    · rw [ir,power]; omega

theorem bucket_padding {layers : Array (Array Nat)} {width start height : Nat}
    (source : OriginalTree layers width start height) (edge : Nat)
    (lower : start ≤ edge) (upper : edge < start+2^height) (padding : layers.size-1 ≤ edge) :
    bucket source edge = some #[] := by
  induction source with
  | leaf => simp only [pow_zero] at upper; omega
  | pad here _ =>
    have same : edge = here := by simp only [pow_zero] at upper; omega
    simp [bucket,same]
  | @branch start height left right il ir =>
    have power : 2^(height+1) = 2^height+2^height := by simp [pow_succ]; omega
    simp only [bucket]
    split
    · apply il lower; assumption
    · apply ir (by omega)
      rw [power] at upper
      omega

/-- First matching replacement. Accepted patches give the same bucket for every
matching entry, so this specification needs no uniqueness assumption. -/
def replaceBuckets (old : Buckets) : Edits → Buckets
  | [], edge => old edge
  | (index,clauses)::rest, edge => if edge = index then some clauses else replaceBuckets old rest edge

theorem patched_buckets {layers : Array (Array Nat)} {width : Nat}
    {old new : CheckedNode layers width} {edits : Edits} (patch : Patched old new edits) :
    ∀ edge, bucket new.source edge = replaceBuckets (bucket old.source) edits edge := by
  intro edge
  have helper : ∀ (xs : Edits),
      (∀ clauses, (edge,clauses) ∈ xs → bucket new.source edge = some clauses) →
      ((∀ clauses, (edge,clauses) ∉ xs) → bucket new.source edge = bucket old.source edge) →
      bucket new.source edge = replaceBuckets (bucket old.source) xs edge := by
    intro xs
    induction xs with
    | nil => intro _ unchanged; exact unchanged (by simp)
    | cons entry rest ih =>
      rcases entry with ⟨index,clauses⟩
      intro replaced unchanged
      simp only [replaceBuckets]
      split
      · rename_i same
        exact replaced clauses (by simp [same])
      · rename_i different
        apply ih
        · intro c member; exact replaced c (by simp [member])
        · intro absent; exact unchanged (by simpa [different] using absent)
  exact helper edits (patch.replaced edge) (patch.unchanged edge)

def updatedFormula {layers : Array (Array Nat)} {width : Nat}
    (old : CheckedNode layers width) (edits : Edits) : Array (Array Int) :=
  (flatten old.start old.height (replaceBuckets (bucket old.source) edits)).toArray

theorem patched_formula {layers : Array (Array Nat)} {width : Nat}
    {old new : CheckedNode layers width} {edits : Edits} (patch : Patched old new edits) :
    new.source.clauses.toArray = updatedFormula old edits := by
  have same : bucket new.source = replaceBuckets (bucket old.source) edits := funext (patched_buckets patch)
  unfold updatedFormula
  rw [← flatten_source new.source,same]
  congr 2
  · exact patch.start.symm
  · exact patch.height.symm

theorem patched_decide {layers : Array (Array Nat)} {width : Nat}
    {old new : CheckedNode layers width} {edits : Edits} (patch : Patched old new edits)
    (layout : CheckedLayout layers width) :
    new.decide = true ↔ ∃ valuation, sourceCNFEval (updatedFormula old edits) valuation = true := by
  rw [new.decide_exact layout,patched_formula patch]

theorem patched_unsat {layers : Array (Array Nat)} {width : Nat}
    {old new : CheckedNode layers width} {edits : Edits} (patch : Patched old new edits)
    (layout : CheckedLayout layers width) :
    new.decide = false ↔ ¬ ∃ valuation, sourceCNFEval (updatedFormula old edits) valuation = true := by
  rw [← patched_decide patch layout]
  cases new.decide <;> decide

end OracleMachines.SourceFormula
