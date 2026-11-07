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
