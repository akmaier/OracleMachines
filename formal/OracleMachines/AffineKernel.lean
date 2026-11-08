import OracleMachines.AffineNormalize
import Std.Data.HashMap.Lemmas

/-! Exact algebraic transitions shared by distinct original histories. Cache
entries retain coefficient inputs and results, never source-history ancestors.
Hashing selects one bounded slot; dependent equality checks justify every hit. -/
namespace OracleMachines.Affine

structure Kernel {b : Nat} (previous : List (Row b)) (equations : List (Row (b+b))) where
  summary : List (Row b)
  exact : ∀ v, Holds summary v ↔ ∃ u, Holds previous u ∧ Holds equations (Fin.append u v)
  compact : summary.length ≤ b+1
  answer : Bool
  answer_exact : answer = decide summary
  charge : Nat
  charge_bound : previous.length ≤ b+1 → charge ≤ appendBudget b equations.length

def compileKernel {b : Nat} (previous : List (Row b)) (equations : List (Row (b+b))) : Kernel previous equations :=
  let result := extendRun previous equations
  let decision := decideRun result.1
  ⟨result.1,by intro v; rw [extendRun_value]; exact extend_exact previous equations v,
    by rw [extendRun_value]; exact extend_size _ _,
    decision.1,decideRun_value _,result.2+decision.2,extendRun_bound previous equations⟩

theorem compileKernel_charge {b : Nat} (previous : List (Row b)) (equations : List (Row (b+b))) :
    (compileKernel previous equations).charge =
      (extendRun previous equations).2 + (decideRun (extendRun previous equations).1).2 := rfl

theorem compileKernel_summary {b : Nat} (previous : List (Row b)) (equations : List (Row (b+b))) :
    (compileKernel previous equations).summary = (extendRun previous equations).1 := rfl

def Kernel.attach {b : Nat} {equations : List (Row (b+b))} (previous : Resident b)
    (kernel : Kernel previous.summary equations) : Resident b :=
  ⟨previous.past.map (fun old => .append old equations),kernel.summary,by
    intro v
    rw [kernel.exact,Erased.map_out]
    exact exists_congr (fun u => and_congr_left (fun _ => previous.exact u)),kernel.compact⟩

theorem Kernel.attach_history {b : Nat} {equations : List (Row (b+b))} (previous : Resident b)
    (kernel : Kernel previous.summary equations) :
    (kernel.attach previous).history = .append previous.history equations := by
  simp [Kernel.attach,Resident.history]

theorem Kernel.bound {b : Nat} {previous : List (Row b)} {equations : List (Row (b+b))}
    (kernel : Kernel previous equations) (compact : previous.length ≤ b+1) :
    kernel.charge ≤ appendBudget b equations.length := kernel.charge_bound compact

/-- Attach normalized computation to the exact original batch, without storing
or computing a second elimination result for the uncompressed batch. -/
def Kernel.restoreOriginal {b : Nat} {previous : List (Row b)} {original : List (Row (b+b))}
    (prepared : PreparedRows original) (kernel : Kernel previous prepared.rows) : Kernel previous original :=
  ⟨kernel.summary,by
    intro v
    rw [kernel.exact]
    exact exists_congr (fun u => and_congr_right (fun _ => prepared.exact (Fin.append u v))),
    kernel.compact,kernel.answer,kernel.answer_exact,kernel.charge,
    fun compact => le_trans (kernel.bound compact) (appendBudget_mono b _ _ prepared.bound)⟩

theorem Kernel.restoreOriginal_charge {b : Nat} {previous : List (Row b)} {original : List (Row (b+b))}
    (prepared : PreparedRows original) (kernel : Kernel previous prepared.rows) :
    (Kernel.restoreOriginal prepared kernel).charge = kernel.charge := rfl

structure KernelEntry where
  width : Nat
  previous : List (Row width)
  equations : List (Row (width+width))
  kernel : Kernel previous equations

