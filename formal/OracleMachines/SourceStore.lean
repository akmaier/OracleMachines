import OracleMachines.SourceNodes
import Std.Data.HashMap.Lemmas

/-! Named source metadata and pointwise agreement of the two native maps.
The runtime preserves this invariant by paired insertions and erasures. It does
not scan the store to reconstruct the proof. Named child dependencies, reference
counts, requested patches and persistence remain separate obligations. -/
namespace OracleMachines.SourceStore
open Lean OracleMachines.Layered OracleMachines.SourceNodes

structure Parsed (α : Type) [FromJson α] (body : Json) (field : String) where
  value : α
  exact : body.getObjValAs? α field = .ok value

def readParsed (α : Type) [FromJson α] (body : Json) (field : String) : Except String (Parsed α body field) :=
  match result : body.getObjValAs? α field with
  | .error error => .error error
  | .ok value => .ok ⟨value,result⟩

def expectEqual {α : Type} [DecidableEq α] (actual expected : α) (error : String) :
    Except String (PLift (actual = expected)) :=
  if same : actual = expected then .ok ⟨same⟩ else .error error

structure Header (layoutId id : String) (width : Nat) (body : Json) where
  start : Nat
  height : Nat
  name : body.getObjValAs? String "id" = .ok id
  layout : body.getObjValAs? String "layout" = .ok layoutId
  dimension : body.getObjValAs? Nat "width" = .ok width
  location : body.getObjValAs? Nat "start" = .ok start
  level : body.getObjValAs? Nat "height" = .ok height

def readHeader (layoutId : String) (width : Nat) (body : Json) (name : Parsed String body "id") :
    Except String (Header layoutId name.value width body) := do
  let layout ← readParsed String body "layout"
  let layoutEq ← expectEqual layout.value layoutId "Source layout mismatch"
  let dimension ← readParsed Nat body "width"
  let widthEq ← expectEqual dimension.value width "Source width mismatch"
  let location ← readParsed Nat body "start"
  let level ← readParsed Nat body "height"
  return ⟨location.value,level.value,name.exact,
    by simpa only [layoutEq.down] using layout.exact,
    by simpa only [widthEq.down] using dimension.exact,location.exact,level.exact⟩

structure BodyMatches {layers : Array (Array Nat)} {width : Nat}
    (layoutId id : String) (body : Json) (model : CheckedNode layers width) : Prop where
  name : body.getObjValAs? String "id" = .ok id
  layout : body.getObjValAs? String "layout" = .ok layoutId
  dimension : body.getObjValAs? Nat "width" = .ok width
  location : body.getObjValAs? Nat "start" = .ok model.start
  level : body.getObjValAs? Nat "height" = .ok model.height
  payload : ∀ clauses, model.source.rootClauses = some clauses →
    body.getObjValAs? (Array (Array Int)) "clauses" = .ok clauses

