import OracleMachines.SourceLifetime

/-! Requested source replacements, connected to the live native store.
Bucket functions and transition propositions are specifications only. The
checker visits edited paths and compares original arrays; it never flattens a
source or rebuilds a relation summary. -/
namespace OracleMachines.SourcePatch
open Lean OracleMachines.Layered OracleMachines.SourceNodes OracleMachines.SourceStore
open OracleMachines.SourceLinks

abbrev Clauses := Array (Array Int)
abbrev Edits := List (Nat × Clauses)

def bucket {layers : Array (Array Nat)} {width : Nat} :
    {start height : Nat} → OriginalTree layers width start height → Nat → Option Clauses
  | _, _, .leaf start clauses _ _, edge => if edge = start then some clauses else none
  | _, _, .pad start _, edge => if edge = start then some #[] else none
  | start, height+1, .branch left right, edge =>
    if edge < start+2^height then bucket left edge else bucket right edge

theorem bucket_reindex {layers : Array (Array Nat)} {width start other h k : Nat}
    (hs : start = other) (hh : h = k) (source : OriginalTree layers width start h) (edge : Nat) :
    bucket (source.reindex hs hh) edge = bucket source edge := by
  cases hs; cases hh; rfl

theorem bucket_join {layers : Array (Array Nat)} {width : Nat} (a b : CheckedNode layers width)
    (height : b.height = a.height) (consecutive : b.start = a.start+2^a.height) (edge : Nat) :
    bucket (checkedJoin a b height consecutive).source edge =
      if edge < a.start+2^a.height then bucket a.source edge else bucket b.source edge := by
  simp [checkedJoin,bucket,bucket_reindex]

theorem bucket_leaf {layers : Array (Array Nat)} {width start height : Nat}
    (source : OriginalTree layers width start height) (zero : height = 0) :
    ∃ clauses, source.rootClauses = some clauses ∧
      ∀ edge, bucket source edge = if edge = start then some clauses else none := by
  cases source with
  | leaf _ clauses _ _ => exact ⟨clauses,rfl,fun _ => rfl⟩
  | pad => exact ⟨#[],rfl,fun _ => rfl⟩
  | branch => simp at zero

structure Patched {layers : Array (Array Nat)} {width : Nat}
    (old new : CheckedNode layers width) (edits : Edits) : Prop where
  start : old.start = new.start
  height : old.height = new.height
  replaced : ∀ edge clauses, (edge,clauses) ∈ edits → bucket new.source edge = some clauses
  unchanged : ∀ edge, (∀ clauses, (edge,clauses) ∉ edits) →
    bucket new.source edge = bucket old.source edge

theorem patched_same {layers : Array (Array Nat)} {width : Nat} (node : CheckedNode layers width) :
    Patched node node [] :=
  ⟨rfl,rfl,by simp,fun _ _ => rfl⟩

theorem patched_leaf {layers : Array (Array Nat)} {width : Nat} (old new : CheckedNode layers width)
    (start : old.start = new.start) (height : old.height = new.height) (zero : old.height = 0)
    (clauses : Clauses) (payload : new.source.rootClauses = some clauses) :
    Patched old new [(old.start,clauses)] := by
  obtain ⟨a,_,ha⟩ := bucket_leaf old.source zero
  obtain ⟨b,hb,hbAt⟩ := bucket_leaf new.source (height.symm.trans zero)
  have same : b = clauses := Option.some.inj (hb.symm.trans payload)
  subst b
  refine ⟨start,height,?_,?_⟩
  · intro edge c member
    simp only [List.mem_singleton,Prod.mk.injEq] at member
    rcases member with ⟨rfl,rfl⟩
    simp [hbAt,start]
  · intro edge absent
    have different : edge ≠ old.start := by
      intro eq
      exact absent clauses (by simp [eq])
    simp [ha,hbAt,← start,different]

theorem patched_join {layers : Array (Array Nat)} {width : Nat}
    (a b c d : CheckedNode layers width)
    (ab : b.height = a.height) (bc : b.start = a.start+2^a.height)
    (cd : d.height = c.height) (dc : d.start = c.start+2^c.height)
    (edits : Edits) (start : a.start = c.start) (height : a.height = c.height)
    (left : Patched a c (edits.filter (fun e => e.1 < a.start+2^a.height)))
    (right : Patched b d (edits.filter (fun e => e.1 ≥ a.start+2^a.height))) :
    Patched (checkedJoin a b ab bc) (checkedJoin c d cd dc) edits := by
  have middle : c.start+2^c.height = a.start+2^a.height := by rw [start,height]
  refine ⟨start,congrArg (·+1) height,?_,?_⟩
  · intro edge clauses member
    rw [bucket_join,middle]
    split
    · rename_i less
      exact left.replaced edge clauses (by simp [List.mem_filter,member,less])
    · rename_i greater
      exact right.replaced edge clauses (by simp [List.mem_filter,member,Nat.le_of_not_gt greater])
  · intro edge absent
    rw [bucket_join,bucket_join,middle]
    split
    · exact left.unchanged edge (fun clauses member => absent clauses (List.mem_of_mem_filter member))
    · exact right.unchanged edge (fun clauses member => absent clauses (List.mem_of_mem_filter member))

