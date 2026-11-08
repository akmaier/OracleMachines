import OracleMachines.SourceGrouping

/-! Checked compilation for a supplied ordered partition of CNF variables.
Every clause must lie in one block or two adjacent blocks of width at most four.
Variable positions, local translations and global clause grouping carry proofs.
SourceBinding checks complete-tree binding. JSON parsing and mutable node/patch
invariants remain separate obligations. This is not a general SAT compiler. -/
namespace OracleMachines.Layered
open Lean

structure CompiledSource where
  width : Nat
  layers : Array (Array Nat)
  mapping : CheckedLayout layers width
  clauses : Array (Array Int)
  grouped : GroupedCNF layers width (layers.size-1) clauses

def CompiledSource.positions (source : CompiledSource) : SourcePositions source.layers source.width :=
  source.mapping.positions

def CompiledSource.buckets (source : CompiledSource) : Array LocalCNF := source.grouped.buckets

def CompiledSource.original (source : CompiledSource) : Array (Array (Array Int)) := source.grouped.original

def compileSource (request : Json) : Except String CompiledSource := do
  let width ← request.getObjValAs? Nat "width"
  if width == 0 || width > 4 then throw "Source width must be 1 to 4"
  let layers ← request.getObjValAs? (Array (Array Nat)) "layers"
  if layers.size < 2 || layers.size > 65537 then throw "Supply 2 to 65537 variable blocks"
  let mapping ← buildSourcePositions layers width
  let clauses ← request.getObjValAs? (Array (Array Int)) "clauses"
  let grouped ← groupClauses mapping clauses
  return ⟨width,layers,mapping,clauses,grouped⟩

def compileRequest (request : Json) : Except String Json := do
  let source ← compileSource request
  let masks := source.buckets.map fun bucket => relationMask (compileLocal source.width bucket)
  return Json.mkObj [("masks",toJson masks),("edges",toJson masks.size),
    ("buckets",toJson source.original),
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

def relationPath {q : Nat} : List (Relation q) → (Nat → Fin q) → Prop
  | [], _ => True
  | edge::rest, states => edge (states 0) (states 1) = true ∧
      relationPath rest (fun i => states (i+1))

theorem relationPath_iff {q : Nat} (edges : List (Relation q)) (states : Nat → Fin q) :
    relationPath edges states ↔ ∀ (i : Nat) (inside : i < edges.length),
      edges[i] (states i) (states (i+1)) = true := by
  induction edges generalizing states with
  | nil => simp [relationPath]
  | cons edge rest ih =>
    constructor
    · rintro ⟨head,tail⟩ i inside
      cases i with
      | zero => exact head
      | succ i => exact (ih _).mp tail i (by simpa using inside)
    · intro all
      refine ⟨all 0 (by simp),(ih _).mpr ?_⟩
      intro i inside
      exact all (i+1) (by simpa using inside)

theorem sequence_path {q : Nat} (edges : List (Relation q)) (x z : Fin q) :
    sequence edges x z = true ↔ ∃ states : Nat → Fin q,
      states 0 = x ∧ states edges.length = z ∧ relationPath edges states := by
  induction edges generalizing x z with
  | nil =>
    simp only [sequence,List.foldr_nil,identity,beq_iff_eq,List.length_nil,relationPath,and_true]
    constructor
    · intro same; exact ⟨fun _ => x,rfl,same⟩
    · rintro ⟨states,start,finish⟩; exact start.symm.trans finish
  | cons edge rest ih =>
    change compose edge (sequence rest) x z = true ↔ _
    rw [compose_exact]
    constructor
    · rintro ⟨y,head,tail⟩
      obtain ⟨states,start,finish,path⟩ := (ih y z).mp tail
      let extended := fun i => if i = 0 then x else states (i-1)
      refine ⟨extended,by simp [extended],by simpa [extended] using finish,?_⟩
      simpa [relationPath,extended,start,head] using path
    · rintro ⟨states,start,finish,head,path⟩
      refine ⟨states 1,by simpa [start] using head,(ih (states 1) z).mpr ?_⟩
      exact ⟨fun i => states (i+1),rfl,finish,path⟩

theorem sequence_nonempty {q : Nat} (edges : List (Relation q)) :
    (∃ x z, sequence edges x z = true) ↔ ∃ states, relationPath edges states := by
  constructor
  · rintro ⟨x,z,accepts⟩
    obtain ⟨states,_,_,path⟩ := (sequence_path edges x z).mp accepts
    exact ⟨states,path⟩
  · rintro ⟨states,path⟩
    exact ⟨states 0,states edges.length,(sequence_path edges _ _).mpr ⟨states,rfl,rfl,path⟩⟩

theorem GroupedCNF.accepts_path {layers : Array (Array Nat)} {width edges : Nat}
    {source : Array (Array Int)} (grouped : GroupedCNF layers width edges source)
    (states : Nat → Fin (2^width)) :
    grouped.Accepts states ↔ relationPath (grouped.buckets.toList.map (compileLocal width)) states := by
  rw [relationPath_iff]
  simp only [List.length_map,Array.length_toList,grouped.bucket_count,List.getElem_map,Array.getElem_toList]
  rfl

theorem GroupedCNF.sequence_exact {layers : Array (Array Nat)} {width edges : Nat}
    {source : Array (Array Int)} (layout : CheckedLayout layers width)
    (grouped : GroupedCNF layers width edges source) :
    (∃ valuation, sourceCNFEval source valuation = true) ↔
      ∃ x z, sequence (grouped.buckets.toList.map (compileLocal width)) x z = true := by
  rw [grouped.satisfiable_exact layout,sequence_nonempty]
  exact exists_congr (fun states => grouped.accepts_path states)

/-- The whole original CNF theorem once native tree binding is supplied.
The grouping premise is carried by compilation. SourceBinding supplies the
binding premise for complete-source checks; patch preservation is separate. -/
theorem CompiledSource.bound_tree_exact (source : CompiledSource) {h : Nat}
    (tree : Tree (2^source.width) h) (valid : tree.Valid) (padding : Nat)
    (binding : tree.leaves = source.buckets.toList.map (compileLocal source.width) ++
      List.replicate padding identity) :
    (∃ valuation, sourceCNFEval source.clauses valuation = true) ↔
      ∃ x z, tree.summary x z = true := by
  rw [source_binding_exact tree valid _ padding binding]
  exact source.grouped.sequence_exact source.mapping

theorem CompiledSource.bound_tree_unsat (source : CompiledSource) {h : Nat}
    (tree : Tree (2^source.width) h) (valid : tree.Valid) (padding : Nat)
    (binding : tree.leaves = source.buckets.toList.map (compileLocal source.width) ++
      List.replicate padding identity) :
    (¬ ∃ x z, tree.summary x z = true) ↔
      ¬ ∃ valuation, sourceCNFEval source.clauses valuation = true :=
  not_congr (source.bound_tree_exact tree valid padding binding).symm

end OracleMachines.Layered
