import OracleMachines.SourceStore

/-! A native join records the child names it decoded and the exact models found
in its registration snapshot. Preservation under later updates is conditional:
fresh insertions preserve links, and erasure must avoid both named children.
The runtime reference-count policy still needs to discharge that condition. -/
namespace OracleMachines.SourceLinks
open Lean OracleMachines.Layered OracleMachines.SourceNodes OracleMachines.SourceStore

def JoinLinks {layers : Array (Array Nat)} {width : Nat}
    (models : Std.HashMap String (CheckedNode layers width)) (body : Json)
    (node : CheckedNode layers width) : Prop :=
  ∃ (left right : String) (a b : CheckedNode layers width)
    (height : b.height = a.height) (consecutive : b.start = a.start+2^a.height),
    body.getObjValAs? String "left" = .ok left ∧
    body.getObjValAs? String "right" = .ok right ∧
    models[left]? = some a ∧ models[right]? = some b ∧
    node = checkedJoin a b height consecutive

/-- The proof concerns these actual getters and map lookups, not supplied
abstract child meanings. Failed lookup or shape checks return no node. -/
def readJoin {layers : Array (Array Nat)} {width : Nat}
    (models : Std.HashMap String (CheckedNode layers width)) (body : Json) :
    Except String {node : CheckedNode layers width // JoinLinks models body node} := do
  let left ← readParsed String body "left"
  let right ← readParsed String body "right"
  match leftFound : models[left.value]? with
  | none => throw "Missing left source invariant"
  | some a =>
    match rightFound : models[right.value]? with
    | none => throw "Missing right source invariant"
    | some b =>
      if height : b.height = a.height then
        if consecutive : b.start = a.start+2^a.height then
          return ⟨checkedJoin a b height consecutive,
            ⟨left.value,right.value,a,b,height,consecutive,
              left.exact,right.exact,leftFound,rightFound,rfl⟩⟩
        else throw "Source children do not cover consecutive edges"
      else throw "Unbalanced source children"

theorem JoinLinks.rootClauses_none {layers : Array (Array Nat)} {width : Nat}
    {models : Std.HashMap String (CheckedNode layers width)} {body : Json} {node : CheckedNode layers width}
    (links : JoinLinks models body node) : node.source.rootClauses = none := by
  obtain ⟨left,right,a,b,height,consecutive,hl,hr,ha,hb,rfl⟩ := links
  rfl

/-- Each source occurrence is attributed to the children actually retrieved by
name. Relation equivalence alone is not used to identify original sources. -/
theorem JoinLinks.original_clauses {layers : Array (Array Nat)} {width : Nat}
    {models : Std.HashMap String (CheckedNode layers width)} {body : Json} {node : CheckedNode layers width}
    (links : JoinLinks models body node) :
    ∃ left right a b,
      body.getObjValAs? String "left" = .ok left ∧
      body.getObjValAs? String "right" = .ok right ∧
      models[left]? = some a ∧ models[right]? = some b ∧
      node.source.clauses = a.source.clauses ++ b.source.clauses := by
  obtain ⟨left,right,a,b,height,consecutive,hl,hr,ha,hb,rfl⟩ := links
  exact ⟨left,right,a,b,hl,hr,ha,hb,checkedJoin_clauses a b height consecutive⟩

theorem JoinLinks.distinct_children {layers : Array (Array Nat)} {width : Nat}
    {models : Std.HashMap String (CheckedNode layers width)} {body : Json} {node : CheckedNode layers width}
    (links : JoinLinks models body node) :
    ∃ left right, body.getObjValAs? String "left" = .ok left ∧
      body.getObjValAs? String "right" = .ok right ∧ left ≠ right := by
  obtain ⟨left,right,a,b,height,consecutive,hl,hr,ha,hb,same⟩ := links
  refine ⟨left,right,hl,hr,?_⟩
  intro equal
  subst right
  have ab : a = b := Option.some.inj (ha.symm.trans hb)
  subst b
  have positive : 0 < 2^a.height := Nat.two_pow_pos a.height
  omega

/-- Both named sources must hold under one valuation, not under separately
chosen satisfying assignments. -/
theorem JoinLinks.decision_exact {layers : Array (Array Nat)} {width : Nat}
    {models : Std.HashMap String (CheckedNode layers width)} {body : Json} {node : CheckedNode layers width}
    (links : JoinLinks models body node) (layout : CheckedLayout layers width) :
    ∃ left right a b,
      body.getObjValAs? String "left" = .ok left ∧
      body.getObjValAs? String "right" = .ok right ∧
      models[left]? = some a ∧ models[right]? = some b ∧
      (node.decide = true ↔ ∃ valuation, a.source.eval valuation = true ∧ b.source.eval valuation = true) := by
  obtain ⟨left,right,a,b,hl,hr,ha,hb,clauses⟩ := links.original_clauses
  refine ⟨left,right,a,b,hl,hr,ha,hb,?_⟩
  have exact := node.decide_exact layout
  rw [clauses] at exact
  simpa [OriginalTree.eval_flat,sourceCNFEval] using exact

theorem JoinLinks.preserve {layers : Array (Array Nat)} {width : Nat}
    {models next : Std.HashMap String (CheckedNode layers width)} {body : Json} {node : CheckedNode layers width}
    (links : JoinLinks models body node)
    (retained : ∀ (name : String) (value : CheckedNode layers width),
      models[name]? = some value → next[name]? = some value) :
    JoinLinks next body node := by
  obtain ⟨left,right,a,b,height,consecutive,hl,hr,ha,hb,same⟩ := links
  exact ⟨left,right,a,b,height,consecutive,hl,hr,retained left a ha,retained right b hb,same⟩

theorem JoinLinks.insert_fresh {layers : Array (Array Nat)} {width : Nat}
    {models : Std.HashMap String (CheckedNode layers width)} {body : Json} {node : CheckedNode layers width}
    (links : JoinLinks models body node) (id : String) (value : CheckedNode layers width)
    (fresh : models[id]? = none) : JoinLinks (models.insert id value) body node := by
  apply links.preserve
  intro name old found
  have different : id ≠ name := by intro same; subst name; simp [fresh] at found
  simpa [Std.HashMap.getElem?_insert,different] using found

/-- This premise is the lifetime obligation; an incoming count of zero is not
assumed to imply it until the separate count invariant is proved. -/
theorem JoinLinks.erase_unreferenced {layers : Array (Array Nat)} {width : Nat}
    {models : Std.HashMap String (CheckedNode layers width)} {body : Json} {node : CheckedNode layers width}
    (links : JoinLinks models body node) (id : String)
    (notLeft : body.getObjValAs? String "left" ≠ .ok id)
    (notRight : body.getObjValAs? String "right" ≠ .ok id) :
    JoinLinks (models.erase id) body node := by
  obtain ⟨left,right,a,b,height,consecutive,hl,hr,ha,hb,same⟩ := links
  have dl : id ≠ left := by intro eq; subst left; exact notLeft hl
  have dr : id ≠ right := by intro eq; subst right; exact notRight hr
  refine ⟨left,right,a,b,height,consecutive,hl,hr,?_,?_,same⟩
  · simpa [Std.HashMap.getElem?_erase,dl] using ha
  · simpa [Std.HashMap.getElem?_erase,dr] using hb

end OracleMachines.SourceLinks
