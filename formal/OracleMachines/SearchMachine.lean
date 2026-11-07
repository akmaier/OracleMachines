import OracleMachines.StackMachine

/-!
# Operational search across complete assignments

Each step either advances the evaluator by one instruction/read cell, selects
an assignment, or consumes its final Boolean. Candidate generation and binary
parsing are supplied separately. Thus this closes the search/evaluation
composition, not the full finite-alphabet simulation obligation.
-/
namespace OracleMachines.SAT

inductive SearchState where
  | next (pending : List Word)
  | evaluating (assignment : Word) (pending : List Word) (state : EvalState)
  | done (answer : Option Word)
  | invalid
  deriving DecidableEq, Repr

def searchFinish (a : Word) (rest : List Word) : EvalState → SearchState
  | .exec [] [true] => .done (some a)
  | .exec [] [false] => .next rest
  | _ => .invalid

def searchStep (code : List Instruction) : SearchState → Option SearchState
  | .next [] => some (.done none)
  | .next (a :: rest) => some (.evaluating a rest (.exec code []))
  | .evaluating a rest s => match evalStep a s with
    | some t => some (.evaluating a rest t)
    | none => some (searchFinish a rest s)
  | .done _ | .invalid => none

inductive SearchSteps (code : List Instruction) : Nat → SearchState → SearchState → Prop where
  | refl (s) : SearchSteps code 0 s s
  | cons {s t u n} : searchStep code s = some t → SearchSteps code n t u →
      SearchSteps code (n + 1) s u

theorem SearchSteps.trans {code : List Instruction} {s t u : SearchState} {m n : Nat}
    (h : SearchSteps code m s t) (k : SearchSteps code n t u) :
    SearchSteps code (m + n) s u := by
  induction h with
  | refl => simpa using k
  | cons step _ ih =>
    have ht := SearchSteps.cons step (ih k)
    simpa [Nat.add_assoc, Nat.add_comm, Nat.add_left_comm] using ht

theorem lift_evaluation (code : List Instruction) (a : Word) (rest : List Word)
    {n : Nat} {s t : EvalState} (h : EvalSteps a n s t) :
    SearchSteps code n (.evaluating a rest s) (.evaluating a rest t) := by
  induction h with
  | refl => exact .refl _
  | cons step _ ih => exact .cons (by simp [searchStep, step]) ih

def searchMachineCost (f : Formula) : List Word → Nat
  | [] => 1
  | a :: rest => (evalRun f a).2 + 2 + if (evalRun f a).1 then 0 else searchMachineCost f rest

theorem search_machine_steps (f : Formula) (assignments : List Word) :
    SearchSteps (compile f) (searchMachineCost f assignments) (.next assignments)
      (.done (assignments.find? (fun a => f.eval (valuation a)))) := by
  induction assignments with
  | nil => exact .cons rfl (.refl _)
  | cons a rest ih =>
    have eval := lift_evaluation (compile f) a rest (compile_machine_steps f a [] [])
    simp only [List.append_nil] at eval
    have first : SearchSteps (compile f) 1 (.next (a :: rest))
        (.evaluating a rest (.exec (compile f) [])) := .cons rfl (.refl _)
    cases hb : (evalRun f a).1 with
    | false =>
      rw [hb] at eval
      have last : SearchSteps (compile f) 1 (.evaluating a rest (.exec [] [false])) (.next rest) :=
        .cons rfl (.refl _)
      have trace := ((first.trans eval).trans last).trans ih
      convert trace using 1 <;> simp [searchMachineCost, List.find?, ← evalRun_value, hb,
        Nat.add_comm]
      all_goals omega
    | true =>
      rw [hb] at eval
      have last : SearchSteps (compile f) 1 (.evaluating a rest (.exec [] [true])) (.done (some a)) :=
        .cons rfl (.refl _)
      have trace := (first.trans eval).trans last
      convert trace using 1 <;> simp [searchMachineCost, List.find?, ← evalRun_value, hb,
        Nat.add_comm]
      all_goals omega

theorem search_machine_bound (f : Formula) (assignments : List Word) :
    searchMachineCost f assignments ≤ 1 + assignments.length * (weight f + 2) := by
  induction assignments with
  | nil => simp [searchMachineCost]
  | cons a rest ih =>
    have he := evalRun_bound f a
    simp only [searchMachineCost, List.length_cons]
    split <;> nlinarith

theorem search_machine_complete (f : Formula) :
    ∃ count, count ≤ 1 + 2 ^ f.width * (weight f + 2) ∧
      SearchSteps (compile f) count (.next (words f.width)) (.done (findWitness f)) := by
  refine ⟨searchMachineCost f (words f.width), ?_, search_machine_steps f (words f.width)⟩
  simpa using search_machine_bound f (words f.width)

def assignmentPayload : List Word → Nat
  | [] => 0
  | a :: rest => a.length + 1 + assignmentPayload rest

theorem assignment_payload_bound (assignments : List Word) (width : Nat)
    (bounded : ∀ a ∈ assignments, a.length ≤ width) :
    assignmentPayload assignments ≤ (width + 1) * assignments.length := by
  induction assignments with
  | nil => simp [assignmentPayload]
  | cons a rest ih =>
    have ha := bounded a (by simp)
    have hr := ih (fun b hb => bounded b (by simp [hb]))
    simp only [assignmentPayload, List.length_cons]
    nlinarith

