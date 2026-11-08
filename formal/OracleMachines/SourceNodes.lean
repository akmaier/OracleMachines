import OracleMachines.SourceBinding

/-! Original-source nodes indexed by their layout, width, start and height.
Leaf translation proofs survive registration; joins require consecutive ranges.
The specification flattens clauses only in proofs, never in a warm decision.
Identity lookup and requested-patch refinement remain separate obligations. -/
namespace OracleMachines.SourceNodes
open OracleMachines.Layered

inductive OriginalTree (layers : Array (Array Nat)) (width : Nat) : Nat → Nat → Type where
  | leaf (start : Nat) (clauses : Array (Array Int)) (inside : start < layers.size-1)
      (checked : CheckedCNF layers width start clauses) : OriginalTree layers width start 0
  | pad (start : Nat) (outside : layers.size-1 ≤ start) : OriginalTree layers width start 0
  | branch {start h : Nat} (left : OriginalTree layers width start h)
      (right : OriginalTree layers width (start+2^h) h) : OriginalTree layers width start (h+1)

def OriginalTree.compile {layers : Array (Array Nat)} {width : Nat} :
    {start h : Nat} → OriginalTree layers width start h → Tree (2^width) h
  | _, _, .leaf _ _ _ checked => .leaf (compileLocal width checked.localCNF)
  | _, _, .pad _ _ => .leaf identity
  | _, _, .branch l r => join l.compile r.compile

theorem OriginalTree.compile_valid {layers : Array (Array Nat)} {width start h : Nat}
    (source : OriginalTree layers width start h) : source.compile.Valid := by
  induction source with
  | leaf => trivial
  | pad => trivial
  | branch l r il ir => exact join_valid _ _ il ir

def OriginalTree.clauses {layers : Array (Array Nat)} {width : Nat} :
    {start h : Nat} → OriginalTree layers width start h → List (Array Int)
  | _, _, .leaf _ clauses _ _ => clauses.toList
  | _, _, .pad _ _ => []
  | _, _, .branch l r => l.clauses ++ r.clauses

/-- Inspect only the root constructor; joins do not flatten their sources. -/
def OriginalTree.rootClauses {layers : Array (Array Nat)} {width : Nat} :
    {start h : Nat} → OriginalTree layers width start h → Option (Array (Array Int))
  | _, _, .leaf _ clauses _ _ => some clauses
  | _, _, .pad _ _ => some #[]
  | _, _, .branch _ _ => none

def OriginalTree.eval {layers : Array (Array Nat)} {width : Nat} :
    {start h : Nat} → OriginalTree layers width start h → (Nat → Bool) → Bool
  | _, _, .leaf _ clauses _ _, valuation => sourceCNFEval clauses valuation
  | _, _, .pad _ _, _ => true
  | _, _, .branch l r, valuation => l.eval valuation && r.eval valuation

theorem OriginalTree.eval_flat {layers : Array (Array Nat)} {width start h : Nat}
    (source : OriginalTree layers width start h) (valuation : Nat → Bool) :
    source.eval valuation = sourceCNFEval source.clauses.toArray valuation := by
  induction source with
  | leaf => simp [OriginalTree.eval,OriginalTree.clauses]
  | pad => simp [OriginalTree.eval,OriginalTree.clauses,sourceCNFEval]
  | branch l r il ir => simpa [OriginalTree.eval,OriginalTree.clauses,sourceCNFEval] using congrArg₂ Bool.and il ir

def OriginalTree.Accepts {layers : Array (Array Nat)} {width : Nat} :
    {start h : Nat} → OriginalTree layers width start h → (Nat → Fin (2^width)) → Prop
  | _, _, .leaf edge _ _ checked, states =>
      compileLocal width checked.localCNF (states edge) (states (edge+1)) = true
  | _, _, .pad edge _, states => states edge = states (edge+1)
  | _, _, .branch l r, states => l.Accepts states ∧ r.Accepts states

theorem relationPath_append {q : Nat} (a b : List (Relation q)) (states : Nat → Fin q) :
    relationPath (a++b) states ↔ relationPath a states ∧ relationPath b (fun i => states (a.length+i)) := by
  induction a generalizing states with
  | nil => simp [relationPath]
  | cons edge rest ih =>
    simpa [relationPath,Nat.add_assoc,Nat.add_comm,Nat.add_left_comm,and_assoc] using
      and_congr_right (fun _ => ih (fun i => states (i+1)))

theorem leaves_length {q h : Nat} (tree : Tree q h) : tree.leaves.length = 2^h := by
  induction tree with
  | leaf => simp [Tree.leaves]
  | branch r l t il ir => simp only [Tree.leaves,List.length_append,il,ir,pow_succ]; omega

