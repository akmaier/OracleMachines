import OracleMachines.LayeredSource
import OracleMachines.LayeredCosts

/-! Immutable source/update specification and executable reference counts.
The clauses themselves survive in the source tree, even when their projected
relation is unchanged. JSON, hash-map and database refinement remain separate. -/
namespace OracleMachines.SourceInvariant
open OracleMachines.Layered

abbrev Payload := Option LocalCNF

def meaning (width : Nat) : Payload → Relation (2^width)
  | none => identity
  | some clauses => compileLocal width clauses

inductive SourceTree : Nat → Type where
  | leaf : Payload → SourceTree 0
  | branch {h : Nat} : SourceTree h → SourceTree h → SourceTree (h+1)

def SourceTree.compile (width : Nat) : {h : Nat} → SourceTree h → Tree (2^width) h
  | _, .leaf p => .leaf (meaning width p)
  | _, .branch l r => join (l.compile width) (r.compile width)

def SourceTree.Holds (width : Nat) : {h : Nat} → SourceTree h → Fin (2^width) → Fin (2^width) → Prop
  | _, .leaf p, x, y => meaning width p x y = true
  | _, .branch l r, x, z => ∃ y, l.Holds width x y ∧ r.Holds width y z

theorem compile_valid (width : Nat) {h : Nat} (source : SourceTree h) :
    (source.compile width).Valid := by
  induction source with
  | leaf p => trivial
  | branch l r il ir => exact join_valid _ _ il ir

theorem compile_exact (width : Nat) {h : Nat} (source : SourceTree h) (x y : Fin (2^width)) :
    (source.compile width).summary x y = true ↔ source.Holds width x y := by
  induction source generalizing x y with
  | leaf p => rfl
  | branch l r il ir =>
    change freeze (compose (l.compile width).summary (r.compile width).summary) x y = true ↔ _
    rw [freeze_eq,compose_exact]
    exact exists_congr (fun z => and_congr (il _ _) (ir _ _))

def decision {q h : Nat} (tree : Tree q h) : Bool :=
  (List.finRange q).any fun x => (List.finRange q).any fun y => tree.summary x y

theorem decision_exact (width : Nat) {h : Nat} (source : SourceTree h) :
    decision (source.compile width) = true ↔ ∃ x y, source.Holds width x y := by
  simp only [decision,List.any_eq_true,List.mem_finRange,true_and]
  exact exists_congr (fun x => exists_congr (fun y => compile_exact width source x y))

def SourceTree.at : {h : Nat} → SourceTree h → (Fin h → Bool) → Payload
  | 0, .leaf p, _ => p
  | _+1, .branch l r, path => if path 0 then r.at (fun i => path i.succ) else l.at (fun i => path i.succ)

/-- Return the new source and count allocated source nodes, not the whole tree. -/
def editRun : {h : Nat} → SourceTree h → (Fin h → Bool) → Payload → SourceTree h × Nat
  | 0, .leaf _, _, value => (.leaf value,1)
  | _+1, .branch l r, path, value =>
    if path 0 then
      let child := editRun r (fun i => path i.succ) value
      (.branch l child.1,child.2+1)
    else
      let child := editRun l (fun i => path i.succ) value
      (.branch child.1 r,child.2+1)

theorem edit_nodes {h : Nat} (source : SourceTree h) (path : Fin h → Bool) (value : Payload) :
    (editRun source path value).2 = h+1 := by
  induction source with
  | leaf p => rfl
  | branch l r il ir => simp only [editRun]; split <;> simp_all

theorem edit_at {h : Nat} (source : SourceTree h) (path : Fin h → Bool) (value : Payload) :
    (editRun source path value).1.at path = value := by
  induction source with
  | leaf p => rfl
  | branch l r il ir => simp only [editRun]; split <;> simp_all [SourceTree.at]

