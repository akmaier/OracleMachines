import OracleMachines.AffineGrowth

/-! Charges attached to the executed elimination loops. A pivot scan is charged
its whole row list, including early exits. A reduction is charged n+1 produced
coefficient/rhs cells per row. Terminal checks are charged all rows and a possible
contradiction vector. These are reference upper charges, not instructions or bytes. -/
namespace OracleMachines.Affine
variable {n : Nat}

def basisRun : List (Fin n) → List (Row n) → List (Row n) × Nat
  | [], rows => (constants rows,rows.length+n+1)
  | i::todo, rows =>
    match choose rows i with
    | .absent _ =>
      let next := basisRun todo rows
      (next.1,rows.length+next.2)
    | .found p _ _ =>
      let next := basisRun todo (rows.map (fun r => p.reduce r i))
      (p::next.1,rows.length*(n+2)+next.2)

def projectRun : List (Fin n) → List (Row n) → List (Row n) × Nat
  | [], rows => (rows,0)
  | i::todo, rows =>
    match choose rows i with
    | .absent _ =>
      let next := projectRun todo rows
      (next.1,rows.length+next.2)
    | .found p _ _ =>
      let next := projectRun todo (rows.map (fun r => p.reduce r i))
      (next.1,rows.length*(n+2)+next.2)

theorem basisRun_value (todo : List (Fin n)) (rows : List (Row n)) :
    (basisRun todo rows).1 = basisAux todo rows := by
  induction todo generalizing rows with
  | nil => rfl
  | cons i todo ih =>
    simp only [basisRun,basisAux]
    cases choose rows i <;> simp only [ih]

theorem projectRun_value (todo : List (Fin n)) (rows : List (Row n)) :
    (projectRun todo rows).1 = project todo rows := by
  induction todo generalizing rows with
  | nil => rfl
  | cons i todo ih =>
    simp only [projectRun,project,eliminate]
    cases choose rows i <;> simp only [ih]

theorem basisRun_bound (todo : List (Fin n)) (rows : List (Row n)) :
    (basisRun todo rows).2 ≤ eliminationBudget n todo.length rows.length := by
  induction todo generalizing rows with
  | nil => simp [basisRun,eliminationBudget]; omega
  | cons i todo ih =>
    simp only [basisRun,List.length_cons]
    cases choose rows i with
    | absent =>
      have h := ih rows
      dsimp [eliminationBudget] at *
      nlinarith
    | found p _ _ =>
      have h := ih (rows.map (fun r => p.reduce r i))
      simp only [List.length_map] at h
      dsimp [eliminationBudget] at *
      nlinarith

theorem projectRun_bound (todo : List (Fin n)) (rows : List (Row n)) :
    (projectRun todo rows).2 ≤ todo.length*(n+2)*rows.length := by
  induction todo generalizing rows with
  | nil => simp [projectRun]
  | cons i todo ih =>
    simp only [projectRun,List.length_cons]
    cases choose rows i with
    | absent => have h := ih rows; dsimp; nlinarith
    | found p _ _ =>
      have h := ih (rows.map (fun r => p.reduce r i))
      simp only [List.length_map] at h
      dsimp; nlinarith

def decideRun (rows : List (Row n)) : Bool × Nat :=
  let result := projectRun (List.finRange n) rows
  (result.1.all (fun r => r.rhs == 0),result.2+result.1.length)

theorem decideRun_value (rows : List (Row n)) : (decideRun rows).1 = decide rows := by
  simp only [decideRun,projectRun_value,decide]

theorem decideRun_bound (rows : List (Row n)) :
    (decideRun rows).2 ≤ eliminationBudget n n rows.length := by
  have h := projectRun_bound (List.finRange n) rows
  simp only [List.length_finRange] at h
  simp only [decideRun,projectRun_value,project_length]
  dsimp [eliminationBudget]
  nlinarith

/-- The native append executes this pair; its first component is certified exact. -/
def extendRun {b : Nat} (previous : List (Row b)) (equations : List (Row (b+b))) :
    List (Row b) × Nat :=
  let input := previous.map Row.liftLeft ++ equations
  let projected := projectRun (leftIndices b) input
  let dropped := projected.1.map Row.dropLeft
  let normalized := basisRun (List.finRange b) dropped
  (normalized.1,previous.length*(2*b+1)+projected.2+dropped.length*(b+1)+normalized.2)

theorem extendRun_value {b : Nat} (previous : List (Row b)) (equations : List (Row (b+b))) :
    (extendRun previous equations).1 = extend previous equations := by
  simp only [extendRun,projectRun_value,basisRun_value,extend,basis]

