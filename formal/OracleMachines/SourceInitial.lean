import OracleMachines.SourceVerdict

/-! Exact initial source binding: actual decoded input, live original buckets,
complete clause multiplicities, and the native returned decision. Byte transport,
serialized witness contents and persistent operation histories are separate. -/
namespace OracleMachines.SourceInitial
open Lean OracleMachines.Layered OracleMachines.SourceNodes OracleMachines.SourceStore
open OracleMachines.SourcePatch OracleMachines.SourceFormula OracleMachines.SourceVerdict

structure DecodedCompilation (request : Json) (source : CompiledSource) : Prop where
  width : request.getObjValAs? Nat "width" = .ok source.width
  layers : request.getObjValAs? (Array (Array Nat)) "layers" = .ok source.layers
  clauses : request.getObjValAs? Clauses "clauses" = .ok source.clauses

/-- Recover input equations from the existing compiler's successful execution;
there is no second parser or duplicate compilation implementation. -/
theorem compileSource_fields (request : Json) (source : CompiledSource)
    (accepted : compileSource request = .ok source) : DecodedCompilation request source := by
  cases widthField : request.getObjValAs? Nat "width" with
  | error message => simp [compileSource,bind,Except.bind,widthField] at accepted
  | ok width =>
    by_cases badWidth : width = 0 ∨ width > 4
    · simp [compileSource,bind,Except.bind,widthField,badWidth] at accepted
    · cases layersField : request.getObjValAs? (Array (Array Nat)) "layers" with
      | error message => simp [compileSource,bind,pure,Except.bind,Except.pure,widthField,badWidth,layersField] at accepted
      | ok layers =>
        by_cases badLayers : layers.size < 2 ∨ layers.size > 65537
        · simp [compileSource,bind,pure,Except.bind,Except.pure,widthField,badWidth,layersField,badLayers] at accepted
        · cases positions : buildSourcePositions layers width with
          | error message => simp [compileSource,bind,pure,Except.bind,Except.pure,widthField,badWidth,layersField,badLayers,positions] at accepted
          | ok mapping =>
            cases clausesField : request.getObjValAs? Clauses "clauses" with
            | error message =>
              simp [compileSource,bind,pure,Except.bind,Except.pure,widthField,badWidth,layersField,badLayers,positions,clausesField] at accepted
            | ok clauses =>
              cases grouping : groupClauses mapping clauses with
              | error message =>
                simp [compileSource,bind,pure,Except.bind,Except.pure,widthField,badWidth,layersField,badLayers,positions,clausesField,grouping] at accepted
              | ok grouped =>
                have same : (⟨width,layers,mapping,clauses,grouped⟩ : CompiledSource) = source := by
                  simpa [compileSource,bind,pure,Except.bind,Except.pure,Except.map,widthField,badWidth,layersField,badLayers,positions,clausesField,grouping] using accepted
                subst source
                exact ⟨widthField,layersField,clausesField⟩

