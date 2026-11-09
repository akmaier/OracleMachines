import OracleMachines.SAT
import Mathlib.Data.Fintype.Card

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

/-- A checked refutation under one assumption forces its opposite in every
model. The hypothesis must be proved; an inconclusive probe does not supply it.
This semantic rule does not verify Python unit traces or bound probe cost. -/
theorem failed_condition_forces (f : Formula) (index : Nat) (value : Bool)
    (refuted : ¬ Satisfiable (f.condition index value))
    (v : Nat → Bool) (model : f.eval v = true) : v index = !value := by
  have different : v index ≠ value := by
    intro same
    exact refuted ((satisfiable_condition f index value).mpr ⟨v, same, model⟩)
  cases actual : v index <;> cases value <;> simp_all

/-- Refuting a branch permits exact SAT reduction to the other branch without
using another arbitrary split. Acquiring the refutation still has a cost. -/
theorem satisfiable_failed_condition (f : Formula) (index : Nat) (value : Bool)
    (refuted : ¬ Satisfiable (f.condition index value)) :
    Satisfiable f ↔ Satisfiable (f.condition index (!value)) := by
  constructor
  · rintro ⟨v, model⟩
    exact (satisfiable_condition f index (!value)).mpr
      ⟨v, failed_condition_forces f index value refuted v model, model⟩
  · intro remaining
    obtain ⟨v, _, model⟩ := (satisfiable_condition f index (!value)).mp remaining
    exact ⟨v, model⟩

/-- An implication proved under both Boolean assumptions holds in every parent
model. Each implication is an explicit hypothesis, not a claim that an
inconclusive probe automatically proves a common consequence. -/
theorem common_condition_forces (f : Formula) (index target : Nat) (value : Bool)
    (low : ∀ v, v index = false → f.eval v = true → v target = value)
    (high : ∀ v, v index = true → f.eval v = true → v target = value)
    (v : Nat → Bool) (model : f.eval v = true) : v target = value := by
  cases assumption : v index with
  | false => exact low v assumption model
  | true => exact high v assumption model

/-- Conditioning on a common consequence preserves satisfiability exactly.
The acquisition/checking of the two implications is outside this semantic rule. -/
theorem satisfiable_common_condition (f : Formula) (index target : Nat) (value : Bool)
    (low : ∀ v, v index = false → f.eval v = true → v target = value)
    (high : ∀ v, v index = true → f.eval v = true → v target = value) :
    Satisfiable f ↔ Satisfiable (f.condition target value) := by
  constructor
  · rintro ⟨v, model⟩
    exact (satisfiable_condition f target value).mpr
      ⟨v, common_condition_forces f index target value low high v model, model⟩
  · intro remaining
    obtain ⟨v, _, model⟩ := (satisfiable_condition f target value).mp remaining
    exact ⟨v, model⟩

/-- Replace every variable by a signed representative, throughout the formula.
This syntax operation does not discover or certify the required equivalences. -/
def Formula.signedSubstitute (f : Formula) (rep : Nat → Nat) (flip : Nat → Bool) : Formula :=
  match f with
  | .falsum => .falsum
  | .var i => if flip i then .neg (.var (rep i)) else .var (rep i)
  | .neg g => .neg (g.signedSubstitute rep flip)
  | .conj g h => .conj (g.signedSubstitute rep flip) (h.signedSubstitute rep flip)

theorem signed_substitute_eval (f : Formula) (rep : Nat → Nat) (flip : Nat → Bool)
    (v : Nat → Bool) :
    (f.signedSubstitute rep flip).eval v =
      f.eval (fun i => if flip i then !(v (rep i)) else v (rep i)) := by
  induction f with
  | falsum => rfl
  | var i => cases h : flip i <;> simp [Formula.signedSubstitute, Formula.eval, h]
  | neg g ih => simp [Formula.signedSubstitute, Formula.eval, ih]
  | conj g h ihg ihh => simp [Formula.signedSubstitute, Formula.eval, ihg, ihh]

/-- Opposite consequences of both assumptions give a signed equality. Each
implication is a hypothesis, not a conclusion from mere lack of conflict. -/
theorem opposite_conditions_force_equivalence (f : Formula) (index target : Nat)
    (flip : Bool)
    (low : ∀ v, v index = false → f.eval v = true → v target = flip)
    (high : ∀ v, v index = true → f.eval v = true → v target = !flip)
    (v : Nat → Bool) (model : f.eval v = true) :
    v target = if flip then !(v index) else v index := by
  cases assumption : v index with
  | false => have h := low v assumption model; cases flip <;> simpa using h
  | true => have h := high v assumption model; cases flip <;> simpa using h

