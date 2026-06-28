# Structural Word Representations — Design (wordgraphs)

## Context

This is a deliberately fresh research question, decoupled from MVD's original
RAG/chunking hypothesis (vowel-dropping for LLM token/embedding efficiency),
which was tested and falsified in `docs/probe_results.md` (token counts
increased ~77% on average instead of decreasing; embedding similarity
collapsed to a mean of 0.17 against a 0.85 target). That result stands as-is
and is not revisited here.

The new hypothesis under investigation: instead of treating a word as a
linear character sequence, represent it as a structural object (graph, tree,
automaton) built around the consonant/vowel split, on the intuition that
consonants may act as a stable "skeleton" while vowels encode something more
like transitions or attachment points. This is explicitly *not* a claim —
it is a hypothesis to be falsified or supported by direct measurement, with
no predetermined target metric (unlike the RAG probe, which had numeric
pass/fail thresholds). Negative results ("no representation here is
mathematically interesting") are an acceptable, fully valid outcome.

Explicitly out of scope for this investigation: LLMs, tokenizers, embeddings,
and any compression/token-efficiency objective. Those are the prior failed
hypothesis's framing and must not leak into how this work is scoped or
evaluated.

## Directory and naming

New top-level directory: `wordgraphs/` — not phase-numbered, to mark a clean
break from MVD's `phase0`/`phase2`/`phase3` roadmap naming. Reuses
`mvd_encode` from `phase2/mvd_comp.py` only for the basic vowel/consonant
character split (a generic, correct text utility, not part of the falsified
RAG hypothesis) — no other MVD code or framing is reused.

## Data sources

- **Dictionary**: `nltk.corpus.words` (236,736 entries; already downloaded
  to the local NLTK data directory in this environment). Filtered to
  purely alphabetic entries, lowercased, deduplicated after lowercasing,
  length >= 2. This removes the corpus's many single-letter/abbreviation
  noise entries and case-duplicate pairs (e.g. `"A"` / `"a"`) without
  reducing real coverage.
- **Frequency corpus** (optional, used only if a specific experiment needs
  word frequency, e.g. to bias misspelling/morphology examples toward
  common words): `nltk.corpus.brown` (1,161,192 word tokens; already
  downloaded).

## The 8 prototype representations

Consolidated from the 11 originally-named examples (trees, rooted trees,
directed graphs, DAGs, bipartite graphs, alternating vowel/consonant graphs,
consonant skeletons with vowel-labelled edges, consonant nodes with vowel
routing, trie-like representations, finite automata, graph grammars), with
2 kept as explicit "control" prototypes specifically to test (not assume)
that they collapse to redundancy with the consolidated set:

1. **CV-pattern baseline** — not a graph. `"hello"` → `"CVCCV"`. Null-
   hypothesis comparator: if a graph representation performs no better than
   this trivial string on any measured dimension, that representation isn't
   adding value.
2. **Consonant-chain, vowel-labeled edges** — nodes are the word's
   consonants in order; an edge between consecutive consonant nodes is
   labeled with the (possibly empty) vowel substring between them in the
   original word. Leading/trailing vowels become labeled edges to explicit
   START/END nodes. Words with zero consonants (e.g. `"a"`, `"aa"`) become
   a single START→END edge labeled with the full vowel string. This merges
   "consonant skeleton with vowel-labelled edges," "consonant nodes with
   vowel routing," and "rooted trees" (a chain is a degenerate rooted tree
   with branching factor 1 per word — real branching shows up only at the
   corpus level, in #4/#5).
3. **Alternating bipartite C/V graph** — explicit typed node per character
   (type=C or V, with the actual letter as an attribute), path-connected in
   sequence. Covers "bipartite graphs" and "alternating vowel/consonant
   graphs." Note for the survey: true bipartiteness (C-nodes only adjacent
   to V-nodes) requires strict CV alternation, which most English words
   violate via consonant clusters (e.g. `"str"`) — this is itself a finding
   to report, not a reason to skip building it.
4. **Corpus-wide trie over consonant skeletons** — covers "trie-like
   representations" and is the natural way to measure collision rate,
   branching factor distribution, and whether morphology (shared
   prefixes/suffixes) emerges structurally. Built over the full filtered
   dictionary (~200k+ words; trie insertion is linear in total characters,
   trivially cheap at this scale).
5. **DAWG (suffix-merged trie) over consonant skeletons** — covers "DAGs."
   Same input as #4, but with identical subtrees merged, to test whether
   suffix-sharing reveals more structure (or just compresses redundant
   storage without revealing anything new) compared to the plain trie.
6. **Ambiguity/automaton view of colliding skeletons** — covers "finite
   automata." Built from #4's collision groups (skeletons shared by 2+
   distinct words): for a sample of colliding groups, construct the minimal
   automaton/explicit mapping from skeleton path to the set of words that
   produce it. Directly answers "is reconstruction unique" quantitatively.