structure LiveNode {layoutId : String} {layers : Array (Array Nat)} {width : Nat}
    (store : OracleMachines.SourceLifetime.Store layoutId layers width) (id : String) where
  body : Json
  model : CheckedNode layers width
  found : store.relations.nodes[id]? = some (body,model.checkedTree)
  mapped : store.models[id]? = some model
  binding : BodyMatches layoutId id body model

def readNode {layoutId : String} {layers : Array (Array Nat)} {width : Nat}
    (store : OracleMachines.SourceLifetime.Store layoutId layers width) (id : String)
    (unknown : String := "Unknown source patch node") :
    Except String (LiveNode store id) := do
  match found : store.relations.nodes[id]? with
  | none => throw unknown
  | some (body,tree) =>
    match mapped : store.models[id]? with
    | none => throw "Missing source invariant"
    | some model =>
      have exact : tree = model.checkedTree ∧ BodyMatches layoutId id body model := by
        obtain ⟨other,hm,ht,hb⟩ := store.core.lookup_exact id body tree found
        have same : other = model := Option.some.inj (hm.symm.trans mapped)
        subst other
        exact ⟨ht,hb⟩
      return ⟨body,model,by simpa only [exact.1] using found,mapped,exact.2⟩

structure Parts {layoutId : String} {layers : Array (Array Nat)} {width : Nat}
    {store : OracleMachines.SourceLifetime.Store layoutId layers width} {id : String}
    (parent : LiveNode store id) where
  leftName : String
  rightName : String
  left : LiveNode store leftName
  right : LiveNode store rightName
  height : right.model.height = left.model.height
  consecutive : right.model.start = left.model.start+2^left.model.height
  joined : parent.model = checkedJoin left.model right.model height consecutive

/-- Recover the current typed children using decoded names. This does not run
checkedJoin: the equality with that constructor is erased proof data. -/
def readParts {layoutId : String} {layers : Array (Array Nat)} {width : Nat}
    {store : OracleMachines.SourceLifetime.Store layoutId layers width} {id : String}
    (parent : LiveNode store id) (nonzero : parent.model.height ≠ 0) :
    Except String (Parts parent) := do
  let ln ← readParsed String parent.body "left"
  let rn ← readParsed String parent.body "right"
  let left ← readNode store ln.value
  let right ← readNode store rn.value
  have joined : ∃ (height : right.model.height = left.model.height)
      (consecutive : right.model.start = left.model.start+2^left.model.height),
      parent.model = checkedJoin left.model right.model height consecutive := by
    obtain ⟨l,r,a,b,h,c,hl,hr,ha,hb,same⟩ :=
      store.linked id parent.body parent.model.checkedTree parent.model parent.found parent.mapped nonzero
    have el : l = ln.value := Except.ok.inj (hl.symm.trans ln.exact)
    have er : r = rn.value := Except.ok.inj (hr.symm.trans rn.exact)
    subst l; subst r
    have ea : a = left.model := Option.some.inj (ha.symm.trans left.mapped)
    have eb : b = right.model := Option.some.inj (hb.symm.trans right.mapped)
    subst a; subst b
    exact ⟨h,c,same⟩
  have height : right.model.height = left.model.height := by obtain ⟨h,_,_⟩ := joined; exact h
  have consecutive : right.model.start = left.model.start+2^left.model.height := by
    obtain ⟨_,c,_⟩ := joined; exact c
  have same : parent.model = checkedJoin left.model right.model height consecutive := by
    obtain ⟨_,_,same⟩ := joined; exact same
  return ⟨ln.value,rn.value,left,right,height,consecutive,same⟩