/-- Any globally justified signed substitution preserves satisfiability. The
reverse direction supplies a model lift even without the justification; the
forward direction needs all equivalences in every parent model. No resource
bound or refinement of the Python trace checker is asserted. -/
theorem satisfiable_signed_substitute (f : Formula) (rep : Nat → Nat) (flip : Nat → Bool)
    (compatible : ∀ v, f.eval v = true → ∀ i,
      v i = if flip i then !(v (rep i)) else v (rep i)) :
    Satisfiable f ↔ Satisfiable (f.signedSubstitute rep flip) := by
  constructor
  · rintro ⟨v, model⟩
    refine ⟨v, ?_⟩
    rw [signed_substitute_eval]
    have agree : (fun i => if flip i then !(v (rep i)) else v (rep i)) = v := by
      funext i
      exact (compatible v model i).symm
    simpa [agree] using model
  · rintro ⟨v, model⟩
    exact ⟨fun i => if flip i then !(v (rep i)) else v (rep i),
      (signed_substitute_eval f rep flip v).symm.trans model⟩

/-- Instantiate Left with selected choice groups and Right with their possible
resources. This is the cardinality obstruction behind a Hall certificate, not
a proof of the Python CNF recognizer or matching algorithm. -/
theorem no_injective_choice_of_card_lt (Left Right : Type)
    [Fintype Left] [Fintype Right]
    (deficient : Fintype.card Right < Fintype.card Left) :
    ¬ ∃ f : Left → Right, Function.Injective f := by
  rintro ⟨f, hf⟩
  exact (not_lt_of_ge (Fintype.card_le_of_injective f hf)) deficient

/-- Satisfaction of an unsigned (positive) clause. Kept separate from the
Python signed-literal encoding; no parser refinement is asserted here. -/
def PositiveClauseHolds (clause : List Nat) (v : Nat → Bool) : Prop :=
  ∃ i ∈ clause, v i = true

theorem positive_clause_subsumption (small large : List Nat) (v : Nat → Bool)
    (included : small ⊆ large) (satisfied : PositiveClauseHolds small v) :
    PositiveClauseHolds large v := by
  obtain ⟨i, hi, hv⟩ := satisfied
  exact ⟨i, included hi, hv⟩

/-- Every source clause has a retained subset, and every retained clause comes
from the source. These hypotheses preserve all models, not only SAT status. -/
theorem positive_core_models (source core : List (List Nat)) (v : Nat → Bool)
    (retained : core ⊆ source)
    (covered : ∀ c ∈ source, ∃ d ∈ core, d ⊆ c) :
    (∀ c ∈ source, PositiveClauseHolds c v) ↔
      (∀ c ∈ core, PositiveClauseHolds c v) := by
  constructor
  · intro h c hc
    exact h c (retained hc)
  · intro h c hc
    obtain ⟨d, hd, included⟩ := covered c hc
    exact positive_clause_subsumption d c v included (h d hd)

/-- The same retained core covers an added clause only with a fresh subset
witness. Deleting or weakening its witness does not satisfy this hypothesis. -/
theorem positive_core_extension (source core : List (List Nat)) (added : List Nat)
    (covered : ∀ c ∈ source, ∃ d ∈ core, d ⊆ c)
    (witness : ∃ d ∈ core, d ⊆ added) :
    ∀ c ∈ added :: source, ∃ d ∈ core, d ⊆ c := by
  intro c hc
  rcases List.mem_cons.mp hc with h | h
  · subst c
    exact witness
  · exact covered c h

/-- A whole append-only history of covered positive clauses preserves every
base model. An unchanged background constraint can be conjoined on both sides.
This is a semantic invariant, not a proof of the SQLite history implementation. -/
theorem positive_history_models (base additions : List (List Nat)) (v : Nat → Bool)
    (covered : ∀ c ∈ additions, ∃ d ∈ base, d ⊆ c) :
    (∀ c ∈ base ++ additions, PositiveClauseHolds c v) ↔
      (∀ c ∈ base, PositiveClauseHolds c v) := by
  apply positive_core_models (base ++ additions) base v
  · intro c hc
    exact List.mem_append_left additions hc
  · intro c hc
    rcases List.mem_append.mp hc with h | h
    · exact ⟨c, h, fun _ hi => hi⟩
    · exact covered c h

