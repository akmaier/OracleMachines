import OracleMachines.CostedSAT
import OracleMachines.Decision

/-!
# Counted binary parsing

List inspection, unary-index construction, instruction/formula allocation, and
control are charged explicitly. Formula subtrees are shared, not copied. Cost
counters, native integer representation, garbage collection, and JSON are not
part of this abstract model. The accepted language is unchanged.
-/

namespace OracleMachines.SAT

def readNatRun : Word → Run (Option (Nat × Word))
  | [] => (none, 1)
  | false :: rest => (some (0, rest), 2)
  | true :: rest =>
    let r := readNatRun rest
    (r.1.map (fun (n, tail) => (n + 1, tail)), r.2 + 2)

theorem readNatRun_value (bits : Word) : (readNatRun bits).1 = readNat bits := by
  induction bits with
  | nil => rfl
  | cons b rest ih =>
    cases b <;> simp [readNatRun, readNat, ih]
    cases readNat rest <;> rfl

theorem readNatRun_bound (bits : Word) : (readNatRun bits).2 ≤ 2 * bits.length + 1 := by
  induction bits with
  | nil => simp [readNatRun]
  | cons b rest ih => cases b <;> simp [readNatRun] <;> omega

/-- Unconsumed suffix length pays for the recursive parser's future work. -/
theorem readNatRun_consumed (bits tail : Word) (n : Nat)
    (h : (readNatRun bits).1 = some (n, tail)) :
    (readNatRun bits).2 + 2 * tail.length = 2 * bits.length := by
  induction bits generalizing n tail with
  | nil => simp [readNatRun] at h
  | cons b rest ih =>
    cases b with
    | false => simp only [readNatRun, Option.some.injEq, Prod.mk.injEq] at h; rcases h with ⟨rfl, rfl⟩; simp [readNatRun]; omega
    | true =>
      cases hr : (readNatRun rest).1 with
      | none => simp [readNatRun, hr] at h
      | some pair =>
        rcases pair with ⟨i, suffix⟩
        have hi := ih suffix i hr
        simp only [readNatRun, hr, Option.map_some, Option.some.injEq, Prod.mk.injEq] at h
        rcases h with ⟨rfl, rfl⟩
        simp only [readNatRun, List.length_cons]
        omega

def parseProgramRun : Nat → Word → Run (Option (List Instruction))
  | 0, _ => (none, 1)
  | _ + 1, [] => (some [], 1)
  | fuel + 1, false :: false :: rest =>
    let r := parseProgramRun fuel rest
    (r.1.map (.falsum :: ·), r.2 + 4)
  | fuel + 1, false :: true :: rest =>
    let index := readNatRun rest
    match index.1 with
    | none => (none, index.2 + 3)
    | some (i, tail) =>
      let r := parseProgramRun fuel tail
      (r.1.map (.load i :: ·), index.2 + r.2 + 4)
  | fuel + 1, true :: false :: rest =>
    let r := parseProgramRun fuel rest
    (r.1.map (.neg :: ·), r.2 + 4)
  | fuel + 1, true :: true :: rest =>
    let r := parseProgramRun fuel rest
    (r.1.map (.conj :: ·), r.2 + 4)
  | _, _ => (none, 2)

theorem parseProgramRun_value (fuel : Nat) (bits : Word) :
    (parseProgramRun fuel bits).1 = parseProgram fuel bits := by
  induction fuel generalizing bits with
  | zero => rfl
  | succ fuel ih =>
    rcases bits with _ | ⟨b, _ | ⟨c, rest⟩⟩
    · rfl
    · cases b <;> rfl
    · cases b <;> cases c
      · simp only [parseProgramRun, parseProgram, ih]
        cases parseProgram fuel rest <;> rfl
      · simp only [parseProgramRun, parseProgram, readNatRun_value]
        cases readNat rest with
        | none => rfl
        | some pair =>
          rcases pair with ⟨i, tail⟩
          change ((parseProgramRun fuel tail).1).map (.load i :: ·) =
            (parseProgram fuel tail).bind (fun code => some (.load i :: code))
          rw [ih]
          cases parseProgram fuel tail <;> rfl
      · simp only [parseProgramRun, parseProgram, ih]
        cases parseProgram fuel rest <;> rfl
      · simp only [parseProgramRun, parseProgram, ih]
        cases parseProgram fuel rest <;> rfl

