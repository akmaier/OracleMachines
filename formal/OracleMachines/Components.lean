import OracleMachines.CDCL
import Mathlib.Data.Nat.Pairing

/-!
# Reusable conjuncts and small-interface expansion

Renamed component refutations transfer only through checked conjunct embeddings.
For a family with disjoint private indices and b shared indices, component
relations on the shared interface compose by intersection. The exponential
parameter is interface/private component width, not total global variable count.
-/
namespace OracleMachines.SAT

def Formula.rename : Formula → (Nat → Nat) → Formula
  | .falsum, _ => .falsum
  | .var i, r => .var (r i)
  | .neg f, r => .neg (f.rename r)
  | .conj f g, r => .conj (f.rename r) (g.rename r)

theorem eval_rename (f : Formula) (r : Nat → Nat) (v : Nat → Bool) :
    (f.rename r).eval v = f.eval (fun i => v (r i)) := by
  induction f <;> simp_all [Formula.rename, Formula.eval]

theorem rename_unsat (f : Formula) (r : Nat → Nat) (h : ¬ Satisfiable f) :
    ¬ Satisfiable (f.rename r) := by
  rintro ⟨v, hv⟩
  exact h ⟨fun i => v (r i), (eval_rename f r v).symm.trans hv⟩

def conjoin : List Formula → Formula
  | [] => .neg .falsum
  | f :: fs => .conj f (conjoin fs)

theorem conjoin_eval (fs : List Formula) (v : Nat → Bool) :
    (conjoin fs).eval v = true ↔ ∀ f ∈ fs, f.eval v = true := by
  induction fs <;> simp_all [conjoin, Formula.eval]

/-- Paths may descend through conjunctions only. -/
def conjunctAt : Formula → Word → Option Formula
  | f, [] => some f
  | .conj f _, false :: path => conjunctAt f path
  | .conj _ g, true :: path => conjunctAt g path
  | _, _ => none

theorem conjunctAt_entails (f g : Formula) (path : Word) (v : Nat → Bool)
    (found : conjunctAt f path = some g) (sat : f.eval v = true) : g.eval v = true := by
  induction path generalizing f with
  | nil =>
    simp only [conjunctAt, Option.some.injEq] at found
    subst g
    exact sat
  | cons b path ih =>
    cases f <;> cases b <;> simp [conjunctAt] at found
    all_goals simp only [Formula.eval, Bool.and_eq_true] at sat
    · exact ih _ found sat.1
    · exact ih _ found sat.2

def selectedConjunction (f : Formula) (paths : List Word) : Option Formula :=
  conjoin <$> paths.mapM (conjunctAt f)

theorem selectedConjunction_entails (f g : Formula) (paths : List Word) (v : Nat → Bool)
    (found : selectedConjunction f paths = some g) (sat : f.eval v = true) :
    g.eval v = true := by
  unfold selectedConjunction at found
  cases hs : paths.mapM (conjunctAt f) with
  | none => simp [hs] at found
  | some fs =>
    simp [hs] at found
    subst g
    apply (conjoin_eval fs v).mpr
    have all : ∀ g ∈ fs, g.eval v = true := by
      induction paths generalizing fs with
      | nil => simp at hs; subst fs; simp
      | cons path rest ih =>
        simp only [List.mapM_cons, Option.bind_eq_bind] at hs
        cases hp : conjunctAt f path with
        | none => simp [hp] at hs
        | some g =>
          cases hr : rest.mapM (conjunctAt f) with
          | none => simp [hp, hr] at hs
          | some gs =>
            simp [hp, hr] at hs
            subst fs
            intro a ha
            rcases List.mem_cons.mp ha with rfl | ha
            · exact conjunctAt_entails f a path v hp sat
            · exact ih gs hr a ha
    exact all

def componentEmbedding (f base : Formula) (paths : List Word) (ids : List Nat) : Bool :=
  selectedConjunction f paths == some (base.rename (fun i => ids.getD i 0))

theorem componentEmbedding_unsat (f base : Formula) (paths : List Word) (ids : List Nat)
    (embedded : componentEmbedding f base paths ids = true) (unsat : ¬ Satisfiable base) :
    ¬ Satisfiable f := by
  have found : selectedConjunction f paths = some (base.rename (fun i => ids.getD i 0)) := by
    simpa [componentEmbedding] using embedded
  rintro ⟨v, hv⟩
  exact rename_unsat base _ unsat ⟨v, selectedConjunction_entails f _ paths v found hv⟩

def componentLRAT (f base : Formula) (paths : List Word) (ids : List Nat)
    (proof : Array Std.Tactic.BVDecide.LRAT.IntAction) : Bool :=
  componentEmbedding f base paths ids && checkLRAT base proof