/-- A refuted base remains refuted after arbitrary conjunctive additions.
The constructor/proof cost of the base is not bounded by this semantic rule. -/
theorem unsatisfiable_conj_extension (base added : Formula)
    (refuted : ¬ Satisfiable base) : ¬ Satisfiable (.conj base added) := by
  rintro ⟨v, hv⟩
  have both : base.eval v = true ∧ added.eval v = true := by
    simpa [Formula.eval] using hv
  exact refuted ⟨v, both.1⟩

/-- One fixed checked assignment suffices for a whole compatible history.
This preserves a model, not the set of all base models. -/
theorem fixed_model_history (base : Formula) (additions : List Formula)
    (v : Nat → Bool) (base_holds : base.eval v = true)
    (compatible : ∀ f ∈ additions, f.eval v = true) :
    (additions.foldl Formula.conj base).eval v = true := by
  induction additions generalizing base with
  | nil => exact base_holds
  | cons f rest ih =>
    apply ih (.conj base f)
    · simp [Formula.eval, base_holds, compatible f (by simp)]
    · intro g hg
      exact compatible g (by simp [hg])

theorem satisfiable_fixed_model_history (base : Formula) (additions : List Formula)
    (v : Nat → Bool) (base_holds : base.eval v = true)
    (compatible : ∀ f ∈ additions, f.eval v = true) :
    Satisfiable (additions.foldl Formula.conj base) := by
  exact ⟨v, fixed_model_history base additions v base_holds compatible⟩

theorem unsatisfiable_history (base : Formula) (additions : List Formula)
    (refuted : ¬ Satisfiable base) :
    ¬ Satisfiable (additions.foldl Formula.conj base) := by
  induction additions generalizing base with
  | nil => exact refuted
  | cons f rest ih =>
    exact ih (.conj base f) (unsatisfiable_conj_extension base f refuted)

/-- Signed literals are variable/polarity pairs here, not Python integers. -/
def SignedClauseHolds (clause : List (Nat × Bool)) (v : Nat → Bool) : Prop :=
  ∃ lit ∈ clause, v lit.1 = lit.2

/-- A proved consequence under one assumption licenses a binary clause in the
original source. The implication hypothesis must come from a checked proof. -/
theorem probe_implication_entails_clause (source : List (List (Nat × Bool)))
    (index target : Nat) (assumption consequence : Bool)
    (implied : ∀ v, (∀ c ∈ source, SignedClauseHolds c v) →
      v index = assumption → v target = consequence)
    (v : Nat → Bool) (model : ∀ c ∈ source, SignedClauseHolds c v) :
    SignedClauseHolds [(index, !assumption), (target, consequence)] v := by
  by_cases same : v index = assumption
  · exact ⟨(target, consequence), by simp, implied v model same⟩
  · refine ⟨(index, !assumption), by simp, ?_⟩
    cases actual : v index <;> cases assumption <;> simp_all

/-- A batch whose clauses are all justified on the original source preserves
every model. This excludes circular justification by the newly added batch. -/
theorem entailed_signed_batch_models (source additions : List (List (Nat × Bool)))
    (entailed : ∀ a ∈ additions, ∀ v,
      (∀ c ∈ source, SignedClauseHolds c v) → SignedClauseHolds a v)
    (v : Nat → Bool) :
    (∀ c ∈ source ++ additions, SignedClauseHolds c v) ↔
      (∀ c ∈ source, SignedClauseHolds c v) := by
  constructor
  · intro model c hc
    exact model c (List.mem_append_left additions hc)
  · intro model c hc
    rcases List.mem_append.mp hc with original | added
    · exact model c original
    · exact entailed c added v model

/-- A local unit reason under a partial assignment. Its source clause is
explicit; extending the source never removes that reason. -/
def SignedUnitReason (source : List (List (Nat × Bool)))
    (assigned : Nat → Option Bool) (lit : Nat × Bool) : Prop :=
  assigned lit.1 = none ∧ ∃ clause ∈ source, lit ∈ clause ∧
    ∀ other ∈ clause, other ≠ lit → assigned other.1 = some (!other.2)

/-- A sequence of valid unit steps, including the empty sequence. -/
inductive SignedUnitDerivation (source : List (List (Nat × Bool))) :
    (Nat → Option Bool) → (Nat → Option Bool) → Prop where
  | refl (assigned) : SignedUnitDerivation source assigned assigned
  | step (assigned final) (lit : Nat × Bool) :
      SignedUnitReason source assigned lit →
      SignedUnitDerivation source (Function.update assigned lit.1 (some lit.2)) final →
      SignedUnitDerivation source assigned final