theorem parseProgramRun_bound (fuel : Nat) (bits : Word) :
    (parseProgramRun fuel bits).2 ≤ 2 * bits.length + 1 := by
  induction fuel generalizing bits with
  | zero => simp [parseProgramRun]
  | succ fuel ih =>
    rcases bits with _ | ⟨b, _ | ⟨c, rest⟩⟩
    · simp [parseProgramRun]
    · cases b <;> simp [parseProgramRun]
    · cases b <;> cases c
      · have h := ih rest; simp only [parseProgramRun, List.length_cons]; omega
      · have hb := readNatRun_bound rest
        cases hr : (readNatRun rest).1 with
        | none => simp only [parseProgramRun, hr, List.length_cons]; omega
        | some pair =>
          rcases pair with ⟨i, tail⟩
          have hc := readNatRun_consumed rest tail i hr
          have ht := ih tail
          simp only [parseProgramRun, hr, List.length_cons]
          omega
      · have h := ih rest; simp only [parseProgramRun, List.length_cons]; omega
      · have h := ih rest; simp only [parseProgramRun, List.length_cons]; omega

theorem parseProgramRun_length (fuel : Nat) (bits : Word) (p : List Instruction)
    (h : (parseProgramRun fuel bits).1 = some p) : p.length ≤ bits.length := by
  induction fuel generalizing bits p with
  | zero => simp [parseProgramRun] at h
  | succ fuel ih =>
    rcases bits with _ | ⟨b, _ | ⟨c, rest⟩⟩
    · simp only [parseProgramRun, Option.some.injEq] at h; subst p; simp
    · cases b <;> simp [parseProgramRun] at h
    · cases b <;> cases c
      all_goals simp only [parseProgramRun] at h
      · cases hr : (parseProgramRun fuel rest).1 with
        | none => simp [hr] at h
        | some tail => have ht := ih rest tail hr; simp [hr] at h; subst p; simp; omega
      · cases hr : (readNatRun rest).1 with
        | none => simp [hr] at h
        | some pair =>
          rcases pair with ⟨i, suffix⟩
          have hc := readNatRun_consumed rest suffix i hr
          simp only [hr] at h
          cases hp : (parseProgramRun fuel suffix).1 with
          | none => simp [hp] at h
          | some tail => have ht := ih suffix tail hp; simp [hp] at h; subst p; simp; omega
      · cases hr : (parseProgramRun fuel rest).1 with
        | none => simp [hr] at h
        | some tail => have ht := ih rest tail hr; simp [hr] at h; subst p; simp; omega
      · cases hr : (parseProgramRun fuel rest).1 with
        | none => simp [hr] at h
        | some tail => have ht := ih rest tail hr; simp [hr] at h; subst p; simp; omega


def assembleRun : List Instruction → List Formula → Run (Option (List Formula))
  | [], stack => (some stack, 1)
  | .falsum :: rest, stack => let r := assembleRun rest (.falsum :: stack); (r.1, r.2 + 5)
  | .load i :: rest, stack => let r := assembleRun rest (.var i :: stack); (r.1, r.2 + 5)
  | .neg :: rest, f :: stack => let r := assembleRun rest (.neg f :: stack); (r.1, r.2 + 5)
  | .conj :: rest, g :: f :: stack => let r := assembleRun rest (.conj f g :: stack); (r.1, r.2 + 5)
  | _, _ => (none, 3)

theorem assembleRun_value (p : List Instruction) (stack : List Formula) :
    (assembleRun p stack).1 = assemble p stack := by
  induction p generalizing stack with
  | nil => rfl
  | cons i rest ih =>
    cases i with
    | falsum => simp [assembleRun, assemble, ih]
    | load i => simp [assembleRun, assemble, ih]
    | neg => cases stack <;> simp [assembleRun, assemble, ih]
    | conj => rcases stack with _ | ⟨g, _ | ⟨f, tail⟩⟩ <;> simp [assembleRun, assemble, ih]

theorem assembleRun_bound (p : List Instruction) (stack : List Formula) :
    (assembleRun p stack).2 ≤ 5 * p.length + 1 := by
  induction p generalizing stack with
  | nil => simp [assembleRun]
  | cons i rest ih =>
    cases i with
    | falsum => have h := ih (.falsum :: stack); simp only [assembleRun, List.length_cons]; omega
    | load i => have h := ih (.var i :: stack); simp only [assembleRun, List.length_cons]; omega
    | neg =>
      cases stack with
      | nil => simp [assembleRun]; omega
      | cons f tail => have h := ih (.neg f :: tail); simp only [assembleRun, List.length_cons]; omega
    | conj =>
      rcases stack with _ | ⟨g, _ | ⟨f, tail⟩⟩
      · simp [assembleRun]; omega
      · simp [assembleRun]; omega
      · have h := ih (.conj f g :: tail); simp only [assembleRun, List.length_cons]; omega