/-- Successful checking returns its path-visit counter together with the exact
bucket transition. Neither the counter nor equal relation masks replace the
original-clause checks. Failed checks return no certificate. -/
def checkNodes {layoutId : String} {layers : Array (Array Nat)} {width : Nat}
    {store : OracleMachines.SourceLifetime.Store layoutId layers width} :
    Nat → {oldId newId : String} → (old : LiveNode store oldId) → (new : LiveNode store newId) →
      (edits : Edits) → Except String {_visits : Nat // Patched old.model new.model edits}
  | 0, _, _, _, _, _ => .error "Source patch depth exhausted"
  | fuel+1, oldId, newId, old, new, edits => do
    if empty : edits = [] then
      if same : oldId = newId then
        have equal : old.model = new.model := by
          exact Option.some.inj (old.mapped.symm.trans
            ((congrArg (fun name => store.models[name]?) same).trans new.mapped))
        return ⟨1,by simpa only [empty,equal] using patched_same old.model⟩
      else throw "Source patch changed an unedited subtree"
    let start ← expectEqual old.model.start new.model.start "Source patch changed the partition"
    let height ← expectEqual old.model.height new.model.height "Source patch changed the partition"
    if zero : old.model.height = 0 then
      match shape : edits with
      | [(edge,clauses)] =>
        let atStart ← expectEqual edge old.model.start "Source patch clauses differ"
        let payload ← expectEqual new.model.source.rootClauses (some clauses) "Source patch clauses differ"
        return ⟨1,by
          simpa only [shape,atStart.down] using
            patched_leaf old.model new.model start.down height.down zero clauses payload.down⟩
      | _ => throw "Duplicate or missing source edge edit"
    else
      let a ← readParts old zero
      let b ← readParts new (by simpa only [← height.down] using zero)
      have starts : a.left.model.start = b.left.model.start := by
        have hs := start.down
        rw [a.joined,b.joined] at hs
        exact hs
      have heights : a.left.model.height = b.left.model.height := by
        have hh := height.down
        rw [a.joined,b.joined] at hh
        exact Nat.add_right_cancel hh
      let middle := a.left.model.start+2^a.left.model.height
      let left ← checkNodes fuel a.left b.left (edits.filter (fun e => e.1 < middle))
      let right ← checkNodes fuel a.right b.right (edits.filter (fun e => e.1 ≥ middle))
      return ⟨left.val+right.val+1,by
        rw [a.joined,b.joined]
        exact patched_join a.left.model a.right.model b.left.model b.right.model
          a.height a.consecutive b.height b.consecutive edits starts heights left.property right.property⟩

def NamedPatch {layoutId : String} {layers : Array (Array Nat)} {width : Nat}
    (store : OracleMachines.SourceLifetime.Store layoutId layers width) (oldId newId : String)
    (edits : Edits) : Prop :=
  ∃ old new, store.models[oldId]? = some old ∧ store.models[newId]? = some new ∧ Patched old new edits

def check {layoutId : String} {layers : Array (Array Nat)} {width : Nat}
    (fuel : Nat) (store : OracleMachines.SourceLifetime.Store layoutId layers width)
    (oldId newId : String) (edits : Edits) :
    Except String {_visits : Nat // NamedPatch store oldId newId edits} := do
  let old ← readNode store oldId
  let new ← readNode store newId
  let checked ← checkNodes fuel old new edits
  return ⟨checked.val,old.model,new.model,old.mapped,new.mapped,checked.property⟩

def DecodedEdits (raw : List Json) (edits : Edits) : Prop :=
  List.Forall₂ (fun body edit => body.getObjValAs? Nat "edge" = .ok edit.1 ∧
    body.getObjValAs? Clauses "clauses" = .ok edit.2) raw edits

/-- Every accepted entry is tied to its actual JSON getters and logical-edge
bound. Duplicate detection is retained; soundness does not assume uniqueness. -/
def readEdits (limit : Nat) : (raw : List Json) → Std.HashSet Nat →
    Except String {edits : Edits // DecodedEdits raw edits ∧ ∀ edit ∈ edits, edit.1 < limit}
  | [], _ => .ok ⟨[],List.Forall₂.nil,by simp⟩
  | body::rest, seen => do
    let edge ← readParsed Nat body "edge"
    if inside : edge.value < limit then
      if seen.contains edge.value then throw "Invalid or duplicate source edit"
      let clauses ← readParsed Clauses body "clauses"
      let next ← readEdits limit rest (seen.insert edge.value)
      return ⟨(edge.value,clauses.value)::next.val,
        List.Forall₂.cons ⟨edge.exact,clauses.exact⟩ next.property.1,by
          intro edit member
          rcases List.mem_cons.mp member with same | tail
          · simpa only [same] using inside
          · exact next.property.2 edit tail⟩
    else throw "Invalid or duplicate source edit"

def RequestPatch {layoutId : String} {layers : Array (Array Nat)} {width : Nat}
    (store : OracleMachines.SourceLifetime.Store layoutId layers width) (limit : Nat) (request : Json) : Prop :=
  ∃ (oldId newId : String) (raw : Array Json) (edits : Edits),
    request.getObjValAs? String "base" = .ok oldId ∧
    request.getObjValAs? String "root" = .ok newId ∧
    request.getObjValAs? (Array Json) "edits" = .ok raw ∧
    raw.size ≤ 4096 ∧ DecodedEdits raw.toList edits ∧
    (∀ edit ∈ edits, edit.1 < limit) ∧ NamedPatch store oldId newId edits

def checkRequest {layoutId : String} {layers : Array (Array Nat)} {width : Nat}
    (store : OracleMachines.SourceLifetime.Store layoutId layers width) (limit : Nat) (request : Json) :
    Except String {_visits : Nat // RequestPatch store limit request} := do
  let old ← readParsed String request "base"
  let new ← readParsed String request "root"
  let raw ← readParsed (Array Json) request "edits"
  if capacity : raw.value.size ≤ 4096 then
    let edits ← readEdits limit raw.value.toList {}
    let checked ← check 18 store old.value new.value edits.val
    return ⟨checked.val,old.value,new.value,raw.value,edits.val,
      old.exact,new.exact,raw.exact,capacity,edits.property.1,edits.property.2,checked.property⟩
  else throw "Source edit batch exceeds capacity"

end OracleMachines.SourcePatch
