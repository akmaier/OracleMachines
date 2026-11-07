# Literature review of learned reasoning and oracle complexity

Review date: 7 November 2026. Draft assessed: `paper/bounded_domain_sat_and_amortized_reasoning.tex`, commit `1600c68`.

Revision status: the subsequent manuscript revision incorporates the closest
precedents and the Deolalikar/Wen discussion recommended below, with 15 additional
references. It also clarifies input-independent advice and decision-to-search
coverage; adds a finite-workload cache bound, an expected break-even proposition,
and a bounded-overhead proposition; and states the remaining algorithmic and
empirical questions with an evaluation protocol. The review below records the
assessment of the earlier draft; its revision recommendations are no longer a list
of wholly outstanding manuscript edits. Compact exact learning, practical savings,
and performance under memory limits or changing workloads remain unestablished
by this perspective.

A targeted priority check below assesses the reuse corollary and fixed-policy
savings result as they appeared in commit `42c17ee`. Its new references and
attribution have also been incorporated into the manuscript.

A further [publication-status reassessment](#publication-status-of-the-generalized-observations)
checks the generalized observations from commit `41d8e4d`. It adds five manuscript
references and records the new OpenAlex/SemOpenAlex search below.

The subsequent [induction audit](#inductive-expansion-proof-and-limitations)
records the new constructive expansion proof and its resource limitations,
added after commit `23ec82c`.

The literature contains substantially closer precedents than the initial review identified. In particular, Lin et al. (2021) already combine neural parameters, arbitrary preprocessing or oracle assistance, polynomial advice, computational limitations, and bounded-length lookup representations. Hertrich and Skutella (2023) explicitly distinguish uniform neural constructions from nonuniform existence when drawing consequences from NP-hardness. The broad connection between neural representations and complexity classes therefore needs to be presented as established literature. The draft can contribute a focused exposition of these distinctions for exact SAT, oracle terminology, certification, and amortized reuse; the search does not establish that this particular exposition is unique.

The widely reported failed proof identified by the author is Vinay Deolalikar's August 2010 claim that P differs from NP. It belongs in a discussion of the limits of inferring algorithmic complexity from representation or solution-space structure. It is not a learning-based proof of P=NP.

## Closest precedents

### Lin et al 2021

**Chu-Cheng Lin, Aaron Jaech, Xin Li, Matthew R. Gormley, and Jason Eisner. Limitations of Autoregressive Models and Their Alternatives. NAACL 2021, 5147–5173.** [Publication and corrected PDF](https://aclanthology.org/2021.naacl-main.405/) · [OpenAlex](https://openalex.org/W3171737424).

**Very close overlap.** Sections 2.3–2.4 allow parameters acquired by unrestricted computation or an oracle and relate compact parameter families to P/poly. Section 4.3 discusses bounded-length lookup with exponential storage and linear query time. Its weighted-language, scoring, and sampling theorems differ from exact SAT decision. Compare it directly with the introduction and Sections 3, 6, and 8. Checked printed pp. 5147–5150 and Section 4.3 in the corrected v2 PDF.

### Hertrich and Skutella 2023

**Christoph Hertrich and Martin Skutella. Provably Good Solutions to the Knapsack Problem via Neural Networks of Bounded Size. INFORMS Journal on Computing 35(5), 1079–1097.** Earlier AAAI 2021 version and 2020 preprint. [Publication](https://doi.org/10.1287/ijoc.2021.0225) · [Accepted manuscript](https://eprints.lse.ac.uk/123502/1/Provably_Good_Solutions_to_the_Knapsack_Problem_via_Neural_Networks_of_Bounded_Size.pdf) · [OpenAlex](https://openalex.org/W3032255069).

**Very close overlap with Section 8.** The subsection on uniformity explains that polynomial-size neural constructions computed uniformly in polynomial time would give polynomial-time algorithms for knapsack. It explicitly warns that P≠NP alone does not rule out the existence of polynomial-size neural networks without that uniformity condition. Its dynamic-programming networks provide a constructive example. Retain the draft's distinct bit-precision assumptions when comparing them. Checked accepted-manuscript pp. 6–7, headed “Uniformity and Lower Bounds Implied by NP-Hardness.”

### Balcazar Gavaldà and Siegelmann 1997

**José L. Balcázar, Ricard Gavaldà, and Hava T. Siegelmann. Computational Power of Neural Networks: A Characterization in Terms of Kolmogorov Complexity. IEEE Transactions on Information Theory 43(4), 1175–1183.** [Publication](https://doi.org/10.1109/18.605580) · [Author-hosted paper](https://people.cs.umass.edu/~binds/papers/1997_Balcazar_IEEETransInfoTheory.pdf) · [OpenAlex](https://openalex.org/W2099977515).

**Direct historical precedent for neural weights as computational information.** The authors characterize how information in real-valued weights affects recurrent-network power and relate polynomial-time models to advice classes. This establishes that neural representations, nonuniformity, and classical computational complexity were connected decades ago. Infinite-precision analog constants and polynomial-size finite parameter strings are different resource assumptions; the draft should explain that difference. Checked abstract, introduction, and advice discussion on pp. 1175–1177. This paper also explicitly connects its analysis to Karp–Lipton.

### Fortnow 2022

**Lance Fortnow. Fifty Years of P vs. NP and the Possibility of the Impossible. Communications of the ACM 65(1), 76–85.** Online publication 17 December 2021; January 2022 issue. [Publication](https://doi.org/10.1145/3460351) · [Author manuscript](https://lance.fortnow.com/papers/files/pvnp50.pdf) · [SemOpenAlex](https://semopenalex.org/work/W4200092783).

**Direct conceptual precedent for viewing practical learning through P-versus-NP.** The article discusses algorithms, machine learning, and hardware as routes to solving many difficult instances in practice, without resolving the worst-case question. Its “Optiland” discussion is relevant to the draft's motivation. It does not establish that an exact compact SAT oracle can be learned efficiently. Publisher metadata, abstract, and the author's description of the article were checked; this entry is a perspective-level comparison.

### Fortnow 2026

**Lance Fortnow. How Does Machine Learning Manage Complexity?** [arXiv:2604.07233](https://arxiv.org/abs/2604.07233) · [ECCC TR26-053](https://eccc.weizmann.ac.il/report/2026/053/).

**Very relevant recent preprint.** Section 5 of the original ECCC text explicitly motivates trained weights as nonuniform advice and distinguishes training from inference. Its mathematical framework concerns efficiently computable distributions and pseudorandomness, rather than exact SAT classification. This is a closer contemporary connection between machine learning and P/poly than Yu et al. The work is a preprint/report, not a verified journal publication in this review. The ECCC original was read; arXiv lists a revised v2 dated 3 November 2026, whose abstract was checked, but its full revised text was not available through the browser fetch.

### Speedup learning and the utility problem

**Steven Minton. Quantitative Results Concerning the Utility of Explanation-Based Learning. AAAI 1988.** [Proceedings paper](https://cdn.aaai.org/AAAI/1988/AAAI88-100.pdf).

Learning useful search-control knowledge already required accounting for the cost of testing and applying that knowledge. The paper directly studies whether cumulative savings outweigh the added costs. This is a historical antecedent of the draft's break-even inequality, not merely a general reference to machine learning. Use the proceedings source for the 1988 date: SemOpenAlex title matches contain inconsistent years and multiple versions.

**Prasad Tadepalli. A Theory of Unsupervised Speedup Learning. AAAI 1992.** [Paper](https://cdn.aaai.org/AAAI/1992/AAAI92-036.pdf) · [SemOpenAlex](https://semopenalex.org/work/W75224112).

The paper formalizes problem-solving performance improving with experience and distinguishes learning from supplied solutions from learning by solving problems. Its guarantees apply to specified domain structure, including serial decomposability; they are not unrestricted SAT guarantees.

**Prasad Tadepalli and Balas K. Natarajan. A Formal Framework for Speedup Learning from Problems and Solutions. JAIR 4, 445–475, 1996.** [Publication](https://doi.org/10.1613/jair.154) · [Author paper](https://web.engr.oregonstate.edu/~tadepall/papers/speedup-learning.pdf) · [OpenAlex](https://openalex.org/W1680127546).

This formal framework studies acquiring efficient problem-solving behavior from examples, using control rules and macro-operators, with constructive sufficient conditions. It makes the idea of learning as acceleration a longstanding theoretical topic. It is more specific than the draft's cache accounting and should be discussed alongside Khardon–Roth. Abstract and introductory framework checked; no claim is made here to have independently reverified all its learning theorems.

## Targeted priority check: reuse savings under either P-versus-NP hypothesis

**Question checked, 7 November 2026:** Is the claim that a fast retrieval or
certified prediction path can save computation, whether P=NP or P differs from
NP, already published?

**Assessment:** the underlying reuse principle and benefit-minus-overhead
criterion are established. The manuscript's cache identity is an elementary
specialization of memoization accounting. Its expected online savings have a
particularly close explicit predecessor in Minton's utility formula. Neither
adding a setup-cost break-even threshold nor observing that the derivation uses
no P-versus-NP hypothesis establishes novelty. The exact SAT notation and
certification assumptions remain useful for exposition. This search did not
locate a publication stating the identical SAT corollary with both alternatives
named, and cannot establish that none exists.

### Closest publications and the precise overlap

1. **Donald Michie (1968), “Memo” Functions and Machine Learning. Nature 218,
   19–22.** [Publication](https://doi.org/10.1038/218019a0) ·
   [Original scan](https://www.cs.utexas.edu/~hunt/research/hash-cons/hash-cons-papers/michie-memo-nature-1968.pdf).
   The original opening describes combining a computation procedure with stored
   input-output answers and adding each freshly computed result to the stored
   part. This directly precedes the “solve when unknown, retrieve when known”
   architecture. It supplies the mechanism, rather than our displayed cost identity.

2. **Steven Minton (1988), Quantitative Results Concerning the Utility of
   Explanation-Based Learning. AAAI, 564–569.**
   [Proceedings](https://cdn.aaai.org/AAAI/1988/AAAI88-100.pdf), Section 4.3,
   printed p. 566. Its explicit utility formula multiplies conditional savings
   by application frequency, then subtracts matching cost. This closely matches
   the structure of our expected online savings. Minton evaluates search-control
   rules; our certified successes avoid an entire baseline solve. The paper
   does not state our initial-cost threshold or SAT corollary.

3. **Nir Ailon, Bernard Chazelle, Kenneth L. Clarkson, Ding Liu, Wolfgang
   Mulzer, and C. Seshadhri (2011), Self-Improving Algorithms. SIAM Journal on
   Computing 40(2), 350–375.**
   [Publication](https://doi.org/10.1137/090766437) ·
   [Author preprint](https://arxiv.org/pdf/0907.0884), Theorems 1.1 and 1.3.
   For sorting and Delaunay triangulation under unknown product distributions,
   training supports expected limiting time governed by output entropy, with
   an O(n log n) worst-case bound. This is a constructive example of learning
   improving polynomial-time tasks. The introductory guarantees were checked;
   the complete proofs were not independently reverified.

4. **Smitha Milli, Falk Lieder, and Thomas L. Griffiths (2021), A Rational
   Reinterpretation of Dual-Process Theories. Cognition 217, 104881.**
   [Publication](https://doi.org/10.1016/j.cognition.2021.104881) ·
   [Published author-hosted PDF](https://cocosci.princeton.edu/papers/millirational.pdf).
   Section 3 charges action, reasoning, and metareasoning separately. Its models
   and simulations identify conditions favoring fast/slow systems. This is
   direct prior work on the efficiency rationale for dual-process arbitration;
   it concerns decision quality and computation, rather than exact SAT certification.

5. **Marianna Bergamaschi Ganapini et al. (2025), Fast, Slow, and Metacognitive
   Thinking in AI. npj Artificial Intelligence 1, 27.**
   [Publication](https://doi.org/10.1038/s44387-025-00027-5).
   SOFAI starts with a fast solver and uses metacognitive control to decide
   whether to invoke a slow solver. Its grid-based evaluation compares time and
   decision quality with individual solvers. Publisher-indexed architecture and
   results text and OpenAlex metadata were checked. This is an architectural
   and empirical precedent, not an exact SAT or full acquisition-cost theorem.

### Mapping the utility formula to our proposition

Our policy has certified success indicator H, baseline cost s, and fast-path
cost f. The identity

\[
\mathbb E[Hs]
=\Pr(H=1)\,\mathbb E[s\mid H=1]
\]

uses the right side as zero when success has probability zero. Thus
`delta = E[Hs] - E[f]` has the conditional-benefit-times-frequency-minus-overhead
structure already used in the utility literature. The specialization charges
the entire solve as avoided work on a certified success. Adding acquisition
cost C gives `E[baseline - hybrid] = Q delta - C`. This algebra explains the
break-even condition and does not provide an algorithm that achieves positive
delta.

The cache comparison makes an even weaker demand: count how many solves are
avoided for identical inputs and subtract actual cache costs. It is compatible
with polynomial or superpolynomial solver costs. A formal comparison with one
solver does not establish optimality against all algorithms, and a competing
solver could itself include memoization.

### The architectural claim and the narrower priority question

The author's intended conclusion concerns the rationale for the combined
architecture: **the benefit of acquiring reusable knowledge and selectively
invoking expensive reasoning does not depend on resolving P versus NP**. This
is a different priority question from whether memoization or a cost-benefit
identity is known. The earlier assessment establishes prior publication of
those components; it does not establish prior explicit publication of this
architectural conclusion.

A further targeted search combined variants of P=NP, P versus NP, System 1,
System 2, dual-process/dual-system architectures, metareasoning, bounded
rationality, and amortized reasoning. It did not identify a verified publication
that explicitly states and proves this architectural conclusion under both
alternatives. This is a search outcome, not evidence sufficient to claim first
publication. The present manuscript frames the point as a synthesis supported
by its unconditional cost comparisons.

Two additional primary sources help delimit the claim:

- **Vincent Conitzer (2008), Metareasoning as a Formal Computational Problem.**
  [AAAI workshop paper](https://cdn.aaai.org/Workshops/2008/WS-08-07/WS08-07-005.pdf).
  The section on implications for metareasoning systems explains how hardness
  of optimal computation selection can depend on P versus NP or P versus
  PSPACE, while actual workloads can have easier structure. Thus, global
  irrelevance of complexity separations to every aspect of the architecture
  would be too broad. The unconditional savings criterion is the narrower claim.

- **Xin Li (2026), The Two Dragons of Cognition: Recursive Condensation for
  Predictive Processing. Frontiers in Computational Neuroscience 20, 1778902.**
  [Publication](https://doi.org/10.3389/fncom.2026.1778902) ·
  [Full text](https://pmc.ncbi.nlm.nih.gov/articles/PMC13050847/).
  This published conceptual account connects memory-amortized inference,
  learned oracle-like responses, and computational complexity. Sections 2 and
  7 treat P differing from NP as a constraint; they do not establish our
  two-alternative conclusion. Its claimed application of Savitch's theorem
  requires separate scrutiny: that theorem gives a space simulation, not a
  polynomial-time retrieval or efficient-learning guarantee. Relevant passages
  were screened; its full mathematical and neurobiological account was not audited.

### What the P-versus-NP qualification adds

The publications above establish the component ideas without requiring a
resolution of P versus NP. This review did not locate their authors explicitly
stating our two-case SAT corollary. The conclusion that its derivation applies
under either hypothesis is **our interpretation of the unconditional cost
identity**, not a quotation or theorem attributed to those authors. In
particular, the polynomial-time tasks in Ailon et al. show why NP-hardness is
unnecessary for useful learned acceleration. This does not guarantee that a
particular SAT workload is faster under either hypothesis.

For broader complexity context, **Martin Avanzini and Ugo Dal Lago,
On Sharing, Memoization, and Polynomial Time**, appeared at
[STACS 2015](https://doi.org/10.4230/LIPIcs.STACS.2015.62) and in
[Information and Computation 261 (2018), 3–22](https://doi.org/10.1016/j.ic.2018.05.003).
They prove cost-model invariance and results on ramified recurrence. This is
related formal memoization literature, but not the same cross-query savings
identity. The abstract and STACS introduction/conclusion were checked.

A search also surfaced **Qi Wang et al. (29 October 2026), Does Scaling Toward
AGI Depend on What System-1 Lets System-2 Execute?**
[arXiv:2610.39497](https://arxiv.org/abs/2610.39497).
Its abstract describes selective expensive execution and conditional cost
savings. Only the abstract and submission record were screened. It is a recent
preprint, not used here as proof of the exact SAT result or as evidence of
peer-reviewed publication.

### Search record and implications for the manuscript

Targeted searches combined memoization, lookup overhead, amortized analysis,
speedup learning, utility, metareasoning, dual processes, and both spellings of
P=NP/P≠NP. Primary publications and author-hosted copies were then inspected.
SemOpenAlex exact-title queries returned 13 records, including duplicates and
misdated Minton records; the original AAAI proceedings establish 1988. The
SOFAI title was absent from that response, but its publisher text and direct
OpenAlex DOI lookup verify publication in 2025. The three direct OpenAlex
lookups for Ailon, Milli, and SOFAI all succeeded. Raw responses and the query
are saved in the evidence directory. Indexed dates and title matches alone
were not treated as mathematical evidence or exhaustive priority coverage.

The manuscript now attributes the expected-cost structure specifically to
Minton Section 4.3, adds Ailon et al. as a constructive polynomial-time
precedent, and discusses Milli et al. and SOFAI as fast/slow-arbitration prior
work. The appropriate contribution remains a perspective with explicit SAT
correctness and accounting assumptions. A new learning guarantee, a stronger
bound under realistic resource constraints, or a reproducible end-to-end
evaluation would require additional research.

## Deolalikar and the failure of the claimed separation

**Vinay Deolalikar. P is not equal to NP. Circulated manuscript, 6 August 2010.** [Archived original 66-page manuscript](https://wscor.win.tue.nl/woeginger/P-versus-NP/Deolalikar.pdf).

The manuscript attempts to connect descriptive complexity, least fixed-point logic, conditional independence in graphical models, and the structure of random k-SAT solution spaces. It aims to prove P≠NP through limitations on the distributions or dependencies associated with polynomial-time computation. Relevant parts of the archived original were inspected, including the synopsis and Chapters 2–4. The best-known technical criticisms refer to a later 102-page typesetting; page numbers must not be transferred between versions. The manuscript is a failed separation claim, not an accepted theorem or a learning-based construction of a SAT oracle.

**Neil Immerman's technical objections, published by Richard Lipton, 12 August 2010.** [Letter and discussion](https://rjlipton.com/2010/08/12/fatal-flaws-in-deolalikars-proof/).

Immerman identifies two central defects. An order-independent final answer does not require every intermediate fixed-point stage to be order-independent. Also, reducing attention to monadic fixed points does not preserve the general computational power being claimed without additional relations; those relations undermine the locality argument. Consequently, the restricted formalism in the argument does not capture all of P. This is a direct technical response by a descriptive-complexity expert, published online; it should not be described as a separately peer-reviewed journal refutation.

**Scott Aaronson's survey discussion.** [P=?NP, author-hosted survey](https://www.scottaaronson.com/papers/pvsnp.pdf) · [ECCC version](https://eccc.weizmann.ac.il/report/2017/004/).

Aaronson explains the additional XORSAT diagnostic: the solution-space characteristics invoked in the argument also arise in a problem decidable by polynomial-time linear algebra. The proposed structural argument therefore fails to isolate the computational difficulty of SAT. This corroborates the failure of the bridge from solution-space properties to unrestricted lower bounds. The survey's discussion of Deolalikar was checked; the full 110-page survey was not independently audited.

**Relevance to this draft.** The useful connection is methodological. A complicated space of solutions does not establish a lower bound against all algorithms. Conversely, a compact description of that space does not supply an efficient decision procedure. The SAT formula itself is already a compact description of all satisfying assignments. The draft should therefore require both representation bounds and an explicit evaluation algorithm, and should state that its constructions give upper bounds, not lower bounds. Its current finite-table and advice arguments survive these objections because their assumptions are explicit; citing Deolalikar does not turn them into a new separation argument.

Do not describe the claim as P=NP, as formally retracted by the author, or as a refuted learning theory. The supported description is a circulated P≠NP argument with documented fatal objections. It received substantial news coverage, consistent with the author's recollection. [Contemporary MIT CSAIL coverage](https://www.csail.mit.edu/news/p-vs-np-debate-heats).

## Wen and related learned-oracle claims

### Wen June 2010

**Han Xiao Wen. Mirrored Language Structure and Innate Logic of the Human Brain as a Computable Model of the Oracle Turing Machine.** [arXiv:1006.2495](https://arxiv.org/abs/1006.2495) · [OpenAlex](https://openalex.org/W1551696747).

**Close thematic precedent, unestablished proof claim.** The two-page manuscript explicitly links a model of brain organization, stored relations, learned recognition, oracle Turing machines, and a claimed P=NP consequence. Both pages were read. Independent diagnosis: the paper asserts efficient relation storage and recognition but does not supply a uniform polynomial-time SAT decider, a complete runtime proof, or a reduction demonstrating the required NP-hardness. It also conflates oracle and nondeterministic machines. Thus it does not establish P=NP. No specific external technical refutation of this manuscript was located; call it a claimed proof with these identified gaps, rather than attributing a formal refutation to someone else. Woeginger's catalogue lists it as entry 63; that listing is not an endorsement.

### Wen September 2010

**Han Xiao Wen. Knowledge Recognition Algorithm enables P = NP.** [arXiv:1009.0884](https://arxiv.org/abs/1009.0884) · [OpenAlex](https://openalex.org/W1646008629).

All three pages were read. The proof in Section 2 treats a deterministic transition function and a nondeterministic transition relation as enough to identify P and NP, without proving polynomial bounds or NP-completeness for the constructed language. Independent diagnosis: proving that one language lies in both P and NP cannot establish equality of the classes. The displayed equality between a language and two language classes is also not a valid inference. This is an especially useful contrast for the draft's emphasis on target correctness, acquisition cost, and uniformity. It is a preprint claim, not an accepted collapse theorem.

### The related 3SAT manuscript

**Xiaowen Han, David Zhu, and Cuifeng Zhou. 3-SAT Polynomial Solution of Knowledge Recognition Algorithm.** [arXiv:1009.3687](https://arxiv.org/abs/1009.3687) · [SemOpenAlex](https://semopenalex.org/work/W1936515665).

The record, abstract, and revision history were screened; the full algorithm was not audited. It proposes deciding SAT through iterative rejection of locally incompatible triples. A complete analysis would have to prove that surviving local possibilities always admit a globally consistent assignment; that implication cannot be assumed. Include it as a related unverified claim, without claiming a demonstrated counterexample to the complete published algorithm. The record lists 12 versions ending in December 2010.

## Additional established connections

| Work and source | Connection and scope |
| --- | --- |
| Moses and Tennenholtz, *Off-line Reasoning for On-line Efficiency*, IJCAI 1993; extended knowledge-base article, Artificial Intelligence 83(2), 229–239, 1996. [1993 paper](https://www.ijcai.org/Proceedings/93-1/Papers/069.pdf) · [1996 DOI](https://doi.org/10.1016/0004-3702(95)00015-1) | Explicitly studies offline work to reduce later reasoning cost over many queries. A direct ancestor of the resource-accounting perspective. |
| Selman and Kautz, *Knowledge Compilation and Theory Approximation*, JACM 43(2), 193–224, 1996. [Author bibliography](https://www.cs.cornell.edu/selman/papers/) · [SemOpenAlex](https://semopenalex.org/work/W2038897673) | Approximate compiled theories support useful reasoning with a different representation. Distinguish approximation guarantees from exact SAT lookup. Bibliographic screening and citation trail, rather than a full proof audit, support this entry. |
| Cadoli, Donini, Liberatore, and Schaerf, *Preprocessing of Intractable Problems*, 2002. [Publication](https://doi.org/10.1006/inco.2001.3043) | Formal compilability theory is the established framework for preprocessing and online complexity under representation constraints. Already added to the draft. |
| Darwiche and Marquis, *A Knowledge Compilation Map*, JAIR 2002. [Paper](https://arxiv.org/abs/1106.1819) | Succinctness and supported polynomial-time queries are separate dimensions. Compiling one knowledge base differs from tabulating all SAT instances up to a bound. |
| Khardon and Roth, *Learning to Reason*, JACM 1997. [Paper](https://homes.luddy.indiana.edu/rkhardon/PUB/jacm97-l2r.pdf) | Explicitly integrates acquisition, knowledge representation, environment, and later efficient reasoning. Already added to the draft. |
| Juba, *Implicit Learning of Common Sense for Reasoning*, IJCAI 2013. [Publication](https://ijcai.org/proceedings/2013/144) | Efficiently combines partial data and reasoning through implicit learning under PAC semantics. Its guarantees are distributional and proof-system dependent, unlike total exact SAT decision. |
| Siegelmann and Sontag, *Analog Computation via Neural Networks*, Theoretical Computer Science 131, 331–360, 1994; and *On the Computational Power of Neural Nets*, JCSS 1995. [Author research overview](https://groups.cs.umass.edu/binds/analog-neural-networks-analog-computational-power/) · [1995 DOI](https://doi.org/10.1006/jcss.1995.1013) | Fundamental computation results depend on weight and resource assumptions. The 1995 work is already cited; the 1997 advice characterization deserves its own treatment. |
| Šíma and Orponen, *General-Purpose Computation with Neural Networks: A Survey of Complexity Theoretic Results*, Neural Computation 15(12), 2727–2778, 2003. [Institutional record](https://research.aalto.fi/en/publications/general-purpose-computation-with-neural-networks-a-survey-of-comp/) | A taxonomy of architectures, time models, state types, weights, and network families. Useful to avoid treating all neural models as one complexity model. Abstract and metadata screened. |
| Aaronson, *Oracles Are Subtle But Not Malicious*, CCC 2006; preprint 2005. [Publication](https://doi.org/10.1109/CCC.2006.32) · [Preprint](https://arxiv.org/abs/cs/0504048) | Connects exact circuit learning, NP-oracle queries, and relativization. It is not a theorem that learning implements an arbitrary oracle. |
| Xu, Hutter, Hoos, and Leyton-Brown, *SATzilla: Portfolio-based Algorithm Selection for SAT*, JAIR 32, 565–606, 2008. [Paper](https://new.aaai.org/Papers/JAIR/Vol32/JAIR-3214.pdf) | Learned predictions select solvers per instance. It explicitly requires predictive overhead to be offset by solving gains. A practical antecedent for evaluating hybrid costs. |
| Selsam et al., *Learning a SAT Solver from Single-Bit Supervision*, ICLR 2019; and Selsam and Bjørner, *Guiding High-Performance SAT Solvers with Unsat-Core Predictions*, SAT 2019. [NeuroSAT](https://arxiv.org/abs/1802.03685) · [NeuroCore](https://arxiv.org/abs/1903.04671) | Empirical learning and exact-search guidance supply concrete implementations. They do not give all-instance polynomial-time SAT guarantees. |
| Merrill and Sabharwal, *The Expressive Power of Transformers with Chain of Thought*, ICLR 2024; preprint 2023. [Paper](https://arxiv.org/abs/2310.07923) | Relates intermediate decoding steps to expressivity. Polynomial-step characterizations require the paper's precise transformer and normalization assumptions. It supports explicit accounting for reasoning length. |
| Michie (1968), Gershman and Goodman (2014), Stuhlmüller et al. (2013), Yu et al. (2024). [Memoization](https://doi.org/10.1038/218019a0) · [Cognitive inference](https://web.stanford.edu/~ngoodman/papers/amortized_inference.pdf) · [Stochastic inverses](https://proceedings.neurips.cc/paper/2013/hash/7f53f8c6c730af6aeb52e66eb74d8507-Abstract.html) · [Distillation](https://arxiv.org/abs/2407.06023) | Established reuse and distillation mechanisms. Yu et al. supports distillation; it does not supply the oracle-machine or P-versus-NP analysis. |

## Other failed arguments and resource cautions

**Norbert Blum, A Solution of the P versus NP Problem, 2017.** [Author withdrawal, arXiv v2](https://arxiv.org/abs/1708.03486v2). The author explicitly withdrew the claimed separation and stated that the proof was wrong. This concerns extending monotone-circuit approximation arguments to nonmonotone circuits, rather than learned advice. The current v3 has a different title and purpose; cite the version that actually records the withdrawal. This Norbert Blum is distinct from Avrim Blum, coauthor of the neural-network training-hardness paper cited in the draft.

**Hemaspaandra, Murray, and Tang, Barbosa, Uniform Polynomial Time Bounds, and Promises, 2011.** [Technical report](https://arxiv.org/abs/1106.1150). A direct critique of a different claimed separation, identifying a uniformity failure and a change in the meaning of P and NP. This is a useful methodological citation for the draft's quantifier discipline; it is not the famous Deolalikar case.

**Memcomputing claims and their specific critique.** [Aaronson's 2015 response](https://scottaaronson.blog/?p=2212) identifies frequency resolution and signal-strength costs in the analog subset-sum proposal it addresses. This is a relevant resource-accounting caution, but it does not justify declaring every later digital memcomputing implementation refuted. It is not the proof the author recalled and need not receive extensive space in the manuscript.

**Rass et al., Computer-Aided Verification of P/NP Proofs: A Survey and Discussion, IEEE Access, 2024.** [Publication](https://doi.org/10.1109/ACCESS.2024.3355540). Its bibliography includes both Deolalikar and Wen's June manuscript. It is a catalogue and discussion of proof attempts, not an endorsement of those claims or a complete formal refutation of every item.

## Implications for positioning and revision

1. **Make Lin et al. the closest explicit comparison.** The combination of bounded-length lookup, unrestricted acquisition, compact parameters, and P/poly cannot be presented as an unexplored general connection. The draft differs by organizing elementary exact SAT constructions, finite-oracle elimination, and certified fallback into one exposition.
2. **Add Hertrich–Skutella and Balcázar–Gavaldà–Siegelmann beside the advice proposition.** Cite the former for the explicit uniformity warning and the latter for the older neural/advice connection. Specify finite parameter bit strings versus ideal real constants.
3. **Place resource accounting in the speedup-learning and utility literature.** Minton and Tadepalli–Natarajan already ask whether learned knowledge makes future problem solving cheaper, including overhead. A break-even identity alone is not a new research result.
4. **Use Fortnow's 2022 article and 2026 preprint to situate the modern motivation.** Label the latter as a preprint and avoid treating its probability-distribution theorems as exact SAT decision results.
5. **Add a short cautionary historical discussion of Deolalikar.** Explain the failed inference from restrictions on a particular formalism or solution-space description to limits on all polynomial-time computation. Do not imply that the draft repairs or validates his separation claim.
6. **Mention Wen in a clearly labeled discussion of claimed learned oracles.** There is a close thematic precedent, with concrete missing proof obligations. Distinguish this independent diagnosis from an externally documented refutation.
7. **Keep the contribution claim narrow and positive.** The supported contribution is a focused perspective explaining how finite-domain compilation, uniformity, oracle access, and certification constrain interpretations of learned reasoning. No novel theorem or priority for that entire synthesis is established by this review.

A possible contribution paragraph is:

> Building on work on speedup learning, knowledge compilation, neural advice, and the computational limitations of learned models, this perspective organizes the resource assumptions behind learned reasoning for bounded-domain SAT. It contrasts finite tabulation, fixed oracle access, and nonuniform model families, and uses exact certification to separate correctness from computational savings. The elementary constructions serve to expose these assumptions and clarify the scope of the resulting complexity conclusions.

## Search scope and evidence

The review used SemOpenAlex's public SPARQL endpoint for exact-title matching, backward citation traversal, and selected forward citation traversal. Three title-query batches returned **45 distinct work records**, including duplicate versions of publications and unrelated papers sharing generic titles. These records are not 45 independently validated papers. Backward queries returned **414 citation edges** from eight selected records. A title-filtered forward query returned **74 edges** from three records. Incoming citations to the two Wen seed records returned **two edges**. Candidate titles were screened, and the closest sources were checked at the passage or section level noted above.

The direct OpenAlex search endpoint rejected the query because the shared anonymous-IP daily budget was below the search cost. Individual-work requests succeeded for **six central records**, whose complete metadata responses are saved. Thus the review combines direct OpenAlex metadata with actual search and graph traversal through the OpenAlex-derived SemOpenAlex service. The graph is not guaranteed to contain recent works or all citations: Fortnow's 2026 paper was found through arXiv/ECCC, not the title-match batches. No absence of a graph match is used as evidence that a work does not exist.

Other sources were arXiv, ECCC, ACL Anthology, AAAI/IJCAI proceedings, publisher metadata, institutional and author repositories, DBLP bibliographic records, Woeginger's historical catalogue, and primary technical commentary. Web searches included combinations of P=NP/P≠NP with preprocessing, precomputation, lookup, neural networks, learning, oracle, refutation, and withdrawal, followed by searches for named works and authors. The work did not run independent native searches inside every commercial scholarly database; publisher pages were reached through web search and citation links.

All SPARQL queries, raw graph responses, the direct OpenAlex responses, and the quota rejection are under [evidence/2026-11-07](evidence/2026-11-07/). [Supplementary BibTeX](related-work.bib) supplies the main newly identified references. The review is a targeted literature assessment, not a proof of bibliographic exhaustiveness. Publication identity and status were checked separately from graph labels; in particular, ambiguous generic P≠NP title matches were not assigned to Deolalikar.

## Detailed argument audit and scope beyond NP

**Audit date: 7 November 2026. Baseline: commit `2d11d92`.** This audit checks
every formal statement and its proof, the surrounding cost estimates, and the
proposed extension beyond NP. The accompanying revision repairs the setup-cost
omission below and generalizes the reuse and certified-policy statements. This
is a mathematical review, not machine-checked verification or an independent
reproof of every cited external theorem.

**Assessment.** No contradiction or fatal flaw was found in the central reuse
identity, finite-domain argument, or advice implication under their explicit
assumptions. One cost omission required correction. Several interpretations
would go beyond what the arguments prove: guaranteed speedup for every workload,
cheap verification for arbitrary hard problems, efficient optimal arbitration,
or effective acquisition for an undecidable language. The revised manuscript
rules out these readings explicitly.

### Findings and corrections

1. **Setup cost was missing from the first cache bound.** Lemma 9.1 called its
   quantity total runtime but began from an empty cache without charging setup.
   The later reuse corollary did charge setup. The lemma and both its average
   and distributional consequences now include `C`. For example, one distinct
   query with solving cost 1, dictionary cost 1, and setup cost 10 has total cost
   12. The earlier displayed bound would give 2 if interpreted end to end.
   It was valid only as an online bound with setup excluded. The revision makes
   the accounting consistent.
2. **The reuse proof uses no NP-specific premise.** Corollary 9.2 now quantifies
   over any decidable language and any finite sequence of finite binary inputs.
   It uses actual non-solving work `L_Q` and optional per-query bounds `c_i`.
   No fixed maximum input length or polynomial solver bound is needed. The
   finite-domain result remains a specialization. Solver invocations start
   from the same state, the cache starts empty, and answers are retained.
3. **Expectations need an extra condition on unbounded domains.** Proposition
   10.2 now requires finite expected baseline and fast-path costs. Previously
   the finite domain and terminating procedures supplied these automatically.
   For an unbounded counterexample, let `Pr(X = 0^n) = 2^-n` for `n >= 1`, and
   let a deliberately slow decider cost `2^n` on `0^n`. Every run terminates,
   while its expected cost is infinite. If a sound fast policy answers all
   those inputs at finite expected cost, writing `mu - delta` would produce
   the undefined subtraction infinity minus infinity. The realized finite
   sequence identity remains valid.
4. **Simulation from a supplied state is not uniform acquisition.** Section 8
   now says explicitly that its polynomial update simulation is given the
   initial state. Obtaining that state still requires its own cost and
   uniformity argument. Polynomial updates cannot erase a nonuniform advice
   assumption or unpaid training computation.
5. **The abstraction charges all extra work.** Setup or insertion pays for
   allocation and initialization. Lookup includes input reading, exact key
   comparison, bookkeeping, and delivery of the answer bit. Random-access
   overhead requires sufficient address space; sequential-tape lookup can
   depend on total storage. The comparison is additive work, with the same
   solver cost on every miss. Resource contention, a warm-started baseline,
   or changes to fallback search require a new comparison.

### Check of the mathematical arguments

The identifiers below are LaTeX labels where available; they remain stable if
section numbering changes.

| Argument | Audit and necessary assumptions |
| --- | --- |
| Direct addressing (`lem:table`) | For length `n`, `2^n - 1 + val(x)` covers exactly the interval `[2^n - 1, 2^(n+1) - 2]`. The intervals partition the required addresses, including the empty string at zero. Linear bit work suffices to form the address. Fast retrieval depends on the explicit initialized random-access model; it is not a claim about free access on a sequential tape. |
| Table construction and witnesses | At length `n` there are `2^n` strings and at most `2^n` assignments per well-formed formula. Summing yields the stated upper bound `O(4^N poly(N))`, not a lower bound. One assignment per positive entry fits in `O(N 2^N)` bits. Enumerating all assignments has a separate output cost. |
| Finite restrictions (`lem:restriction`) and finite NP-hardness corollary | A trie with a rejecting sink gives a fixed finite automaton for every subset of the fixed finite domain. Runtime is linear in the query length, while machine description size depends on the domain. Composition with an NP-hardness reduction would put all of NP in P. The new generalization to any class containing REG follows from the same two inclusions. Neither argument identifies the unrestricted classes. |
| Oracle elimination (`lem:eliminate`) | Polynomially many polynomial-length queries to a fixed polynomial-time decider have polynomial aggregate cost. Replacing queries on each nondeterministic branch preserves acceptance. A finite oracle and a length-indexed family of tables are different resources. |
| Dense and recurrent neural costs | The arithmetic counts hold for the specified architecture, prescribed epochs, available labels, bounded-cost activations, and stated arithmetic precision. They do not bound the number of iterations needed to learn an exact model. Recurrent steps, generated tokens, label acquisition, and the actual bit lengths remain separate charged resources. |
| ReLU table (`lem:relu`) | The preactivation is `1 - HammingDistance(x,u)` on the Boolean cube. Each selected unit is exactly its vertex indicator; at most one is nonzero. Input weights take one bit, biases take logarithmically many bits, and dense serialization gives the stated description bound. Hidden partial sums have magnitude `O(N+1)` and readout sums are at most one. Addresses and loop counters are explicitly outside the numerical-intermediate bound. Empty accepting sets and `N=0` are covered. |
| Advice and uniform construction (`prop:advice`) | One shared finite string per input length is polynomial advice. A uniform polynomial constructor followed by the evaluator is a polynomial decider. Advice for all possible reduction-output lengths can be concatenated within a polynomial bound. The Karp-Lipton consequence is an attributed external theorem, not reproved here. P differing from NP alone does not exclude nonuniform polynomial-size SAT advice. |
| Decision to witness | Each self-reduction query preserves a satisfying extension. At most one query per variable is needed after a positive initial answer. The table or advice must cover the intermediate encoding lengths; merely covering the original input length is insufficient. This returns one witness. |
| Cache amortization (`lem:cache`) and occurrence expectation | Each distinct input is solved once under no eviction. Include setup as corrected above. Under i.i.d. queries, the chance of seeing `x` by query `Q` is `1-(1-p_x)^Q`. No independence of occurrence indicators for different strings is needed. The vanishing solving contribution holds at fixed finite domain with enough memory; it is not a joint limit in domain size and query count. |
| Reuse savings (`cor:reuse-savings`) | Subtract `C + L_Q + sum_distinct s(x)` from `sum_distinct m_Q(x)s(x)`. This proves an exact identity against a specified restarted solver, not optimality among all algorithms. Its sufficient condition uses an upper bound on overhead; failure of that sufficient condition does not itself prove a loss. Actual avoided work versus actual overhead is necessary and sufficient. |
| Polynomial scaling example | For one repeated input, dividing by `Q s_n` gives `C_n/(Q s_n) + ell_n/s_n + 1/Q`. Under the stated bounds and `Q=n`, this tends to zero. The assumptions describe a selected solver and family. They do not prove that SAT requires that solving cost or that every language admits this advantage. |
| Certified fallback (`prop:soundness`) | Each accepted fast answer is sound; all other inputs reach a terminating exact solver. Fast-path termination is essential and includes certificate generation and checking. The proof is independent of the decision language. A timeout on the fallback would instead allow incomplete answers. |
| Negative certificates | Checking a proof in polynomial time in its combined input and proof length does not bound that proof length. The cited Cook-Reckhow equivalence concerns existence of a polynomially bounded proof system, not every proof system or an efficient algorithm for finding proofs. |
| Fixed-policy savings (`prop:savings`) | The per-query cost is exactly `f(x) + (1-H(x))s(x)`. Linearity of expectation gives the claimed total under fixed marginals; queries need not be independent. The revised finite-expectation conditions justify subtraction. A history-dependent policy or online updates cannot simply reuse the same fixed `delta`. |
| Budgeted overhead (`prop:overhead`) | Each query costs at most its unchanged baseline cost plus the full fast-path and update budgets. Summing gives the additive bound. It implies neither a speedup nor a universal multiplicative ratio and assumes the baseline resources remain available. |
| Effective finite tables (`prop:effective-tables`, added) | A decider constructs every finite table by enumeration. Conversely, a total uniform constructor and evaluator decide any input by constructing the table at that input's length. This proves equivalence with decidability, with no resource bound. It pinpoints why mere finite representability of an undecidable language does not make it learnable or computable. |

### What extends beyond NP

The exact cost identity applies to every decidable language, including complete
problems for PSPACE, EXPTIME, and EXPSPACE. All first solves remain charged.
No complexity-class equality or inequality occurs in the subtraction. A larger
class does not itself imply a more favorable workload or a cheaper cache.

The finite-restriction equality is broader still: every language class containing
REG realizes every subset of a fixed finite binary domain. An individual
undecidable language has finite restrictions too, but a uniform computable
constructor for all of them would decide the original language. The new
proposition supplies the exact converse as well.

Certification does not transfer for free. A universal polynomial-length,
deterministically polynomial-checkable positive certificate system puts its
language in NP. Such systems for both answers put it in NP intersect coNP.
Applied to a PSPACE-complete language, the first condition implies PSPACE=NP.
The manuscript permits longer certificates or coverage of selected inputs and
charges generation and checking. Prior exact cache entries need not be
recertified by a short proof if their provenance and storage are trusted.

Uniform polynomial acquisition and evaluation for an EXPTIME-complete language
would put EXPTIME in P, contrary to the time hierarchy theorem. Thus the reuse
accounting also applies where the impossibility of a polynomial-time uniform
decider is already established, independently of P versus NP. It provides
workload-specific savings, not such a decider.

For function problems, the same accounting can be formulated for a fixed exact
solver, but all output copying, storage, and delivery must be included. A cached
long output is not a constant-cost decision bit. The revised manuscript states
this limit without claiming a new function-complexity theorem.

The primary background checks used Michael Sipser's MIT course materials:
[Lecture 18, PSPACE-completeness](https://ocw.mit.edu/courses/18-404j-theory-of-computation-fall-2020/resources/lecture-18-pspace-completeness/)
and [Lecture 22, hierarchy results and oracles](https://ocw.mit.edu/courses/18-404j-theory-of-computation-fall-2020/50cb369d1be3c7fbe0886e318aea13c2_MIT18_404f20_lec22.pdf),
particularly Lecture 22 slides 2-4. These support the standard class definitions,
TQBF completeness, and hierarchy consequences; the generalized reuse proof and
effective-table equivalence are given directly in our manuscript.

### Scope of the architectural claim

The statement that P versus NP is irrelevant to every aspect of a dual-process
architecture would be too strong. The revised claim concerns validity of the
accounting criterion and the possibility of conditional savings. Acquiring
knowledge, producing certificates, and finding an optimal policy have their own
complexity constraints. Conitzer's
[2008 paper](https://cdn.aaai.org/Workshops/2008/WS-08-07/WS08-07-005.pdf),
especially printed page 31, gives an explicit published reason to retain this
qualification. Its discussion of NP-hard and PSPACE-hard optimal metareasoning
was checked again and is now cited in the manuscript. No new priority claim
follows from extending an elementary accounting identity to more language classes.

### Revision checks

The revised source contains 12 proof environments, 45 displayed equation
environments, 51 unique labels, and 41 bibliography entries. All internal
references and citation keys resolve. In addition to the argument review,
finite sanity checks covered direct addresses through maximum length 10;
5,461 pairs of ReLU vertices through length 6; all 278 Boolean functions on
domains of 0 through 3 input bits; and 1,093 cache streams over three inputs
through six queries, with nonzero setup and state-dependent overhead. Exact
rational enumeration verified the occurrence expectation. Twenty-four
fixed-policy/cost combinations also checked the expected-cost formula with
perfectly correlated queries, confirming that independence is unnecessary.
These small cases check arithmetic and edge conditions; they are not substitutes
for the general proofs. The revised LaTeX builds without warnings.

## Publication status of the generalized observations

**Question checked, 7 November 2026:** Are the observations extending reuse
beyond NP, separating finite existence from effective construction, and limiting
the P-versus-NP claim already established in the literature?

**Assessment:** yes at the level of the mathematical mechanisms. Some have direct
published algorithmic precedents; others are elementary consequences of standard
definitions and theorems. We found no basis for claiming a new theorem from their
combination. The manuscript now makes this attribution explicit in Section 11
and adds a closely related dual-process thesis in Section 12. Its defensible
contribution remains a focused synthesis of resource accounting for learned
reasoning.

| Observation | Prior work and status | Consequence for this draft |
| --- | --- | --- |
| Reusing an exact answer can help any terminating solver. | [Michie's memo functions](https://doi.org/10.1038/218019a0); [Goré and Nguyen's global caching](https://doi.org/10.1007/s10817-011-9243-0). | Established reuse mechanism; our identity is elementary accounting. |
| Net savings require avoided work to repay overhead. | [Minton's utility analysis](https://cdn.aaai.org/AAAI/1988/AAAI88-100.pdf), examined in the earlier priority check. | Adding setup cost gives an elementary break-even condition. |
| The same criterion applies under either P-versus-NP outcome. | Memoization and utility accounting use actual costs; [self-improving algorithms](https://doi.org/10.1137/090766437) already accelerate polynomial-time tasks. | The hypothesis-free applicability is a consequence of these mechanisms, even without identical wording in an earlier paper. |
| Finite answer tables exist without an effective uniform constructor. | [Turing's computable sequences](https://doi.org/10.1112/plms/s2-42.1.230). | The effective-table equivalence reformulates decidability. |
| Uniform polynomial construction and evaluation cannot solve every EXPTIME-complete input. | [Hartmanis and Stearns's hierarchy foundation](https://doi.org/10.1090/S0002-9947-1965-0170805-7), with the modern consequence in [Sipser's Lecture 22](https://ocw.mit.edu/courses/18-404j-theory-of-computation-fall-2020/50cb369d1be3c7fbe0886e318aea13c2_MIT18_404f20_lec22.pdf). | Standard hierarchy consequence, independent of P versus NP. |
| Short deterministic certificates and optimal control need additional assumptions. | The NP verifier definition and [Conitzer's metareasoning analysis](https://cdn.aaai.org/Workshops/2008/WS-08-07/WS08-07-005.pdf). | Reuse does not supply cheap verification or an efficiently computable optimal policy. |

### Newly incorporated references and checked passages

**Goré and Nguyen (2013), ExpTime Tableaux for ALC Using Sound Global Caching.**
Journal of Automated Reasoning 50(4), 355–381; online 2011.
[Publisher](https://doi.org/10.1007/s10817-011-9243-0) ·
[Author manuscript](https://users.cecs.anu.edu.au/~rpg/Publications/ALC/sound-global-caching.pdf).
Checked the introduction, Remark 1.1, Theorem 5.3, and Theorem 6.2 with its
complexity argument. This is a direct published EXPTIME-complete example.
Remark 1.1 corrects an error in the 2007 workshop algorithm; we cite the journal
version. This is internal subproblem reuse, not a learned cross-query system.

**Ferrara, Liberatore, and Schaerf (2007), Model Checking and Preprocessing.**
AI*IA 2007, LNCS 4733, 48–59.
[Publisher](https://doi.org/10.1007/978-3-540-74782-6_6).
Checked publisher metadata and abstract. The paper studies repeated queries
with a preprocessed model or formula and polynomial-size output. The full
chapter was not obtained. Accordingly, the manuscript cites its problem setting
without restating a particular lower-bound theorem or omitting its assumptions.

**Turing (1937), On Computable Numbers, with an Application to the
Entscheidungsproblem.** Proceedings of the London Mathematical Society
s2-42(1), 230–265.
[Publication](https://doi.org/10.1112/plms/s2-42.1.230) ·
[Reprint](https://people.math.ethz.ch/~halorenz/4students/Literatur/TuringComputableNumbers.pdf).
Checked the original article's Sections 1–2, especially printed pp. 232–233.
This supports the sequence-computability foundation. Our finite-table statement
is a reformulation using the characteristic sequence in length-lexicographic
order, not a theorem attributed verbatim to Turing. The bibliography follows
the publisher's 1937 date.

**Hartmanis and Stearns (1965), On the Computational Complexity of Algorithms.**
Transactions of the American Mathematical Society 117, 285–306.
[Publisher PDF](https://www.ams.org/journals/tran/1965-117-00/S0002-9947-1965-0170805-7/S0002-9947-1965-0170805-7.pdf).
Checked the introduction and Section IV, particularly Theorem 9, pp. 298–299.
This supplies historical attribution for the time hierarchy. We retain Sipser
for the modern language-class formulation P strictly contained in EXPTIME;
we do not attribute a later sharpened simulation bound to the original paper.

**Riedmiller (2025), Exploring the Computational Necessity of Dual Processes
for Intelligence.** MSc thesis, University of Amsterdam, ILLC MoL-2025-18.
[Institutional text](https://eprints.illc.uva.nl/2389/1/MoL-2025-18.text.pdf).
Checked the abstract and Chapter 4, especially Sections 4.2–4.3, printed
pp. 57–63. Its bounded-reasoning discussion explicitly invokes P≠NP and
ETH/SETH. This is close thematic prior work, clearly labeled a thesis. We do
not adopt its broader necessity claim or treat its hardness discussion as our
conditional savings result.

### Additional sources and version limits

Ferrara, Liberatore, and Schaerf's related
[2010 preprint](https://arxiv.org/abs/1012.3018), *On the Size of Data Structures
Used in Symbolic Model Checking*, was checked in Sections 2.3 and 3.2.
Theorems 6–7 make representation-size obstructions conditional on class
separations; the following paragraph explicitly rejects an unconditional
version. Such bounds must not be paraphrased as proving that preprocessing
never saves work. OpenAlex links this preprint to the authors'
[2016 IEEE article](https://doi.org/10.1109/TC.2015.2512872), *The Size of BDDs
and Other Data Structures in Temporal Logics Model Checking*. Its publication
metadata and institutional abstract were verified, but its deposited final
text returned HTTP 403. We therefore do not claim to have checked the final
article's theorem wording or numbering.

The citation graph also returned later global-caching work on hybrid PDL,
SHIQ, and SHOQ, and work on preprocessing limits and average-case compilability.
These are discovery leads, not independently audited theorems in this review.
Keyword searches also returned proposed P-versus-NP proofs and philosophical
preprints. Their metadata or titles do not establish either a complexity
separation or priority for the cost identity.

### Search coverage and reproducibility

This pass saved 12 SemOpenAlex exact-title records and 50 filtered incoming
citation edges from the global-caching and preprocessing seeds. Records include
duplicates and online/journal versions. Five additional direct OpenAlex work
lookups verified publication metadata. Six OpenAlex searches each returned
10 candidates: global caching; model checking preprocessing; dual process
computational complexity; memoization computational complexity; quoted
System 1/System 2/P=NP terms; and the thesis title. All 60 returned titles
were screened; only relevant primary sources were examined further. Broad
search totals include many irrelevant results and are not counts of relevant
papers. The thesis did not appear among its query's first ten results and was
verified through its institutional repository instead.

The earlier anonymous OpenAlex quota failure did not recur in this pass.
Primary-source discovery also used publisher pages, arXiv, author repositories,
and targeted web queries. The saved queries, responses, URLs, source-check
notes, and checksums are in
[the evidence directory](evidence/2026-11-07/manifest.json).
This is a targeted follow-up search, not an exhaustive priority proof. We did
not verify an earlier publication with exactly our combined formulation under
both P-versus-NP alternatives. That absence does not establish novelty: the
underlying deductions already follow from established results.

### Checks on this revision

The 12 proof environments, 45 equation environments, and all lemma, proposition,
and corollary statements are unchanged from the audited commit. All 51 labels
and 46 bibliography entries resolve. The 22-page PDF builds without LaTeX
warnings; all pages were visually inspected, with the revised Sections 11–12
also checked at full page size. The evidence manifest verifies 41 saved files,
including all unchanged earlier records, and lists 14 direct OpenAlex work
lookups across the review passes.

## Inductive expansion proof and limitations

The manuscript now gives the proposed induction explicitly in Section 12,
*Inductive expansion and its resource limits*. It adds three formal results.
They refine the earlier effective-table and reuse statements; no new complexity
separation, learning guarantee, or publication-priority claim is made.

| Result | What the proof establishes | Additional obligation or limitation |
| --- | --- | --- |
| Proposition 12.1: inductive exact expansion | The base table answers the empty string; each step appends exact answers for the next length. Every finite stage terminates and preserves old answers. | A terminating exact decider supplies all new labels. The induction does not bound its cost or establish that learning alone finds those labels. |
| Corollary 12.2: uniformly bounded expansion | Fixed polynomial bounds on every stage and on evaluation give one polynomial-time decider. | Costs must be polynomial in the stage/input-length parameter with shared constants, in the ordinary bit model, including construction and control. No such SAT scheme is supplied. |
| Proposition 12.3: staged expansion and reuse | Total work includes the base state, every expansion, and all query work. Subtraction gives an exact strict-savings criterion. | Growing domains amortize only when cumulative expansion cost is small relative to cumulative query count; enough net query savings must also repay it. |

### Proof audit

The coverage invariant is exactness on all strings of length at most N, together
with retention of the earlier answer bits. The empty-string base case is
included. The step contains a finite number of calls to a total decider and
appends their answers at the next disjoint block of addresses. Induction thus
establishes both correctness and termination at every finite stage. On a query
of length n, construction can stop at stage n; no completed infinite table is
required. This argument depends on decidability, consistent with Proposition
11.1 and the existing Turing citation.

For the polynomial-time corollary, the sum of n stage budgets bounded by
c(j+1)^k is at most c n(n+1)^k. Adding fixed base cost, input reading, and a
polynomial evaluator gives a uniform polynomial runtime. The construction must
pay for all explicit state, copying, and index/control work. A polynomial bound
in the size of an exponentially large previous state is insufficient. Likewise,
a polynomial bound in an arbitrary enumeration's stage number needs a suitable
bound relating coverage stage to input length.

The cost proof uses the recurrence T_j = T_(j-1) + a_j + query work at stage j.
All expansion costs remain charged even when a phase serves no queries. The
average-cost statement is used only when total query count is positive, and
its limit assumes that count tends to infinity. The baseline is a fixed exact
solver restarted on every query, using the same work measure. The upper bound
on query cost gives a sufficient savings condition; the condition using actual
query costs is necessary and sufficient.

### Explicit limits and counterexamples

Finite termination does not imply a polynomial resource bound: stage costs
2^j sum to 2^(N+1)-2. Materializing the explicit answer table also requires
2^(N+1)-1 answer bits. This is a cost of the stated table construction, not a
lower bound on every possible SAT representation. The same induction works
for EXPTIME-complete languages, which cannot have uniform polynomial-time
deciders by the cited hierarchy theorem.

Fast lookup remains conditional on the access model. Neither the correctness
induction nor the staged accounting makes exponentially large storage free,
gives cheap sequential-tape access, or bounds the cost of producing long
outputs. A cache populated only on demand covers its retained solved inputs;
it need not cover the whole bounded domain. A learned replacement must preserve
old correctness and establish exactness on every newly covered input.

The fixed-domain limit in Section 9 cannot be carried over to an expanding
domain without a growth condition. For expansion costs 2^j, one query per
phase leaves divergent average expansion cost, while 4^j queries per phase
make that contribution vanish. Neither workload is asserted to describe an
actual SAT system. Vanishing expansion cost per query still permits growing
query cost, memory, and expansion latency. The result is aggregate-work
accounting and does not give a worst-case response-time guarantee.

### Verification scope

Finite checks covered all 128 labelings of the seven strings in D_2, checking
the base case and both expansion steps (384 coverage checks). Arithmetic checks
covered 28,848 staged cost configurations, including zero-query phases, nonzero
base costs, and retrieval more expensive than solving. The average-cost identity
was checked with exact rational arithmetic in the 27,680 configurations with
positive total query count. A further 165 cases checked the polynomial sum
bound and exponential recurrence, including N=0, and 32 cases checked the two
geometric-sum examples. These checks exercise edge cases and arithmetic; they
do not replace the general proofs.

The revised manuscript contains 15 proof environments, 53 equation environments,
62 unique labels, and 46 bibliography entries. All cross-references resolve;
every previously audited formal statement, proof, and displayed equation is
unchanged. The 24-page PDF builds without warnings. All rendered pages were
visually inspected, with the new section on pages 17–19 checked at full page size.

## Lean verification of expansion and resource limits

This subsection records the earlier `332e8cd` milestone. Its outstanding
implementation obligations are reassessed in the next subsection below.

The repository now contains a [Lean project](../formal/README.md) with 40 named
theorems. It uses Lean 4.24.0 and mathlib v4.24.0, with transitive dependency
commits recorded in `formal/lake-manifest.json`. The theorem map in its README
identifies which claims from Section 12 are checked and which remain outside
the formalization.

The checked results cover finite binary-word enumeration, the empty-word base,
exact finite-table answers, preservation under expansion, eventual coverage,
and the answer-entry count. A separate theorem proves the invariant for an
arbitrary state representation, conditional on exact base answers, preservation,
and exact new coverage. The numerical cost results prove the cumulative
recurrence, the uniform polynomial stage-sum bound, an explicit monomial bound,
and closure under a polynomial coverage schedule. They also prove staged cost
accounting, the necessary-and-sufficient criterion using actual query costs,
and the sufficient criterion using a retrieval upper bound.

The limits are now proved generally, rather than only exercised by the previous
finite arithmetic checks. Exponential stage costs have exponential cumulative
cost, and neither that sequence nor the explicit table's entry count is
polynomially bounded. The average expansion contribution diverges for one query
per stage and tends to zero for `4^j` queries per stage, including any fixed base
cost. A cast lemma connects real-valued geometric sums to natural query counts.
The accounting proof separately establishes eventual positive query count when
that count tends to infinity. Lean's totalized division at zero has no
average-cost interpretation; the documentation states this boundary explicitly.

### What remains unproved

The solver used to label the table is supplied as a parameter. Its correctness
for a language is an explicit premise. No SAT parser, SAT solver, computability
predicate, machine model, or complexity class has been formalized in this
development. A total function in Lean's logic can be noncomputably specified;
its type alone does not certify an executable algorithm. The concrete table
definitions use finite recursion when supplied an executable solver.

The list implementation stores keys and answers and performs sequential lookup.
It verifies coverage and answer-entry count, not the packed addressing scheme,
physical memory consumption, or direct-access time. Cost functions are charged
numerical ledgers. Their connection to implementation steps remains an
obligation. The conditional polynomial calculation does not provide a uniform
efficient exact SAT constructor, an efficient learned representation, or an
empirical speedup. These distinctions are now explicit in Section 12.4 of the
paper. The cited conventional complexity results and the paper's other proofs
remain outside this Lean development.

### Verification and manuscript changes

`lake build` succeeds with warnings treated as errors. The integrated axiom
audit checks 116 project declarations, including 89 theorem declarations when
Lean-generated equations and helper theorems are counted. Only `propext`,
`Classical.choice`, and `Quot.sound` are permitted. There are no admitted proofs
or additional axioms in the project. Temporary negative-control files containing
a custom axiom and an admitted proof were both rejected by the same audit; they
are not part of the repository.

The manuscript adds the explicit polynomial bound and clarifies the need to
charge a coverage schedule, expansion control, and evaluation. Its formal
statements retain their previous wording; one proof gains the explicit bound.
Section 12.4 describes the verification scope and the remaining algorithmic
obligations. The revised 25-page PDF has 15 proof environments, 54 equation
environments, 64 unique labels, and 46 bibliography entries. All cross-references
resolve, the final LaTeX pass has no warnings, and all rendered pages were
visually inspected, including full-page checks of the changed material on
pages 18–20.

## Concrete SAT core, persistent results, and executed cost study

The follow-up development addresses the four implementation obligations without
claiming the missing unrestricted SAT bound. The current formal library contains
102 explicitly named source theorems. Its default build audits 555 declarations,
including 312 theorem declarations when Lean-generated equations and helpers are
counted. Lean 4.24.0 and the pinned mathlib build pass with warnings as errors;
only `propext`, `Classical.choice`, and `Quot.sound` are allowed.

| Obligation | New evidence | Remaining boundary |
| --- | --- | --- |
| Concrete expansion | `SAT.lean` verifies exhaustive satisfiability and witness search. `Encoding.lean` verifies binary round trips and instantiates exact finite-domain expansion with that solver. | The explicit answer table is exponential. Its list lookup does not implement the paper's packed direct-access layout. |
| Uniform resource bounds | `CostedSAT.lean` proves `T <= W^2 + 2^v (W+13) + 2` and, for a fixed variable cap `K`, `T <= (14*2^K+3)(L+1)^2`. | The coefficient is exponential in `K`; this is not a uniform unrestricted SAT bound. No polynomial full-table construction follows. |
| Program-to-proof connection | The executable counted evaluator realizes inductive read/evaluation judgments; the counted solver returns the proved solver's result. `Hybrid.lean` verifies the concrete adaptive policy, overhead, and history-dependent savings. `Cache.lean` proves exact-result insertion and retention. | Counter arithmetic, binary parsing cost, native compilation/runtime, JSON, Python, SQLite, and disk integrity are outside the core cost proof. Complexity classes and machine simulation remain conventional rather than formalized. |
| Workload savings | A native Lean process and the SQLite adapter execute 288 reproducible runs with 9,216 correct answers. Fresh state charges acquisition inside each run. Core work, complete wrapper setup, service time, shutdown, and persistent database sizes are separately recorded. | Synthetic mechanism controls with three timing repetitions are not representative SAT or neural-learning benchmarks. Interpreter startup, engine compilation, observer work, peak process memory, and energy are not included in the timing/storage claims. |

### Persistence and its trust boundary

The local service accumulates every completed SAT/UNSAT result and retains SAT
witnesses. It separately records an active witness for transfer to new formulas.
State survives process restarts. Complete binary keys avoid treating a hash
collision as input equality; engine fingerprints separate versions without
removing older results. SQLite transactions commit answers and active state;
there is no eviction. Negative answers are retained only after an exact solve,
not after invalid input, an error, or an interrupted computation.

The exact-cache invariant assumes an intact cache produced by prior writes.
Checksums detect accidental changes to semantic fields but do not authenticate
hostile edits. `audit` can re-solve the current engine's retained records and
check positive witnesses. All nine integration tests pass against the real
compiled engine, covering restart, positive/negative retention, cross-formula
transfer, concurrent writers, version namespaces, malformed inputs, checksums,
and detection of a deliberately forged negative answer during semantic audit.
A separate local service demonstration retains two SAT answers and one UNSAT
answer across process invocations. After the isolated benchmark, all 352 distinct
experiment inputs were solved through the normal persistent service as well,
with their labels checked. The local database now retains 355 records: 226 SAT
and 129 UNSAT. All 355 pass a fresh semantic audit. This replay does not change
the fresh-state benchmark records. The database is ignored by Git and remains
in `solver/.cache/results.sqlite3`.

### Results and interpretation

The [saved study](../experiments/README.md) includes six ordered workloads at
variable widths 2, 4, 8, and 12. The first true formula requires all variables to
be true. Even negation wrappers produce distinct inputs sharing that witness.
Contrasting controls change the required assignment, alternate incompatible
assignments, or introduce an explicit contradictory literal. These syntactically
simple formulas isolate the reuse mechanism. The baseline eagerly materializes
all assignments and performs no preprocessing or clause learning.

At width 12, the persistent hybrid uses 467,333 core operations on 32 distinct
formulas sharing a witness, against 18,880,128 for repeated solving. Its median
total time is 146.58 ms versus 229.40 ms with the same front end. The first solve
is charged, and there are 31 successful transfers. The exact cache alone has no
hits on that stream. Alternating witnesses and distinct UNSAT streams add work
and have slower hybrid total times. Small core-work ratios therefore cannot be
read as proportional wall-clock speedups. The checked-in records include all
variants and widths, including losing cases, rather than only the favorable
example. Input hashes, raw-record hash, mode counts, acquisition/hit accounting,
and setup + service + shutdown totals were independently checked.

### Manuscript changes and verification

Sections 12.4–12.7 now distinguish verified expansion, the restricted executable
core bound, persistent witness/result reuse, and the executed mechanism study.
The new proposition and proof state exactly which operations are charged. The
text explains that fixed-variable formulas can have unbounded length, while the
constant remains exponential in the cap. It also retains the distinction between
one-query cost and full-domain construction. Abstract, introduction, evaluation
protocol, and conclusion reflect the new evidence without a novelty claim.

All 15 previous proof environments, all previous proposition/lemma/corollary
statements, and all 54 previous equation environments remain textually unchanged.
The new version has 16 proofs, 57 equation environments plus the new aligned
weight definition, 72 unique labels, and the same 46 bibliography entries. All
references resolve. The full axiom audit and executable build pass. The LaTeX
build produces 27 pages without warnings. All rendered pages were visually
inspected, with the new proof, persistence discussion, and result table on pages
20–22 checked at full page size.