def lengthRun : Word → Run Nat
  | [] => (0, 1)
  | _ :: tail => let r := lengthRun tail; (r.1 + 1, r.2 + 1)

theorem lengthRun_spec (bits : Word) :
    (lengthRun bits).1 = bits.length ∧ (lengthRun bits).2 = bits.length + 1 := by
  induction bits with
  | nil => simp [lengthRun]
  | cons b tail ih => simp [lengthRun, ih]

def decodeRun (bits : Word) : Run (Option Formula) :=
  let len := lengthRun bits
  let parsed := parseProgramRun (len.1 + 1) bits
  match parsed.1 with
  | none => (none, len.2 + parsed.2 + 1)
  | some instructions =>
    let assembled := assembleRun instructions []
    let result := match assembled.1 with
      | some [f] => some f
      | _ => none
    (result, len.2 + parsed.2 + assembled.2 + 4)

theorem decodeRun_value (bits : Word) : (decodeRun bits).1 = decode bits := by
  simp only [decodeRun, (lengthRun_spec bits).1, parseProgramRun_value, decode]
  cases parseProgram (bits.length + 1) bits with
  | none => rfl
  | some instructions =>
    change (match (assembleRun instructions []).1 with
      | some [f] => some f
      | _ => none) = (assemble instructions []).bind (fun stack =>
        match stack with | [f] => some f | _ => none)
    rw [assembleRun_value]
    cases assemble instructions [] with
    | none => rfl
    | some stack => rcases stack with _ | ⟨f, _ | ⟨g, rest⟩⟩ <;> rfl

theorem decodeRun_bound (bits : Word) : (decodeRun bits).2 ≤ 8 * bits.length + 7 := by
  have hp := parseProgramRun_bound (bits.length + 1) bits
  simp only [decodeRun, (lengthRun_spec bits).1, (lengthRun_spec bits).2]
  cases h : (parseProgramRun (bits.length + 1) bits).1 with
  | none => simp only; omega
  | some instructions =>
    have hl := parseProgramRun_length (bits.length + 1) bits instructions h
    have ha := assembleRun_bound instructions []
    simp only
    omega

/-- Includes decoding; no verdict is produced for a malformed encoding. -/
def decideRun (bits : Word) : Run (Option Bool) :=
  let parsed := decodeRun bits
  match parsed.1 with
  | none => (none, parsed.2 + 1)
  | some f =>
    let solved := solveRun f
    (some solved.1.isSome, parsed.2 + solved.2 + 2)

theorem solveRun_isSome (f : Formula) : (solveRun f).1.isSome = solve f := by
  have h := solveRun_correct f
  have hs := solve_correct f
  cases h1 : (solveRun f).1 <;> cases h2 : solve f <;> simp_all

theorem decideRun_value (bits : Word) : (decideRun bits).1 = decideEncoded bits := by
  simp only [decideRun, decodeRun_value, decideEncoded]
  cases decode bits <;> simp [solveRun_isSome]

theorem decideRun_sat (bits : Word) : (decideRun bits).1 = some true ↔ EncodedSAT bits := by
  rw [decideRun_value, decision_sat_iff]

theorem decideRun_unsat (bits : Word) : (decideRun bits).1 = some false ↔ EncodedUNSAT bits := by
  rw [decideRun_value, decision_unsat_iff]

theorem decideRun_invalid_bound (bits : Word) (invalid : decode bits = none) :
    (decideRun bits).2 ≤ 8 * bits.length + 8 := by
  have h := decodeRun_bound bits
  simp only [decideRun, decodeRun_value, invalid]
  omega

theorem decideRun_fixed_width (f : Formula) (K : Nat) (cap : f.width ≤ K) :
    (decideRun (encode f)).2 ≤ (14 * 2 ^ K + 12) * ((encode f).length + 1) ^ 2 := by
  have hp := decodeRun_bound (encode f)
  have hs := solveRun_fixed_width f K cap
  simp only [decideRun, decodeRun_value, decode_encode]
  nlinarith [Nat.zero_le (encode f).length]

end OracleMachines.SAT
