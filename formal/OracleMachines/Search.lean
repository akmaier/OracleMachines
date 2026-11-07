import OracleMachines.CostedSAT

/-!
# Lazy search on occurring variables, with checked pruning and refutations

Sparse assignments retain original variable identities. The search never builds
the list of all assignments. A three-valued evaluator can close a branch before
all variables are assigned. Negative results carry independently checkable trees.
Counters charge abstract operations; native allocation and JSON remain outside.
-/
namespace OracleMachines.SAT

abbrev Sparse := List (Nat × Bool)

def sparseRead : Sparse → Nat → Run (Option Bool)
  | [], _ => (none, 1)
  | (j, b) :: rest, i =>
    if i = j then (some b, i + j + 3)
    else let r := sparseRead rest i; (r.1, r.2 + i + j + 3)

def Extends (v : Nat → Bool) (s : Sparse) : Prop :=
  ∀ i b, (sparseRead s i).1 = some b → v i = b

def sparseVal (s : Sparse) (i : Nat) : Bool := (sparseRead s i).1.getD false

theorem sparseVal_extends (s : Sparse) : Extends (sparseVal s) s := by
  intro i b h; simp [sparseVal, h]

theorem extends_cons (v : Nat → Bool) (s : Sparse) (i : Nat) (b : Bool)
    (h : Extends v s) (hb : v i = b) : Extends v ((i, b) :: s) := by
  intro j c hc
  by_cases hj : j = i
  · subst j; simpa [sparseRead] using hb.trans (by simpa [sparseRead] using hc)
  · simp only [sparseRead, if_neg hj] at hc; exact h j c hc

def partialRun : Formula → Sparse → Run (Option Bool)
  | .falsum, _ => (some false, 1)
  | .var i, s => let r := sparseRead s i; (r.1, r.2 + 1)
  | .neg f, s => let r := partialRun f s; (r.1.map (! ·), r.2 + 1)
  | .conj f g, s =>
    let l := partialRun f s
    if l.1 = some false then (some false, l.2 + 1)
    else
      let r := partialRun g s
      let value := if r.1 = some false then some false
        else if l.1 = some true then r.1 else none
      (value, l.2 + r.2 + 2)

theorem partialRun_sound (f : Formula) (s : Sparse) (v : Nat → Bool)
    (ext : Extends v s) (b : Bool) (h : (partialRun f s).1 = some b) : f.eval v = b := by
  induction f generalizing b with
  | falsum => simpa [partialRun, Formula.eval] using h
  | var i => exact ext i b h
  | neg f ih =>
    cases hp : (partialRun f s).1 with
    | none => simp [partialRun, hp] at h
    | some c =>
      have hc := ih c hp
      simpa [partialRun, hp, Formula.eval, hc] using h
  | conj f g ihf ihg =>
    cases hl : (partialRun f s).1 with
    | none =>
      cases hr : (partialRun g s).1 with
      | none => simp [partialRun, hl, hr] at h
      | some c =>
        cases c with
        | false => simp [partialRun, hl, hr] at h; subst b; simp [Formula.eval, ihg false hr]
        | true => simp [partialRun, hl, hr] at h
    | some c =>
      have hc := ihf c hl
      cases c with
      | false => simp [partialRun, hl] at h; subst b; simp [Formula.eval, hc]
      | true =>
        cases hr : (partialRun g s).1 with
        | none => simp [partialRun, hl, hr] at h
        | some d =>
          have hd := ihg d hr
          cases d <;> simp [partialRun, hl, hr] at h <;> subst b <;> simp [Formula.eval, hc, hd]

def occurs : Formula → List Nat
  | .falsum => []
  | .var i => [i]
  | .neg f => occurs f
  | .conj f g => occurs f ++ occurs g