theorem assignment_payload_words (width : Nat) :
    assignmentPayload (words width) ≤ (width + 1) * 2 ^ width := by
  have h := assignment_payload_bound (words width) width (fun a ha => le_of_eq ((mem_words a width).mp ha))
  simpa using h

def SearchInvariant (code : List Instruction) (payload width : Nat) : SearchState → Prop
  | .next pending => assignmentPayload pending ≤ payload ∧ ∀ a ∈ pending, a.length ≤ width
  | .evaluating a pending s =>
    assignmentPayload pending + a.length + 1 ≤ payload ∧ a.length ≤ width ∧
    (∀ b ∈ pending, b.length ≤ width) ∧
    evalPotential s ≤ (encodeProgram code).length ∧ evalReadLength s ≤ a.length
  | .done result => ∀ a ∈ result, a.length ≤ width
  | .invalid => True

theorem searchStep_invariant (code : List Instruction) (payload width : Nat) (s t : SearchState)
    (safe : SearchInvariant code payload width s) (step : searchStep code s = some t) :
    SearchInvariant code payload width t := by
  cases s with
  | done result => simp [searchStep] at step
  | invalid => simp [searchStep] at step
  | next pending =>
    rcases safe with ⟨hp, hw⟩
    cases pending with
    | nil => simp [searchStep] at step; subst t; simp [SearchInvariant]
    | cons a rest =>
      simp [searchStep] at step; subst t
      have ha := hw a (by simp)
      have hr : ∀ b ∈ rest, b.length ≤ width := fun b hb => hw b (by simp [hb])
      refine ⟨?_, ha, hr, ?_, ?_⟩
      · simp [assignmentPayload] at hp; omega
      · simp [evalPotential]
      · simp [evalReadLength]
  | evaluating a pending state =>
    rcases safe with ⟨hp, ha, hr, hq, hs⟩
    cases he : evalStep a state with
    | some next =>
      simp [searchStep, he] at step; subst t
      exact ⟨hp, ha, hr, (evalStep_potential a state next he).trans hq,
        evalStep_readLength a state next hs he⟩
    | none =>
      simp only [searchStep, he, Option.some.injEq] at step; subst t
      unfold searchFinish
      split
      · simpa [SearchInvariant] using ha
      · exact ⟨by omega, hr⟩
      · trivial

theorem SearchSteps.invariant {code : List Instruction} {payload width n : Nat} {s t : SearchState}
    (trace : SearchSteps code n s t) (safe : SearchInvariant code payload width s) :
    SearchInvariant code payload width t := by
  induction trace with
  | refl => exact safe
  | cons step _ ih => exact ih (searchStep_invariant _ _ _ _ _ safe step)

/-- Payload symbols, not physical heap bytes or pointer representations. -/
def searchDataSize (code : List Instruction) (s : SearchState) : Nat :=
  (encodeProgram code).length + match s with
  | .next pending => assignmentPayload pending + 1
  | .evaluating a pending state => assignmentPayload pending + evalDataSize a state + 2
  | .done none | .invalid => 1
  | .done (some a) => a.length + 1

theorem searchInvariant_space (code : List Instruction) (payload width : Nat) (s : SearchState)
    (safe : SearchInvariant code payload width s) :
    searchDataSize code s ≤ payload + width + 2 * (encodeProgram code).length + 2 := by
  cases s with
  | next pending => simp only [SearchInvariant] at safe; simp only [searchDataSize]; omega
  | invalid => simp [searchDataSize]; omega
  | evaluating a pending state =>
    simp only [SearchInvariant] at safe
    simp only [searchDataSize, evalDataSize]
    omega
  | done result =>
    cases result with
    | none => simp [searchDataSize]; omega
    | some a => simp only [SearchInvariant, Option.mem_some_iff] at safe
                have ha := safe a rfl
                simp only [searchDataSize]
                omega

theorem search_machine_space (f : Formula) (n : Nat) (s : SearchState)
    (trace : SearchSteps (compile f) n (.next (words f.width)) s) :
    searchDataSize (compile f) s ≤
      (f.width + 1) * 2 ^ f.width + f.width + 2 * (encode f).length + 2 := by
  have start : SearchInvariant (compile f) (assignmentPayload (words f.width)) f.width
      (.next (words f.width)) := ⟨le_rfl, fun a ha => le_of_eq ((mem_words a f.width).mp ha)⟩
  have bound := searchInvariant_space (compile f) _ f.width s (trace.invariant start)
  have candidates := assignment_payload_words f.width
  change searchDataSize (compile f) s ≤ _ + _ + 2 * (encode f).length + 2 at bound
  omega

theorem search_machine_restricted_space (f : Formula) (n : Nat) (s : SearchState)
    (small : 2 ^ f.width ≤ (encode f).length + 1)
    (trace : SearchSteps (compile f) n (.next (words f.width)) s) :
    searchDataSize (compile f) s ≤ 5 * ((encode f).length + 1) ^ 2 := by
  have bound := search_machine_space f n s trace
  have width := (width_le_weight f).trans (weight_le_encoding f)
  have product := Nat.mul_le_mul (Nat.add_le_add_right width 1) small
  nlinarith

end OracleMachines.SAT