theorem OriginalTree.path_exact {layers : Array (Array Nat)} {width start h : Nat}
    (source : OriginalTree layers width start h) (states : Nat → Fin (2^width)) :
    relationPath source.compile.leaves (fun i => states (start+i)) ↔ source.Accepts states := by
  induction source with
  | leaf => simp [OriginalTree.compile,Tree.leaves,relationPath,OriginalTree.Accepts]
  | pad => simp [OriginalTree.compile,Tree.leaves,relationPath,OriginalTree.Accepts,identity]
  | @branch start h l r il ir =>
    simpa [OriginalTree.compile,join,Tree.leaves,relationPath_append,leaves_length,Nat.add_assoc,
      OriginalTree.Accepts] using and_congr il ir

theorem OriginalTree.paths_exact {layers : Array (Array Nat)} {width start h : Nat}
    (source : OriginalTree layers width start h) :
    (∃ states, relationPath source.compile.leaves states) ↔ ∃ states, source.Accepts states := by
  constructor
  · rintro ⟨states,path⟩
    refine ⟨fun i => states (i-start),(source.path_exact _).mp ?_⟩
    simpa using path
  · rintro ⟨states,path⟩
    exact ⟨fun i => states (start+i),(source.path_exact states).mpr path⟩

theorem OriginalTree.accepts_eval {layers : Array (Array Nat)} {width start h : Nat}
    (source : OriginalTree layers width start h) (valuation : Nat → Bool)
    (states : Nat → Fin (2^width)) (agreement : SourceAgrees layers valuation (fun i => (states i).val))
    (accepted : source.Accepts states) : source.eval valuation = true := by
  induction source with
  | leaf edge clauses inside checked =>
    exact (checked.exact valuation _ agreement).symm.trans accepted
  | pad => rfl
  | branch l r il ir => simpa only [OriginalTree.eval,Bool.and_eq_true] using And.intro (il accepted.1) (ir accepted.2)

/-- Repeat the final block state throughout padding. Other source coordinates
are unchanged, including empty and short blocks. -/
def paddedStates {layers : Array (Array Nat)} {width : Nat} (layout : CheckedLayout layers width)
    (valuation : Nat → Bool) (i : Nat) : Fin (2^width) :=
  ⟨sourceWords layers valuation (min i (layers.size-1)),layout.sourceWords_bound valuation _⟩

theorem paddedStates_agree {layers : Array (Array Nat)} {width : Nat}
    (layout : CheckedLayout layers width) (valuation : Nat → Bool) :
    SourceAgrees layers valuation (fun i => (paddedStates layout valuation i).val) := by
  intro i j
  have bound : i.val ≤ layers.size-1 := by have := i.isLt; omega
  simpa only [paddedStates,Nat.min_eq_left bound] using sourceWords_agree layers valuation i j

theorem OriginalTree.eval_accepts {layers : Array (Array Nat)} {width start h : Nat}
    (source : OriginalTree layers width start h) (layout : CheckedLayout layers width)
    (valuation : Nat → Bool) (satisfies : source.eval valuation = true) :
    source.Accepts (paddedStates layout valuation) := by
  induction source with
  | leaf edge clauses inside checked =>
    exact (checked.exact valuation _ (paddedStates_agree layout valuation)).trans satisfies
  | pad edge outside =>
    have next : layers.size-1 ≤ edge+1 := by omega
    simp [OriginalTree.Accepts,paddedStates,Nat.min_eq_right outside,Nat.min_eq_right next]
  | branch l r il ir =>
    simp only [OriginalTree.eval,Bool.and_eq_true] at satisfies
    exact ⟨il satisfies.1,ir satisfies.2⟩

theorem OriginalTree.satisfiable_exact {layers : Array (Array Nat)} {width start h : Nat}
    (source : OriginalTree layers width start h) (layout : CheckedLayout layers width) :
    (∃ states, source.Accepts states) ↔ ∃ valuation, sourceCNFEval source.clauses.toArray valuation = true := by
  constructor
  · rintro ⟨states,accepted⟩
    let words := fun i => (states i).val
    refine ⟨sourceValuation layout.positions words,?_⟩
    rw [← source.eval_flat]
    exact source.accepts_eval _ states (layout.sourceValuation_agrees words) accepted
  · rintro ⟨valuation,satisfies⟩
    refine ⟨paddedStates layout valuation,source.eval_accepts layout valuation ?_⟩
    rwa [source.eval_flat]

structure CheckedNode (layers : Array (Array Nat)) (width : Nat) where
  start : Nat
  height : Nat
  source : OriginalTree layers width start height
  tree : Tree (2^width) height
  aligned : tree = source.compile