/-- Syntactic unit fixed point: each clause is satisfied or has at least two
unassigned literal occurrences. Normalized CNFs have no repeated variables
within a non-tautological clause. This property alone does not establish SAT. -/
def SignedUnitFixedPoint (source : List (List (Nat × Bool)))
    (assigned : Nat → Option Bool) : Prop :=
  ∀ clause ∈ source,
    (∃ lit ∈ clause, assigned lit.1 = some lit.2) ∨
    2 ≤ (clause.filter (fun lit => (assigned lit.1).isNone)).length

theorem signed_unit_reason_append (source additions : List (List (Nat × Bool)))
    (assigned : Nat → Option Bool) (lit : Nat × Bool)
    (reason : SignedUnitReason source assigned lit) :
    SignedUnitReason (source ++ additions) assigned lit := by
  obtain ⟨unset, clause, member, occurs, forced⟩ := reason
  exact ⟨unset, clause, List.mem_append_left additions member, occurs, forced⟩

theorem signed_unit_derivation_append (source additions : List (List (Nat × Bool)))
    (initial final : Nat → Option Bool)
    (derivation : SignedUnitDerivation source initial final) :
    SignedUnitDerivation (source ++ additions) initial final := by
  induction derivation with
  | refl assigned => exact .refl assigned
  | step assigned final lit reason _ ih =>
    exact .step assigned final lit (signed_unit_reason_append source additions assigned lit reason) ih

/-- Once the original fixed point is checked, only added clauses can invalidate
it. Both directions hold; an active addition rules out this exact reuse. -/
theorem signed_unit_fixed_point_append (source additions : List (List (Nat × Bool)))
    (assigned : Nat → Option Bool) (closed : SignedUnitFixedPoint source assigned) :
    SignedUnitFixedPoint (source ++ additions) assigned ↔ SignedUnitFixedPoint additions assigned := by
  constructor
  · intro combined clause member
    exact combined clause (List.mem_append_right source member)
  · intro delta clause member
    rcases List.mem_append.mp member with old | added
    · exact closed clause old
    · exact delta clause added

theorem checked_unit_closure_append (source additions : List (List (Nat × Bool)))
    (initial final : Nat → Option Bool)
    (derivation : SignedUnitDerivation source initial final)
    (closed : SignedUnitFixedPoint source final)
    (delta : SignedUnitFixedPoint additions final) :
    SignedUnitDerivation (source ++ additions) initial final ∧
      SignedUnitFixedPoint (source ++ additions) final := by
  exact ⟨signed_unit_derivation_append source additions initial final derivation,
    (signed_unit_fixed_point_append source additions final closed).mpr delta⟩

def SignedOccurs (source : List (List (Nat × Bool))) (lit : Nat × Bool) : Prop :=
  ∃ clause ∈ source, lit ∈ clause

theorem signed_occurs_append (source : List (List (Nat × Bool)))
    (added : List (Nat × Bool)) (lit : Nat × Bool) :
    SignedOccurs (source ++ [added]) lit ↔ SignedOccurs source lit ∨ lit ∈ added := by
  simp only [SignedOccurs, List.mem_append, List.mem_singleton]
  constructor
  · rintro ⟨clause, hc | hc, hl⟩
    · exact Or.inl ⟨clause, hc, hl⟩
    · subst clause; exact Or.inr hl
  · rintro (⟨clause, hc, hl⟩ | hl)
    · exact ⟨clause, Or.inl hc, hl⟩
    · exact ⟨added, Or.inr rfl, hl⟩

/-- Assigning a pure literal true cannot invalidate a previous clause. Absence
is required in the whole parent source, including all earlier additions. -/
theorem pure_repair_preserves (source : List (List (Nat × Bool)))
    (v : Nat → Bool) (index : Nat) (polarity : Bool)
    (model : ∀ c ∈ source, SignedClauseHolds c v)
    (absent : ¬ SignedOccurs source (index, !polarity)) :
    ∀ c ∈ source, SignedClauseHolds c
      (fun i => if i = index then polarity else v i) := by
  intro c hc
  obtain ⟨⟨i, b⟩, member, satisfied⟩ := model c hc
  refine ⟨(i, b), member, ?_⟩
  by_cases same : i = index
  · have sign : b = polarity := by
      by_contra different
      have opposite : b = !polarity := by
        cases b <;> cases polarity <;> simp_all
      exact absent ⟨c, hc, by simpa [same, opposite] using member⟩
    simp [same, sign]
  · simpa [same] using satisfied

