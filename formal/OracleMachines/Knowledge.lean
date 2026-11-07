import OracleMachines.Search

/-!
# Reuse checked witnesses and refutations across queries

Candidates need not be trusted or syntactically related to the new formula.
Every witness and every negative certificate is checked against that formula.
The caller can bound the number and serialized size of proposed candidates.
-/
namespace OracleMachines.SAT

def probeWitnesses (f : Formula) : List Word → Run (Option Word)
  | [] => (none, 1)
  | a :: rest =>
    let test := evalRun f a
    if test.1 then (some a, test.2 + 2)
    else let tail := probeWitnesses f rest; (tail.1, test.2 + tail.2 + 2)

theorem probeWitnesses_sound (f : Formula) (xs : List Word) (a : Word)
    (h : (probeWitnesses f xs).1 = some a) : f.eval (valuation a) = true := by
  induction xs with
  | nil => simp [probeWitnesses] at h
  | cons b rest ih =>
    simp only [probeWitnesses] at h
    split at h
    · rename_i ht; simp only [Option.some.injEq] at h; subst b
      exact (evalRun_value f a).symm.trans ht
    · exact ih h

def probeRefutations (f : Formula) : List Refutation → Run (Option Refutation)
  | [] => (none, 1)
  | p :: rest =>
    let test := checkRefutation f [] p
    if test.1 then (some p, test.2 + 2)
    else let tail := probeRefutations f rest; (tail.1, test.2 + tail.2 + 2)

theorem probeRefutations_checked (f : Formula) (xs : List Refutation) (p : Refutation)
    (h : (probeRefutations f xs).1 = some p) : (checkRefutation f [] p).1 = true := by
  induction xs with
  | nil => simp [probeRefutations] at h
  | cons q rest ih =>
    simp only [probeRefutations] at h
    split at h
    · rename_i ht; simp only [Option.some.injEq] at h; subst q; exact ht
    · exact ih h

structure CheckedResult where
  witness : Option Word
  certificate : Option Refutation
  work : Nat
  nodes : Nat
  source : Nat -- 0: fallback, 1: checked witness, 2: checked refutation
  deriving Repr

def Verified (f : Formula) (r : CheckedResult) : Prop :=
  (∀ a, r.witness = some a → f.eval (valuation a) = true) ∧
  (r.witness = none → ∃ p, r.certificate = some p ∧ (checkRefutation f [] p).1 = true)

def solveSearch (f : Formula) : CheckedResult :=
  let r := solveSparse f
  match r.assignment with
  | none => ⟨none, some r.proof, r.work + 1, r.nodes, 0⟩
  | some a =>
    let width := widthRun f
    let word := materialize a width.1
    ⟨some word.1, none, r.work + width.2 + word.2 + 2, r.nodes, 0⟩

theorem solveSearch_verified (f : Formula) : Verified f (solveSearch f) := by
  cases h : (solveSparse f).assignment with
  | none =>
    constructor
    · intro a ha; simp [solveSearch, h] at ha
    · intro _; exact ⟨(solveSparse f).proof, by simp [solveSearch, h], solveSparse_certificate f h⟩
  | some a =>
    constructor
    · intro b hb
      simp only [solveSearch, h, widthRun_value f, Option.some.injEq] at hb
      subst b
      exact materialize_satisfies f a (searchSparse_sound f _ [] a h)
    · intro hn; simp [solveSearch, h] at hn

def reuseSearch (f : Formula) (witnesses : List Word) (proofs : List Refutation) : CheckedResult :=
  let w := probeWitnesses f witnesses
  match w.1 with
  | some a => ⟨some a, none, w.2 + 1, 0, 1⟩
  | none =>
    let p := probeRefutations f proofs
    match p.1 with
    | some c => ⟨none, some c, w.2 + p.2 + 2, 0, 2⟩
    | none =>
      let r := solveSearch f
      { r with work := w.2 + p.2 + r.work + 2 }

theorem reuseSearch_verified (f : Formula) (ws : List Word) (ps : List Refutation) :
    Verified f (reuseSearch f ws ps) := by
  cases hw : (probeWitnesses f ws).1 with
  | some a =>
    constructor
    · intro b hb; simp [reuseSearch, hw] at hb; subst b; exact probeWitnesses_sound f ws a hw
    · intro hn; simp [reuseSearch, hw] at hn
  | none =>
    cases hp : (probeRefutations f ps).1 with
    | some p =>
      constructor
      · intro a ha; simp [reuseSearch, hw, hp] at ha
      · intro _; exact ⟨p, by simp [reuseSearch, hw, hp], probeRefutations_checked f ps p hp⟩
    | none => simpa [Verified, reuseSearch, hw, hp] using solveSearch_verified f

theorem verified_correct (f : Formula) (r : CheckedResult) (h : Verified f r) :
    r.witness.isSome = true ↔ Satisfiable f := by
  cases hw : r.witness with
  | some a => simp only [Option.isSome_some, true_iff]; exact ⟨valuation a, h.1 a hw⟩
  | none =>
    simp only [Option.isSome_none, Bool.false_eq_true, false_iff]
    obtain ⟨p, _, hp⟩ := h.2 hw
    intro ⟨v, hv⟩
    have no := checkRefutation_sound f [] p hp v (by intro i b hi; simp [sparseRead] at hi)
    rw [hv] at no; contradiction

theorem reuseSearch_correct (f : Formula) (ws : List Word) (ps : List Refutation) :
    (reuseSearch f ws ps).witness.isSome = true ↔ Satisfiable f :=
  verified_correct f _ (reuseSearch_verified f ws ps)

end OracleMachines.SAT