structure KernelCache where
  slots : Nat := 64
  entries : Std.HashMap Nat KernelEntry := {}
  deduplicate : Bool := true
  prepared : Std.HashMap Nat PreparedEntry := {}

structure KernelUse {b : Nat} (previous : List (Row b)) (equations : List (Row (b+b))) where
  kernel : Kernel previous equations
  cache : KernelCache
  hit : Bool
  keyCells : Nat
  comparisonCells : Nat
  evicted : Bool
  inputRows : Nat := 0
  normalizedRows : Nat := 0
  preparationHit : Bool := false
  preparationCells : Nat := 0
  preparationCompareCells : Nat := 0
  normalizationCells : Nat := 0

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

def kernelHash {b : Nat} (previous : List (Row b)) (equations : List (Row (b+b))) : UInt64 :=
  equations.foldl rowHash (mixHash (previous.foldl rowHash (hash b)) (hash previous.length))

def kernelInputCells {b : Nat} (previous : List (Row b)) (equations : List (Row (b+b))) : Nat :=
  previous.length*(b+1)+equations.length*(2*b+1)

def KernelCache.obtainRaw {b : Nat} (cache : KernelCache) (previous : List (Row b))
    (equations : List (Row (b+b))) : KernelUse previous equations :=
  if cache.slots = 0 then ⟨compileKernel previous equations,cache,false,0,0,false,0,0,false,0,0,0⟩
  else
    let cells := kernelInputCells previous equations
    let slot := (kernelHash previous equations).toNat % cache.slots
    let prior := cache.entries[slot]?
    match prior.bind (fun entry => entry.matchInput previous equations) with
    | some kernel => ⟨kernel,cache,true,cells,cells,false,0,0,false,0,0,0⟩
    | none =>
      let kernel := compileKernel previous equations
      let entry := KernelEntry.mk b previous equations kernel
      ⟨kernel,{cache with entries := cache.entries.insert slot entry},false,cells,
        if prior.isSome then cells else 0,prior.isSome,0,0,false,0,0,0⟩

def KernelCache.obtain {b : Nat} (cache : KernelCache) (previous : List (Row b))
    (equations : List (Row (b+b))) : KernelUse previous equations :=
  if !cache.deduplicate then
    let used := cache.obtainRaw previous equations
    {used with inputRows := equations.length,normalizedRows := equations.length}
  else
    let cells := equations.length*(2*b+1)
    let slot := if cache.slots = 0 then 0 else (equations.foldl rowHash (hash (b+b))).toNat % cache.slots
    let prior := if cache.slots = 0 then none else cache.prepared[slot]?
    let (prepared,hit) := match prior.bind (fun entry => entry.matchInput equations) with
      | some result => (result,true)
      | none => (prepareRows equations,false)
    let next := if hit || cache.slots = 0 then cache else
      {cache with prepared := cache.prepared.insert slot ⟨b+b,equations,prepared⟩}
    let used := next.obtainRaw previous prepared.rows
    ⟨Kernel.restoreOriginal prepared used.kernel,used.cache,used.hit,used.keyCells,used.comparisonCells,used.evicted,
      equations.length,prepared.rows.length,hit,if cache.slots = 0 then 0 else cells,
      if prior.isSome then cells else 0,if hit then 0 else cells⟩

/-- Input coefficient payload scanned for hashing and, at most, one full match.
Length checks, dimensions, allocation and map operations are separate costs. -/
theorem kernelInputCells_bound {b : Nat} (previous : List (Row b)) (equations : List (Row (b+b)))
    (compact : previous.length ≤ b+1) :
    kernelInputCells previous equations ≤ (b+1)^2+equations.length*(2*b+1) := by
  have h := Nat.mul_le_mul_right (b+1) compact
  simpa [kernelInputCells,pow_two] using Nat.add_le_add_right h (equations.length*(2*b+1))

end OracleMachines.Affine
