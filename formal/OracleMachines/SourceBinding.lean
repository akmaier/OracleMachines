import OracleMachines.SourceInvariant

/-! Checked binding of a complete compiled source to an actual native tree.
The executable comparison supplies the ordered-leaf/padding premise instead of
assuming it. Mutable identity, patch, JSON and persistence refinement remain
separate obligations. Counts cover relation comparisons, not machine costs. -/
namespace OracleMachines.Layered
open Lean

/-- Difference-list traversal: one visit per node, one cons per leaf. -/
def Tree.leavesInto {q : Nat} : {h : Nat} → Tree q h → List (Relation q) → List (Relation q)
  | _, .leaf r, tail => r::tail
  | _, .branch _ l r, tail => l.leavesInto (r.leavesInto tail)

theorem Tree.leavesInto_exact {q h : Nat} (tree : Tree q h) (tail : List (Relation q)) :
    tree.leavesInto tail = tree.leaves ++ tail := by
  induction tree generalizing tail with
  | leaf r => rfl
  | branch r l t il ir => simp [Tree.leavesInto,Tree.leaves,il,ir,List.append_assoc]

/-- Accumulated count makes the long successful scan tail recursive. -/
def bindingScan {q : Nat} : List (Relation q) → List (Relation q) → Nat → Bool × Nat
  | [], [], used => (true,used)
  | a::as, b::bs, used =>
    if relationEqual a b then bindingScan as bs (used+1) else (false,used+1)
  | _, _, used => (false,used)

theorem bindingScan_exact {q : Nat} (actual expected : List (Relation q)) (used : Nat) :
    (bindingScan actual expected used).1 = true ↔ actual = expected := by
  induction actual generalizing expected used with
  | nil => cases expected <;> simp [bindingScan]
  | cons a rest ih =>
    cases expected with
    | nil => simp [bindingScan]
    | cons b tail =>
      simp only [bindingScan]
      split
      · have same : a = b := (relationEqual_exact a b).mp (by assumption)
        simp [same,ih]
      · have different : a ≠ b := by
          intro same
          subst b
          have equal := (relationEqual_exact a a).mpr rfl
          contradiction
        simp [different]

theorem bindingScan_bound {q : Nat} (actual expected : List (Relation q)) (used : Nat) :
    (bindingScan actual expected used).2 ≤ used+actual.length := by
  induction actual generalizing expected used with
  | nil => cases expected <;> simp [bindingScan]
  | cons a rest ih =>
    cases expected with
    | nil => simp [bindingScan]
    | cons b tail =>
      simp only [bindingScan]
      split
      · have bound := ih tail (used+1)
        simpa [Nat.add_assoc,Nat.add_comm,Nat.add_left_comm] using bound
      · simp

theorem bindingScan_self {q : Nat} (actual : List (Relation q)) (used : Nat) :
    (bindingScan actual actual used).2 = used+actual.length := by
  induction actual generalizing used with
  | nil => simp [bindingScan]
  | cons a rest ih =>
    have same := (relationEqual_exact a a).mpr rfl
    simp [bindingScan,same,ih,Nat.add_assoc,Nat.add_comm]

theorem bindingScan_complete {q : Nat} (actual expected : List (Relation q)) (used : Nat)
    (accepted : (bindingScan actual expected used).1 = true) :
    (bindingScan actual expected used).2 = used+actual.length := by
  have same := (bindingScan_exact actual expected used).mp accepted
  subst expected
  exact bindingScan_self actual used

structure BoundCompilation (source : CompiledSource) where
  height : Nat
  tree : Tree (2^source.width) height
  valid : tree.Valid
  padding : Nat
  binding : tree.leaves = source.buckets.toList.map (compileLocal source.width) ++
    List.replicate padding identity
  leaves : Nat
  leaves_exact : leaves = tree.leaves.length
  comparisons : Nat
  comparisons_exact : comparisons = leaves

def bindCompilation (source : CompiledSource) (checked : CheckedTree) :
    Except String (BoundCompilation source) := do
  if width : checked.width = source.width then
    let tree : Tree (2^source.width) checked.height := width ▸ checked.tree
    have valid : tree.Valid := cast_width_valid width checked.tree checked.valid
    let actual := tree.leavesInto []
    let expected := source.buckets.toList.map (compileLocal source.width)
    if actual.length < expected.length then throw "Source exceeds checked root"
    let padding := actual.length-expected.length
    let run := bindingScan actual (expected ++ List.replicate padding identity) 0
    if accepted : run.1 = true then
      have binding : tree.leaves = expected ++ List.replicate padding identity := by
        have same := (bindingScan_exact actual _ 0).mp accepted
        simpa [actual,Tree.leavesInto_exact] using same
      return ⟨checked.height,tree,valid,padding,binding,actual.length,
        by simp [actual,Tree.leavesInto_exact],run.2,
        by simpa [run] using bindingScan_complete actual (expected ++ List.replicate padding identity) 0 accepted⟩
    else throw "Source relation or identity padding differs from checked root"
  else throw "Source/root width mismatch"

def BoundCompilation.decide {source : CompiledSource} (bound : BoundCompilation source) : Bool :=
  OracleMachines.SourceInvariant.decision bound.tree

theorem BoundCompilation.decide_exact {source : CompiledSource} (bound : BoundCompilation source) :
    bound.decide = true ↔ ∃ valuation, sourceCNFEval source.clauses valuation = true := by
  simp only [BoundCompilation.decide,OracleMachines.SourceInvariant.decision,
    List.any_eq_true,List.mem_finRange,true_and]
  exact (source.bound_tree_exact bound.tree bound.valid bound.padding bound.binding).symm

theorem BoundCompilation.unsat_exact {source : CompiledSource} (bound : BoundCompilation source) :
    bound.decide = false ↔ ¬ ∃ valuation, sourceCNFEval source.clauses valuation = true := by
  rw [← bound.decide_exact]
  cases bound.decide <;> decide

/-- Diagnostic reference bounds. The comparison count is proved above;
source test weights use the existing clause/literal ledger. Neither includes
allocation, source indexing, bit arithmetic or native instructions. -/
def BoundCompilation.metrics {source : CompiledSource} (bound : BoundCompilation source) : Json :=
  Json.mkObj [("binding_leaves",toJson bound.leaves),
    ("binding_relation_comparisons",toJson bound.comparisons),
    ("binding_cell_bound",toJson (bound.comparisons*(2^source.width)^2)),
    ("binding_source_test_bound",toJson ((bound.leaves + source.clauses.size +
      (source.clauses.toList.map Array.size).sum)*(2^source.width)^2))]

/-- Compile and certify the complete original source against the actual cached
tree. Witness construction is additionally checked by the existing protocol. -/
def sourceQuery (store : Store) (request : Json) : Except String Json := do
  let source ← compileSource request
  let root ← request.getObjValAs? String "root"
  let some (_, checked) := store.nodes[root]? | throw "Unknown source root"
  let bound ← bindCompilation source checked
  let answer := bound.decide
  let want ← request.getObjValAs? Bool "witness"
  let verdict ← query store (Json.mkObj [("root",toJson root),("size",toJson source.buckets.size),
    ("left",toJson (2^(2^source.width)-1)),("right",toJson (2^(2^source.width)-1)),
    ("witness",toJson want)])
  if (← verdict.getObjValAs? Bool "answer") != answer then throw "Source decision disagrees with binding proof"
  return (verdict.setObjVal! "answer" (toJson answer)).mergeObj bound.metrics

end OracleMachines.Layered
