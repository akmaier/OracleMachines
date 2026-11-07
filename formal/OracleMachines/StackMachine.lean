import OracleMachines.CostedSAT

/-!
# An explicit transition machine for formula evaluation

The machine executes already supplied postfix instructions with a Boolean value
stack. A variable read walks the assignment one cell at a time and decrements a
unary index. Each transition counts one step; no transition calls `evalRun`.
The evaluation theorem identifies the exact transition count with `evalRun`.

This is a list/stack machine, not a Turing machine or a model of compiled Lean.
Supplying the program, pointer access, memory management, and counter arithmetic
require separate treatment. The space bound counts data payload symbols,
including unary indices and a second copy of the current assignment suffix.
It includes one control tag, but not addresses, list headers, or serialization
delimiters. It is not a claim about physical heap bytes.
-/

namespace OracleMachines.SAT

inductive EvalState where
  | exec (code : List Instruction) (values : Word)
  | read (suffix : Word) (index : Nat) (code : List Instruction) (values : Word)
  | fault
  deriving DecidableEq, Repr

def evalStep (assignment : Word) : EvalState → Option EvalState
  | .exec [] _ => none
  | .exec (.falsum :: rest) values => some (.exec rest (false :: values))
  | .exec (.load i :: rest) values => some (.read assignment i rest values)
  | .exec (.neg :: rest) (b :: values) => some (.exec rest ((!b) :: values))
  | .exec (.conj :: rest) (b :: a :: values) => some (.exec rest ((a && b) :: values))
  | .exec _ _ => some .fault
  | .read [] _ rest values => some (.exec rest (false :: values))
  | .read (b :: _) 0 rest values => some (.exec rest (b :: values))
  | .read (_ :: tail) (i + 1) rest values => some (.read tail i rest values)
  | .fault => none

inductive EvalSteps (assignment : Word) : Nat → EvalState → EvalState → Prop where
  | refl (s : EvalState) : EvalSteps assignment 0 s s
  | cons {s t u : EvalState} {n : Nat} :
      evalStep assignment s = some t → EvalSteps assignment n t u →
      EvalSteps assignment (n + 1) s u

theorem EvalSteps.trans {a : Word} {s t u : EvalState} {m n : Nat}
    (h : EvalSteps a m s t) (k : EvalSteps a n t u) : EvalSteps a (m + n) s u := by
  induction h with
  | refl => simpa using k
  | cons step _ ih =>
    have ht := EvalSteps.cons step (ih k)
    simpa [Nat.add_assoc, Nat.add_comm, Nat.add_left_comm] using ht

theorem read_machine_steps (a suffix : Word) (i : Nat)
    (rest : List Instruction) (values : Word) :
    EvalSteps a (readRun suffix i).2 (.read suffix i rest values)
      (.exec rest ((readRun suffix i).1 :: values)) := by
  induction suffix generalizing i with
  | nil => exact .cons rfl (.refl _)
  | cons b tail ih =>
    cases i with
    | zero => exact .cons rfl (.refl _)
    | succ i => exact .cons rfl (ih i)

theorem compile_machine_steps (f : Formula) (a values : Word) (rest : List Instruction) :
    EvalSteps a (evalRun f a).2 (.exec (compile f ++ rest) values)
      (.exec rest ((evalRun f a).1 :: values)) := by
  induction f generalizing rest values with
  | falsum => exact .cons rfl (.refl _)
  | var i => exact .cons rfl (read_machine_steps a a i rest values)
  | neg f ih =>
    have h := (ih values (.neg :: rest)).trans
      (EvalSteps.cons (assignment := a) (s := .exec (.neg :: rest) ((evalRun f a).1 :: values))
        rfl (.refl _))
    simpa [compile, evalRun, List.append_assoc] using h
  | conj f g ihf ihg =>
    have h := ((ihf values (compile g ++ .conj :: rest)).trans
      (ihg ((evalRun f a).1 :: values) (.conj :: rest))).trans
      (EvalSteps.cons (assignment := a)
        (s := .exec (.conj :: rest) ((evalRun g a).1 :: (evalRun f a).1 :: values))
        rfl (.refl _))
    simpa [compile, evalRun, List.append_assoc] using h

def evalMachineRun (a : Word) : Nat → EvalState → EvalState
  | 0, s => s
  | fuel + 1, s => match evalStep a s with
    | none => s
    | some t => evalMachineRun a fuel t

theorem EvalSteps.run {a : Word} {s t : EvalState} {n : Nat}
    (h : EvalSteps a n s t) : evalMachineRun a n s = t := by
  induction h with
  | refl => rfl
  | cons step _ ih => simpa [evalMachineRun, step] using ih

theorem evalMachineRun_add (a : Word) (m n : Nat) (s : EvalState) :
    evalMachineRun a (m + n) s = evalMachineRun a n (evalMachineRun a m s) := by
  induction m generalizing s with
  | zero => simp [evalMachineRun]
  | succ m ih =>
    simp only [Nat.succ_add, evalMachineRun]
    cases h : evalStep a s with
    | some t => simpa [h] using ih t
    | none =>
      have stop : ∀ k, evalMachineRun a k s = s := by
        intro k; cases k <;> simp [evalMachineRun, h]
      simp [stop]