7. **Unrestricted directed-graph builder (control)** — covers "directed
   graphs" without forcing a path structure. Builds a directed multigraph
   per word allowing arbitrary node identity (e.g. one node per *distinct*
   consonant letter, with edges for each adjacency, allowing repeats to
   create genuine cycles/branching when a consonant repeats non-adjacently,
   e.g. `"banana"`'s skeleton `"bnn"` could be built either as a 3-node path
   or, under this builder, as a 2-node graph with a self-loop/repeat edge on
   `"n"`). This is the empirical test of whether "directed graphs" ever
   differs structurally from the plain chain (#2) for real English words.
8. **Toy graph-grammar encoding (control)** — covers "graph grammars."
   Minimal production-rule view: for a small handful of hand-picked words
   (not the full corpus — this is explicitly a toy, not a corpus-scale
   grammar induction system, which is out of scope), hand/programmatically
   derive a tiny rule set (e.g. `S -> C V_run, V_run -> vowel-edge-label`)
   and check whether it says anything #2 doesn't already say. Expected to
   be the representation most likely to land on "uninteresting without a
   real grammar learner" — but tested, not assumed.

## Experiments

All experiments use **`random.seed(42)`** for sampling (same convention as
Phase 2's `get_phase2_corpora()`), recorded in the results doc for
reproducibility — same discipline as the RAG probe.

- **Per-word structural stats** (#2, #3, #7, #8): fixed-seed 500-word sample
  from the filtered dictionary. Measure: branching factor, depth/length,
  node/edge counts. Expectation to test explicitly, not assume: #2/#3
  should show branching factor 1 (paths) for virtually all words; #7 is the
  one that might differ — if it doesn't, that's the falsification of
  "directed graphs add anything beyond the chain."
- **Corpus-wide structural stats** (#4, #5): full filtered dictionary.
  Measure: collision rate (fraction of distinct words sharing an identical
  consonant skeleton), branching factor distribution at each trie depth,
  node-count reduction from trie (#4) to DAWG (#5).
- **Reconstruction ambiguity** (#6): sampled from #4's actual collision
  groups (not hypothetical). Measure: average and max collision-group size,
  and whether group members are semantically/morphologically related or
  arbitrary collisions.
- **Morphology emergence**: inspect #4/#5 for whether known English
  affixes (e.g. `-ing`, `-ed`, `-tion`, `un-`, `re-`) appear as shared
  subtree paths *without being told to look for them* — i.e., check if the
  trie/DAWG structure surfaces them as an emergent property of branching
  patterns, not by grepping for the substrings directly.
- **Misspelling robustness**: ~30 words (fixed sample) each given one
  single-character edit (insertion, deletion, or substitution; fixed seed).
  Compare graph-edit-distance (or a structural proxy distance for whichever
  representations have one cheaply computable) between original and typo
  under each representation, against plain Levenshtein distance on the raw
  strings. Question to answer: does any representation's distance metric
  behave differently (better, worse, or just different) than plain edit
  distance on the same pairs?
- **Homophone/pronunciation check**: a small hand-picked set of homophone
  pairs (e.g. `to`/`too`/`two`, `their`/`there`, `bear`/`bare`). Check
  whether they collapse to identical or different structures under each
  representation.
- **Word-family clustering**: a few hand-picked morphological families
  (e.g. `run`/`running`/`runner`, `swim`/`swimming`/`swimmer`). Check
  whether family members are structurally closer to each other than to
  unrelated words of similar length, under each representation that has a
  comparison/distance notion.

## Explicit non-goals (per the research brief)

- No optimization of any representation toward a positive result.
- No predetermined "passing" threshold — verdicts are descriptive
  ("interesting: yes/no, on what basis") not pass/fail against a number
  chosen in advance.
- LLMs, tokenizers, and embeddings are out of scope for evaluating these
  representations. Downstream-application analysis (deliverable #6) may
  *mention* LLM preprocessing as one of many possible applications, but
  must not be weighted ahead of the other listed applications (retrieval,
  indexing, compression, OCR, ASR, spelling correction, morphology, graph
  search, approximate matching).

## Deliverables

1. **Survey doc** (`docs/wordgraphs_survey.md`) — analytical coverage of
   all candidates (the 8 prototyped, plus explicit notes on why the 11
   original named examples map onto them), each addressing: why it could
   make sense, why it probably fails, computational complexity, information
   preserved/lost, reconstruction uniqueness, morphology ease, comparison
   ease. Written before or alongside the prototypes — not a post-hoc
   rationalization of whatever the code happened to produce.
2. **Prototype implementations** (`wordgraphs/representations.py` for #1-3
   and #7-8 per-word builders; `wordgraphs/skeleton_trie.py` for #4-5
   corpus-scale structures; `wordgraphs/ambiguity.py` for #6).
3. **Experiment scripts + results doc** (`wordgraphs/experiments.py` +
   `docs/wordgraphs_results.md`, numbers-first, same style as
   `docs/probe_results.md`).
4. **Visualizations** (`wordgraphs/visualize.py`, saved PNG files under
   `wordgraphs/figures/`): at minimum, one rendered graph per representation
   for a simple example word, plus one for a colliding-skeleton pair, one
   for a misspelling pair, and one for a morphology family — using
   `networkx` + `matplotlib`, both already available.
5. **Novelty analysis** — a dedicated section in the results doc directly
   answering whether anything here appears fundamentally novel, grounded in
   the actual measurements, not aspiration.
6. **Downstream-application analysis** — a dedicated section in the results
   doc walking through each of the 9 listed application areas (retrieval,
   indexing, compression, OCR, ASR, spelling correction, morphology, graph
   search, approximate matching) plus LLM preprocessing, stating for each
   whether the experiments give any support, no support, or are silent.

## Out of scope

- Building a production algorithm or library — these are research
  prototypes for measurement, not deliverable software.
- Full corpus-scale graph-grammar induction (toy example only, see #8).
- Any LLM/tokenizer/embedding-based evaluation of these representations.
