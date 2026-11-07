import OracleMachines.Hybrid
import OracleMachines.Decision

/-!
# Exact accumulated results

Every completed solve can be retained, including negative answers. The proof
assumes that a loaded cache has the invariant established by prior writes;
SQLite, serialization, and disk integrity remain outside the Lean kernel.
-/

namespace OracleMachines.SAT

def CacheExact (cache : Table) : Prop :=
  ∀ bits answer, (bits, answer) ∈ cache → (answer = true ↔ EncodedSAT bits)

theorem empty_cache_exact : CacheExact [] := by simp [CacheExact]

theorem cache_lookup_sound (cache : Table) (exact : CacheExact cache)
    (bits : Word) (answer : Bool) (found : lookup bits cache = some answer) :
    answer = true ↔ EncodedSAT bits := by
  induction cache with
  | nil => simp [lookup] at found
  | cons entry tail ih =>
    rcases entry with ⟨key, value⟩
    by_cases heq : bits = key
    · subst key
      have hv : value = answer := by simpa [lookup] using found
      subst value
      exact exact bits answer (by simp)
    · have ht : CacheExact tail := fun x b hx => exact x b (List.mem_cons_of_mem _ hx)
      exact ih ht (by simpa [lookup, heq] using found)

def remember (cache : Table) (bits : Word) : Table := (bits, solveEncoded bits) :: cache

theorem remember_exact (cache : Table) (exact : CacheExact cache) (bits : Word) :
    CacheExact (remember cache bits) := by
  intro key answer h
  rcases List.mem_cons.mp h with h | h
  · cases h
    exact solveEncoded_correct bits
  · exact exact key answer h

theorem remember_retains (cache : Table) (bits : Word) (entry : Word × Bool)
    (h : entry ∈ cache) : entry ∈ remember cache bits := List.mem_cons_of_mem _ h

def cacheStep (cache : Table) (bits : Word) : Bool × Table :=
  match lookup bits cache with
  | some answer => (answer, cache)
  | none => (solveEncoded bits, remember cache bits)

theorem cacheStep_correct (cache : Table) (exact : CacheExact cache) (bits : Word) :
    (cacheStep cache bits).1 = true ↔ EncodedSAT bits := by
  cases h : lookup bits cache with
  | none => simpa [cacheStep, h] using solveEncoded_correct bits
  | some answer => simpa [cacheStep, h] using cache_lookup_sound cache exact bits answer h

theorem cacheStep_exact (cache : Table) (exact : CacheExact cache) (bits : Word) :
    CacheExact (cacheStep cache bits).2 := by
  cases h : lookup bits cache with
  | none => simpa [cacheStep, h] using remember_exact cache exact bits
  | some answer => simpa [cacheStep, h] using exact

theorem cacheStep_retains (cache : Table) (bits : Word) (entry : Word × Bool)
    (h : entry ∈ cache) : entry ∈ (cacheStep cache bits).2 := by
  cases hl : lookup bits cache <;> simp [cacheStep, hl, remember, h]

/-- Only valid encodings permit interpreting a cached false bit as UNSAT. -/
theorem cache_lookup_unsat (cache : Table) (exact : CacheExact cache)
    (bits : Word) (valid : ValidEncoding bits) (found : lookup bits cache = some false) :
    EncodedUNSAT bits := by
  have h := cache_lookup_sound cache exact bits false found
  apply (valid_not_sat_iff_unsat bits valid).mp
  simpa using h.symm

end OracleMachines.SAT