theorem edit_other {h : Nat} (source : SourceTree h) (path other : Fin h → Bool) (value : Payload)
    (different : path ≠ other) : (editRun source path value).1.at other = source.at other := by
  induction source with
  | leaf p => exact False.elim (different (funext (fun i => Fin.elim0 i)))
  | @branch h l r il ir =>
    have tails : path 0 = other 0 → (fun i : Fin h => path i.succ) ≠ (fun i : Fin h => other i.succ) := by
      intro same eq
      apply different
      funext i
      exact Fin.cases same (fun j => congrFun eq j) i
    cases hp : path 0 <;> cases ho : other 0 <;>
      simp [editRun,SourceTree.at,hp,ho,il,ir,tails]

theorem edit_compile (width : Nat) {h : Nat} (source : SourceTree h) (path : Fin h → Bool) (value : Payload) :
    (editRun source path value).1.compile width = replace (source.compile width) path (meaning width value) := by
  induction source with
  | leaf p => rfl
  | branch l r il ir =>
    cases hp : path 0 <;> simp [editRun,SourceTree.compile,join,replace,hp,il,ir]

def cnfRun (clauses : List (Array LocalLiteral)) (x y : Nat) : Bool × Nat :=
  match clauses with
  | [] => (true,1)
  | clause::rest =>
    let current := anyRun (fun lit => lit.eval x y) clause.toList
    if current.1 then
      let next := cnfRun rest x y
      (next.1,1+current.2+next.2)
    else (false,1+current.2)

def syntaxWeight (clauses : List (Array LocalLiteral)) : Nat :=
  clauses.length + (clauses.map Array.size).sum

theorem cnfRun_value (clauses : List (Array LocalLiteral)) (x y : Nat) :
    (cnfRun clauses x y).1 = clauses.all (fun c => c.toList.any (fun lit => lit.eval x y)) := by
  induction clauses with
  | nil => rfl
  | cons c cs ih => simp only [cnfRun]; split <;> simp_all [anyRun_value]

theorem cnfRun_tests (clauses : List (Array LocalLiteral)) (x y : Nat) :
    (cnfRun clauses x y).2 ≤ syntaxWeight clauses+1 := by
  induction clauses with
  | nil => simp [cnfRun,syntaxWeight]
  | cons c cs ih =>
    have bound := anyRun_tests (fun lit => lit.eval x y) c.toList
    simp only [Array.length_toList] at bound
    simp only [cnfRun]; split <;> simp only [syntaxWeight,List.length_cons,List.map_cons,List.sum_cons] at * <;> omega

@[noinline] def sourceTableRun (width : Nat) (clauses : LocalCNF) :
    Vector (Vector (Bool × Nat) (2^width)) (2^width) :=
  Vector.ofFn fun x => Vector.ofFn fun y => cnfRun clauses.toList x.val y.val

theorem sourceTable_value (width : Nat) (clauses : LocalCNF) :
    tableValue (sourceTableRun width clauses) = compileLocal width clauses := by
  funext x y
  simp [tableValue,sourceTableRun,cnfRun_value,compileLocal,localEval]

theorem sourceTable_tests (width : Nat) (clauses : LocalCNF) :
    tableTests (sourceTableRun width clauses) ≤ (2^width)^2*(syntaxWeight clauses.toList+1) := by
  have bound : ∀ x y : Fin (2^width), ((sourceTableRun width clauses)[x][y]).2 ≤ syntaxWeight clauses.toList+1 := by
    intro x y
    simpa [sourceTableRun] using cnfRun_tests clauses.toList x.val y.val
  calc
    tableTests (sourceTableRun width clauses) ≤ ∑ _x : Fin (2^width), ∑ _y : Fin (2^width), (syntaxWeight clauses.toList+1) :=
      Finset.sum_le_sum (fun x _ => Finset.sum_le_sum (fun y _ => bound x y))
    _ = (2^width)^2*(syntaxWeight clauses.toList+1) := by simp; ring