def occursRun : Formula → Run (List Nat)
  | .falsum => ([], 1)
  | .var i => ([i], 2)
  | .neg f => let r := occursRun f; (r.1, r.2 + 1)
  | .conj f g =>
    let l := occursRun f
    let r := occursRun g
    (l.1 ++ r.1, l.2 + r.2 + 2 * l.1.length + 2)

theorem occursRun_value (f : Formula) : (occursRun f).1 = occurs f := by
  induction f <;> simp_all [occursRun, occurs]

def memberRun (i : Nat) : List Nat → Run Bool
  | [] => (false, 1)
  | j :: rest => if i = j then (true, i + j + 2)
    else let r := memberRun i rest; (r.1, r.2 + i + j + 2)

theorem memberRun_value (i : Nat) (xs : List Nat) : (memberRun i xs).1 = true ↔ i ∈ xs := by
  induction xs with
  | nil => simp [memberRun]
  | cons j rest ih => by_cases h : i = j <;> simp [memberRun, h, ih]

def distinctRun : List Nat → Run (List Nat)
  | [] => ([], 1)
  | i :: rest =>
    let tail := distinctRun rest
    let test := memberRun i tail.1
    (if test.1 then tail.1 else i :: tail.1, tail.2 + test.2 + 2)

theorem distinctRun_mem (i : Nat) (xs : List Nat) : i ∈ (distinctRun xs).1 ↔ i ∈ xs := by
  induction xs with
  | nil => simp [distinctRun]
  | cons j rest ih =>
    simp only [distinctRun]
    split
    · rename_i h
      have hj := (memberRun_value j _).mp h
      simp only [List.mem_cons]
      constructor
      · exact fun hi => Or.inr (ih.mp hi)
      · rintro (rfl | hi); exact hj; exact ih.mpr hi
    · simpa using or_congr Iff.rfl ih

theorem distinctRun_nodup (xs : List Nat) : (distinctRun xs).1.Nodup := by
  induction xs with
  | nil => simp [distinctRun]
  | cons j rest ih =>
    simp only [distinctRun]
    split
    · exact ih
    · rename_i h; exact List.nodup_cons.mpr ⟨fun hj => h ((memberRun_value _ _).mpr hj), ih⟩

def Covers (f : Formula) (pending : List Nat) (s : Sparse) : Prop :=
  ∀ i ∈ occurs f, i ∈ pending ∨ ∃ b, (sparseRead s i).1 = some b

theorem covers_cons (f : Formula) (xs : List Nat) (s : Sparse) (i : Nat) (b : Bool)
    (h : Covers f (i :: xs) s) : Covers f xs ((i, b) :: s) := by
  intro j hj
  by_cases heq : j = i
  · subst j; exact Or.inr ⟨b, by simp [sparseRead]⟩
  · rcases h j hj with hp | ⟨c, hc⟩
    · exact Or.inl (by simpa [heq] using hp)
    · exact Or.inr ⟨c, by simpa [sparseRead, heq] using hc⟩

theorem partialRun_total (f : Formula) (s : Sparse) (h : Covers f [] s) :
    ∃ b, (partialRun f s).1 = some b := by
  induction f with
  | falsum => exact ⟨false, rfl⟩
  | var i => simpa [Covers, occurs, partialRun] using h
  | neg f ih =>
    obtain ⟨b, hb⟩ := ih h
    exact ⟨!b, by simp [partialRun, hb]⟩
  | conj f g ihf ihg =>
    have hf : Covers f [] s := fun i hi => h i (List.mem_append_left _ hi)
    have hg : Covers g [] s := fun i hi => h i (List.mem_append_right _ hi)
    obtain ⟨b, hb⟩ := ihf hf
    obtain ⟨c, hc⟩ := ihg hg
    cases b <;> cases c <;> simp [partialRun, hb, hc]

inductive Refutation where
  | conflict
  | split (index : Nat) (low high : Refutation)
  deriving Repr, DecidableEq

