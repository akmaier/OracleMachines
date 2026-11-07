import OracleMachines.Encoding
import OracleMachines.Resources

/-!
# An executable SAT core with an explicit cost semantics

One unit is a Boolean operation, formula-node dispatch, list-cell inspection,
or list-cell allocation in the abstract evaluator described in formal/README.md.
Variable access walks the assignment list. Counters are instrumentation and are
not themselves charged. This is not a model of Lean's compiled machine code.
Inputs here are parsed formulas; binary parsing is outside this cost theorem.
-/

namespace OracleMachines.SAT

abbrev Run (α : Type) := α × Nat

def readRun : Word → Nat → Run Bool
  | [], _ => (false, 1)
  | b :: _, 0 => (b, 1)
  | _ :: tail, i + 1 =>
    let r := readRun tail i
    (r.1, r.2 + 1)

inductive ReadTrace : Word → Nat → Bool → Nat → Prop where
  | nil (i : Nat) : ReadTrace [] i false 1
  | head (b : Bool) (tail : Word) : ReadTrace (b :: tail) 0 b 1
  | tail {a : Word} {i c : Nat} {b h : Bool} :
      ReadTrace a i b c → ReadTrace (h :: a) (i + 1) b (c + 1)

theorem readRun_trace (a : Word) (i : Nat) : ReadTrace a i (readRun a i).1 (readRun a i).2 := by
  induction a generalizing i with
  | nil => exact .nil i
  | cons b tail ih =>
    cases i with
    | zero => exact .head b tail
    | succ i => exact .tail (ih i)

theorem readRun_value (a : Word) (i : Nat) : (readRun a i).1 = valuation a i := by
  induction a generalizing i with
  | nil => simp [readRun, valuation]
  | cons b tail ih => cases i <;> simp [readRun, valuation] at *; exact ih _

theorem readRun_bound (a : Word) (i : Nat) : (readRun a i).2 ≤ i + 1 := by
  induction a generalizing i with
  | nil => simp [readRun]
  | cons b tail ih => cases i <;> simp [readRun]; exact ih _

def evalRun : Formula → Word → Run Bool
  | .falsum, _ => (false, 1)
  | .var i, a => let r := readRun a i; (r.1, r.2 + 1)
  | .neg f, a => let r := evalRun f a; (!r.1, r.2 + 1)
  | .conj f g, a =>
    let r := evalRun f a
    let s := evalRun g a
    (r.1 && s.1, r.2 + s.2 + 1)

inductive EvalTrace (a : Word) : Formula → Bool → Nat → Prop where
  | falsum : EvalTrace a .falsum false 1
  | var {i c : Nat} {b : Bool} : ReadTrace a i b c → EvalTrace a (.var i) b (c + 1)
  | neg {f : Formula} {b : Bool} {c : Nat} :
      EvalTrace a f b c → EvalTrace a (.neg f) (!b) (c + 1)
  | conj {f g : Formula} {b d : Bool} {c e : Nat} :
      EvalTrace a f b c → EvalTrace a g d e → EvalTrace a (.conj f g) (b && d) (c + e + 1)

theorem evalRun_trace (f : Formula) (a : Word) :
    EvalTrace a f (evalRun f a).1 (evalRun f a).2 := by
  induction f with
  | falsum => exact .falsum
  | var i => exact .var (readRun_trace a i)
  | neg f ih => exact .neg ih
  | conj f g ihf ihg => exact .conj ihf ihg

theorem evalRun_value (f : Formula) (a : Word) : (evalRun f a).1 = f.eval (valuation a) := by
  induction f with
  | falsum => rfl
  | var i => exact readRun_value a i
  | neg f ih => simp [evalRun, Formula.eval, ih]
  | conj f g ihf ihg => simp [evalRun, Formula.eval, ihf, ihg]

/-- A syntactic work bound with unary variable indices. -/
def weight : Formula → Nat
  | .falsum => 1
  | .var i => i + 2
  | .neg f => weight f + 1
  | .conj f g => weight f + weight g + 1

theorem weight_pos (f : Formula) : 0 < weight f := by cases f <;> simp [weight]

