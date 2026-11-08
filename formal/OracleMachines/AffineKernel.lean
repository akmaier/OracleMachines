import OracleMachines.AffineResident
import Std.Data.HashMap.Lemmas

/-! Exact algebraic transitions shared by distinct original histories. Cache
entries retain coefficient inputs and results, never source-history ancestors.
Hashing selects one bounded slot; dependent equality checks justify every hit. -/
namespace OracleMachines.Affine

structure Kernel {b : Nat} (previous : List (Row b)) (equations : List (Row (b+b))) where
  summary : List (Row b)
  summary_exact : summary = (extendRun previous equations).1
  answer : Bool
  answer_exact : answer = decide summary
  charge : Nat
  charge_exact : charge = (extendRun previous equations).2 + (decideRun summary).2

def compileKernel {b : Nat} (previous : List (Row b)) (equations : List (Row (b+b))) : Kernel previous equations :=
  let result := extendRun previous equations
  let decision := decideRun result.1
  ⟨result.1,rfl,decision.1,decideRun_value _,result.2+decision.2,rfl⟩

def Kernel.attach {b : Nat} {equations : List (Row (b+b))} (previous : Resident b)
    (kernel : Kernel previous.summary equations) : Resident b :=
  ⟨previous.past.map (fun old => .append old equations),kernel.summary,by
    intro v
    rw [kernel.summary_exact,extendRun_value,extend_exact,Erased.map_out]
    exact exists_congr (fun u => and_congr_left (fun _ => previous.exact u)),by
    rw [kernel.summary_exact,extendRun_value]; exact extend_size _ _⟩

theorem Kernel.attach_history {b : Nat} {equations : List (Row (b+b))} (previous : Resident b)
    (kernel : Kernel previous.summary equations) :
    (kernel.attach previous).history = .append previous.history equations := by
  simp [Kernel.attach,Resident.history]

theorem Kernel.bound {b : Nat} {previous : List (Row b)} {equations : List (Row (b+b))}
    (kernel : Kernel previous equations) (compact : previous.length ≤ b+1) :
    kernel.charge ≤ appendBudget b equations.length := by
  rw [kernel.charge_exact,kernel.summary_exact]
  exact extendRun_bound previous equations compact

structure KernelEntry where
  width : Nat
  previous : List (Row width)
  equations : List (Row (width+width))
  kernel : Kernel previous equations

structure KernelCache where
  slots : Nat := 64
  entries : Std.HashMap Nat KernelEntry := {}

structure KernelUse {b : Nat} (previous : List (Row b)) (equations : List (Row (b+b))) where
  kernel : Kernel previous equations
  cache : KernelCache
  hit : Bool
  keyCells : Nat
  comparisonCells : Nat
  evicted : Bool

def KernelUse.executedCharge {b : Nat} {previous : List (Row b)} {equations : List (Row (b+b))}
    (used : KernelUse previous equations) : Nat := if used.hit then 0 else used.kernel.charge

theorem KernelUse.executed_bound {b : Nat} {previous : List (Row b)} {equations : List (Row (b+b))}
    (used : KernelUse previous equations) (compact : previous.length ≤ b+1) :
    used.executedCharge ≤ appendBudget b equations.length := by
  unfold KernelUse.executedCharge
  split
  · exact Nat.zero_le _
  · exact used.kernel.bound compact

/-- Full structural comparisons, with casts only after width equality. The proof
transport erases; it cannot execute Gaussian elimination on a hit. -/
def KernelEntry.matchInput {b : Nat} (entry : KernelEntry) (previous : List (Row b))
    (equations : List (Row (b+b))) : Option (Kernel previous equations) :=
  if width : entry.width = b then by
    cases width
    exact if boundary : entry.previous = previous then
      if batch : entry.equations = equations then some (boundary ▸ batch ▸ entry.kernel)
      else none
    else none
  else none

def rowHash {n : Nat} (seed : UInt64) (row : Row n) : UInt64 :=
  mixHash (row.coeff.toArray.foldl (fun acc value => mixHash acc (hash value.val)) seed) (hash row.rhs.val)

def kernelHash {b : Nat} (previous : List (Row b)) (equations : List (Row (b+b))) : UInt64 :=
  equations.foldl rowHash (mixHash (previous.foldl rowHash (hash b)) (hash previous.length))

def kernelInputCells {b : Nat} (previous : List (Row b)) (equations : List (Row (b+b))) : Nat :=
  previous.length*(b+1)+equations.length*(2*b+1)

def KernelCache.obtain {b : Nat} (cache : KernelCache) (previous : List (Row b))
    (equations : List (Row (b+b))) : KernelUse previous equations :=
  if cache.slots = 0 then ⟨compileKernel previous equations,cache,false,0,0,false⟩
  else
    let cells := kernelInputCells previous equations
    let slot := (kernelHash previous equations).toNat % cache.slots
    let prior := cache.entries[slot]?
    match prior.bind (fun entry => entry.matchInput previous equations) with
    | some kernel => ⟨kernel,cache,true,cells,cells,false⟩
    | none =>
      let kernel := compileKernel previous equations
      let entry := KernelEntry.mk b previous equations kernel
      ⟨kernel,{cache with entries := cache.entries.insert slot entry},false,cells,
        if prior.isSome then cells else 0,prior.isSome⟩

/-- Input coefficient payload scanned for hashing and, at most, one full match.
Length checks, dimensions, allocation and map operations are separate costs. -/
theorem kernelInputCells_bound {b : Nat} (previous : List (Row b)) (equations : List (Row (b+b)))
    (compact : previous.length ≤ b+1) :
    kernelInputCells previous equations ≤ (b+1)^2+equations.length*(2*b+1) := by
  have h := Nat.mul_le_mul_right (b+1) compact
  simpa [kernelInputCells,pow_two] using Nat.add_le_add_right h (equations.length*(2*b+1))

end OracleMachines.Affine
