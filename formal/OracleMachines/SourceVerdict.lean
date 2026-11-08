import OracleMachines.SourceFormula

/-! Certified native root coverage and returned decision fields. Patch verdicts
compose actual request decoding, live identities and exact original-formula
replacement. Initial raw-CNF binding and serialized witness contents remain
separate from this decision contract. -/
namespace OracleMachines.SourceVerdict
open Lean OracleMachines.Layered OracleMachines.SourceNodes OracleMachines.SourceStore
open OracleMachines.SourcePatch OracleMachines.SourceFormula

structure Covers {layers : Array (Array Nat)} {width : Nat} (model : CheckedNode layers width) : Prop where
  origin : model.start = 0
  enough : layers.size-1 ≤ 2^model.height
  minimal : model.height = 0 ∨ 2^(model.height-1) < layers.size-1

theorem Covers.logical_present {layers : Array (Array Nat)} {width : Nat}
    {model : CheckedNode layers width} (coverage : Covers model) (edge : Nat)
    (inside : edge < layers.size-1) : ∃ clauses, bucket model.source edge = some clauses := by
  apply (bucket_present model.source edge).mpr
  constructor
  · rw [coverage.origin]; omega
  · have := coverage.enough; rw [coverage.origin]; omega

theorem Covers.predecessor {layers : Array (Array Nat)} {width : Nat}
    {old new : CheckedNode layers width} {edits : Edits} (coverage : Covers new)
    (patch : Patched old new edits) : Covers old := by
  refine ⟨patch.start.trans coverage.origin,?_,?_⟩
  · rw [patch.height]; exact coverage.enough
  · rw [patch.height]; exact coverage.minimal

def Response {layoutId : String} {layers : Array (Array Nat)} {width : Nat}
    (store : OracleMachines.SourceLifetime.Store layoutId layers width) (request result : Json) : Prop :=
  ∃ name model, request.getObjValAs? String "root" = .ok name ∧
    store.models[name]? = some model ∧ Covers model ∧
    result.getObjValAs? Bool "answer" = .ok model.decide

theorem decision_field (answer : Bool) (height : Nat) :
    (Json.mkObj [("answer",toJson answer),("witness",Json.null),("height",toJson height)]).getObjValAs?
      Bool "answer" = .ok answer := by
  cases answer <;> rfl