theorem width_le_weight (f : Formula) : f.width ≤ weight f := by
  induction f with
  | falsum => simp [Formula.width, weight]
  | var i => simp [Formula.width, weight]
  | neg f ih => simp only [Formula.width, weight]; omega
  | conj f g ihf ihg => simp only [Formula.width, weight]; omega

theorem evalRun_bound (f : Formula) (a : Word) : (evalRun f a).2 ≤ weight f := by
  induction f with
  | falsum => rfl
  | var i => simpa [evalRun, weight] using Nat.add_le_add_right (readRun_bound a i) 1
  | neg f ih => simpa [evalRun, weight] using Nat.add_le_add_right ih 1
  | conj f g ihf ihg => simp only [evalRun, weight]; omega

theorem weight_le_encoding (f : Formula) : weight f ≤ (encode f).length := by
  induction f with
  | falsum => simp [weight, encode, compile, encodeProgram, encodeInstruction]
  | var i => simp [weight, encode, compile, encodeProgram, encodeInstruction, putNat]
  | neg f ih => simp [weight, encode, compile, encodeProgram, encodeInstruction] at *; omega
  | conj f g ihf ihg => simp [weight, encode, compile, encodeProgram, encodeInstruction] at *; omega

/-- Width discovery charges unary comparisons at conjunctions. -/
def widthRun : Formula → Run Nat
  | .falsum => (0, 1)
  | .var i => (i + 1, 1)
  | .neg f => let r := widthRun f; (r.1, r.2 + 1)
  | .conj f g =>
    let r := widthRun f
    let s := widthRun g
    (max r.1 s.1, r.2 + s.2 + min r.1 s.1 + 2)

theorem widthRun_value (f : Formula) : (widthRun f).1 = f.width := by
  induction f <;> simp_all [widthRun, Formula.width]

theorem widthRun_bound (f : Formula) : (widthRun f).2 ≤ (weight f) ^ 2 := by
  induction f with
  | falsum => simp [widthRun, weight]
  | var i => exact one_le_pow₀ (by simp [weight])
  | neg f ih =>
    change (widthRun f).2 + 1 ≤ (weight f + 1) ^ 2
    nlinarith [weight_pos f]
  | conj f g ihf ihg =>
    simp only [widthRun, widthRun_value, weight]
    have hf := weight_pos f
    have hg := weight_pos g
    have hm := (Nat.min_le_left f.width g.width).trans (width_le_weight f)
    nlinarith

/-- Prefixing allocates the bit cell and outer list cell and inspects a cell. -/
def prefixRun (b : Bool) : List Word → Run (List Word)
  | [] => ([], 1)
  | a :: rest => let r := prefixRun b rest; ((b :: a) :: r.1, r.2 + 3)

def appendRun : List Word → List Word → Run (List Word)
  | [], ys => (ys, 1)
  | x :: xs, ys => let r := appendRun xs ys; (x :: r.1, r.2 + 2)

theorem prefixRun_spec (b : Bool) (xs : List Word) :
    (prefixRun b xs).1 = xs.map (b :: ·) ∧ (prefixRun b xs).2 = 3 * xs.length + 1 := by
  induction xs with
  | nil => simp [prefixRun]
  | cons a rest ih => simp [prefixRun, ih]; omega

theorem appendRun_spec (xs ys : List Word) :
    (appendRun xs ys).1 = xs ++ ys ∧ (appendRun xs ys).2 = 2 * xs.length + 1 := by
  induction xs with
  | nil => simp [appendRun]
  | cons a rest ih => simp [appendRun, ih]; omega

def wordsRun : Nat → Run (List Word)
  | 0 => ([[]], 2)
  | n + 1 =>
    let r := wordsRun n
    let l := prefixRun false r.1
    let h := prefixRun true r.1
    let joined := appendRun l.1 h.1
    (joined.1, r.2 + l.2 + h.2 + joined.2 + 1)

theorem wordsRun_value (n : Nat) : (wordsRun n).1 = words n := by
  induction n with
  | zero => rfl
  | succ n ih => simp [wordsRun, words, (prefixRun_spec _ _).1, (appendRun_spec _ _).1, ih]

