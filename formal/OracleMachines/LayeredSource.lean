import OracleMachines.LayeredProtocol

/-! Checked compilation for a supplied ordered partition of CNF variables.
Every clause must lie in one block or two adjacent blocks of width at most four.
The JSON parser/partition checker is executable; the local semantic model and
its relation conversion are proved below. This is not a general SAT compiler. -/
namespace OracleMachines.Layered
open Lean

structure LocalLiteral where
  right : Bool
  slot : Nat
  positive : Bool

def LocalLiteral.eval (lit : LocalLiteral) (x y : Nat) : Bool :=
  (if lit.right then y else x).testBit lit.slot == lit.positive

abbrev LocalCNF := Array (Array LocalLiteral)

def localEval (cnf : LocalCNF) (x y : Nat) : Bool :=
  cnf.toList.all fun clause => clause.toList.any fun lit => lit.eval x y

def compileLocal (width : Nat) (cnf : LocalCNF) : Relation (2^width) :=
  fun x y => localEval cnf x.val y.val

theorem compileLocal_exact (width : Nat) (cnf : LocalCNF) (x y : Fin (2^width)) :
    compileLocal width cnf x y = true ↔
      ∀ clause ∈ cnf.toList, ∃ lit ∈ clause.toList, lit.eval x.val y.val = true := by
  simp only [compileLocal,localEval,List.all_eq_true,List.any_eq_true]

structure CompiledSource where
  width : Nat
  buckets : Array LocalCNF

def compileSource (request : Json) : Except String CompiledSource := do
  let width ← request.getObjValAs? Nat "width"
  if width == 0 || width > 4 then throw "Source width must be 1 to 4"
  let layers ← request.getObjValAs? (Array (Array Nat)) "layers"
  if layers.size < 2 || layers.size > 65537 then throw "Supply 2 to 65537 variable blocks"
  let mut positions : Std.HashMap Nat (Nat × Nat) := {}
  for i in [:layers.size] do
    let block := layers[i]!
    if block.size > width then throw "Variable block exceeds supplied width"
    for j in [:block.size] do
      let varId := block[j]!
      if varId == 0 || positions.contains varId then throw "Variable blocks must be disjoint positive IDs"
      positions := positions.insert varId (i,j)
  let clauses ← request.getObjValAs? (Array (Array Int)) "clauses"
  if clauses.size > 200000 then throw "Source clause cap exceeded"
  let mut buckets : Array LocalCNF := Array.replicate (layers.size-1) #[]
  let mut literals := 0
  for clause in clauses do
    literals := literals+clause.size
    if literals > 2000000 then throw "Source literal cap exceeded"
    let mut lo := layers.size
    let mut hi := 0
    let mut located : Array (Nat × Nat × Bool) := #[]
    for lit in clause do
      if lit == 0 then throw "Zero is not a literal"
      let some (layer,slot) := positions[lit.natAbs]? | throw "Source variable missing from blocks"
      lo := min lo layer
      hi := max hi layer
      located := located.push (layer,slot,decide (lit > 0))
    if !clause.isEmpty && hi > lo+1 then throw "Clause crosses nonadjacent blocks"
    let edge := if clause.isEmpty then 0 else min lo (layers.size-2)
    let localClause := located.map fun (layer,slot,positive) =>
      LocalLiteral.mk (decide (layer = edge+1)) slot positive
    buckets := buckets.modify edge (·.push localClause)
  return ⟨width,buckets⟩

def compileRequest (request : Json) : Except String Json := do
  let source ← compileSource request
  let masks := source.buckets.map fun bucket => relationMask (compileLocal source.width bucket)
  return Json.mkObj [("masks",toJson masks),("edges",toJson masks.size),
    ("relation_cells",toJson (masks.size*(2^source.width)^2))]

def Tree.leaves {q : Nat} : {h : Nat} → Tree q h → List (Relation q)
  | _, .leaf r => [r]
  | _, .branch _ l r => l.leaves ++ r.leaves

def sequence {q : Nat} (edges : List (Relation q)) : Relation q :=
  edges.foldr compose identity

theorem sequence_append {q : Nat} (a b : List (Relation q)) :
    sequence (a++b) = compose (sequence a) (sequence b) := by
  induction a with
  | nil => simp [sequence,identity_compose]
  | cons r a ih => simp only [sequence,List.cons_append,List.foldr_cons] at *; rw [ih,compose_assoc]

theorem leaves_summary {q h : Nat} (t : Tree q h) (valid : t.Valid) :
    sequence t.leaves = t.summary := by
  induction t with
  | leaf r => simp [Tree.leaves,Tree.summary,sequence,compose_identity]
  | branch r l t il ir =>
    rcases valid with ⟨hl,hr,eq⟩
    change sequence (l.leaves++t.leaves) = r
    rw [sequence_append,il hl,ir hr,← eq]

theorem sequence_padding {q : Nat} (n : Nat) :
    sequence (List.replicate n (identity : Relation q)) = identity := by
  induction n with
  | zero => rfl
  | succ n ih => simp only [List.replicate_succ,sequence,List.foldr_cons] at *; rw [ih,identity_compose]

/-- Connect source edges, exact identity padding, and the checked decision
summary. The executable source checker establishes these equalities rowwise. -/
theorem source_binding_exact {q h : Nat} (t : Tree q h) (valid : t.Valid)
    (edges : List (Relation q)) (padding : Nat)
    (binding : t.leaves = edges ++ List.replicate padding identity) :
    t.summary = sequence edges := by
  rw [← leaves_summary t valid,binding,sequence_append,sequence_padding,compose_identity]

/-- Recompute compilation and bind every source edge to the checked root;
identity padding and the logical length are checked before exposing a verdict.
This intentionally charges a linear source-binding pass. -/
def sourceQuery (store : Store) (request : Json) : Except String Json := do
  let source ← compileSource request
  let root ← request.getObjValAs? String "root"
  let some (_, checked) := store[root]? | throw "Unknown source root"
  if w : source.width = checked.width then
    let expected : List (Relation (2^checked.width)) := source.buckets.toList.map fun bucket =>
      w ▸ compileLocal source.width bucket
    let actual := checked.tree.leaves
    if expected.length > actual.length then throw "Source exceeds checked root"
    for (a,b) in actual.take expected.length |>.zip expected do
      if !relationEqual a b then throw "Source relation differs from checked root"
    for a in actual.drop expected.length do
      if !relationEqual a identity then throw "Source padding is not identity"
    let want ← request.getObjValAs? Bool "witness"
    query store (Json.mkObj [("root",toJson root),("size",toJson expected.length),
      ("left",toJson (2^(2^checked.width)-1)),("right",toJson (2^(2^checked.width)-1)),
      ("witness",toJson want)])
  else throw "Source/root width mismatch"
end OracleMachines.Layered