theorem eliminationBudget_mono (n stages a b : Nat) (bound : a ≤ b) :
    eliminationBudget n stages a ≤ eliminationBudget n stages b := by
  unfold eliminationBudget
  exact Nat.add_le_add_right (Nat.mul_le_mul_left _ bound) _

theorem extendRun_bound {b : Nat} (previous : List (Row b)) (equations : List (Row (b+b)))
    (compact : previous.length ≤ b+1) :
    (extendRun previous equations).2 + (decideRun (extendRun previous equations).1).2 ≤
      appendBudget b equations.length := by
  let input := previous.map Row.liftLeft ++ equations
  let dropped := (projectRun (leftIndices b) input).1.map Row.dropLeft
  have size : input.length ≤ b+1+equations.length := by simp [input]; omega
  have droppedSize : dropped.length = input.length := by
    simp [dropped,projectRun_value,project_length]
  have projection := projectRun_bound (leftIndices b) input
  have projBound : (projectRun (leftIndices b) input).2 ≤
      eliminationBudget (b+b) b (b+1+equations.length) := by
    have mono := eliminationBudget_mono (b+b) b input.length (b+1+equations.length) size
    have length : (leftIndices b).length = b := by simp [leftIndices]
    rw [length] at projection
    dsimp [eliminationBudget] at *
    nlinarith
  have norm := basisRun_bound (List.finRange b) dropped
  simp only [List.length_finRange,droppedSize] at norm
  have normBound := le_trans norm (eliminationBudget_mono b b _ _ size)
  have decision := decideRun_bound (extendRun previous equations).1
  have compactNew : (extendRun previous equations).1.length ≤ b+1 := by
    rw [extendRun_value]; exact extend_size _ _
  have decBound := le_trans decision (eliminationBudget_mono b b _ _ compactNew)
  have liftBound := Nat.mul_le_mul_right (2*b+1) compact
  have dropBound := Nat.mul_le_mul_right (b+1) size
  change previous.length*(2*b+1)+(projectRun (leftIndices b) input).2+
    dropped.length*(b+1)+(basisRun (List.finRange b) dropped).2+
    (decideRun (extendRun previous equations).1).2 ≤ _
  rw [droppedSize]
  dsimp [appendBudget]
  omega

def State.appendRun {b : Nat} (state : State b) (equations : List (Row (b+b))) : State b × Nat :=
  let result := extendRun state.summary equations
  (⟨.append state.history equations,result.1,by
      intro v
      rw [extendRun_value,extend_exact]
      exact exists_congr (fun u => and_congr_left (fun _ => state.exact u)),by
      rw [extendRun_value]; exact extend_size _ _⟩,result.2)

theorem State.appendRun_history {b : Nat} (state : State b) (equations : List (Row (b+b))) :
    (state.appendRun equations).1.history = .append state.history equations := rfl

theorem State.appendRun_bound {b : Nat} (state : State b) (equations : List (Row (b+b))) :
    (state.appendRun equations).2 + (decideRun (state.appendRun equations).1.summary).2 ≤
      appendBudget b equations.length := extendRun_bound _ _ state.compact

/-- Composition of the same charged appends over the original equation history.
The initial unconstrained state is assigned zero coefficient-cell charge. -/
def replayRun {b : Nat} : History b → State b × Nat
  | .empty => (initial b,0)
  | .append old equations =>
    let previous := replayRun old
    let next := previous.1.appendRun equations
    (next.1,previous.2+next.2+(decideRun next.1.summary).2)

theorem replayRun_history {b : Nat} (history : History b) :
    (replayRun history).1.history = history := by
  induction history with
  | empty => rfl
  | append old equations ih => simp only [replayRun,State.appendRun_history,ih]

theorem replayRun_budget {b : Nat} (history : History b) :
    (replayRun history).2 ≤ history.workBudget := by
  induction history with
  | empty => exact Nat.le_refl 0
  | append old equations ih =>
    have step := (replayRun old).1.appendRun_bound equations
    change (replayRun old).2 + ((replayRun old).1.appendRun equations).2 +
      (decideRun ((replayRun old).1.appendRun equations).1.summary).2 ≤
      old.workBudget+appendBudget b equations.length
    omega

theorem replayRun_bound {b cap : Nat} (history : History b) (bounded : history.Bounded cap) :
    (replayRun history).2 ≤ history.steps*appendBudget b cap :=
  le_trans (replayRun_budget history) (history_work_bound history bounded)

end OracleMachines.Affine