/-- Given a cached representation, update source and compiled relation together.
The first counter charges literal/clause tests, the second joins/node events,
the third source-node allocations. Runtime transport/storage are not unit tests. -/
def checkedEditRun (width : Nat) {h : Nat} (source : SourceTree h) (cached : Tree (2^width) h)
    (path : Fin h → Bool) (clauses : LocalCNF) : SourceTree h × Tree (2^width) h × Nat × Nat × Nat :=
  let table := sourceTableRun width clauses
  let next := replaceRun cached path (tableValue table)
  let provenance := editRun source path (some clauses)
  (provenance.1,next.1,tableTests table,next.2,provenance.2)

theorem checkedEditRun_correct (width : Nat) {h : Nat} (source : SourceTree h) (cached : Tree (2^width) h)
    (path : Fin h → Bool) (clauses : LocalCNF) (aligned : cached = source.compile width) :
    (checkedEditRun width source cached path clauses).2.1 =
      (checkedEditRun width source cached path clauses).1.compile width := by
  simp only [checkedEditRun,replaceRun_value,sourceTable_value,aligned]
  exact (edit_compile width source path (some clauses)).symm

theorem checkedEditRun_budget (width : Nat) {h : Nat} (source : SourceTree h) (cached : Tree (2^width) h)
    (path : Fin h → Bool) (clauses : LocalCNF) :
    let run := checkedEditRun width source cached path clauses
    run.2.2.1 + run.2.2.2.1 + run.2.2.2.2 ≤
      (2^width)^2*(syntaxWeight clauses.toList+1) + h*(2^width)^3 + 2*(h+1) := by
  have table := sourceTable_tests width clauses
  have update := replaceRun_tests cached path (tableValue (sourceTableRun width clauses))
  have sourceCount := edit_nodes source path (some clauses)
  simp only [checkedEditRun,replacementBudget] at *
  omega

structure CheckedSource where
  width : Nat
  height : Nat
  source : SourceTree height
  tree : Tree (2^width) height
  aligned : tree = source.compile width

def checkedLeaf (width : Nat) (payload : Payload) (r : Relation (2^width))
    (same : r = meaning width payload) : CheckedSource :=
  ⟨width,0,.leaf payload,.leaf r,congrArg Tree.leaf same⟩

theorem cast_aligned {w v h k : Nat} (hw : w = v) (hh : h = k)
    (s : SourceTree k) (t : Tree (2^v) k) (same : t = s.compile v) :
    (hh.symm ▸ hw.symm ▸ t : Tree (2^w) h) = (hh.symm ▸ s : SourceTree h).compile w := by
  cases hw; cases hh; exact same

def checkedJoin (a b : CheckedSource) (w : a.width = b.width) (h : a.height = b.height) : CheckedSource :=
  let sourceB : SourceTree a.height := h.symm ▸ b.source
  let treeB : Tree (2^a.width) a.height := h.symm ▸ w.symm ▸ b.tree
  have alignedB : treeB = sourceB.compile a.width := cast_aligned w h b.source b.tree b.aligned
  ⟨a.width,a.height+1,.branch a.source sourceB,join a.tree treeB,by
    change join a.tree treeB = join (a.source.compile a.width) (sourceB.compile a.width)
    rw [a.aligned,alignedB]⟩

def CheckedSource.checkedTree (source : CheckedSource) : CheckedTree :=
  ⟨source.width,source.height,source.tree,by rw [source.aligned]; exact compile_valid _ _⟩

def CheckedSource.decide (source : CheckedSource) : Bool := decision source.tree

theorem checked_decide_exact (source : CheckedSource) :
    source.decide = true ↔ ∃ x y, source.source.Holds source.width x y := by
  simp only [CheckedSource.decide,source.aligned]
  exact decision_exact _ _

theorem checked_unsat_exact (source : CheckedSource) :
    source.decide = false ↔ ¬ ∃ x y, source.source.Holds source.width x y := by
  rw [← checked_decide_exact]
  cases source.decide <;> decide

end OracleMachines.SourceInvariant