theorem componentLRAT_sound (f base : Formula) (paths : List Word) (ids : List Nat)
    (proof : Array Std.Tactic.BVDecide.LRAT.IntAction) (h : componentLRAT f base paths ids proof = true) :
    ¬ Satisfiable f := by
  have hh : componentEmbedding f base paths ids = true ∧ checkLRAT base proof = true := by
    simpa only [componentLRAT, Bool.and_eq_true] using h
  exact componentEmbedding_unsat f base paths ids hh.1 (checkLRAT_sound base proof hh.2)

/-- Every component has b shared indices, then its own private indices. -/
def componentIndex (b i j : Nat) : Nat := if j < b then j else b + Nat.pair i (j - b)

def localValuation (b : Nat) (boundary localValues : Nat → Bool) (j : Nat) : Bool :=
  if j < b then boundary j else localValues (j - b)

def joinedValuation {m : Nat} (b : Nat) (boundary : Nat → Bool)
    (localValues : Fin m → Nat → Bool) (j : Nat) : Bool :=
  if j < b then boundary j else
    let index := Nat.unpair (j - b)
    if h : index.1 < m then localValues ⟨index.1, h⟩ index.2 else false

theorem joined_component {m : Nat} (b : Nat) (boundary : Nat → Bool)
    (localValues : Fin m → Nat → Bool) (i : Fin m) (j : Nat) :
    joinedValuation b boundary localValues (componentIndex b i j) =
      localValuation b boundary (localValues i) j := by
  by_cases h : j < b
  · simp [componentIndex, localValuation, joinedValuation, h]
  · simp [componentIndex, localValuation, joinedValuation, h, Nat.not_lt.mpr (Nat.le_add_right _ _)]

def componentSystem {m : Nat} (b : Nat) (fs : Fin m → Formula) : Formula :=
  conjoin (List.ofFn (fun i => (fs i).rename (componentIndex b i)))

theorem componentSystem_sat_iff {m : Nat} (b : Nat) (fs : Fin m → Formula) :
    Satisfiable (componentSystem b fs) ↔
      ∃ boundary : Nat → Bool, ∀ i, ∃ localValues : Nat → Bool,
        (fs i).eval (localValuation b boundary localValues) = true := by
  constructor
  · rintro ⟨v, hv⟩
    have all := (conjoin_eval _ v).mp hv
    refine ⟨v, fun i => ⟨fun j => v (b + Nat.pair i j), ?_⟩⟩
    have hi := all ((fs i).rename (componentIndex b i)) (List.mem_ofFn.mpr ⟨i, rfl⟩)
    rw [eval_rename] at hi
    simpa only [componentIndex, localValuation, apply_ite] using hi
  · rintro ⟨boundary, witnesses⟩
    classical
    let localValues := fun i => Classical.choose (witnesses i)
    let v := joinedValuation b boundary localValues
    refine ⟨v, (conjoin_eval _ v).mpr ?_⟩
    intro f hf
    rcases List.mem_ofFn.mp hf with ⟨i, rfl⟩
    rw [eval_rename]
    have agreement : (fun j => v (componentIndex b i j)) = localValuation b boundary (localValues i) := by
      funext j
      exact joined_component b boundary localValues i j
    rw [agreement]
    exact Classical.choose_spec (witnesses i)

def boundaryRelation (f : Formula) (b k : Nat) (boundary : Word) : Bool :=
  (words k).any (fun localValues => f.eval (localValuation b (valuation boundary) (valuation localValues)))

theorem boundaryRelation_exact (f : Formula) (b k : Nat) (boundary : Word)
    (width : f.width ≤ b + k) :
    boundaryRelation f b k boundary = true ↔
      ∃ localValues : Nat → Bool, f.eval (localValuation b (valuation boundary) localValues) = true := by
  simp only [boundaryRelation, List.any_eq_true]
  constructor
  · rintro ⟨localValues, _, hp⟩
    exact ⟨valuation localValues, hp⟩
  · rintro ⟨localValues, hp⟩
    let assignment := List.ofFn (fun j : Fin k => localValues j)
    refine ⟨assignment, by simp [assignment], ?_⟩
    have agree := eval_agrees f
      (localValuation b (valuation boundary) (valuation assignment))
      (localValuation b (valuation boundary) localValues) (by
        intro j hj
        by_cases hb : j < b
        · simp [localValuation, hb]
        · simp only [localValuation, hb, ↓reduceIte]
          exact valuation_ofFn k localValues (j - b) (by omega))
    exact agree.trans hp

def survivingBoundaries (b k : Nat) (fs : List Formula) : List Word :=
  (words b).filter (fun boundary => fs.all (fun f => boundaryRelation f b k boundary))

theorem surviving_expand (b k : Nat) (fs : List Formula) (next : Formula) :
    survivingBoundaries b k (fs ++ [next]) =
      (survivingBoundaries b k fs).filter (boundaryRelation next b k) := by
  simp [survivingBoundaries, List.filter_filter, Bool.and_comm]

