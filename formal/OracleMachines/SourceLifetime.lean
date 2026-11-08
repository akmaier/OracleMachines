import OracleMachines.SourceLinks
import OracleMachines.ReferenceCounts

/-! Live source branches retain their exact named children. Exact incoming
counts discharge the deletion premise; all aggregate witnesses erase. -/
namespace OracleMachines.SourceLifetime
open Lean OracleMachines.Layered OracleMachines.SourceNodes OracleMachines.SourceStore
open OracleMachines.SourceLinks OracleMachines.ReferenceCounts

def registration {layers : Array (Array Nat)} {width : Nat} {layoutId id : String} {body : Json}
    {models : Std.HashMap String (CheckedNode layers width)}
    (bound : {node : CheckedNode layers width // BodyMatches layoutId id body node})
    (shape : bound.val.height = 0 ∨ JoinLinks models body bound.val) :
    {node : CheckedNode layers width // BodyMatches layoutId id body node ∧
      (node.height = 0 ∨ JoinLinks models body node)} :=
  ⟨bound.val,bound.property,shape⟩

def Linked {layers : Array (Array Nat)} {width : Nat}
    (nodes : Nodes) (models : Std.HashMap String (CheckedNode layers width)) : Prop :=
  ∀ (id : String) (body : Json) (tree : CheckedTree) (model : CheckedNode layers width),
    nodes[id]? = some (body,tree) → models[id]? = some model →
    model.height ≠ 0 → JoinLinks models body model

theorem linked_empty {layers : Array (Array Nat)} {width : Nat} :
    Linked (layers := layers) (width := width) {} {} := by
  intro id body tree model found
  simp at found

theorem linked_insert {layers : Array (Array Nat)} {width : Nat}
    {nodes : Nodes} {models : Std.HashMap String (CheckedNode layers width)}
    (prior : Linked nodes models) (id : String) (body : Json) (model : CheckedNode layers width)
    (fresh : models[id]? = none) (shape : model.height = 0 ∨ JoinLinks models body model) :
    Linked (nodes.insert id (body,model.checkedTree)) (models.insert id model) := by
  intro key stored tree value found mapped nonzero
  by_cases same : id = key
  · subst key
    simp only [Std.HashMap.getElem?_insert_self,Option.some.injEq,Prod.mk.injEq] at found mapped
    obtain ⟨rfl,rfl⟩ := found
    subst value
    exact (shape.resolve_left nonzero).insert_fresh id model fresh
  · have oldFound : nodes[key]? = some (stored,tree) := by
      simpa [Std.HashMap.getElem?_insert,same] using found
    have oldMapped : models[key]? = some value := by
      simpa [Std.HashMap.getElem?_insert,same] using mapped
    exact (prior key stored tree value oldFound oldMapped nonzero).insert_fresh id model fresh

theorem linked_erase {layers : Array (Array Nat)} {width : Nat} {layoutId : String}
    (core : OracleMachines.SourceStore.Store layoutId layers width)
    (prior : Linked core.relations.nodes core.models)
    (counts : Exact core.relations.nodes core.relations.incoming)
    (id : String) (zero : count core.relations.incoming id = 0) :
    Linked (core.relations.nodes.erase id) (core.models.erase id) := by
  intro key body tree model found mapped nonzero
  by_cases same : id = key
  · subst key; simp at found
  · have oldFound : core.relations.nodes[key]? = some (body,tree) := by
      simpa [Std.HashMap.getElem?_erase,same] using found
    have oldMapped : core.models[key]? = some model := by
      simpa [Std.HashMap.getElem?_erase,same] using mapped
    have links := prior key body tree model oldFound oldMapped nonzero
    have agreement := core.agrees key
    simp only [oldFound,oldMapped] at agreement
    have binding : BodyMatches layoutId key body model := agreement.2
    obtain ⟨left,right,a,b,height,consecutive,hl,hr,ha,hb,equal⟩ := links
    have level : model.height = a.height+1 := by rw [equal]; rfl
    have decoded : children body = .ok [left,right] := by
      simp [children,binding.level,level,hl,hr]
      rfl
    have absent := counts.zero_no_child id zero key (body,tree) oldFound [left,right] decoded
    have notLeft : body.getObjValAs? String "left" ≠ .ok id := by
      intro eq
      have same : left = id := Except.ok.inj (hl.symm.trans eq)
      simp [same] at absent
    have notRight : body.getObjValAs? String "right" ≠ .ok id := by
      intro eq
      have same : right = id := Except.ok.inj (hr.symm.trans eq)
      simp [same] at absent
    exact (prior key body tree model oldFound oldMapped nonzero).erase_unreferenced id notLeft notRight

structure Store (layoutId : String) (layers : Array (Array Nat)) (width : Nat) where
  core : OracleMachines.SourceStore.Store layoutId layers width
  counted : Exact core.relations.nodes core.relations.incoming
  linked : Linked core.relations.nodes core.models

def Store.relations {layoutId : String} {layers : Array (Array Nat)} {width : Nat}
    (store : Store layoutId layers width) : OracleMachines.Layered.Store := store.core.relations

def Store.models {layoutId : String} {layers : Array (Array Nat)} {width : Nat}
    (store : Store layoutId layers width) : Std.HashMap String (CheckedNode layers width) := store.core.models

def Store.empty (layoutId : String) (layers : Array (Array Nat)) (width : Nat) : Store layoutId layers width :=
  ⟨.empty layoutId layers width,exact_empty,linked_empty⟩

theorem Store.lookup_branch {layoutId : String} {layers : Array (Array Nat)} {width : Nat}
    (store : Store layoutId layers width) (id : String) (body : Json) (tree : CheckedTree)
    (found : store.relations.nodes[id]? = some (body,tree)) (branch : tree.height ≠ 0) :
    ∃ model, store.models[id]? = some model ∧ BodyMatches layoutId id body model ∧
      JoinLinks store.models body model := by
  obtain ⟨model,mapped,same,binding⟩ := store.core.lookup_exact id body tree found
  have nonzero : model.height ≠ 0 := by simpa [same,CheckedNode.checkedTree] using branch
  exact ⟨model,mapped,binding,store.linked id body tree model found mapped nonzero⟩

def Store.insert {layoutId : String} {layers : Array (Array Nat)} {width : Nat}
    (store : Store layoutId layers width) (id : String) (body : Json) (model : CheckedNode layers width)
    (binding : BodyMatches layoutId id body model)
    (shape : model.height = 0 ∨ JoinLinks store.models body model)
    (fresh : store.relations.nodes[id]? = none) : Except String (Store layoutId layers width) := do
  match decoded : children body with
  | .error error => throw error
  | .ok refs =>
    let incoming := increment store.relations.incoming refs
    let core : OracleMachines.SourceStore.Store layoutId layers width :=
      ⟨⟨store.relations.nodes.insert id (body,model.checkedTree),incoming⟩,store.models.insert id model,
        corresponds_insert store.core.agrees id body model binding⟩
    return ⟨core,exact_insert store.counted id (body,model.checkedTree) refs fresh decoded,
      linked_insert store.linked id body model ((store.core.missing_exact id).mp fresh) shape⟩

def Store.erase {layoutId : String} {layers : Array (Array Nat)} {width : Nat}
    (store : Store layoutId layers width) (id : String) : Except String (Store layoutId layers width) := do
  match found : store.relations.nodes[id]? with
  | none => throw "Unknown evicted node"
  | some node =>
    if zero : count store.relations.incoming id = 0 then
      match decoded : children node.1 with
      | .error error => throw error
      | .ok refs =>
        let next ← decrement store.relations.incoming refs
        let core : OracleMachines.SourceStore.Store layoutId layers width :=
          ⟨⟨store.relations.nodes.erase id,next.val.erase id⟩,store.models.erase id,
            corresponds_erase store.core.agrees id⟩
        return ⟨core,exact_erase store.counted id node refs found decoded zero next.property,
          linked_erase store.core store.linked store.counted id zero⟩
    else throw "Cannot evict a referenced node"

end OracleMachines.SourceLifetime