def checkRefutation (f : Formula) : Sparse → Refutation → Run Bool
  | s, .conflict => let r := partialRun f s; (r.1 == some false, r.2 + 1)
  | s, .split i low high =>
    let l := checkRefutation f ((i, false) :: s) low
    if !l.1 then (false, l.2 + 3)
    else let r := checkRefutation f ((i, true) :: s) high
         (r.1, l.2 + r.2 + 5)

theorem checkRefutation_sound (f : Formula) (s : Sparse) (p : Refutation)
    (h : (checkRefutation f s p).1 = true) :
    ∀ v, Extends v s → f.eval v = false := by
  induction p generalizing s with
  | conflict =>
    intro v ext
    exact partialRun_sound f s v ext false (by simpa [checkRefutation] using h)
  | split i low high ihl ihr =>
    simp only [checkRefutation] at h
    split at h
    · simp at h
    · rename_i hl
      have hl' : (checkRefutation f ((i, false) :: s) low).1 = true := by simpa using hl
      intro v ext
      cases hv : v i with
      | false => exact ihl _ hl' v (extends_cons v s i false ext hv)
      | true => exact ihr _ h v (extends_cons v s i true ext hv)

structure SearchResult where
  assignment : Option Sparse
  proof : Refutation
  work : Nat
  nodes : Nat
  deriving Repr

def searchSparse (f : Formula) : List Nat → Sparse → SearchResult
  | pending, s =>
    let test := partialRun f s
    match test.1 with
    | some true => ⟨some s, .conflict, test.2 + 1, 1⟩
    | some false => ⟨none, .conflict, test.2 + 1, 1⟩
    | none => match pending with
      | [] => ⟨none, .conflict, test.2 + 1, 1⟩
      | i :: rest =>
        let low := searchSparse f rest ((i, false) :: s)
        match low.assignment with
        | some a => ⟨some a, low.proof, test.2 + low.work + 4, low.nodes + 1⟩
        | none =>
          let high := searchSparse f rest ((i, true) :: s)
          ⟨high.assignment, .split i low.proof high.proof,
            test.2 + low.work + high.work + 7, low.nodes + high.nodes + 1⟩

theorem searchSparse_sound (f : Formula) (xs : List Nat) (s a : Sparse)
    (h : (searchSparse f xs s).assignment = some a) : f.eval (sparseVal a) = true := by
  induction xs generalizing s with
  | nil =>
    cases ht : (partialRun f s).1 with
    | none => simp [searchSparse, ht] at h
    | some b => cases b <;> simp [searchSparse, ht] at h
                subst a; exact partialRun_sound f s (sparseVal s) (sparseVal_extends s) true ht
  | cons i rest ih =>
    cases ht : (partialRun f s).1 with
    | none =>
      cases hl : (searchSparse f rest ((i, false) :: s)).assignment with
      | none => exact ih _ (by simpa [searchSparse, ht, hl] using h)
      | some b => simp [searchSparse, ht, hl] at h; subst b; exact ih _ hl
    | some b => cases b <;> simp [searchSparse, ht] at h
                subst a; exact partialRun_sound f s (sparseVal s) (sparseVal_extends s) true ht

theorem searchSparse_certificate (f : Formula) (xs : List Nat) (s : Sparse)
    (cover : Covers f xs s) (h : (searchSparse f xs s).assignment = none) :
    (checkRefutation f s (searchSparse f xs s).proof).1 = true := by
  induction xs generalizing s with
  | nil =>
    obtain ⟨b, hb⟩ := partialRun_total f s cover
    cases b <;> simp [searchSparse, hb] at h ⊢
    simp [checkRefutation, hb]
  | cons i rest ih =>
    cases ht : (partialRun f s).1 with
    | some b => cases b <;> simp [searchSparse, ht] at h ⊢
                simp [checkRefutation, ht]
    | none =>
      cases hl : (searchSparse f rest ((i, false) :: s)).assignment with
      | some a => simp [searchSparse, ht, hl] at h
      | none =>
        have hh : (searchSparse f rest ((i, true) :: s)).assignment = none := by
          simpa [searchSparse, ht, hl] using h
        have cl := ih _ (covers_cons f rest s i false cover) hl
        have ch := ih _ (covers_cons f rest s i true cover) hh
        simp [searchSparse, ht, hl, checkRefutation, cl, ch]

