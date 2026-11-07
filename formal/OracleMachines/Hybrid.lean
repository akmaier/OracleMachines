import OracleMachines.CostedSAT

/-!
# A concrete certified fast/slow policy

The learned state is one satisfying assignment obtained from a previous fallback
solve. It can transfer to a different formula. Every proposal is checked against
the full current formula; a rejected proposal invokes the exact solver. This is
a minimal witness-reuse learner, not a neural predictor or full-domain compiler.
-/

namespace OracleMachines.SAT

def probeRun (state : Option Word) (f : Formula) : Run Bool :=
  match state with
  | none => (false, 1)
  | some a => let e := evalRun f a; (e.1, e.2 + 1)

theorem probeRun_sound (state : Option Word) (f : Formula) (h : (probeRun state f).1 = true) :
    Satisfiable f := by
  cases state with
  | none => simp [probeRun] at h
  | some a => exact ⟨valuation a, (evalRun_value f a).symm.trans h⟩

theorem probeRun_bound (state : Option Word) (f : Formula) :
    (probeRun state f).2 ≤ weight f + 1 := by
  cases state with
  | none => simp [probeRun]
  | some a => exact Nat.add_le_add_right (evalRun_bound f a) 1

def copyRun : Word → Run Word
  | [] => ([], 1)
  | b :: tail => let r := copyRun tail; (b :: r.1, r.2 + 2)

theorem copyRun_spec (a : Word) : (copyRun a).1 = a ∧ (copyRun a).2 = 2 * a.length + 1 := by
  induction a with
  | nil => simp [copyRun]
  | cons b tail ih => simp [copyRun, ih]; omega

structure HybridResult where
  answer : Bool
  state : Option Word
  work : Nat
  fast : Bool
  deriving Repr

def hybridRun (state : Option Word) (f : Formula) : HybridResult :=
  let probe := probeRun state f
  if probe.1 then
    { answer := true, state := state, work := probe.2 + 1, fast := true }
  else
    let solved := solveRun f
    match solved.1 with
    | none =>
      { answer := false, state := state, work := probe.2 + solved.2 + 2, fast := false }
    | some a =>
      let copied := copyRun a
      { answer := true, state := some copied.1,
        work := probe.2 + solved.2 + copied.2 + 2, fast := false }

theorem hybridRun_correct (state : Option Word) (f : Formula) :
    (hybridRun state f).answer = true ↔ Satisfiable f := by
  unfold hybridRun
  dsimp only
  split
  · rename_i hp
    simp only
    exact iff_of_true True.intro (probeRun_sound state f hp)
  · cases hs : (solveRun f).1 with
    | none => simp only; exact iff_of_false (by decide) ((solveRun_correct f).mp hs)
    | some a =>
      have hw : findWitness f = some a := (solveRun_value f).symm.trans hs
      simp only
      exact iff_of_true True.intro ⟨valuation a, witness_sound f a hw⟩

theorem hybridRun_answer (state : Option Word) (f : Formula) :
    (hybridRun state f).answer = solve f := by
  have h := hybridRun_correct state f
  have hs := solve_correct f
  cases h1 : (hybridRun state f).answer <;> cases h2 : solve f <;> simp_all

theorem hybridRun_hit (state : Option Word) (f : Formula) (h : (probeRun state f).1 = true) :
    (hybridRun state f).state = state ∧
      (hybridRun state f).work = (probeRun state f).2 + 1 ∧
      (hybridRun state f).fast = true := by
  simp [hybridRun, h]

theorem solveRun_witness_length (f : Formula) (a : Word) (h : (solveRun f).1 = some a) :
    a.length = f.width := by
  have hw : findWitness f = some a := (solveRun_value f).symm.trans h
  exact (mem_words a f.width).mp (List.mem_of_find?_eq_some hw)

/-- Even on misses, the policy's extra charged work is bounded. -/
theorem hybridRun_overhead (state : Option Word) (f : Formula) :
    (hybridRun state f).work ≤ (solveRun f).2 + weight f + 2 * f.width + 4 := by
  have hp := probeRun_bound state f
  unfold hybridRun
  dsimp only
  split
  · simp only; omega
  · cases hs : (solveRun f).1 with
    | none => simp only; omega
    | some a =>
      have hl := solveRun_witness_length f a hs
      simp only [(copyRun_spec a).2]
      omega

structure StreamResult where
  answers : List Bool
  state : Option Word
  work : Nat
  hits : Nat
  deriving Repr

/-- One additional unit per served query charges the stream controller. -/
def serve (state : Option Word) : List Formula → StreamResult
  | [] => { answers := [], state := state, work := 0, hits := 0 }
  | f :: rest =>
    let current := hybridRun state f
    let tail := serve current.state rest
    { answers := current.answer :: tail.answers, state := tail.state,
      work := current.work + 1 + tail.work,
      hits := (if current.fast then 1 else 0) + tail.hits }

theorem serve_correct (state : Option Word) (fs : List Formula) :
    (serve state fs).answers = fs.map solve := by
  induction fs generalizing state with
  | nil => rfl
  | cons f rest ih => simp [serve, ih, hybridRun_answer]

def baselineWork (fs : List Formula) : Nat :=
  (fs.map (fun f => (solveRun f).2 + 2)).sum

/-- Actual net savings, recomputed along the same evolving state as `serve`. -/
def netSaved (state : Option Word) : List Formula → Int
  | [] => 0
  | f :: rest =>
    let current := hybridRun state f
    ((solveRun f).2 : Int) + 2 - ((current.work : Int) + 1) + netSaved current.state rest

theorem actual_savings_identity (state : Option Word) (fs : List Formula) :
    (baselineWork fs : Int) - ((serve state fs).work : Int) = netSaved state fs := by
  induction fs generalizing state with
  | nil => simp [baselineWork, serve, netSaved]
  | cons f rest ih => simp [baselineWork, serve, netSaved] at *; rw [← ih]; omega

theorem repeated_hit_work (state : Option Word) (f : Formula)
    (hit : (probeRun state f).1 = true) (q : Nat) :
    (serve state (List.replicate q f)).work = q * ((probeRun state f).2 + 2) := by
  induction q with
  | zero => simp [serve]
  | succ q ih =>
    simp only [List.replicate_succ, serve, (hybridRun_hit state f hit).1,
      (hybridRun_hit state f hit).2.1, ih]
    ring

/-- A finite, concrete break-even condition including an external training bill.
The training bill must be the actual charged acquisition cost for `state`. -/
theorem repeated_hit_savings (state : Option Word) (f : Formula)
    (hit : (probeRun state f).1 = true) (q training margin : Nat)
    (gap : (probeRun state f).2 + margin ≤ (solveRun f).2)
    (repaid : training < q * margin) :
    training + (serve state (List.replicate q f)).work < baselineWork (List.replicate q f) := by
  rw [repeated_hit_work state f hit q]
  simp only [baselineWork, List.map_replicate, List.sum_replicate, smul_eq_mul]
  nlinarith [Nat.mul_le_mul_left q gap]

end OracleMachines.SAT