theorem wordsRun_cost (n : Nat) : (wordsRun n).2 + 6 = 8 * 2 ^ n + 4 * n := by
  induction n with
  | zero => simp [wordsRun]
  | succ n ih =>
    simp only [wordsRun, (prefixRun_spec _ _).2, (appendRun_spec _ _).2,
      (prefixRun_spec _ _).1, wordsRun_value, List.length_map, length_words, pow_succ]
    omega

theorem nat_le_two_pow (n : Nat) : n ≤ 2 ^ n := by
  induction n with
  | zero => simp
  | succ n ih => rw [pow_succ]; have := Nat.one_le_pow n 2 (by omega); omega

theorem wordsRun_bound (n : Nat) : (wordsRun n).2 ≤ 12 * 2 ^ n := by
  have h := wordsRun_cost n
  have hn := nat_le_two_pow n
  omega

def searchRun (f : Formula) : List Word → Run (Option Word)
  | [] => (none, 1)
  | a :: rest =>
    let e := evalRun f a
    if e.1 then (some a, e.2 + 1)
    else let r := searchRun f rest; (r.1, e.2 + r.2 + 1)

theorem searchRun_value (f : Formula) (xs : List Word) :
    (searchRun f xs).1 = xs.find? (fun a => f.eval (valuation a)) := by
  induction xs with
  | nil => rfl
  | cons a rest ih =>
    cases h : f.eval (valuation a) <;> simp [searchRun, evalRun_value, List.find?, ih, h]

theorem searchRun_bound (f : Formula) (xs : List Word) :
    (searchRun f xs).2 ≤ 1 + xs.length * (weight f + 1) := by
  induction xs with
  | nil => simp [searchRun]
  | cons a rest ih =>
    have h := evalRun_bound f a
    simp only [searchRun, List.length_cons]
    split <;> simp only <;> nlinarith

def solveRun (f : Formula) : Run (Option Word) :=
  let width := widthRun f
  let assignments := wordsRun width.1
  let result := searchRun f assignments.1
  (result.1, width.2 + assignments.2 + result.2 + 1)

theorem solveRun_value (f : Formula) : (solveRun f).1 = findWitness f := by
  simp [solveRun, widthRun_value, wordsRun_value, searchRun_value, findWitness]

theorem solveRun_correct (f : Formula) : (solveRun f).1 = none ↔ ¬ Satisfiable f := by
  rw [solveRun_value, no_witness_iff]

theorem solveRun_bound (f : Formula) :
    (solveRun f).2 ≤ (weight f) ^ 2 + 2 ^ f.width * (weight f + 13) + 2 := by
  have hw := widthRun_bound f
  have hg := wordsRun_bound f.width
  have hs := searchRun_bound f (words f.width)
  simp only [length_words] at hs
  simp only [solveRun, widthRun_value, wordsRun_value]
  nlinarith

/-- A genuine restricted polynomial bound: the variable cap K is fixed. The
constant remains exponential in K, so this gives no uniform unrestricted bound. -/
theorem solveRun_fixed_width (f : Formula) (K : Nat) (cap : f.width ≤ K) :
    (solveRun f).2 ≤ (14 * 2 ^ K + 3) * ((encode f).length + 1) ^ 2 := by
  have h := solveRun_bound f
  have hw := weight_le_encoding f
  have hp : 2 ^ f.width ≤ 2 ^ K := pow_le_pow_right' (by norm_num) cap
  have hp' := Nat.mul_le_mul_right (weight f + 13) hp
  have hs : weight f ^ 2 ≤ ((encode f).length + 1) ^ 2 :=
    pow_le_pow_left' (by omega) 2
  have hl : weight f + 13 ≤ 14 * ((encode f).length + 1) ^ 2 := by
    nlinarith [Nat.zero_le (encode f).length]
  have hm := Nat.mul_le_mul_left (2 ^ K) hl
  have hone : 1 ≤ ((encode f).length + 1) ^ 2 := one_le_pow₀ (by omega)
  nlinarith

end OracleMachines.SAT