theorem searchSparse_nodes (f : Formula) (xs : List Nat) (s : Sparse) :
    (searchSparse f xs s).nodes + 1 ≤ 2 ^ (xs.length + 1) := by
  induction xs generalizing s with
  | nil => cases ht : (partialRun f s).1 with
    | none => simp [searchSparse, ht]
    | some b => cases b <;> simp [searchSparse, ht]
  | cons i rest ih =>
    have lo := ih ((i, false) :: s)
    have hi := ih ((i, true) :: s)
    have pos := Nat.one_le_pow (rest.length + 1) 2 (by omega)
    cases ht : (partialRun f s).1 with
    | none =>
      cases hl : (searchSparse f rest ((i, false) :: s)).assignment <;>
        simp [searchSparse, ht, hl, pow_succ] at * <;> omega
    | some b => cases b <;> simp [searchSparse, ht, pow_succ] <;> omega

def solveSparse (f : Formula) : SearchResult :=
  let raw := occursRun f
  let vars := distinctRun raw.1
  let r := searchSparse f vars.1 []
  { r with work := raw.2 + vars.2 + r.work + 1 }

theorem solveSparse_certificate (f : Formula) (h : (solveSparse f).assignment = none) :
    (checkRefutation f [] (solveSparse f).proof).1 = true := by
  apply searchSparse_certificate f _ [] _ h
  intro i hi
  exact Or.inl ((distinctRun_mem i _).mpr (by simpa [occursRun_value] using hi))

theorem solveSparse_nodes (f : Formula) :
    (solveSparse f).nodes + 1 ≤ 2 ^ ((distinctRun (occurs f)).1.length + 1) := by
  simpa [solveSparse, occursRun_value] using
    searchSparse_nodes f (distinctRun (occursRun f).1).1 []

theorem solveSparse_correct (f : Formula) :
    (solveSparse f).assignment = none ↔ ¬ Satisfiable f := by
  have cover : Covers f (distinctRun (occursRun f).1).1 [] := by
    intro i hi; exact Or.inl ((distinctRun_mem i _).mpr (by simpa [occursRun_value] using hi))
  constructor
  · intro h
    have cert := searchSparse_certificate f _ [] cover h
    intro ⟨v, hv⟩
    have no := checkRefutation_sound f [] _ cert v (by intro i b hi; simp [sparseRead] at hi)
    rw [hv] at no; contradiction
  · intro h
    cases hs : (solveSparse f).assignment with
    | none => rfl
    | some a => exact False.elim (h ⟨sparseVal a, searchSparse_sound f _ [] a hs⟩)

def materialize (s : Sparse) (n : Nat) : Run Word :=
  let cells := List.ofFn (fun i : Fin n => sparseRead s i)
  (cells.map (fun r => r.1.getD false), 1 + (cells.map (fun r => r.2 + 4)).sum)

theorem materialize_value (s : Sparse) (n : Nat) :
    (materialize s n).1 = List.ofFn (fun i : Fin n => sparseVal s i) := by
  simp [materialize, List.map_ofFn, sparseVal, Function.comp_def]

theorem materialize_satisfies (f : Formula) (s : Sparse) (h : f.eval (sparseVal s) = true) :
    f.eval (valuation (materialize s f.width).1) = true := by
  rw [materialize_value]
  exact (eval_agrees f _ (sparseVal s) (fun i hi => valuation_ofFn f.width (sparseVal s) i hi)).trans h

end OracleMachines.SAT