def checkedLeaf {layers : Array (Array Nat)} {width : Nat} (start : Nat)
    (clauses : Array (Array Int)) (inside : start < layers.size-1)
    (checked : CheckedCNF layers width start clauses) (r : Relation (2^width))
    (same : r = compileLocal width checked.localCNF) : CheckedNode layers width :=
  ⟨start,0,.leaf start clauses inside checked,.leaf r,congrArg Tree.leaf same⟩

def checkedPad {layers : Array (Array Nat)} {width : Nat} (start : Nat)
    (outside : layers.size-1 ≤ start) (r : Relation (2^width)) (same : r = identity) : CheckedNode layers width :=
  ⟨start,0,.pad start outside,.leaf r,congrArg Tree.leaf same⟩

def OriginalTree.reindex {layers : Array (Array Nat)} {width start other h k : Nat}
    (hs : start = other) (hh : h = k) (source : OriginalTree layers width start h) :
    OriginalTree layers width other k := hh ▸ hs ▸ source

theorem OriginalTree.reindex_clauses {layers : Array (Array Nat)} {width start other h k : Nat}
    (hs : start = other) (hh : h = k) (source : OriginalTree layers width start h) :
    (source.reindex hs hh).clauses = source.clauses := by
  cases hs; cases hh; rfl

theorem cast_aligned {layers : Array (Array Nat)} {width start other h k : Nat}
    (hs : start = other) (hh : h = k) (source : OriginalTree layers width start h)
    (tree : Tree (2^width) h) (same : tree = source.compile) :
    (hh ▸ tree) = (source.reindex hs hh).compile := by
  cases hs; cases hh; exact same

def checkedJoin {layers : Array (Array Nat)} {width : Nat} (a b : CheckedNode layers width)
    (height : b.height = a.height) (consecutive : b.start = a.start+2^a.height) : CheckedNode layers width :=
  let right := b.source.reindex consecutive height
  let treeB : Tree (2^width) a.height := height ▸ b.tree
  have alignedB : treeB = right.compile := cast_aligned consecutive height b.source b.tree b.aligned
  ⟨a.start,a.height+1,.branch a.source right,join a.tree treeB,by
    change join a.tree treeB = join a.source.compile right.compile
    rw [a.aligned,alignedB]⟩

theorem checkedJoin_clauses {layers : Array (Array Nat)} {width : Nat} (a b : CheckedNode layers width)
    (height : b.height = a.height) (consecutive : b.start = a.start+2^a.height) :
    (checkedJoin a b height consecutive).source.clauses = a.source.clauses ++ b.source.clauses := by
  simp [checkedJoin,OriginalTree.clauses,OriginalTree.reindex_clauses]

theorem checkedJoin_occurrences {layers : Array (Array Nat)} {width : Nat} (a b : CheckedNode layers width)
    (height : b.height = a.height) (consecutive : b.start = a.start+2^a.height) (clause : Array Int) :
    (checkedJoin a b height consecutive).source.clauses.count clause =
      a.source.clauses.count clause + b.source.clauses.count clause := by
  rw [checkedJoin_clauses,List.count_append]

def CheckedNode.checkedTree {layers : Array (Array Nat)} {width : Nat} (node : CheckedNode layers width) : CheckedTree :=
  ⟨width,node.height,node.tree,by rw [node.aligned]; exact node.source.compile_valid⟩

def CheckedNode.decide {layers : Array (Array Nat)} {width : Nat} (node : CheckedNode layers width) : Bool :=
  OracleMachines.SourceInvariant.decision node.tree

theorem CheckedNode.decide_exact {layers : Array (Array Nat)} {width : Nat} (node : CheckedNode layers width)
    (layout : CheckedLayout layers width) :
    node.decide = true ↔ ∃ valuation, sourceCNFEval node.source.clauses.toArray valuation = true := by
  simp only [CheckedNode.decide,OracleMachines.SourceInvariant.decision,List.any_eq_true,List.mem_finRange,true_and]
  rw [node.aligned,← leaves_summary node.source.compile node.source.compile_valid,sequence_nonempty,
    node.source.paths_exact]
  exact node.source.satisfiable_exact layout

theorem CheckedNode.unsat_exact {layers : Array (Array Nat)} {width : Nat} (node : CheckedNode layers width)
    (layout : CheckedLayout layers width) :
    node.decide = false ↔ ¬ ∃ valuation, sourceCNFEval node.source.clauses.toArray valuation = true := by
  rw [← node.decide_exact layout]
  cases node.decide <;> decide

end OracleMachines.SourceNodes