theorem pure_repair_extension (source : List (List (Nat × Bool)))
    (added : List (Nat × Bool)) (v : Nat → Bool) (index : Nat) (polarity : Bool)
    (model : ∀ c ∈ source, SignedClauseHolds c v)
    (absent : ¬ SignedOccurs source (index, !polarity))
    (repairs : (index, polarity) ∈ added) :
    ∀ c ∈ source ++ [added], SignedClauseHolds c
      (fun i => if i = index then polarity else v i) := by
  intro c hc
  rcases List.mem_append.mp hc with old | new
  · exact pure_repair_preserves source v index polarity model absent c old
  · have same : c = added := List.mem_singleton.mp new
    subst c
    exact ⟨(index, polarity), repairs, by simp⟩

/-- A clause affected by a flip is protected by the new literal or by an
unchanged true literal. This permits nonpure repairs and tautologies. -/
theorem affected_repair_preserves (source : List (List (Nat × Bool)))
    (v : Nat → Bool) (index : Nat) (polarity : Bool)
    (model : ∀ c ∈ source, SignedClauseHolds c v)
    (protection : ∀ c ∈ source, (index, !polarity) ∈ c →
      (index, polarity) ∈ c ∨ ∃ lit ∈ c, lit.1 ≠ index ∧ v lit.1 = lit.2) :
    ∀ c ∈ source, SignedClauseHolds c
      (fun i => if i = index then polarity else v i) := by
  intro c hc
  obtain ⟨⟨i, b⟩, member, satisfied⟩ := model c hc
  by_cases same : i = index
  · by_cases sign : b = polarity
    · exact ⟨(i, b), member, by simp [same, sign]⟩
    · have opposite : b = !polarity := by
        cases b <;> cases polarity <;> simp_all
      have occurs : (index, !polarity) ∈ c := by simpa [same, opposite] using member
      rcases protection c hc occurs with positive | ⟨lit, hl, different, true_lit⟩
      · exact ⟨(index, polarity), positive, by simp⟩
      · exact ⟨lit, hl, by simpa [different] using true_lit⟩
  · exact ⟨(i, b), member, by simpa [same] using satisfied⟩

theorem affected_repair_extension (source : List (List (Nat × Bool)))
    (added : List (Nat × Bool)) (v : Nat → Bool) (index : Nat) (polarity : Bool)
    (model : ∀ c ∈ source, SignedClauseHolds c v)
    (protection : ∀ c ∈ source, (index, !polarity) ∈ c →
      (index, polarity) ∈ c ∨ ∃ lit ∈ c, lit.1 ≠ index ∧ v lit.1 = lit.2)
    (repairs : (index, polarity) ∈ added) :
    ∀ c ∈ source ++ [added], SignedClauseHolds c
      (fun i => if i = index then polarity else v i) := by
  intro c hc
  rcases List.mem_append.mp hc with old | new
  · exact affected_repair_preserves source v index polarity model protection c old
  · have same : c = added := List.mem_singleton.mp new
    subst c
    exact ⟨(index, polarity), repairs, by simp⟩

/-- Simultaneous changes are checked at their final values. Every clause
touching the changed set is protected; other clauses retain an old witness.
This does not assume that any intermediate single-variable update is valid. -/
theorem joint_repair_preserves (source : List (List (Nat × Bool)))
    (v updated : Nat → Bool) (changed : Nat → Prop)
    (model : ∀ c ∈ source, SignedClauseHolds c v)
    (unchanged : ∀ i, ¬ changed i → updated i = v i)
    (checked : ∀ c ∈ source, (∃ lit ∈ c, changed lit.1) → SignedClauseHolds c updated) :
    ∀ c ∈ source, SignedClauseHolds c updated := by
  intro c hc
  obtain ⟨lit, member, satisfied⟩ := model c hc
  by_cases affected : changed lit.1
  · exact checked c hc ⟨lit, member, affected⟩
  · exact ⟨lit, member, (unchanged lit.1 affected).trans satisfied⟩

theorem joint_repair_extension (source : List (List (Nat × Bool)))
    (added : List (Nat × Bool)) (v updated : Nat → Bool) (changed : Nat → Prop)
    (model : ∀ c ∈ source, SignedClauseHolds c v)
    (unchanged : ∀ i, ¬ changed i → updated i = v i)
    (checked : ∀ c ∈ source, (∃ lit ∈ c, changed lit.1) → SignedClauseHolds c updated)
    (repairs : SignedClauseHolds added updated) :
    ∀ c ∈ source ++ [added], SignedClauseHolds c updated := by
  intro c hc
  rcases List.mem_append.mp hc with old | new
  · exact joint_repair_preserves source v updated changed model unchanged checked c old
  · simpa [List.mem_singleton.mp new] using repairs

end OracleMachines.SAT