def bindHeader {layers : Array (Array Nat)} {width : Nat} {layoutId id : String} {body : Json}
    (header : Header layoutId id width body) (model : CheckedNode layers width)
    (location : model.start = header.start) (level : model.height = header.height)
    (payload : ∀ clauses, model.source.rootClauses = some clauses →
      body.getObjValAs? (Array (Array Int)) "clauses" = .ok clauses) :
    {node : CheckedNode layers width // BodyMatches layoutId id body node} :=
  ⟨model,⟨header.name,header.layout,header.dimension,
    by rw [location]; exact header.location,by rw [level]; exact header.level,payload⟩⟩

def Corresponds {layers : Array (Array Nat)} {width : Nat} (layoutId : String)
    (nodes : Std.HashMap String (Json × CheckedTree)) (models : Std.HashMap String (CheckedNode layers width)) : Prop :=
  ∀ id, match nodes[id]?, models[id]? with
  | none, none => True
  | some (body,tree), some model => tree = model.checkedTree ∧ BodyMatches layoutId id body model
  | _, _ => False

theorem corresponds_empty {layers : Array (Array Nat)} {width : Nat} (layoutId : String) :
    Corresponds (layers := layers) (width := width) layoutId {} {} := by
  intro id
  simp

theorem corresponds_insert {layers : Array (Array Nat)} {width : Nat} {layoutId : String}
    {nodes : Std.HashMap String (Json × CheckedTree)} {models : Std.HashMap String (CheckedNode layers width)}
    (prior : Corresponds layoutId nodes models) (id : String) (body : Json) (model : CheckedNode layers width)
    (binding : BodyMatches layoutId id body model) :
    Corresponds layoutId (nodes.insert id (body,model.checkedTree)) (models.insert id model) := by
  intro key
  by_cases same : id = key
  · subst key
    simp only [Std.HashMap.getElem?_insert_self]
    exact ⟨True.intro,binding⟩
  · simpa [Std.HashMap.getElem?_insert,same] using prior key

theorem corresponds_erase {layers : Array (Array Nat)} {width : Nat} {layoutId : String}
    {nodes : Std.HashMap String (Json × CheckedTree)} {models : Std.HashMap String (CheckedNode layers width)}
    (prior : Corresponds layoutId nodes models) (id : String) :
    Corresponds layoutId (nodes.erase id) (models.erase id) := by
  intro key
  by_cases same : id = key
  · subst key; simp
  · simpa [Std.HashMap.getElem?_erase,same] using prior key

structure Store (layoutId : String) (layers : Array (Array Nat)) (width : Nat) where
  relations : OracleMachines.Layered.Store
  models : Std.HashMap String (CheckedNode layers width)
  agrees : Corresponds layoutId relations.nodes models

def Store.empty (layoutId : String) (layers : Array (Array Nat)) (width : Nat) : Store layoutId layers width :=
  ⟨{},{},corresponds_empty layoutId⟩

def Store.insert {layoutId : String} {layers : Array (Array Nat)} {width : Nat}
    (store : Store layoutId layers width) (id : String) (body : Json) (model : CheckedNode layers width)
    (binding : BodyMatches layoutId id body model) : Except String (Store layoutId layers width) := do
  let incoming ← addReferences store.relations.incoming body
  return ⟨⟨store.relations.nodes.insert id (body,model.checkedTree),incoming⟩,store.models.insert id model,
    corresponds_insert store.agrees id body model binding⟩

/-- Reference counts remain independently checked; the pointwise map invariant
does not assume that their arithmetic or dependency-closure policy is proved. -/
def Store.erase {layoutId : String} {layers : Array (Array Nat)} {width : Nat}
    (store : Store layoutId layers width) (id : String) : Except String (Store layoutId layers width) := do
  let some node := store.relations.nodes[id]? | throw "Unknown evicted node"
  if store.relations.incoming[id]?.getD 0 != 0 then throw "Cannot evict a referenced node"
  let incoming ← removeReferences store.relations.incoming node.1
  return ⟨⟨store.relations.nodes.erase id,incoming.erase id⟩,store.models.erase id,
    corresponds_erase store.agrees id⟩

theorem Store.lookup_exact {layoutId : String} {layers : Array (Array Nat)} {width : Nat}
    (store : Store layoutId layers width) (id : String) (body : Json) (tree : CheckedTree)
    (found : store.relations.nodes[id]? = some (body,tree)) :
    ∃ model, store.models[id]? = some model ∧ tree = model.checkedTree ∧ BodyMatches layoutId id body model := by
  have agreement := store.agrees id
  cases modelFound : store.models[id]? with
  | none => simp [found,modelFound] at agreement
  | some model => exact ⟨model,rfl,by simpa [found,modelFound] using agreement⟩

theorem Store.missing_exact {layoutId : String} {layers : Array (Array Nat)} {width : Nat}
    (store : Store layoutId layers width) (id : String) :
    store.relations.nodes[id]? = none ↔ store.models[id]? = none := by
  have agreement := store.agrees id
  cases a : store.relations.nodes[id]? <;> cases b : store.models[id]? <;> simp_all

theorem Store.lookup_semantics {layoutId : String} {layers : Array (Array Nat)} {width : Nat}
    (store : Store layoutId layers width) (layout : CheckedLayout layers width)
    (id : String) (body : Json) (tree : CheckedTree)
    (found : store.relations.nodes[id]? = some (body,tree)) :
    ∃ model, store.models[id]? = some model ∧ BodyMatches layoutId id body model ∧
      (OracleMachines.SourceInvariant.decision tree.tree = true ↔
        ∃ valuation, sourceCNFEval model.source.clauses.toArray valuation = true) ∧
      (OracleMachines.SourceInvariant.decision tree.tree = false ↔
        ¬ ∃ valuation, sourceCNFEval model.source.clauses.toArray valuation = true) := by
  obtain ⟨model,present,same,binding⟩ := store.lookup_exact id body tree found
  refine ⟨model,present,binding,?_⟩
  subst tree
  exact ⟨model.decide_exact layout,model.unsat_exact layout⟩

end OracleMachines.SourceStore