theorem evalMachineRun_terminal (a values : Word) (n : Nat) :
    evalMachineRun a n (.exec [] values) = .exec [] values := by
  cases n <;> rfl

theorem evalMachine_correct (f : Formula) (a : Word) :
    evalMachineRun a (weight f) (.exec (compile f) []) =
      .exec [] [f.eval (valuation a)] := by
  have h := (compile_machine_steps f a [] []).run
  simp only [List.append_nil, evalRun_value] at h
  have hb := evalRun_bound f a
  have he : weight f = (evalRun f a).2 + (weight f - (evalRun f a).2) := by omega
  rw [he, evalMachineRun_add, h, evalMachineRun_terminal]

/-- Remaining serialized instruction bits, value bits, and unary read index. -/
def evalPotential : EvalState → Nat
  | .exec code values => (encodeProgram code).length + values.length
  | .read _ i code values => (encodeProgram code).length + values.length + i + 1
  | .fault => 0

def evalReadLength : EvalState → Nat
  | .read suffix _ _ _ => suffix.length
  | _ => 0

/-- Read-only assignment, current suffix, control tag, and remaining payload.
This deliberately counts a suffix separately even if a runtime shares it. -/
def evalDataSize (a : Word) (s : EvalState) : Nat :=
  a.length + evalReadLength s + evalPotential s + 1

theorem evalStep_potential (a : Word) (s t : EvalState)
    (h : evalStep a s = some t) : evalPotential t ≤ evalPotential s := by
  cases s with
  | fault => simp [evalStep] at h
  | exec code values =>
    cases code with
    | nil => simp [evalStep] at h
    | cons i rest =>
      cases i with
      | falsum => simp [evalStep] at h; subst t; simp [evalPotential, encodeProgram, encodeInstruction]; omega
      | load i => simp [evalStep] at h; subst t; simp [evalPotential, encodeProgram, encodeInstruction, putNat]; omega
      | neg =>
        cases values <;> simp [evalStep] at h <;> subst t
        · simp [evalPotential]
        · simp [evalPotential, encodeProgram, encodeInstruction]; omega
      | conj =>
        rcases values with _ | ⟨b, _ | ⟨c, tail⟩⟩
        all_goals simp [evalStep] at h; subst t
        · simp [evalPotential]
        · simp [evalPotential]
        · simp [evalPotential, encodeProgram, encodeInstruction]; omega
  | read suffix i code values =>
    cases suffix with
    | nil => simp [evalStep] at h; subst t; simp [evalPotential]; omega
    | cons b tail =>
      cases i <;> simp [evalStep] at h <;> subst t <;> simp [evalPotential]; omega

theorem evalStep_readLength (a : Word) (s t : EvalState)
    (bound : evalReadLength s ≤ a.length) (h : evalStep a s = some t) :
    evalReadLength t ≤ a.length := by
  cases s with
  | fault => simp [evalStep] at h
  | exec code values =>
    cases code with
    | nil => simp [evalStep] at h
    | cons i rest =>
      cases i with
      | falsum => simp [evalStep] at h; subst t; simp [evalReadLength]
      | load i => simp [evalStep] at h; subst t; rfl
      | neg => cases values <;> simp [evalStep] at h <;> subst t <;> simp [evalReadLength]
      | conj =>
        rcases values with _ | ⟨b, _ | ⟨c, tail⟩⟩
        all_goals simp [evalStep] at h; subst t; simp [evalReadLength]
  | read suffix i code values =>
    cases suffix with
    | nil => simp [evalStep] at h; subst t; simp [evalReadLength]
    | cons b tail =>
      cases i <;> simp [evalStep] at h <;> subst t <;> simp [evalReadLength] at *
      omega

theorem EvalSteps.bounds {a : Word} {s t : EvalState} {n : Nat}
    (h : EvalSteps a n s t) (readBound : evalReadLength s ≤ a.length) :
    evalPotential t ≤ evalPotential s ∧ evalReadLength t ≤ a.length := by
  induction h with
  | refl => exact ⟨le_rfl, readBound⟩
  | cons step _ ih =>
    have hi := ih (evalStep_readLength _ _ _ readBound step)
    exact ⟨hi.1.trans (evalStep_potential _ _ _ step), hi.2⟩

theorem evalMachine_space (f : Formula) (a values : Word) (n : Nat) (s : EvalState)
    (h : EvalSteps a n (.exec (compile f) values) s) :
    evalDataSize a s ≤ 2 * a.length + (encode f).length + values.length + 1 := by
  have hb := h.bounds (by simp [evalReadLength])
  change evalPotential s ≤ (encode f).length + values.length ∧
    evalReadLength s ≤ a.length at hb
  simp only [evalDataSize]
  omega

end OracleMachines.SAT
