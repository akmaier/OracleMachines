import OracleMachines.LayeredProtocol
import Std.Data.HashMap.Lemmas
import Mathlib.Algebra.BigOperators.Group.Finset.Basic

/-! Exact incoming-reference accounting. The finite parent domain is a ghost
witness in Prop; neither the sum nor the domain is computed at runtime. -/
namespace OracleMachines.ReferenceCounts
open Lean OracleMachines.Layered

abbrev Nodes := Std.HashMap String (Json × CheckedTree)
abbrev Counts := Std.HashMap String Nat

def count (counts : Counts) (key : String) : Nat := counts[key]?.getD 0

def references (nodes : Nodes) (parent child : String) : Nat :=
  match nodes[parent]? with
  | none => 0
  | some (body,_) => ((children body).toOption.getD []).count child

def Exact (nodes : Nodes) (counts : Counts) : Prop :=
  ∃ parents : Finset String,
    (∀ parent, parent ∈ parents ↔ ∃ node, nodes[parent]? = some node) ∧
    ∀ child, count counts child = ∑ parent ∈ parents, references nodes parent child

theorem exact_empty : Exact {} {} := by
  refine ⟨∅,?_,?_⟩ <;> simp [count]

def increment (counts : Counts) (refs : List String) : Counts :=
  refs.foldl (fun acc key => acc.insert key (count acc key+1)) counts

theorem increment_exact (counts : Counts) (refs : List String) (key : String) :
    count (increment counts refs) key = count counts key + refs.count key := by
  induction refs generalizing counts with
  | nil => simp [increment]
  | cons child rest ih =>
    simp only [increment,List.foldl_cons]
    rw [← increment,ih]
    by_cases same : child = key
    · subst child; simp [count]; omega
    · simp [count,Std.HashMap.getElem?_insert,same]

/-- Successful decrement returns its exact arithmetic equation. Child occurrences
are processed in order, retaining the previous underflow rejection. -/
def decrement (counts : Counts) : (refs : List String) →
    Except String {next : Counts // ∀ key, count next key + refs.count key = count counts key}
  | [] => .ok ⟨counts,by intro key; simp⟩
  | child::rest => do
    if zero : count counts child = 0 then throw "Invalid native reference count"
    else
      let next ← decrement (counts.insert child (count counts child-1)) rest
      return ⟨next.val,by
        intro key
        have eq := next.property key
        by_cases same : child = key
        · subst child
          simp [count] at eq
          simp
          unfold count at zero ⊢
          omega
        · simpa [count,Std.HashMap.getElem?_insert,same,Ne.symm same,List.count_cons] using eq⟩

theorem exact_insert {nodes : Nodes} {counts : Counts} (prior : Exact nodes counts)
    (id : String) (node : Json × CheckedTree) (refs : List String)
    (fresh : nodes[id]? = none) (decoded : children node.1 = .ok refs) :
    Exact (nodes.insert id node) (increment counts refs) := by
  obtain ⟨parents,domain,eq⟩ := prior
  have absent : id ∉ parents := by simp [domain,fresh]
  refine ⟨insert id parents,?_,?_⟩
  · intro parent
    by_cases same : id = parent
    · subst parent; simp
    · simpa [Std.HashMap.getElem?_insert,same,Ne.symm same] using domain parent
  · intro child
    rw [increment_exact,eq,Finset.sum_insert absent]
    have unchanged : ∀ parent ∈ parents,
        references (nodes.insert id node) parent child = references nodes parent child := by
      intro parent member
      have different : id ≠ parent := by intro same; subst parent; exact absent member
      simp [references,Std.HashMap.getElem?_insert,different]
    rw [Finset.sum_congr rfl unchanged]
    simp [references,decoded,Except.toOption,Nat.add_comm]

theorem Exact.reference_le {nodes : Nodes} {counts : Counts} (prior : Exact nodes counts)
    (parent child : String) (node : Json × CheckedTree) (found : nodes[parent]? = some node) :
    references nodes parent child ≤ count counts child := by
  obtain ⟨parents,domain,eq⟩ := prior
  rw [eq]
  exact Finset.single_le_sum (f := fun parent => references nodes parent child)
    (fun _ _ => Nat.zero_le _) ((domain parent).mpr ⟨node,found⟩)

theorem Exact.zero_no_child {nodes : Nodes} {counts : Counts} (prior : Exact nodes counts)
    (child : String) (zero : count counts child = 0)
    (parent : String) (node : Json × CheckedTree) (found : nodes[parent]? = some node)
    (refs : List String) (decoded : children node.1 = .ok refs) : child ∉ refs := by
  have bound := prior.reference_le parent child node found
  simp [references,found,decoded,Except.toOption,zero] at bound
  exact List.count_eq_zero.mp bound

theorem exact_erase {nodes : Nodes} {counts next : Counts} (prior : Exact nodes counts)
    (id : String) (node : Json × CheckedTree) (refs : List String)
    (found : nodes[id]? = some node) (decoded : children node.1 = .ok refs)
    (zero : count counts id = 0)
    (subtracted : ∀ key, count next key + refs.count key = count counts key) :
    Exact (nodes.erase id) (next.erase id) := by
  obtain ⟨parents,domain,eq⟩ := prior
  have member : id ∈ parents := (domain id).mpr ⟨node,found⟩
  refine ⟨parents.erase id,?_,?_⟩
  · intro parent
    by_cases same : id = parent
    · subst parent; simp
    · simpa [Std.HashMap.getElem?_erase,same,Ne.symm same] using domain parent
  · intro child
    have unchanged : ∀ parent ∈ parents.erase id,
        references (nodes.erase id) parent child = references nodes parent child := by
      intro parent member
      have different : id ≠ parent := Ne.symm (Finset.mem_erase.mp member).1
      simp [references,Std.HashMap.getElem?_erase,different]
    rw [Finset.sum_congr rfl unchanged]
    have sum := Finset.sum_erase_add parents (fun parent => references nodes parent child) member
    have removed : references nodes id child = refs.count child := by simp [references,found,decoded,Except.toOption]
    change (∑ parent ∈ parents.erase id, references nodes parent child) + references nodes id child =
      ∑ parent ∈ parents, references nodes parent child at sum
    rw [removed,← eq] at sum
    have subtract := subtracted child
    by_cases same : id = child
    · subst child
      simp [count]
      omega
    · simpa [count,Std.HashMap.getElem?_erase,same] using Nat.add_right_cancel (subtract.trans sum.symm)

end OracleMachines.ReferenceCounts