theorem surviving_preserved (b k : Nat) (fs : List Formula) (next : Formula) (a : Word)
    (h : a ∈ survivingBoundaries b k (fs ++ [next])) : a ∈ survivingBoundaries b k fs := by
  rw [surviving_expand] at h
  exact (List.mem_filter.mp h).1

theorem surviving_size (b k : Nat) (fs : List Formula) :
    (survivingBoundaries b k fs).length ≤ 2 ^ b := by
  exact (List.length_filter_le _ _).trans_eq (length_words b)

/-- Finite interface summaries decide the actual composed SAT instance. -/
theorem surviving_exact {m : Nat} (b k : Nat) (fs : Fin m → Formula)
    (width : ∀ i, (fs i).width ≤ b + k) :
    (∃ a, a ∈ survivingBoundaries b k (List.ofFn fs)) ↔
      Satisfiable (componentSystem b fs) := by
  rw [componentSystem_sat_iff]
  constructor
  · rintro ⟨a, ha⟩
    have all := (List.mem_filter.mp ha).2
    simp only [List.all_eq_true] at all
    exact ⟨valuation a, fun i => (boundaryRelation_exact _ b k a (width i)).mp
      (all (fs i) (List.mem_ofFn.mpr ⟨i, rfl⟩))⟩
  · rintro ⟨boundary, h⟩
    let a := List.ofFn (fun j : Fin b => boundary j)
    refine ⟨a, List.mem_filter.mpr ⟨by simp [a], ?_⟩⟩
    simp only [List.all_eq_true]
    intro f hf
    rcases List.mem_ofFn.mp hf with ⟨i, rfl⟩
    apply (boundaryRelation_exact _ b k a (width i)).mpr
    rcases h i with ⟨localValues, hv⟩
    refine ⟨localValues, ?_⟩
    have agree := eval_agrees (fs i)
      (localValuation b (valuation a) localValues)
      (localValuation b boundary localValues) (by
        intro j _
        by_cases hj : j < b
        · simp only [localValuation, hj, ↓reduceIte]
          exact valuation_ofFn b boundary j hj
        · simp [localValuation, hj])
    exact agree.trans hv

theorem repeated_component (b k : Nat) (fs : List Formula) (f : Formula) :
    survivingBoundaries b k (fs ++ [f, f]) = survivingBoundaries b k (fs ++ [f]) := by
  simp [survivingBoundaries]

theorem equivalent_summaries (b k : Nat) (fs : List Formula) (f g : Formula)
    (same : ∀ a ∈ words b, boundaryRelation f b k a = boundaryRelation g b k a) :
    survivingBoundaries b k (fs ++ [f]) = survivingBoundaries b k (fs ++ [g]) := by
  apply List.filter_congr
  intro a ha
  simp [same a ha]

/-- An explicit truth-table representation, before byte compression. -/
def summaryTable (f : Formula) (b k : Nat) : List Bool :=
  (words b).map (boundaryRelation f b k)

theorem summaryTable_size (f : Formula) (b k : Nat) :
    (summaryTable f b k).length = 2 ^ b := by
  simp [summaryTable, length_words]

/-- Abstract budget: d distinct shapes, m occurrences, size at most s.
Each shape is acquired once by exhaustive local/interface evaluation; each
occurrence is combined once. Parsing, mappings and certificate I/O are separate. -/
def structuralBudget (b k s d m : Nat) : Nat := d * (2 ^ (b + k) * s) + m * 2 ^ b

theorem structuralBudget_expand (b k s d m : Nat) :
    structuralBudget b k s d (m + 1) = structuralBudget b k s d m + 2 ^ b := by
  simp [structuralBudget, Nat.add_mul, Nat.add_assoc]

theorem structuralBudget_linear (b k s d m : Nat) (distinct : d ≤ m) :
    structuralBudget b k s d m ≤ m * (2 ^ (b + k) * s + 2 ^ b) := by
  unfold structuralBudget
  rw [Nat.mul_add]
  exact Nat.add_le_add_right (Nat.mul_le_mul_right _ distinct) _

/-- d relation tables plus one surviving relation; occurrence references are
charged separately. This is a representation bound, not an entropy claim. -/
def summaryBits (b d : Nat) : Nat := (d + 1) * 2 ^ b

theorem summaryBits_reuse (b d m : Nat) (distinct : d ≤ m) :
    summaryBits b d ≤ summaryBits b m := by
  exact Nat.mul_le_mul_right _ (Nat.add_le_add_right distinct 1)

/-- A single summary bit is insufficient when components share a variable. -/
theorem shared_variable_counterexample :
    Satisfiable (.var 0) ∧ Satisfiable (.neg (.var 0)) ∧
      survivingBoundaries 1 0 [.var 0, .neg (.var 0)] = [] := by
  refine ⟨⟨fun _ => true, rfl⟩, ⟨fun _ => false, rfl⟩, ?_⟩
  decide

end OracleMachines.SAT