def readCompilation (request : Json) : Except String {source : CompiledSource // DecodedCompilation request source} :=
  match result : compileSource request with
  | .error error => .error error
  | .ok source => .ok ⟨source,compileSource_fields request source result⟩

def originalBucket (original : Array Clauses) (edge : Nat) : Option Clauses :=
  some (original[edge]?.getD #[])

theorem flatten_original (original : Array Clauses) (start height : Nat) :
    flatten start height (originalBucket original) =
      ((original.toList.drop start).take (2^height)).flatMap Array.toList := by
  induction height generalizing start with
  | zero =>
    simp only [flatten,pow_zero,originalBucket,Option.getD_some,List.take_one,List.head?_drop,Array.getElem?_toList]
    cases original[start]? <;> simp
  | succ height ih =>
    have power : 2^(height+1) = 2^height+2^height := by simp [pow_succ]; omega
    simp only [flatten,ih,power,List.take_add,List.flatMap_append,List.drop_drop]

def Matches {layers : Array (Array Nat)} {width : Nat} (node : CheckedNode layers width)
    (original : Array Clauses) : Prop :=
  ∀ edge, node.start ≤ edge → edge < node.start+2^node.height →
    bucket node.source edge = originalBucket original edge

theorem matches_flat {layers : Array (Array Nat)} {width : Nat} {node : CheckedNode layers width}
    {original : Array Clauses} (agreement : Matches node original) :
    node.source.clauses = ((original.toList.drop node.start).take (2^node.height)).flatMap Array.toList := by
  rw [← flatten_source node.source,← flatten_original]
  exact flatten_congr node.start node.height _ _ agreement

theorem matches_complete {layers : Array (Array Nat)} {width : Nat} {node : CheckedNode layers width}
    {original : Array Clauses} (agreement : Matches node original) (coverage : Covers node)
    (size : original.size = layers.size-1) : node.source.clauses = original.toList.flatMap Array.toList := by
  rw [matches_flat agreement,coverage.origin,List.drop_zero,List.take_of_length_le]
  simpa only [Array.length_toList,size] using coverage.enough

theorem matches_leaf {layers : Array (Array Nat)} {width : Nat} (node : CheckedNode layers width)
    (original : Array Clauses) (zero : node.height = 0)
    (same : node.source.rootClauses = originalBucket original node.start) : Matches node original := by
  obtain ⟨clauses,root,atEdge⟩ := bucket_leaf node.source zero
  intro edge lower upper
  have equal : edge = node.start := by rw [zero] at upper; simp only [pow_zero] at upper; omega
  subst edge
  simpa only [atEdge,ite_true] using root.symm.trans same

theorem matches_join {layers : Array (Array Nat)} {width : Nat}
    (a b : CheckedNode layers width) (height : b.height = a.height)
    (consecutive : b.start = a.start+2^a.height) (original : Array Clauses)
    (left : Matches a original) (right : Matches b original) :
    Matches (checkedJoin a b height consecutive) original := by
  intro edge lower upper
  change a.start ≤ edge at lower
  change edge < a.start+2^(a.height+1) at upper
  rw [bucket_join]
  split
  · exact left edge lower (by assumption)
  · apply right edge
    · rw [consecutive]; omega
    · rw [height,consecutive]
      rw [pow_succ] at upper
      omega

/-- The count covers logical tree-node visits, including padding. It does not
charge map lookups, parsing, array comparisons, allocation or relation scans. -/
def checkBinding {layoutId : String} {layers : Array (Array Nat)} {width : Nat}
    {store : OracleMachines.SourceLifetime.Store layoutId layers width} (original : Array Clauses) :
    (fuel : Nat) → {id : String} → (node : LiveNode store id) →
    Except String {visits : Nat // Matches node.model original ∧
      visits+1 = 2^(node.model.height+1) ∧ node.model.height < fuel}
  | 0, _, _ => .error "Source binding traversal cap exceeded"
  | fuel+1, _, node => do
    if zero : node.model.height = 0 then
      let same ← expectEqual node.model.source.rootClauses (originalBucket original node.model.start)
        "Original source clauses differ from checked leaves"
      return ⟨1,matches_leaf node.model original zero same.down,by simp [zero],by omega⟩
    else
      let parts ← readParts node zero
      let left ← checkBinding original fuel parts.left
      let right ← checkBinding original fuel parts.right
      return ⟨left.val+right.val+1,by
        rw [parts.joined]
        exact matches_join parts.left.model parts.right.model parts.height parts.consecutive original
          left.property.1 right.property.1,by
        rw [parts.joined]
        change left.val+right.val+1+1 = 2^(parts.left.model.height+1+1)
        have hl := left.property.2.1
        have hr := right.property.2.1
        have hr := hr.trans (congrArg (fun h => 2^(h+1)) parts.height)
        calc
          left.val+right.val+1+1 = (left.val+1)+(right.val+1) := by omega
          _ = 2^(parts.left.model.height+1)+2^(parts.left.model.height+1) := congrArg₂ Nat.add hl hr
          _ = 2^(parts.left.model.height+1+1) := by rw [pow_succ]; omega,by
        rw [parts.joined]
        change parts.left.model.height+1 < fuel+1
        have := left.property.2.2
        omega⟩

theorem matched_partition (source : CompiledSource) {layers : Array (Array Nat)} {width : Nat}
    (node : CheckedNode layers width) (sameLayers : source.layers = layers)
    (agreement : Matches node source.original) (coverage : Covers node) :
    node.source.clauses.Perm source.clauses.toList := by
  have size : source.original.size = layers.size-1 := by
    simpa only [CompiledSource.original,sameLayers] using source.grouped.original_count
  rw [matches_complete agreement coverage size]
  exact source.grouped.partition

theorem partition_eval {layers : Array (Array Nat)} {width : Nat}
    (node : CheckedNode layers width) (clauses : Clauses)
    (partition : node.source.clauses.Perm clauses.toList) (valuation : Nat → Bool) :
    sourceCNFEval node.source.clauses.toArray valuation = sourceCNFEval clauses valuation := by
  simpa only [sourceCNFEval,List.toList_toArray] using list_all_perm partition (sourceClauseEval · valuation)

def bindingResponse (source : CompiledSource) (bound : BoundCompilation source) (verdict : Json) (visits : Nat) : Json :=
  (Json.mkObj [("verdict",verdict),("binding_visits",toJson visits)]).mergeObj bound.metrics

theorem bindingResponse_verdict (source : CompiledSource) (bound : BoundCompilation source)
    (verdict : Json) (visits : Nat) :
    (bindingResponse source bound verdict visits).getObjVal? "verdict" = .ok verdict := by
  rfl

theorem bindingResponse_visits (source : CompiledSource) (bound : BoundCompilation source)
    (verdict : Json) (visits : Nat) :
    (bindingResponse source bound verdict visits).getObjValAs? Nat "binding_visits" = .ok visits := by
  rfl

theorem response_at {layoutId : String} {layers : Array (Array Nat)} {width : Nat}
    {store : OracleMachines.SourceLifetime.Store layoutId layers width} {request verdict : Json}
    {name : String} (node : LiveNode store name)
    (root : request.getObjValAs? String "root" = .ok name) (response : Response store request verdict) :
    Covers node.model ∧ verdict.getObjValAs? Bool "answer" = .ok node.model.decide := by
  obtain ⟨foundName,model,field,mapped,coverage,answer⟩ := response
  have nameEq : foundName = name := Except.ok.inj (field.symm.trans root)
  subst foundName
  have modelEq : model = node.model := Option.some.inj (mapped.symm.trans node.mapped)
  subst model
  exact ⟨coverage,answer⟩

/-- The formula is exactly the parsed input. Grouping permits only a permutation
of clause occurrences; the live buckets retain their original arrays. -/
def InitialResponse {layoutId : String} (layout : CompiledSource)
    (store : OracleMachines.SourceLifetime.Store layoutId layout.layers layout.width)
    (request result : Json) : Prop :=
  ∃ (source : CompiledSource) (name : String) (model : CheckedNode layout.layers layout.width)
    (verdict : Json) (visits : Nat),
    DecodedCompilation request source ∧ source.width = layout.width ∧ source.layers = layout.layers ∧
    request.getObjValAs? String "root" = .ok name ∧ store.models[name]? = some model ∧
    Covers model ∧ Matches model source.original ∧ model.source.clauses.Perm source.clauses.toList ∧
    result.getObjVal? "verdict" = .ok verdict ∧ verdict.getObjValAs? Bool "answer" = .ok model.decide ∧
    result.getObjValAs? Nat "binding_visits" = .ok visits ∧
    visits+1 = 2^(model.height+1) ∧ model.height < 17 ∧
    (model.decide = true ↔ ∃ valuation, sourceCNFEval source.clauses valuation = true) ∧
    (model.decide = false ↔ ¬ ∃ valuation, sourceCNFEval source.clauses valuation = true)

def bindSource {layoutId : String} (layout : CompiledSource)
    (store : OracleMachines.SourceLifetime.Store layoutId layout.layers layout.width) (request : Json) :
    Except String {result : Json // InitialResponse layout store request result} := do
  let compiled ← readCompilation request
  let width ← expectEqual compiled.val.width layout.width "Source partition differs"
  let layers ← expectEqual compiled.val.layers layout.layers "Source partition differs"
  let root ← readParsed String request "root"
  let node ← readNode store root.value "Missing source binding node"
  let visited ← checkBinding compiled.val.original 17 node
  let bound ← bindCompilation compiled.val node.model.checkedTree
  let verdict ← OracleMachines.SourceVerdict.query layout store request
  let returned ← readParsed Bool verdict.val "answer"
  let _ ← expectEqual returned.value bound.decide "Source decision disagrees with binding proof"
  have response := response_at node root.exact verdict.property
  have partition := matched_partition compiled.val node.model layers.down visited.property.1 response.1
  have evaluation : (∃ valuation, sourceCNFEval node.model.source.clauses.toArray valuation = true) ↔
      ∃ valuation, sourceCNFEval compiled.val.clauses valuation = true := by
    simp only [partition_eval node.model compiled.val.clauses partition]
  return ⟨bindingResponse compiled.val bound verdict.val visited.val,
    compiled.val,root.value,node.model,verdict.val,visited.val,compiled.property,width.down,layers.down,
    root.exact,node.mapped,response.1,visited.property.1,partition,
    bindingResponse_verdict _ _ _ _,response.2,bindingResponse_visits _ _ _ _,
    visited.property.2.1,visited.property.2.2,
    (node.model.decide_exact layout.mapping).trans evaluation,
    (node.model.unsat_exact layout.mapping).trans (not_congr evaluation)⟩

end OracleMachines.SourceInitial
