import OracleMachines.Restricted
import OracleMachines.StackMachine

/-!
# All accepted binary encodings are canonical

The original round trip was `decode (encode f) = some f`. Its converse is
needed to transfer encoding-length bounds to arbitrary successfully decoded
requests. There is no ignored suffix, padding opcode, or alternate unary index.
-/

namespace OracleMachines.SAT

theorem readNat_inverse (bits tail : Word) (n : Nat)
    (h : readNat bits = some (n, tail)) : putNat n ++ tail = bits := by
  induction bits generalizing tail n with
  | nil => simp [readNat] at h
  | cons b rest ih =>
    cases b with
    | false =>
      simp only [readNat, Option.some.injEq, Prod.mk.injEq] at h
      rcases h with ⟨rfl, rfl⟩
      simp [putNat]
    | true =>
      cases hr : readNat rest with
      | none => simp [readNat, hr] at h
      | some pair =>
        rcases pair with ⟨i, suffix⟩
        have hi := ih suffix i hr
        simp only [readNat, hr] at h
        rcases h with ⟨rfl, rfl⟩
        simpa [putNat, List.replicate_succ, List.append_assoc] using congrArg (true :: ·) hi

theorem parseProgram_inverse (fuel : Nat) (bits : Word) (p : List Instruction)
    (h : parseProgram fuel bits = some p) : encodeProgram p = bits := by
  induction fuel generalizing bits p with
  | zero => simp [parseProgram] at h
  | succ fuel ih =>
    rcases bits with _ | ⟨b, _ | ⟨c, rest⟩⟩
    · simp only [parseProgram, Option.some.injEq] at h; subst p; rfl
    · cases b <;> simp [parseProgram] at h
    · cases b <;> cases c
      all_goals simp only [parseProgram] at h
      · cases hr : parseProgram fuel rest with
        | none => simp [hr] at h
        | some tail =>
          have ht := ih rest tail hr
          simp [hr] at h; subst p
          simpa [encodeProgram, encodeInstruction] using congrArg ([false, false] ++ ·) ht
      · cases hr : readNat rest with
        | none => simp [hr] at h
        | some pair =>
          rcases pair with ⟨i, suffix⟩
          have hc := readNat_inverse rest suffix i hr
          simp only [hr] at h
          cases hp : parseProgram fuel suffix with
          | none => simp [hp] at h
          | some tail =>
            have ht := ih suffix tail hp
            simp [hp] at h; subst p
            change [false, true] ++ putNat i ++ encodeProgram tail = false :: true :: rest
            rw [ht, List.append_assoc, hc]
            rfl
      · cases hr : parseProgram fuel rest with
        | none => simp [hr] at h
        | some tail =>
          have ht := ih rest tail hr
          simp [hr] at h; subst p
          simpa [encodeProgram, encodeInstruction] using congrArg ([true, false] ++ ·) ht
      · cases hr : parseProgram fuel rest with
        | none => simp [hr] at h
        | some tail =>
          have ht := ih rest tail hr
          simp [hr] at h; subst p
          simpa [encodeProgram, encodeInstruction] using congrArg ([true, true] ++ ·) ht

/-- The code already consumed by a formula stack, from its bottom upwards. -/
def stackCode : List Formula → List Instruction
  | [] => []
  | f :: rest => stackCode rest ++ compile f

theorem assemble_code (p : List Instruction) (stack out : List Formula)
    (h : assemble p stack = some out) : stackCode out = stackCode stack ++ p := by
  induction p generalizing stack with
  | nil => simp only [assemble, Option.some.injEq] at h; subst out; simp
  | cons i rest ih =>
    cases i with
    | falsum =>
      have hi := ih (.falsum :: stack) h
      simpa [stackCode, compile, List.append_assoc] using hi
    | load i =>
      have hi := ih (.var i :: stack) h
      simpa [stackCode, compile, List.append_assoc] using hi
    | neg =>
      cases stack with
      | nil => simp [assemble] at h
      | cons f tail =>
        have hi := ih (.neg f :: tail) h
        simpa [stackCode, compile, List.append_assoc] using hi
    | conj =>
      rcases stack with _ | ⟨g, _ | ⟨f, tail⟩⟩
      · simp [assemble] at h
      · simp [assemble] at h
      · have hi := ih (.conj f g :: tail) h
        simpa [stackCode, compile, List.append_assoc] using hi

