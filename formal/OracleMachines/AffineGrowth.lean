import OracleMachines.Affine

/-! Unbounded mathematical append histories with a fixed interface width.
Every append introduces a fresh block. Previous blocks can only be constrained
through the current boundary. Old histories are immutable, but their SAT answers
need not survive adding constraints to a new version. -/
namespace OracleMachines.Affine

inductive History (b : Nat) where
  | empty
  | append (previous : History b) (equations : List (Row (b+b)))

def History.Holds {b : Nat} : History b → (Fin b → F) → Prop
  | .empty, _ => True
  | .append old equations, v => ∃ u, old.Holds u ∧ OracleMachines.Affine.Holds equations (Fin.append u v)

def History.steps {b : Nat} : History b → Nat
  | .empty => 0
  | .append old _ => old.steps+1

def History.sourceCells {b : Nat} : History b → Nat
  | .empty => 0
  | .append old equations => old.sourceCells + equations.length*(2*b+1)

structure State (b : Nat) where
  history : History b
  summary : List (Row b)
  exact : ∀ v, Holds summary v ↔ history.Holds v
  compact : summary.length ≤ b+1

def initial (b : Nat) : State b :=
  ⟨.empty,[],by intro v; simp [Holds,History.Holds],by simp⟩

def State.append {b : Nat} (state : State b) (equations : List (Row (b+b))) : State b :=
  ⟨.append state.history equations,extend state.summary equations,by
    intro v
    rw [extend_exact]
    exact exists_congr (fun u => and_congr_left (fun _ => state.exact u)),extend_size _ _⟩

def State.answer {b : Nat} (state : State b) : Bool := decide state.summary

theorem State.answer_exact {b : Nat} (state : State b) :
    state.answer = true ↔ ∃ v, state.history.Holds v := by
  rw [State.answer,decide_exact]
  exact exists_congr state.exact

theorem State.answer_false {b : Nat} (state : State b) :
    state.answer = false ↔ ¬ ∃ v, state.history.Holds v := by
  rw [← state.answer_exact]
  cases state.answer <;> decide

theorem State.append_steps {b : Nat} (state : State b) (equations : List (Row (b+b))) :
    (state.append equations).history.steps = state.history.steps+1 := rfl

theorem State.summary_cells {b : Nat} (state : State b) :
    state.summary.length*(b+1) ≤ (b+1)^2 := by
  have := Nat.mul_le_mul_right (b+1) state.compact
  simpa [pow_two] using this

/-- Replay is linear in the number of archived appends, with the same exact
boundary invariant after every step. It never treats an old answer as evidence. -/
def replay {b : Nat} : History b → State b
  | .empty => initial b
  | .append old equations => (replay old).append equations

theorem replay_history {b : Nat} (history : History b) : (replay history).history = history := by
  induction history with
  | empty => rfl
  | append old equations ih => simp only [replay,State.append,ih]

theorem replay_exact {b : Nat} (history : History b) :
    (replay history).answer = true ↔ ∃ v, history.Holds v := by
  rw [State.answer_exact,replay_history]

/-- Reference coefficient-cell ledger. Each elimination stage scans at most m
rows and constructs at most m rows of dimension n. The terminal charges cover constant checks and a possible contradiction
vector. This is an upper charge, not a native instruction or memory-byte count. -/
def eliminationBudget (n stages rows : Nat) : Nat := (stages*(n+2)+1)*rows+(n+1)

def appendBudget (b equations : Nat) : Nat :=
  let m := b+1+equations
  (b+1)*(2*b+1) + eliminationBudget (b+b) b m + m*(b+1) +
    eliminationBudget b b m + eliminationBudget b b (b+1)

def History.workBudget {b : Nat} : History b → Nat
  | .empty => 0
  | .append old equations => old.workBudget + appendBudget b equations.length

def History.Bounded {b : Nat} (cap : Nat) : History b → Prop
  | .empty => True
  | .append old equations => old.Bounded cap ∧ equations.length ≤ cap

theorem appendBudget_mono (b c cap : Nat) (bound : c ≤ cap) :
    appendBudget b c ≤ appendBudget b cap := by
  have size : b+1+c ≤ b+1+cap := by omega
  have p := Nat.mul_le_mul_left (b*(b+b+2)+1) size
  have d := Nat.mul_le_mul_right (b+1) size
  have q := Nat.mul_le_mul_left (b*(b+2)+1) size
  dsimp [appendBudget,eliminationBudget]
  omega

theorem history_work_bound {b cap : Nat} (history : History b) (bounded : history.Bounded cap) :
    history.workBudget ≤ history.steps*appendBudget b cap := by
  induction history with
  | empty => simp [History.workBudget,History.steps]
  | append old equations ih =>
    have oldBound := ih bounded.1
    have newBound := appendBudget_mono b equations.length cap bounded.2
    simp only [History.workBudget,History.steps,Nat.add_mul,Nat.one_mul]
    omega

theorem history_source_bound {b cap : Nat} (history : History b) (bounded : history.Bounded cap) :
    history.sourceCells ≤ history.steps*(cap*(2*b+1)) := by
  induction history with
  | empty => simp [History.sourceCells,History.steps]
  | append old equations ih =>
    have oldBound := ih bounded.1
    have newBound := Nat.mul_le_mul_right (2*b+1) bounded.2
    simp only [History.sourceCells,History.steps,Nat.add_mul,Nat.one_mul]
    omega

end OracleMachines.Affine