def query {layoutId : String} (layout : CompiledSource)
    (store : OracleMachines.SourceLifetime.Store layoutId layout.layers layout.width) (request : Json) :
    Except String {result : Json // Response store request result} := do
  let root ← readParsed String request "root"
  let node ← readNode store root.value "Unknown source root"
  if origin : node.model.start = 0 then
    if enough : layout.buckets.size ≤ 2^node.model.height then
      if minimal : node.model.height = 0 ∨ 2^(node.model.height-1) < layout.buckets.size then
        have coverage : Covers node.model := ⟨origin,
          by simpa only [CompiledSource.buckets,layout.grouped.bucket_count] using enough,
          by simpa only [CompiledSource.buckets,layout.grouped.bucket_count] using minimal⟩
        let answer := node.model.decide
        let want ← request.getObjValAs? Bool "witness"
        if !want then
          return ⟨Json.mkObj [("answer",toJson answer),("witness",Json.null),("height",toJson node.model.height)],
            root.value,node.model,root.exact,node.mapped,coverage,decision_field answer node.model.height⟩
        let verdict ← OracleMachines.Layered.query store.relations (Json.mkObj [("root",toJson root.value),
          ("size",toJson layout.buckets.size),("witness",toJson true),
          ("left",toJson (2^(2^layout.width)-1)),("right",toJson (2^(2^layout.width)-1))])
        let returned ← readParsed Bool verdict "answer"
        let same ← expectEqual returned.value answer "Source witness decision disagrees"
        return ⟨verdict,root.value,node.model,root.exact,node.mapped,coverage,
          returned.exact.trans (congrArg Except.ok same.down)⟩
      else throw "Source root does not cover the full partition"
    else throw "Source root does not cover the full partition"
  else throw "Source root does not cover the full partition"

theorem response_semantics {layoutId : String} {layers : Array (Array Nat)} {width : Nat}
    {store : OracleMachines.SourceLifetime.Store layoutId layers width} {request result : Json}
    (response : Response store request result) (layout : CheckedLayout layers width) :
    ∃ name model answer, request.getObjValAs? String "root" = .ok name ∧
      store.models[name]? = some model ∧ Covers model ∧ result.getObjValAs? Bool "answer" = .ok answer ∧
      (answer = true ↔ ∃ valuation, sourceCNFEval model.source.clauses.toArray valuation = true) ∧
      (answer = false ↔ ¬ ∃ valuation, sourceCNFEval model.source.clauses.toArray valuation = true) := by
  obtain ⟨name,model,root,mapped,coverage,answer⟩ := response
  exact ⟨name,model,model.decide,root,mapped,coverage,answer,model.decide_exact layout,model.unsat_exact layout⟩

def PatchAnswer {layoutId : String} {layers : Array (Array Nat)} {width : Nat}
    (store : OracleMachines.SourceLifetime.Store layoutId layers width) (limit : Nat)
    (request verdict : Json) : Prop :=
  ∃ (oldId newId : String) (raw : Array Json) (edits : Edits)
    (old new : CheckedNode layers width) (answer : Bool),
    request.getObjValAs? String "base" = .ok oldId ∧
    request.getObjValAs? String "root" = .ok newId ∧
    request.getObjValAs? (Array Json) "edits" = .ok raw ∧
    raw.size ≤ 4096 ∧ DecodedEdits raw.toList edits ∧ (∀ edit ∈ edits, edit.1 < limit) ∧
    store.models[oldId]? = some old ∧ store.models[newId]? = some new ∧
    Covers old ∧ Covers new ∧ Patched old new edits ∧
    new.source.clauses.toArray = updatedFormula old edits ∧
    verdict.getObjValAs? Bool "answer" = .ok answer ∧
    (answer = true ↔ ∃ valuation, sourceCNFEval (updatedFormula old edits) valuation = true) ∧
    (answer = false ↔ ¬ ∃ valuation, sourceCNFEval (updatedFormula old edits) valuation = true)

theorem compose_patch {layoutId : String} {layers : Array (Array Nat)} {width limit : Nat}
    {store : OracleMachines.SourceLifetime.Store layoutId layers width} {request verdict : Json}
    (patch : RequestPatch store limit request) (response : Response store request verdict)
    (layout : CheckedLayout layers width) : PatchAnswer store limit request verdict := by
  obtain ⟨oldId,newId,raw,edits,oldField,newField,rawField,cap,decoded,inside,
    old,new,oldFound,newFound,transition⟩ := patch
  obtain ⟨name,model,root,mapped,coverage,answer⟩ := response
  have nameEq : name = newId := Except.ok.inj (root.symm.trans newField)
  subst name
  have modelEq : model = new := Option.some.inj (mapped.symm.trans newFound)
  subst model
  exact ⟨oldId,newId,raw,edits,old,new,new.decide,oldField,newField,rawField,cap,decoded,inside,
    oldFound,newFound,coverage.predecessor transition,coverage,transition,patched_formula transition,
    answer,patched_decide transition layout,patched_unsat transition layout⟩

def PatchResponse {layoutId : String} {layers : Array (Array Nat)} {width : Nat}
    (store : OracleMachines.SourceLifetime.Store layoutId layers width) (limit : Nat)
    (request result : Json) : Prop :=
  ∃ verdict, result.getObjVal? "verdict" = .ok verdict ∧ PatchAnswer store limit request verdict

def patchQuery {layoutId : String} (layout : CompiledSource)
    (store : OracleMachines.SourceLifetime.Store layoutId layout.layers layout.width) (request : Json) :
    Except String {result : Json // PatchResponse store layout.buckets.size request result} := do
  let patch ← checkRequest store layout.buckets.size request
  let verdict ← query layout store request
  return ⟨Json.mkObj [("verdict",verdict.val),("patch_visits",toJson patch.val)],verdict.val,
    by rfl,compose_patch patch.property verdict.property layout.mapping⟩

end OracleMachines.SourceVerdict