theorem encode_decode (bits : Word) (f : Formula) (h : decode bits = some f) :
    encode f = bits := by
  unfold decode at h
  cases hp : parseProgram (bits.length + 1) bits with
  | none => simp [hp] at h
  | some p =>
    simp only [hp] at h
    cases hs : assemble p [] with
    | none => simp [hs] at h
    | some stack =>
      rcases stack with _ | ⟨g, _ | ⟨g', tail⟩⟩
      · simp [hs] at h
      · have hg : g = f := by simpa [hs] using h
        subst g
        have ha := assemble_code p [] [f] hs
        simp only [stackCode, List.nil_append] at ha
        exact (congrArg encodeProgram ha).trans (parseProgram_inverse _ _ _ hp)
      · simp [hs] at h

theorem decode_eq_iff (bits : Word) (f : Formula) :
    decode bits = some f ↔ encode f = bits := by
  constructor
  · exact encode_decode bits f
  · intro h; rw [← h, decode_encode]

theorem parseProgram_decode (bits : Word) (f : Formula) (valid : decode bits = some f) :
    parseProgram (bits.length + 1) bits = some (compile f) := by
  rw [← encode_decode bits f valid]
  exact parseProgram_encode (compile f) ((encode f).length + 1)
    (Nat.lt_succ_of_le (encodeProgram_length (compile f)))

/-- The parsed program evaluates one assignment in at most the original input
length many transitions. A false evaluation alone is not an UNSAT verdict. -/
theorem parsed_eval_steps (bits a : Word) (p : List Instruction) (f : Formula)
    (parsed : parseProgram (bits.length + 1) bits = some p)
    (valid : decode bits = some f) :
    ∃ n ≤ bits.length, EvalSteps a n (.exec p []) (.exec [] [f.eval (valuation a)]) := by
  have hp : p = compile f := Option.some.inj (parsed.symm.trans (parseProgram_decode bits f valid))
  subst p
  refine ⟨(evalRun f a).2, ?_, ?_⟩
  · exact (evalRun_bound f a).trans (by simpa [encode_decode bits f valid] using weight_le_encoding f)
  · simpa only [List.append_nil, evalRun_value] using compile_machine_steps f a [] []

theorem parsed_eval_space (bits a : Word) (p : List Instruction) (f : Formula)
    (parsed : parseProgram (bits.length + 1) bits = some p)
    (valid : decode bits = some f) (n : Nat) (s : EvalState)
    (trace : EvalSteps a n (.exec p []) s) :
    evalDataSize a s ≤ 2 * a.length + bits.length + 1 := by
  have hp : p = compile f := Option.some.inj (parsed.symm.trans (parseProgram_decode bits f valid))
  subst p
  simpa [encode_decode bits f valid] using evalMachine_space f a [] n s trace

theorem decideRun_valid_fixed_width (bits : Word) (f : Formula) (K : Nat)
    (valid : decode bits = some f) (cap : f.width ≤ K) :
    (decideRun bits).2 ≤ (14 * 2 ^ K + 12) * (bits.length + 1) ^ 2 := by
  rw [← encode_decode bits f valid]
  exact decideRun_fixed_width f K cap

theorem decideRun_valid_logarithmic_width (bits : Word) (f : Formula)
    (valid : decode bits = some f) (cap : f.width ≤ Nat.log 2 (bits.length + 1)) :
    (decideRun bits).2 ≤ 24 * (bits.length + 1) ^ 2 := by
  have h := encode_decode bits f valid
  rw [← h] at cap ⊢
  exact decideRun_logarithmic_width f cap

end OracleMachines.SAT
