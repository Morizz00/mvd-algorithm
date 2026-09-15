# Structural Word Representations (wordgraphs) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Investigate whether representing English words as graphs/trees/automata built around the consonant/vowel split reveals any mathematically or computationally meaningful structure — a fresh hypothesis, fully decoupled from MVD's falsified RAG/chunking work.

**Architecture:** A new top-level `wordgraphs/` package with per-word representation builders, two corpus-scale structures (trie/DAWG), an ambiguity-analysis module built on the trie's collisions, an experiment runner, and a visualization script. A hand-written analytical survey doc and a numbers-first results doc are the primary research deliverables; code exists to produce real measurements for both.

**Tech Stack:** Python 3.9, pytest, `nltk` (corpus.words, corpus.brown — already downloaded locally), `networkx` 3.2.1, `matplotlib` 3.8.2. No new dependencies. Reuses `mvd_encode` from `phase2/mvd_comp.py` for the basic vowel/consonant character split only.

## Global Constraints

- Vowel/consonant classification reuses `mvd_encode` from `phase2/mvd_comp.py` (`VOWELS = set('aeiouAEIOU')`) — do not reimplement vowel-membership logic elsewhere.
- All random sampling uses `random.seed(42)` (same convention as `phase2.get_phase2_corpora()`), set immediately before the sampling call that needs it.
- Dictionary source: `nltk.corpus.words.words()`, filtered to alphabetic-only, lowercased, deduplicated after lowercasing, length >= 2, returned **sorted** for deterministic ordering before any seeded sampling.
- Per-word structural-stat experiments use a fixed-seed 500-word sample. Misspelling-robustness experiment uses a fixed-seed 30-word sample. Corpus-wide structural stats (trie/DAWG) run on the **full** filtered dictionary.
- No predetermined pass/fail thresholds for "is this representation interesting" — report descriptive findings, not gate verdicts (this differs from the RAG probe's decision-gate pattern).
- Follow the existing project import convention: no packages/`__init__.py`, `sys.path.insert(0, os.path.join(os.path.dirname(__file__), ...))` built from `os.path.dirname(__file__)` (CWD-independent).
- Do not bring in LLM/tokenizer/embedding evaluation anywhere in this plan — out of scope per the design spec.

---

### Task 1: Corpus loading and core text utilities

**Files:**
- Create: `wordgraphs/common.py`
- Test: `wordgraphs/test_common.py`

**Interfaces:**
- Produces: `split_runs(word: str) -> Tuple[List[str], List[str]]` (consonants in order, vowel runs where `len(runs) == len(consonants) + 1`, `runs[i]` is the vowel substring before `consonants[i]` for `i < len(consonants)`, and `runs[-1]` is the trailing vowel substring after the last consonant), `cv_pattern(word: str) -> str` (e.g. `"hello" -> "CVCCV"`), `consonant_skeleton(word: str) -> str` (e.g. `"hello" -> "hll"`), `load_dictionary(min_length: int = 2) -> List[str]` (sorted, deduplicated, lowercase, alphabetic-only words from `nltk.corpus.words`). All four are imported directly by every later task in this plan.

- [ ] **Step 1: Write the failing tests**

Create `wordgraphs/test_common.py`:

```python
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from common import split_runs, cv_pattern, consonant_skeleton, load_dictionary  # noqa: E402


def test_split_runs_hello():
    consonants, runs = split_runs("hello")
    assert consonants == ['h', 'l', 'l']
    assert runs == ['', 'e', '', 'o']


def test_split_runs_no_consonants():
    consonants, runs = split_runs("aeiou")
    assert consonants == []
    assert runs == ['aeiou']


def test_split_runs_no_vowels():
    consonants, runs = split_runs("xyz")
    assert consonants == ['x', 'y', 'z']
    assert runs == ['', '', '', '']


def test_split_runs_single_consonant():
    consonants, runs = split_runs("b")
    assert consonants == ['b']
    assert runs == ['', '']


def test_split_runs_empty_string():
    consonants, runs = split_runs("")
    assert consonants == []
    assert runs == ['']


def test_split_runs_length_invariant():
    for word in ["hello", "aeiou", "xyz", "b", "", "strength", "banana"]:
        consonants, runs = split_runs(word)
        assert len(runs) == len(consonants) + 1


def test_cv_pattern_hello():
    assert cv_pattern("hello") == "CVCCV"


def test_cv_pattern_empty():
    assert cv_pattern("") == ""


def test_consonant_skeleton_hello():
    assert consonant_skeleton("hello") == "hll"


def test_consonant_skeleton_all_vowels():
    assert consonant_skeleton("aeiou") == ""


def test_load_dictionary_properties():
    words = load_dictionary()
    assert len(words) > 50000
    assert words == sorted(words)
    assert len(words) == len(set(words))  # no duplicates
    assert all(w.isalpha() and w.islower() and len(w) >= 2 for w in words)
    assert "hello" in words
    assert "a" not in words  # filtered by min_length=2


def test_load_dictionary_min_length_param():
    words = load_dictionary(min_length=5)
    assert all(len(w) >= 5 for w in words)
    assert "hello" in words
    assert "cat" not in words
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest wordgraphs/test_common.py -v` (from repo root)
Expected: FAIL with `ModuleNotFoundError: No module named 'common'`

- [ ] **Step 3: Write the implementation**

Create `wordgraphs/common.py`:

```python
"""Core text utilities for the wordgraphs structural-representation investigation."""
import os
import sys
from typing import List, Tuple

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'phase2'))
from mvd_comp import mvd_encode  # noqa: E402


def split_runs(word: str) -> Tuple[List[str], List[str]]:
    """
    Split a word into its consonants (in order) and the vowel runs between
    them. len(runs) == len(consonants) + 1: runs[i] is the vowel substring
    immediately before consonants[i], and runs[-1] is the trailing vowel
    substring after the last consonant (or the whole word, if there are no
    consonants at all).
    """
    _, vowels, mask = mvd_encode(word)
    consonants = [ch for ch, bit in zip(word, mask) if bit == 0]
    runs = []
    current = []
    v_idx = 0
    for bit in mask:
        if bit == 1:
            current.append(vowels[v_idx])
            v_idx += 1
        else:
            runs.append(''.join(current))
            current = []
    runs.append(''.join(current))
    return consonants, runs


def cv_pattern(word: str) -> str:
    """Return the word's consonant/vowel pattern, e.g. 'hello' -> 'CVCCV'."""
    _, _, mask = mvd_encode(word)
    return ''.join('V' if bit == 1 else 'C' for bit in mask)


def consonant_skeleton(word: str) -> str:
    """Return just the consonants of a word, in order, e.g. 'hello' -> 'hll'."""
    return mvd_encode(word)[0]


def load_dictionary(min_length: int = 2) -> List[str]:
    """
    Load the NLTK words corpus, filtered to alphabetic-only entries,
    lowercased, deduplicated after lowercasing, length >= min_length,
    returned sorted for deterministic ordering.
    """
    from nltk.corpus import words as nltk_words
    seen = set()
    result = []
    for w in nltk_words.words():
        wl = w.lower()
        if wl.isalpha() and len(wl) >= min_length and wl not in seen:
            seen.add(wl)
            result.append(wl)
    return sorted(result)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest wordgraphs/test_common.py -v`
Expected: 12 passed

- [ ] **Step 5: Commit**

```bash
git add wordgraphs/common.py wordgraphs/test_common.py
git commit -m "Add wordgraphs core text utilities (split_runs, cv_pattern, consonant_skeleton, load_dictionary)"
```

---

### Task 2: Survey doc

**Files:**
- Create: `docs/wordgraphs_survey.md`

**Interfaces:** None — this is a writing-only task with no code dependencies on other tasks.

This survey's analytical content is written below in full. Your job is to create the file with this exact content — do not add, remove, or soften any of the "why it probably fails" sections; the whole point of this document is to falsify candidates honestly before any code is written, not to retroactively justify whatever the prototypes produce.

- [ ] **Step 1: Create the survey doc**

Create `docs/wordgraphs_survey.md`:

```markdown
# Structural Word Representations — Survey

Written before/alongside the prototypes in `wordgraphs/`, not after, so this
analysis isn't a post-hoc rationalization of whatever the code happened to
produce. See `docs/superpowers/specs/2026-06-28-wordgraphs-design.md` for
how each of the original 11 named example representations maps onto the 8
concrete prototypes analyzed here.

## 1. CV-pattern baseline (e.g. "hello" -> "CVCCV")

**Why it could make sense:** the simplest possible structural abstraction
of a word — a degenerate case that's useful precisely because it's a null
hypothesis: if no graph representation below beats this trivial string on
any measured dimension, that representation isn't adding value.

**Why it probably fails:** it throws away all letter identity, keeping
only type (vowel/consonant). It's information-poor by construction, and
guarantees a high collision rate trivially (many unrelated words share a
CV pattern, e.g. "hello" and "belly" are both CVCCV) — a collision rate
this representation produces is uninteresting because it isn't using any
real linguistic signal, just shape.

**Computational complexity:** O(n) to build, O(n) to compare (string
equality or edit distance on the pattern string).

**Information preserved:** syllable-shape-like alternation signal.

**Information lost:** all letter identity — total loss of lexical
identity beyond shape.

**Reconstruction unique?** Never — arbitrarily many words share a CV
pattern.

**Morphology easier?** Marginal. CV pattern doesn't track morpheme
boundaries directly; some inflectional suffixes loosely correlate with a
pattern change (e.g. "-ing" adds "VC"), but this is weak and indirect.

**Comparison easier?** Trivial computationally (string equality), but the
result usually carries little semantic meaning since the relation is too
coarse to distinguish related from unrelated words reliably.

## 2. Consonant-chain, vowel-labeled edges

**Why it could make sense:** this directly encodes the motivating
intuition — consonants as nodes, vowels as labeled transitions between
them. It's a lossless re-encoding of the original string (fully
reversible), just rearranged into graph form.

**Why it probably fails:** structurally, it is always a path graph for
any single word — branching factor 1, by construction. Calling it a
"graph" doesn't add anything a string didn't already have; any genuinely
interesting structure (shared sub-chains across many words) can only
emerge at the corpus level, which is what #4/#5 measure, not this
representation itself.

**Computational complexity:** O(n) to build. Comparison via graph/path
edit distance is in the same complexity class as ordinary string edit
distance, since the chain is structurally a relabeled string.

**Information preserved:** full — the original word is exactly
reconstructable from the chain (consonants in order, plus the vowel run
labeled on each edge).

**Information lost:** none, for a single word in isolation.

**Reconstruction unique?** Yes, trivially — it's a bijection with the
original string.

**Morphology easier?** Not from a single word's chain alone; morphology
requires cross-word comparison, which this representation doesn't provide
by itself.

**Comparison easier?** Possibly, in one specific way worth testing
directly: treating a multi-character vowel run as a single edit unit
(rather than per-character edits) could produce a genuinely different
distance metric than raw Levenshtein distance. Whether this changes
nearest-neighbor relationships in practice is an open, testable question
— the misspelling-robustness experiment checks this directly.

## 3. Alternating bipartite C/V graph

**Why it could make sense:** explicitly typing each node (C or V) makes
"how alternating" a word's structure is directly measurable — e.g.
consonant-cluster run lengths become a first-class structural property
rather than something you'd have to compute separately.

**Why it probably fails:** true bipartiteness (C-nodes only adjacent to
V-nodes) requires strict CV alternation, which most English words violate
via consonant clusters (e.g. "str", "ngth") — so as literally specified,
the resulting graph usually isn't bipartite at all, undermining the
premise of calling it a bipartite graph. The generalized "typed path
graph" still reduces to a path for any single word, the same structural
limitation as #2.

**Computational complexity:** O(n) to build and compare.

**Information preserved:** full — equivalent bijection with the original
string as #2, just exploded into one node per character instead of
grouped consonant/vowel-run units.

**Information lost:** none, for a single word.

**Reconstruction unique?** Yes.

**Morphology easier?** Not directly, at the single-word level.

**Comparison easier?** Not obviously beyond #2 in expressive power (nodes
are characters, so distance is equivalent to character-level edit
distance) — but it does make the consonant-cluster-length distribution
directly available as a measurable, reportable property, which is a real
(if modest) finding regardless of how the comparison question resolves.

## 4. Corpus-wide trie over consonant skeletons

**Why it could make sense:** this is where corpus-level branching and
collision structure can actually appear. Tries are the standard structure
for exactly this kind of prefix-sharing measurement, and a skeleton trie
directly tests whether unrelated words collapse and whether related words
cluster.

**Why it probably fails:** consonant skeletons are shorter and drawn from
a smaller alphabet (21 consonant letters vs. 26) than full words, so a
higher collision rate than a full-word trie is structurally guaranteed by
pigeonhole effects alone — a high collision rate here might just reflect
"shorter strings over a smaller alphabet collide more," not anything
specific to consonants. This experiment must report the full-word trie's
collision rate alongside the skeleton trie's, as a control, to tell these
apart.

**Computational complexity:** O(total characters) to build (linear),
O(depth) per query.

**Information preserved:** skeleton-level structure and prefix-sharing
across the whole dictionary.

**Information lost:** vowels, entirely — the same lossy direction as the
falsified MVD-RAG hypothesis, but measured here as a structural/symbolic
property rather than a token-efficiency one. Worth flagging plainly: this
is the one place this investigation could rediscover the same
information loss as the prior failed work, just put to a different use.

**Reconstruction unique?** By construction, no — that's exactly what #6
measures.

**Morphology easier?** Directly testable: shared prefixes (e.g. "un-",
"re-", "pre-") should appear as branching points in the trie if the
skeletons of prefixed and unprefixed word pairs share a path.

**Comparison easier?** Shared-prefix depth in the trie is a fast
structural proxy for prefix similarity between two words.

## 5. DAWG (suffix-merged trie) over consonant skeletons

**Why it could make sense:** a DAWG additionally merges identical
suffixes, which is the structure needed to detect shared suffixes (e.g.
"-ing", "-tion") that a prefix-only trie can't show directly.

**Why it probably fails:** the same alphabet-size/length collision
artifact noted for #4 applies here too, now from both ends. Also, a
DAWG's main practical benefit — storage compression via shared subtrees —
is a measure of redundancy, not of meaning; node-count reduction vs. the
plain trie doesn't by itself demonstrate anything linguistically
interesting.

**Computational complexity:** typical minimization is O(n log n) (or
O(n) with a suffix-automaton construction) — still cheap at this corpus
scale.

**Information preserved / lost:** same as #4.

**Reconstruction unique?** Same as #4 — a DAWG path can correspond to
multiple original words unless the full word is tracked alongside the
path.

**Morphology easier?** The best candidate of the 8 for surfacing suffix
patterns directly, since shared-suffix subgraphs are exactly what a DAWG
exposes structurally.

**Comparison easier?** Shared-suffix path length as a fast proxy for
suffix similarity.

## 6. Ambiguity/automaton view of colliding skeletons

**Why it could make sense:** this is the most direct way to quantify the
central question of the whole investigation — can two unrelated words
collapse to identical structures, and if so, how often and how badly.

**Why it probably fails:** it isn't really a new representation — it's
an analysis applied to #4's output. If #4's collision rate is low, there
is little to analyze here; if it's high, this mostly confirms what the
collision-rate number already shows, without necessarily adding a new
structural insight beyond the number itself.

**Computational complexity:** O(1) per group lookup given #4 is already
built; enumerating all collision groups is O(number of distinct
skeletons).

**Information preserved:** a full enumeration of which original words a
given skeleton can map back to.

**Information lost:** nothing new beyond what #4 already discards
(vowels).

**Reconstruction unique?** This representation's entire purpose is to
measure exactly how non-unique reconstruction is, per skeleton.

**Morphology easier?** Whether collision groups are morphologically
related (vs. arbitrary unrelated collisions) is itself directly
measurable and worth reporting.

**Comparison easier?** Not a comparison-oriented representation — a
diagnostic tool, not a structure to compare two words against each other.

## 7. Unrestricted directed-graph builder (control)

**Why it could make sense:** tests directly whether collapsing repeated
consonants into a single node (one node per distinct letter, rather than
one per occurrence) reveals cycles, self-loops, or branching that the
plain chain (#2) hides — e.g. "banana"'s skeleton "bnn" could become a
2-node graph (b, n) with a self-loop on "n" (since the two n's are
adjacent in the skeleton), rather than a 3-node path.

**Why it probably fails:** most English consonant skeletons likely lack
the repeated-non-adjacent-letter structure needed to produce a genuinely
cyclic or branching graph; the expectation is that the large majority
still reduce to a path, or a path with a handful of self-loops — no more
structurally interesting than #2. This expectation must be measured, not
assumed; that's the entire reason this is built as a control rather than
dismissed analytically.

**Computational complexity:** O(n) to build (linear scan, deduplicating
nodes by letter identity).

**Information preserved:** structural adjacency between distinct
consonants.

**Information lost:** occurrence count and position become implicit
(folded into edge structure, or lost) once repeated letters are merged
into a single node, unless edge weights/multiplicities are tracked
explicitly.

**Reconstruction unique?** Needs direct testing — likely not unique in
general once merging occurs, since multiple original orderings of
repeated-letter occurrences could plausibly produce the same merged
graph.

**Morphology easier?** Not designed for this; no expectation either way.

**Comparison easier?** In principle, graph-isomorphism-based comparison
could detect "same skeleton shape" — but only if merging behavior is
common and consistent across many words. Most likely outcome: only words
with genuinely repeating, non-adjacent consonants produce a graph
distinguishable from #2's path at all.

## 8. Toy graph-grammar encoding (control)

**Why it could make sense:** production rules could in principle
formalize recurring sub-patterns (common consonant clusters like "str",
"ngth", or common vowel-run lengths) as reusable grammar symbols — the
kind of structure linguists use for templatic/non-concatenative
morphology in some language families.

**Why it probably fails:** deriving a real grammar requires a
corpus-scale induction algorithm (e.g. Sequitur, ADIOS, MDL-based
learners) — not something a toy, handful-of-words prototype can
responsibly claim to test. A hand-built toy rule set risks just encoding
the experimenter's own intuition about which patterns matter, rather than
discovering anything new. This is the representation most likely to be
reported as "uninteresting at this scope" rather than cleanly falsified
— a real test would require building a corpus-scale grammar learner,
which is explicitly out of scope here.

**Computational complexity:** real grammar induction is often
super-linear or NP-hard for minimal-grammar formulations; the toy version
sidesteps this entirely, which is itself a methodological limitation to
state plainly rather than hide.

**Information preserved / lost:** depends entirely on the arbitrary,
hand-built rule set — not a meaningful, generalizable answer at this
scope.

**Reconstruction unique?** Trivially yes for a toy hand-built grammar
(since it's effectively a renaming of the chain in #2), which tells us
nothing new.

**Morphology easier?** This is conceptually where morphology and grammar
induction overlap most directly, but the toy version can't demonstrate
it without a real induction step.

**Comparison easier?** Not meaningfully testable at this scope.
```

- [ ] **Step 2: Commit**

```bash
git add docs/wordgraphs_survey.md
git commit -m "Add structural word representation survey"
```

---

### Task 3: Consonant-chain and bipartite graph builders (#2, #3)

**Files:**
- Create: `wordgraphs/representations.py`
- Test: `wordgraphs/test_representations.py`

**Interfaces:**
- Consumes: `split_runs`, `cv_pattern` from `wordgraphs/common.py` (Task 1).
- Produces: `build_chain_graph(word: str) -> nx.DiGraph`, `build_bipartite_graph(word: str) -> nx.DiGraph`, `max_out_degree(g: nx.DiGraph) -> int`, `is_strictly_alternating(g: nx.DiGraph) -> bool`, `consonant_cluster_lengths(word: str) -> List[int]`. Task 4 adds two more builders to this same file; Task 7 (experiments) imports all builders plus `max_out_degree`, `is_strictly_alternating`, `consonant_cluster_lengths` from this file.

- [ ] **Step 1: Write the failing tests**

Create `wordgraphs/test_representations.py`:

```python
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from representations import (  # noqa: E402
    build_chain_graph,
    build_bipartite_graph,
    max_out_degree,
    is_strictly_alternating,
    consonant_cluster_lengths,
)


def test_build_chain_graph_hello():
    g = build_chain_graph("hello")
    assert set(g.nodes) == {'START', 'C0', 'C1', 'C2', 'END'}
    assert g.nodes['C0']['letter'] == 'h'
    assert g.nodes['C1']['letter'] == 'l'
    assert g.nodes['C2']['letter'] == 'l'
    assert g['START']['C0']['vowels'] == ''
    assert g['C0']['C1']['vowels'] == 'e'
    assert g['C1']['C2']['vowels'] == ''
    assert g['C2']['END']['vowels'] == 'o'


def test_build_chain_graph_no_consonants():
    g = build_chain_graph("aeiou")
    assert set(g.nodes) == {'START', 'END'}
    assert g['START']['END']['vowels'] == 'aeiou'


def test_build_chain_graph_empty():
    g = build_chain_graph("")
    assert set(g.nodes) == {'START', 'END'}
    assert g['START']['END']['vowels'] == ''


def test_max_out_degree_chain_is_always_one():
    for word in ["hello", "strength", "aeiou", "b", "banana"]:
        g = build_chain_graph(word)
        assert max_out_degree(g) == 1


def test_build_bipartite_graph_hello():
    g = build_bipartite_graph("hello")
    assert len(g.nodes) == 5
    assert len(g.edges) == 4
    expected_types = ['C', 'V', 'C', 'C', 'V']
    for i, t in enumerate(expected_types):
        assert g.nodes[f'N{i}']['type'] == t
        assert g.nodes[f'N{i}']['char'] == "hello"[i]


def test_build_bipartite_graph_empty():
    g = build_bipartite_graph("")
    assert len(g.nodes) == 0
    assert len(g.edges) == 0


def test_is_strictly_alternating_hello_is_false():
    # 'hello' = CVCCV: positions 2,3 ('l','l') are both consonants, adjacent
    assert is_strictly_alternating(build_bipartite_graph("hello")) is False


def test_is_strictly_alternating_away_is_true():
    # 'away' = VCVC: strictly alternating
    assert is_strictly_alternating(build_bipartite_graph("away")) is True


def test_is_strictly_alternating_single_char_is_true():
    assert is_strictly_alternating(build_bipartite_graph("a")) is True


def test_consonant_cluster_lengths_strength():
    # 'strength' = s,t,r,e,n,g,t,h -> CCC V CCCC -> clusters [3, 4]
    assert consonant_cluster_lengths("strength") == [3, 4]


def test_consonant_cluster_lengths_no_clusters():
    assert consonant_cluster_lengths("aeiou") == []


def test_consonant_cluster_lengths_single_run():
    assert consonant_cluster_lengths("xyz") == [3]
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest wordgraphs/test_representations.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'representations'`

- [ ] **Step 3: Write the implementation**

Create `wordgraphs/representations.py`:

```python
"""Per-word structural representation builders for the wordgraphs investigation."""
import itertools
import os
import sys
from typing import List

import networkx as nx

sys.path.insert(0, os.path.dirname(__file__))
from common import split_runs, cv_pattern  # noqa: E402


def build_chain_graph(word: str) -> nx.DiGraph:
    """
    Build the consonant-chain representation: consonants are nodes in
    order, edges between consecutive consonants are labeled with the
    vowel run between them. Words with no consonants become a single
    START->END edge labeled with the whole (vowel-only) word.
    """
    consonants, runs = split_runs(word)
    g = nx.DiGraph()
    g.add_node('START')
    g.add_node('END')
    if not consonants:
        g.add_edge('START', 'END', vowels=runs[0])
        return g
    for i, ch in enumerate(consonants):
        g.add_node(f'C{i}', letter=ch)
    g.add_edge('START', 'C0', vowels=runs[0])
    for i in range(len(consonants) - 1):
        g.add_edge(f'C{i}', f'C{i + 1}', vowels=runs[i + 1])
    g.add_edge(f'C{len(consonants) - 1}', 'END', vowels=runs[-1])
    return g


def build_bipartite_graph(word: str) -> nx.DiGraph:
    """
    Build the alternating C/V representation: one typed node per
    character, path-connected in sequence.
    """
    g = nx.DiGraph()
    pattern = cv_pattern(word)
    for i, ch in enumerate(word):
        g.add_node(f'N{i}', char=ch, type=pattern[i])
    for i in range(len(word) - 1):
        g.add_edge(f'N{i}', f'N{i + 1}')
    return g


def max_out_degree(g: nx.DiGraph) -> int:
    """Maximum out-degree across all nodes (branching factor proxy)."""
    return max((g.out_degree(n) for n in g.nodes), default=0)


def is_strictly_alternating(g: nx.DiGraph) -> bool:
    """True if no two adjacent nodes share the same 'type' attribute."""
    for u, v in g.edges():
        if g.nodes[u]['type'] == g.nodes[v]['type']:
            return False
    return True


def consonant_cluster_lengths(word: str) -> List[int]:
    """Lengths of each maximal run of consecutive consonants in the word."""
    pattern = cv_pattern(word)
    return [len(list(group)) for key, group in itertools.groupby(pattern) if key == 'C']
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest wordgraphs/test_representations.py -v`
Expected: 12 passed

- [ ] **Step 5: Commit**

```bash
git add wordgraphs/representations.py wordgraphs/test_representations.py
git commit -m "Add consonant-chain and bipartite C/V graph builders (#2, #3)"
```

---

### Task 4: Control builders — unrestricted digraph and toy grammar (#7, #8)

**Files:**
- Modify: `wordgraphs/representations.py` (append to the file created in Task 3)
- Modify: `wordgraphs/test_representations.py` (append tests)

**Interfaces:**
- Consumes: `consonant_skeleton`, `split_runs` from `wordgraphs/common.py` (Task 1).
- Produces: `build_merged_digraph(word: str) -> nx.MultiDiGraph`, `has_self_loop(g: nx.MultiDiGraph) -> bool`, `build_toy_grammar(word: str) -> List[str]`, `grammar_rule_count(word: str) -> int`. Task 7 (experiments) imports all four.

- [ ] **Step 1: Write the failing tests**

Append to `wordgraphs/test_representations.py`:

```python
from representations import (  # noqa: E402
    build_merged_digraph,
    has_self_loop,
    build_toy_grammar,
    grammar_rule_count,
)


def test_build_merged_digraph_banana_has_self_loop():
    # 'banana' skeleton = 'bnn' (b, n, n) -> nodes {b, n}, edges b->n, n->n
    g = build_merged_digraph("banana")
    assert set(g.nodes) == {'b', 'n'}
    assert g.number_of_edges() == 2
    assert has_self_loop(g) is True


def test_build_merged_digraph_hello_has_self_loop():
    # 'hello' skeleton = 'hll' (h, l, l) -> nodes {h, l}, edges h->l, l->l
    g = build_merged_digraph("hello")
    assert set(g.nodes) == {'h', 'l'}
    assert has_self_loop(g) is True


def test_build_merged_digraph_cat_no_self_loop():
    # 'cat' skeleton = 'ct' (c, t) -> nodes {c, t}, edge c->t, no repeats
    g = build_merged_digraph("cat")
    assert set(g.nodes) == {'c', 't'}
    assert g.number_of_edges() == 1
    assert has_self_loop(g) is False


def test_build_merged_digraph_no_consonants():
    g = build_merged_digraph("aeiou")
    assert len(g.nodes) == 0
    assert has_self_loop(g) is False


def test_build_toy_grammar_hello():
    rules = build_toy_grammar("hello")
    assert rules[0] == "S -> C0 V1 C1 C2 V3"
    assert "C0 -> 'h'" in rules
    assert "V1 -> 'e'" in rules
    assert "C1 -> 'l'" in rules
    assert "C2 -> 'l'" in rules
    assert "V3 -> 'o'" in rules


def test_build_toy_grammar_empty_word():
    rules = build_toy_grammar("")
    assert rules == ["S -> ''"]


def test_grammar_rule_count_matches_rule_list_length():
    for word in ["hello", "strength", "a", ""]:
        assert grammar_rule_count(word) == len(build_toy_grammar(word))
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest wordgraphs/test_representations.py -v -k "merged_digraph or toy_grammar or grammar_rule_count"`
Expected: FAIL with `ImportError: cannot import name 'build_merged_digraph'`

- [ ] **Step 3: Write the implementation**

Append to `wordgraphs/representations.py` (add this import alongside the existing ones at the top of the file, next to `from common import split_runs, cv_pattern`):

```python
from common import consonant_skeleton  # noqa: E402
```

Then append these functions to the end of the file:

```python
def build_merged_digraph(word: str) -> nx.MultiDiGraph:
    """
    Control builder: one node per *distinct* consonant letter (deduplicated
    by identity, not position), with an edge for each adjacency in the
    consonant skeleton. Repeated adjacent consonants (e.g. 'hello' -> 'hll')
    produce a self-loop. Tests whether merging reveals cycles/branching a
    plain chain (build_chain_graph) hides.
    """
    skeleton = consonant_skeleton(word)
    g = nx.MultiDiGraph()
    for ch in skeleton:
        g.add_node(ch)
    for i in range(len(skeleton) - 1):
        g.add_edge(skeleton[i], skeleton[i + 1])
    return g


def has_self_loop(g: nx.MultiDiGraph) -> bool:
    """True if any edge in the graph connects a node to itself."""
    return any(u == v for u, v in g.edges())


def build_toy_grammar(word: str) -> List[str]:
    """
    Control builder: a minimal, hand-built production-rule encoding. One
    rule per consonant/vowel-run symbol, no sharing or compression across
    words. Explicitly a toy (see docs/wordgraphs_survey.md, item #8) — it
    exists only to test whether even a naive grammar view reveals
    something the chain (#2) doesn't.
    """
    consonants, runs = split_runs(word)
    symbols = []
    rules = []
    for i, run in enumerate(runs):
        if run:
            sym = f"V{i}"
            symbols.append(sym)
            rules.append(f"{sym} -> '{run}'")
        if i < len(consonants):
            sym = f"C{i}"
            symbols.append(sym)
            rules.append(f"{sym} -> '{consonants[i]}'")
    start_rule = "S -> " + " ".join(symbols) if symbols else "S -> ''"
    return [start_rule] + rules


def grammar_rule_count(word: str) -> int:
    """Number of rules the toy grammar produces for a word."""
    return len(build_toy_grammar(word))
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest wordgraphs/test_representations.py -v`
Expected: 19 passed

- [ ] **Step 5: Commit**

```bash
git add wordgraphs/representations.py wordgraphs/test_representations.py
git commit -m "Add control builders: unrestricted digraph and toy grammar (#7, #8)"
```

---

### Task 5: Corpus-wide trie and DAWG over consonant skeletons (#4, #5)

**Files:**
- Create: `wordgraphs/skeleton_trie.py`
- Test: `wordgraphs/test_skeleton_trie.py`

**Interfaces:**
- Consumes: `consonant_skeleton` from `wordgraphs/common.py` (Task 1).
- Produces: `TrieNode` class (attributes: `children: Dict[str, TrieNode]`, `words: List[str]`, `is_end: bool`), `build_trie(input_words: List[str], key_fn) -> TrieNode`, `build_skeleton_trie(input_words: List[str]) -> TrieNode`, `build_full_word_trie(input_words: List[str]) -> TrieNode`, `all_nodes(root: TrieNode) -> Iterator[TrieNode]`, `node_count(root: TrieNode) -> int`, `collision_stats(root: TrieNode) -> dict` (keys: `total_distinct_keys`, `total_words`, `colliding_key_count`, `collision_rate`, `words_in_collision`, `max_group_size`), `collision_groups(root: TrieNode, min_size: int = 2) -> List[List[str]]`, `branching_by_depth(root: TrieNode) -> Dict[int, List[int]]`, `minimize_to_dawg(root: TrieNode) -> dict` (keys: `root`, `node_count`). Task 6 (ambiguity view) imports `collision_groups`. Task 7 (experiments) imports everything in this list.

**Design note on DAWG minimization:** nodes are merged based on **structural** signature only — `(is_end: bool, children-signature)` — not on which specific words pass through them. This is because two different end-positions almost never share an identical list of originating words in real data, so word-identity-based signatures would never merge anything. Structural merging is what a real DAWG does (it minimizes state count by sharing indistinguishable suffix continuations, including the trivial case of two different leaves that are both "just an accept state with no further children").

- [ ] **Step 1: Write the failing tests**

Create `wordgraphs/test_skeleton_trie.py`. These tests use a small, fully hand-traceable word list so every expected number can be verified by hand: `["cat", "cats", "car", "care"]` → skeletons `"ct"`, `"cts"`, `"cr"`, `"cr"` (note: `"car"` and `"care"` both skeletonize to `"cr"` — a real collision). The trie has 5 nodes (root, c, t, r, s); the DAWG should merge the two leaf nodes for `"cts"` and `"cr"` (both are `is_end=True` with no children) into 1 shared node, reducing total nodes from 5 to 4.

```python
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from skeleton_trie import (  # noqa: E402
    build_skeleton_trie,
    build_full_word_trie,
    node_count,
    collision_stats,
    collision_groups,
    branching_by_depth,
    minimize_to_dawg,
)

WORDS = ["cat", "cats", "car", "care"]


def test_skeleton_trie_node_count():
    root = build_skeleton_trie(WORDS)
    assert node_count(root) == 5


def test_skeleton_trie_collision_stats():
    root = build_skeleton_trie(WORDS)
    stats = collision_stats(root)
    assert stats['total_distinct_keys'] == 3
    assert stats['total_words'] == 4
    assert stats['colliding_key_count'] == 1
    assert abs(stats['collision_rate'] - (1 / 3)) < 1e-9
    assert stats['words_in_collision'] == 2
    assert stats['max_group_size'] == 2


def test_skeleton_trie_collision_groups():
    root = build_skeleton_trie(WORDS)
    groups = collision_groups(root)
    assert groups == [['car', 'care']]


def test_full_word_trie_has_no_collisions_for_distinct_words():
    root = build_full_word_trie(WORDS)
    stats = collision_stats(root)
    assert stats['total_distinct_keys'] == 4
    assert stats['collision_rate'] == 0.0


def test_branching_by_depth():
    root = build_skeleton_trie(WORDS)
    depths = branching_by_depth(root)
    assert depths[0] == [1]  # root -> 'c'
    assert depths[1] == [2]  # 'c' -> 't', 'r'
    assert sorted(depths[2]) == [0, 1]  # 'r' (leaf, 0 children), 't' -> 's' (1 child)


def test_minimize_to_dawg_reduces_node_count():
    root = build_skeleton_trie(WORDS)
    dawg = minimize_to_dawg(root)
    assert dawg['node_count'] == 4
    assert node_count(dawg['root']) == 4


def test_minimize_to_dawg_no_reduction_when_no_shared_structure():
    # Three words with distinct, non-mergeable skeleton shapes
    root = build_skeleton_trie(["xy", "ab", "pq"])
    dawg = minimize_to_dawg(root)
    # All three leaves ARE structurally identical (is_end=True, no children) -> they DO merge
    # This itself is the expected, correct DAWG behavior: trivial leaves always merge.
    assert dawg['node_count'] < node_count(root)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest wordgraphs/test_skeleton_trie.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'skeleton_trie'`

- [ ] **Step 3: Write the implementation**

Create `wordgraphs/skeleton_trie.py`:

```python
"""Corpus-wide trie and DAWG over consonant skeletons (#4, #5)."""
import os
import sys
from typing import Dict, Iterator, List

sys.path.insert(0, os.path.dirname(__file__))
from common import consonant_skeleton  # noqa: E402


class TrieNode:
    def __init__(self):
        self.children: Dict[str, 'TrieNode'] = {}
        self.words: List[str] = []
        self.is_end: bool = False


def build_trie(input_words: List[str], key_fn) -> TrieNode:
    """Build a trie keyed by key_fn(word) for each word in input_words."""
    root = TrieNode()
    for word in input_words:
        key = key_fn(word)
        node = root
        for ch in key:
            if ch not in node.children:
                node.children[ch] = TrieNode()
            node = node.children[ch]
        node.is_end = True
        node.words.append(word)
    return root


def build_skeleton_trie(input_words: List[str]) -> TrieNode:
    return build_trie(input_words, consonant_skeleton)


def build_full_word_trie(input_words: List[str]) -> TrieNode:
    return build_trie(input_words, lambda w: w)


def all_nodes(root: TrieNode) -> Iterator[TrieNode]:
    """Yield every distinct node reachable from root, deduplicated by object identity."""
    seen = set()
    stack = [root]
    while stack:
        node = stack.pop()
        if id(node) in seen:
            continue
        seen.add(id(node))
        yield node
        stack.extend(node.children.values())


def node_count(root: TrieNode) -> int:
    return sum(1 for _ in all_nodes(root))


def collision_stats(root: TrieNode) -> dict:
    groups = [n.words for n in all_nodes(root) if n.is_end]
    total_distinct = len(groups)
    colliding = [g for g in groups if len(g) > 1]
    total_words = sum(len(g) for g in groups)
    return {
        'total_distinct_keys': total_distinct,
        'total_words': total_words,
        'colliding_key_count': len(colliding),
        'collision_rate': (len(colliding) / total_distinct) if total_distinct else 0.0,
        'words_in_collision': sum(len(g) for g in colliding),
        'max_group_size': max((len(g) for g in groups), default=0),
    }


def collision_groups(root: TrieNode, min_size: int = 2) -> List[List[str]]:
    """All word groups sharing an identical key, with at least min_size members."""
    return [n.words for n in all_nodes(root) if n.is_end and len(n.words) >= min_size]


def branching_by_depth(root: TrieNode) -> Dict[int, List[int]]:
    """Map depth -> list of child-counts for every node at that depth. Tree-shaped input only (not a minimized DAWG, where depth is ill-defined for shared nodes)."""
    result: Dict[int, List[int]] = {}

    def walk(node: TrieNode, depth: int):
        result.setdefault(depth, []).append(len(node.children))
        for child in node.children.values():
            walk(child, depth + 1)

    walk(root, 0)
    return result


def minimize_to_dawg(root: TrieNode) -> dict:
    """
    Minimize a trie into a DAWG by merging nodes with identical
    (is_end, children-signature) from the leaves up. Merging is purely
    structural (does not consider which words pass through a node).
    """
    canonical: Dict[tuple, TrieNode] = {}

    def process(node: TrieNode) -> TrieNode:
        new_children = {ch: process(child) for ch, child in node.children.items()}
        sig = (node.is_end, tuple(sorted((ch, id(c)) for ch, c in new_children.items())))
        if sig in canonical:
            return canonical[sig]
        node.children = new_children
        canonical[sig] = node
        return node

    new_root = process(root)
    return {'root': new_root, 'node_count': len(canonical)}
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest wordgraphs/test_skeleton_trie.py -v`
Expected: 7 passed

- [ ] **Step 5: Commit**

```bash
git add wordgraphs/skeleton_trie.py wordgraphs/test_skeleton_trie.py
git commit -m "Add corpus-wide skeleton trie and DAWG minimization (#4, #5)"
```

---

### Task 6: Ambiguity/automaton view of colliding skeletons (#6)

**Files:**
- Create: `wordgraphs/ambiguity.py`
- Test: `wordgraphs/test_ambiguity.py`

**Interfaces:**
- Consumes: `TrieNode` type from `wordgraphs/skeleton_trie.py` (Task 5) — built directly from a trie's own `children`/`is_end`/`words` attributes, not from Task 5's `collision_groups` (which returns groups without their skeleton key; this task needs the key too).
- Produces: `collect_skeleton_groups(root: TrieNode, min_size: int = 2) -> List[Tuple[str, List[str]]]`, `ambiguity_summary(groups: List[Tuple[str, List[str]]]) -> dict` (keys: `num_collision_groups`, `avg_group_size`, `max_group_size`), `shares_common_prefix(words: List[str], min_len: int = 2) -> bool`, `shares_common_suffix(words: List[str], min_len: int = 2) -> bool`, `related_group_fraction(groups: List[Tuple[str, List[str]]]) -> float`, `related_suffix_fraction(groups: List[Tuple[str, List[str]]]) -> float`. Task 7 (experiments) imports all six.

**Important methodological note for this task:** do NOT implement a "does the suffix/prefix survive as a literal substring of the skeleton" check as a morphology-detection experiment. That check would always return true by construction — `consonant_skeleton` is a per-character filter, so `consonant_skeleton(a + b) == consonant_skeleton(a) + consonant_skeleton(b)` for *any* string split, not just real morphological boundaries. It is a mathematical tautology, not an empirical finding, and reporting it as one would be a false positive. The `shares_common_prefix`/`shares_common_suffix` functions below instead check whether the *actual observed collision groups* (real words that happened to collide on a shared skeleton) are related by a shared prefix or suffix — this is a genuine empirical question with no guaranteed answer.

- [ ] **Step 1: Write the failing tests**

Create `wordgraphs/test_ambiguity.py`:

```python
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from skeleton_trie import build_skeleton_trie  # noqa: E402
from ambiguity import (  # noqa: E402
    collect_skeleton_groups,
    ambiguity_summary,
    shares_common_prefix,
    related_group_fraction,
)


def test_collect_skeleton_groups():
    root = build_skeleton_trie(["cat", "cats", "car", "care"])
    groups = collect_skeleton_groups(root)
    assert groups == [('cr', ['car', 'care'])]


def test_collect_skeleton_groups_respects_min_size():
    root = build_skeleton_trie(["cat", "cats", "car", "care"])
    groups = collect_skeleton_groups(root, min_size=3)
    assert groups == []


def test_ambiguity_summary():
    summary = ambiguity_summary([('cr', ['car', 'care']), ('bg', ['bog', 'bag', 'big'])])
    assert summary['num_collision_groups'] == 2
    assert summary['avg_group_size'] == 2.5
    assert summary['max_group_size'] == 3


def test_ambiguity_summary_empty():
    summary = ambiguity_summary([])
    assert summary == {'num_collision_groups': 0, 'avg_group_size': 0.0, 'max_group_size': 0}


def test_shares_common_prefix_related_words():
    assert shares_common_prefix(['car', 'care']) is True


def test_shares_common_prefix_unrelated_words():
    # 'bog' vs 'bag': share only 'b' (1 char) -- below the min_len=2 threshold
    assert shares_common_prefix(['bog', 'bag']) is False


def test_shares_common_prefix_single_word_is_true():
    assert shares_common_prefix(['solo']) is True


def test_related_group_fraction():
    groups = [('cr', ['car', 'care']), ('bg', ['bog', 'bag'])]
    # 'car'/'care' share prefix 'car' (related), 'bog'/'bag' share only 'b' (not related)
    assert related_group_fraction(groups) == 0.5


def test_related_group_fraction_empty():
    assert related_group_fraction([]) == 0.0


def test_shares_common_suffix_related_words():
    # 'singing' vs 'ringing' share suffix 'inging' (well beyond min_len=2)
    assert shares_common_suffix(['singing', 'ringing']) is True


def test_shares_common_suffix_unrelated_words():
    # 'cat' vs 'dog' share no suffix at all
    assert shares_common_suffix(['cat', 'dog']) is False


def test_related_suffix_fraction():
    groups = [('ng', ['singing', 'ringing']), ('td', ['cat', 'dog'])]
    assert related_suffix_fraction(groups) == 0.5
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest wordgraphs/test_ambiguity.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'ambiguity'`

- [ ] **Step 3: Write the implementation**

Create `wordgraphs/ambiguity.py`:

```python
"""Ambiguity/automaton view of colliding consonant skeletons (#6)."""
import os
import sys
from typing import List, Tuple

sys.path.insert(0, os.path.dirname(__file__))
from skeleton_trie import TrieNode  # noqa: E402


def collect_skeleton_groups(root: TrieNode, min_size: int = 2) -> List[Tuple[str, List[str]]]:
    """All (skeleton, words) pairs where len(words) >= min_size, walked from root."""
    results: List[Tuple[str, List[str]]] = []

    def walk(node: TrieNode, prefix: str):
        if node.is_end and len(node.words) >= min_size:
            results.append((prefix, list(node.words)))
        for ch, child in node.children.items():
            walk(child, prefix + ch)

    walk(root, '')
    return results


def ambiguity_summary(groups: List[Tuple[str, List[str]]]) -> dict:
    sizes = [len(words) for _, words in groups]
    return {
        'num_collision_groups': len(groups),
        'avg_group_size': (sum(sizes) / len(sizes)) if sizes else 0.0,
        'max_group_size': max(sizes, default=0),
    }


def shares_common_prefix(words: List[str], min_len: int = 2) -> bool:
    """True if all words share a common prefix of at least min_len characters."""
    if len(words) < 2:
        return True
    first = words[0]
    common = 0
    for i in range(min(len(w) for w in words)):
        if all(w[i] == first[i] for w in words):
            common += 1
        else:
            break
    return common >= min_len


def related_group_fraction(groups: List[Tuple[str, List[str]]]) -> float:
    """Fraction of collision groups whose members share a common prefix (a rough proxy for 'morphologically related' vs. 'arbitrary collision')."""
    if not groups:
        return 0.0
    related = sum(1 for _, words in groups if shares_common_prefix(words))
    return related / len(groups)


def shares_common_suffix(words: List[str], min_len: int = 2) -> bool:
    """True if all words share a common suffix of at least min_len characters."""
    if len(words) < 2:
        return True
    first = words[0]
    common = 0
    for i in range(1, min(len(w) for w in words) + 1):
        if all(w[-i] == first[-i] for w in words):
            common += 1
        else:
            break
    return common >= min_len


def related_suffix_fraction(groups: List[Tuple[str, List[str]]]) -> float:
    """Fraction of collision groups whose members share a common suffix — tests whether real observed collisions are morphologically related (shared suffix) rather than arbitrary."""
    if not groups:
        return 0.0
    related = sum(1 for _, words in groups if shares_common_suffix(words))
    return related / len(groups)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest wordgraphs/test_ambiguity.py -v`
Expected: 12 passed

- [ ] **Step 5: Commit**

```bash
git add wordgraphs/ambiguity.py wordgraphs/test_ambiguity.py
git commit -m "Add ambiguity/automaton view of colliding skeletons (#6)"
```

---

### Task 7: Experiment runner

**Files:**
- Create: `wordgraphs/experiments.py`
- Test: `wordgraphs/test_experiments.py`

**Interfaces:**
- Consumes: everything from Tasks 1-6: `common.py` (`split_runs`, `cv_pattern`, `consonant_skeleton`, `load_dictionary`), `representations.py` (`build_chain_graph`, `build_bipartite_graph`, `max_out_degree`, `is_strictly_alternating`, `consonant_cluster_lengths`, `build_merged_digraph`, `has_self_loop`, `build_toy_grammar`, `grammar_rule_count`), `skeleton_trie.py` (`build_skeleton_trie`, `build_full_word_trie`, `node_count`, `collision_stats`, `branching_by_depth`, `minimize_to_dawg`), `ambiguity.py` (`collect_skeleton_groups`, `ambiguity_summary`, `related_group_fraction`, `related_suffix_fraction`).
- Produces: `edit_distance(a, b) -> int` (generic, works on strings or lists), `token_sequence(word: str) -> List[str]`, `make_typo(word: str) -> str` (uses the global `random` module's current state — caller must seed first), `per_word_structural_stats(words: List[str]) -> dict`, `corpus_wide_stats(dictionary: List[str]) -> dict`, `misspelling_robustness(dictionary: List[str], sample_size: int = 30) -> dict`, `homophone_check(pairs: List[Tuple[str, str]]) -> List[dict]`, `family_clustering_check(families: List[List[str]], unrelated_pool: List[str]) -> List[dict]`, `run_all_experiments() -> dict`. Task 8 (results doc) runs `run_all_experiments()` directly.

- [ ] **Step 1: Write the failing tests**

Create `wordgraphs/test_experiments.py`:

```python
import os
import random
import sys

sys.path.insert(0, os.path.dirname(__file__))
from experiments import (  # noqa: E402
    edit_distance,
    token_sequence,
    make_typo,
    per_word_structural_stats,
    corpus_wide_stats,
    misspelling_robustness,
    homophone_check,
    family_clustering_check,
)


def test_edit_distance_strings():
    assert edit_distance("kitten", "sitting") == 3
    assert edit_distance("", "") == 0
    assert edit_distance("abc", "abc") == 0
    assert edit_distance("abc", "") == 3


def test_edit_distance_lists():
    assert edit_distance(['a', 'bc', 'd'], ['a', 'bc', 'd']) == 0
    assert edit_distance(['a', 'bc', 'd'], ['a', 'd']) == 1


def test_token_sequence_hello():
    # split_runs("hello") -> consonants ['h','l','l'], runs ['','e','','o']
    assert token_sequence("hello") == ['h', 'e', 'l', 'l', 'o']


def test_token_sequence_groups_vowel_runs_as_one_token():
    # 'queue' = q,u,e,u,e -> consonants=['q'], vowel runs=['','ueue']
    # the multi-char trailing vowel run must stay ONE token, not 4 separate chars
    assert token_sequence("queue") == ['q', 'ueue']


def test_make_typo_is_one_edit_away():
    random.seed(42)
    word = "hello"
    typo = make_typo(word)
    assert edit_distance(word, typo) == 1


def test_per_word_structural_stats_basic_keys():
    stats = per_word_structural_stats(["hello", "cat", "aeiou"])
    assert 'chain_max_branching_factor' in stats
    assert 'bipartite_strictly_alternating_fraction' in stats
    assert 'digraph_self_loop_fraction' in stats
    assert 'grammar_avg_rule_count' in stats
    assert stats['chain_max_branching_factor'] == 1  # always true for chains


def test_corpus_wide_stats_small_dictionary():
    stats = corpus_wide_stats(["cat", "cats", "car", "care"])
    assert stats['skeleton_collision_rate'] > stats['full_word_collision_rate']
    assert stats['dawg_node_count'] < stats['trie_node_count']
    assert 'overall_avg_branching_factor' in stats
    assert 'avg_branching_by_depth' in stats
    assert stats['max_skeleton_depth'] == 3  # root(0) -> c(1) -> t/r(2) -> s(3)


def test_misspelling_robustness_small_sample():
    result = misspelling_robustness(["hello", "world", "python", "banana", "strength"], sample_size=5)
    assert result['avg_raw_distance'] == 1.0  # every typo is exactly one edit away
    assert 'avg_chain_token_distance' in result
    assert 'avg_skeleton_distance' in result
    assert len(result['rows']) == 5


def test_homophone_check():
    results = homophone_check([("to", "too"), ("their", "there")])
    assert len(results) == 2
    assert all('same_skeleton' in r and 'same_cv_pattern' in r for r in results)


def test_family_clustering_check():
    families = [["run", "running", "runner"]]
    unrelated_pool = ["jump", "jumping", "jumper", "swim", "swimming", "swimmer"]
    results = family_clustering_check(families, unrelated_pool)
    assert len(results) == 1
    assert 'avg_within_distance' in results[0]
    assert 'avg_cross_distance' in results[0]
    assert 'clusters_closer' in results[0]
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest wordgraphs/test_experiments.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'experiments'`

- [ ] **Step 3: Write the implementation**

Create `wordgraphs/experiments.py`:

```python
"""Experiment runner tying together all wordgraphs representations (#1-#8)."""
import os
import random
import sys
from typing import List, Tuple

sys.path.insert(0, os.path.dirname(__file__))
from common import split_runs, cv_pattern, consonant_skeleton, load_dictionary  # noqa: E402
from representations import (  # noqa: E402
    build_chain_graph,
    build_bipartite_graph,
    max_out_degree,
    is_strictly_alternating,
    consonant_cluster_lengths,
    build_merged_digraph,
    has_self_loop,
    build_toy_grammar,
    grammar_rule_count,
)
from skeleton_trie import (  # noqa: E402
    build_skeleton_trie,
    build_full_word_trie,
    node_count,
    collision_stats,
    branching_by_depth,
    minimize_to_dawg,
)
from ambiguity import (  # noqa: E402
    collect_skeleton_groups,
    ambiguity_summary,
    related_group_fraction,
    related_suffix_fraction,
)


def edit_distance(a, b) -> int:
    """Generic Levenshtein edit distance — works on strings or lists of tokens."""
    if len(a) < len(b):
        a, b = b, a
    if len(b) == 0:
        return len(a)
    previous = list(range(len(b) + 1))
    for i in range(1, len(a) + 1):
        current = [i] + [0] * len(b)
        for j in range(1, len(b) + 1):
            cost = 0 if a[i - 1] == b[j - 1] else 1
            current[j] = min(previous[j] + 1, current[j - 1] + 1, previous[j - 1] + cost)
        previous = current
    return previous[-1]


def token_sequence(word: str) -> List[str]:
    """A word as an alternating sequence of consonant chars and (multi-char) vowel-run tokens, empty runs omitted."""
    consonants, runs = split_runs(word)
    tokens = []
    if runs[0]:
        tokens.append(runs[0])
    for i, c in enumerate(consonants):
        tokens.append(c)
        if runs[i + 1]:
            tokens.append(runs[i + 1])
    return tokens


def make_typo(word: str) -> str:
    """Apply one random single-character edit (insert/delete/substitute) using the global random module's current state."""
    if len(word) == 0:
        return word
    letters = 'abcdefghijklmnopqrstuvwxyz'
    edit_type = random.choice(['insert', 'delete', 'substitute']) if len(word) > 1 else random.choice(['insert', 'substitute'])
    if edit_type == 'delete':
        pos = random.randrange(len(word))
        return word[:pos] + word[pos + 1:]
    if edit_type == 'substitute':
        pos = random.randrange(len(word))
        new_ch = random.choice([c for c in letters if c != word[pos]])
        return word[:pos] + new_ch + word[pos + 1:]
    pos = random.randrange(len(word) + 1)
    new_ch = random.choice(letters)
    return word[:pos] + new_ch + word[pos:]


def per_word_structural_stats(words: List[str]) -> dict:
    """Per-word stats for representations #2, #3, #7, #8 over the given word list."""
    chain_branching = [max_out_degree(build_chain_graph(w)) for w in words]
    alternating = [is_strictly_alternating(build_bipartite_graph(w)) for w in words if w]
    self_loops = [has_self_loop(build_merged_digraph(w)) for w in words]
    rule_counts = [grammar_rule_count(w) for w in words]
    word_lengths = [len(w) for w in words]
    return {
        'n': len(words),
        'chain_max_branching_factor': max(chain_branching) if chain_branching else 0,
        'bipartite_strictly_alternating_fraction': (sum(alternating) / len(alternating)) if alternating else 0.0,
        'digraph_self_loop_fraction': (sum(self_loops) / len(self_loops)) if self_loops else 0.0,
        'grammar_avg_rule_count': (sum(rule_counts) / len(rule_counts)) if rule_counts else 0.0,
        'grammar_avg_rules_per_letter': (sum(rule_counts) / sum(word_lengths)) if sum(word_lengths) else 0.0,
    }


def corpus_wide_stats(dictionary: List[str]) -> dict:
    """Corpus-wide stats for representations #4, #5, with the full-word trie as an explicit control."""
    skeleton_root = build_skeleton_trie(dictionary)
    full_word_root = build_full_word_trie(dictionary)
    skeleton_collision = collision_stats(skeleton_root)
    full_word_collision = collision_stats(full_word_root)
    dawg = minimize_to_dawg(skeleton_root)
    trie_count = node_count(skeleton_root)

    depths = branching_by_depth(skeleton_root)
    avg_branching_by_depth = {d: (sum(bs) / len(bs)) for d, bs in depths.items()}
    total_nodes_for_avg = sum(len(bs) for bs in depths.values())
    overall_avg_branching = (
        sum(sum(bs) for bs in depths.values()) / total_nodes_for_avg
    ) if total_nodes_for_avg else 0.0

    return {
        'dictionary_size': len(dictionary),
        'skeleton_collision_rate': skeleton_collision['collision_rate'],
        'skeleton_max_group_size': skeleton_collision['max_group_size'],
        'full_word_collision_rate': full_word_collision['collision_rate'],
        'trie_node_count': trie_count,
        'dawg_node_count': dawg['node_count'],
        'dawg_node_reduction_pct': ((trie_count - dawg['node_count']) / trie_count * 100) if trie_count else 0.0,
        'max_skeleton_depth': max(depths.keys()) if depths else 0,
        'overall_avg_branching_factor': overall_avg_branching,
        'avg_branching_by_depth': avg_branching_by_depth,
    }


def misspelling_robustness(dictionary: List[str], sample_size: int = 30) -> dict:
    """Compare raw character edit distance, chain-token edit distance, and skeleton edit distance on single-edit typo pairs."""
    random.seed(42)
    sample = random.sample(dictionary, min(sample_size, len(dictionary)))
    rows = []
    for word in sample:
        typo = make_typo(word)
        rows.append({
            'word': word,
            'typo': typo,
            'raw_distance': edit_distance(word, typo),
            'chain_token_distance': edit_distance(token_sequence(word), token_sequence(typo)),
            'skeleton_distance': edit_distance(consonant_skeleton(word), consonant_skeleton(typo)),
        })
    n = len(rows)
    differs = sum(1 for r in rows if r['chain_token_distance'] != r['raw_distance'])
    return {
        'rows': rows,
        'avg_raw_distance': sum(r['raw_distance'] for r in rows) / n,
        'avg_chain_token_distance': sum(r['chain_token_distance'] for r in rows) / n,
        'avg_skeleton_distance': sum(r['skeleton_distance'] for r in rows) / n,
        'chain_differs_from_raw_fraction': differs / n,
    }


def homophone_check(pairs: List[Tuple[str, str]]) -> List[dict]:
    """For each hand-picked pair, check whether they share a skeleton and/or CV pattern."""
    return [
        {
            'pair': pair,
            'same_skeleton': consonant_skeleton(pair[0]) == consonant_skeleton(pair[1]),
            'same_cv_pattern': cv_pattern(pair[0]) == cv_pattern(pair[1]),
        }
        for pair in pairs
    ]


def family_clustering_check(families: List[List[str]], unrelated_pool: List[str]) -> List[dict]:
    """For each word family, compare average within-family chain-token distance to average distance against similar-length unrelated words."""
    results = []
    for family in families:
        within = [
            edit_distance(token_sequence(a), token_sequence(b))
            for i, a in enumerate(family) for b in family[i + 1:]
        ]
        avg_within = (sum(within) / len(within)) if within else 0.0
        cross = []
        for w in family:
            similar_length_unrelated = [u for u in unrelated_pool if abs(len(u) - len(w)) <= 1 and u not in family]
            for u in similar_length_unrelated[:5]:
                cross.append(edit_distance(token_sequence(w), token_sequence(u)))
        avg_cross = (sum(cross) / len(cross)) if cross else 0.0
        results.append({
            'family': family,
            'avg_within_distance': avg_within,
            'avg_cross_distance': avg_cross,
            'clusters_closer': avg_within < avg_cross,
        })
    return results


def run_all_experiments() -> dict:
    """Run every experiment described in the design spec and return the full results dict."""
    dictionary = load_dictionary()

    random.seed(42)
    sample_500 = random.sample(dictionary, 500)

    word_stats = per_word_structural_stats(sample_500)
    corpus_stats = corpus_wide_stats(dictionary)

    skeleton_root = build_skeleton_trie(dictionary)
    groups = collect_skeleton_groups(skeleton_root)
    ambiguity = ambiguity_summary(groups)
    ambiguity['related_prefix_fraction'] = related_group_fraction(groups)
    ambiguity['related_suffix_fraction'] = related_suffix_fraction(groups)

    misspelling = misspelling_robustness(dictionary, sample_size=30)

    homophones = homophone_check([
        ("to", "too"), ("to", "two"), ("too", "two"),
        ("their", "there"), ("bear", "bare"), ("flour", "flower"),
    ])

    families = family_clustering_check(
        families=[
            ["run", "running", "runner"],
            ["swim", "swimming", "swimmer"],
        ],
        unrelated_pool=[w for w in sample_500 if len(w) <= 10],
    )

    results = {
        'dictionary_size': len(dictionary),
        'per_word_structural_stats': word_stats,
        'corpus_wide_stats': corpus_stats,
        'ambiguity_summary': ambiguity,
        'misspelling_robustness': misspelling,
        'homophone_check': homophones,
        'family_clustering_check': families,
    }

    print(f"Dictionary size: {results['dictionary_size']}")
    print(f"Per-word structural stats: {word_stats}")
    print(f"Corpus-wide stats: {corpus_stats}")
    print(f"Ambiguity summary: {ambiguity}")
    print(f"Misspelling robustness (n={len(misspelling['rows'])}): "
          f"avg_raw={misspelling['avg_raw_distance']:.3f} "
          f"avg_chain_token={misspelling['avg_chain_token_distance']:.3f} "
          f"avg_skeleton={misspelling['avg_skeleton_distance']:.3f}")
    print(f"Homophone check: {homophones}")
    print(f"Family clustering check: {families}")

    return results


if __name__ == "__main__":
    run_all_experiments()
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest wordgraphs/test_experiments.py -v`
Expected: 10 passed

- [ ] **Step 5: Commit**

```bash
git add wordgraphs/experiments.py wordgraphs/test_experiments.py
git commit -m "Add experiment runner for all wordgraphs representations"
```

---

### Task 8: Visualizations

**Files:**
- Create: `wordgraphs/visualize.py`
- Test: `wordgraphs/test_visualize.py`

**Interfaces:**
- Consumes: `build_chain_graph`, `build_bipartite_graph` from `wordgraphs/representations.py` (Task 3), `consonant_skeleton` from `wordgraphs/common.py` (Task 1).
- Produces: `visualize_chain_graph(word: str, output_path: str) -> None`, `visualize_bipartite_graph(word: str, output_path: str) -> None`, `visualize_word_set(words: List[str], output_path: str, title: str = "") -> None`, `generate_all_figures(output_dir: str) -> List[str]` (returns the list of file paths written). Task 9 (results doc) calls `generate_all_figures`.

- [ ] **Step 1: Write the failing tests**

Create `wordgraphs/test_visualize.py`:

```python
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from visualize import (  # noqa: E402
    visualize_chain_graph,
    visualize_bipartite_graph,
    visualize_word_set,
    generate_all_figures,
)


def test_visualize_chain_graph_writes_file(tmp_path):
    path = str(tmp_path / "chain.png")
    visualize_chain_graph("hello", path)
    assert os.path.exists(path)
    assert os.path.getsize(path) > 0


def test_visualize_bipartite_graph_writes_file(tmp_path):
    path = str(tmp_path / "bipartite.png")
    visualize_bipartite_graph("hello", path)
    assert os.path.exists(path)
    assert os.path.getsize(path) > 0


def test_visualize_word_set_writes_file(tmp_path):
    path = str(tmp_path / "set.png")
    visualize_word_set(["car", "care"], path, title="Collision: skeleton 'cr'")
    assert os.path.exists(path)
    assert os.path.getsize(path) > 0


def test_generate_all_figures_writes_multiple_files(tmp_path):
    output_dir = str(tmp_path / "figures")
    paths = generate_all_figures(output_dir)
    assert len(paths) >= 4
    for p in paths:
        assert os.path.exists(p)
        assert os.path.getsize(p) > 0
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest wordgraphs/test_visualize.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'visualize'`

- [ ] **Step 3: Write the implementation**

Create `wordgraphs/visualize.py`:

```python
"""Visualizations for the wordgraphs structural representations."""
import os
import sys
from typing import List

import matplotlib
matplotlib.use('Agg')  # headless backend, no display server needed
import matplotlib.pyplot as plt  # noqa: E402
import networkx as nx  # noqa: E402

sys.path.insert(0, os.path.dirname(__file__))
from representations import build_chain_graph, build_bipartite_graph  # noqa: E402
from common import consonant_skeleton  # noqa: E402


def _path_layout(g: nx.DiGraph) -> dict:
    order = list(nx.topological_sort(g))
    return {node: (i, 0) for i, node in enumerate(order)}


def visualize_chain_graph(word: str, output_path: str) -> None:
    g = build_chain_graph(word)
    pos = _path_layout(g)
    labels = {n: g.nodes[n].get('letter', n) for n in g.nodes}
    edge_labels = {(u, v): d['vowels'] for u, v, d in g.edges(data=True)}
    plt.figure(figsize=(max(4, len(g.nodes)), 2))
    nx.draw(g, pos, labels=labels, with_labels=True, node_color='lightblue', node_size=800, arrows=True)
    nx.draw_networkx_edge_labels(g, pos, edge_labels=edge_labels)
    plt.title(f"Consonant chain: '{word}'")
    plt.savefig(output_path, bbox_inches='tight')
    plt.close()


def visualize_bipartite_graph(word: str, output_path: str) -> None:
    g = build_bipartite_graph(word)
    pos = {n: (i, 0) for i, n in enumerate(g.nodes)}
    colors = ['lightcoral' if g.nodes[n]['type'] == 'V' else 'lightblue' for n in g.nodes]
    labels = {n: g.nodes[n]['char'] for n in g.nodes}
    plt.figure(figsize=(max(4, len(g.nodes)), 2))
    nx.draw(g, pos, labels=labels, with_labels=True, node_color=colors, node_size=800, arrows=True)
    plt.title(f"Bipartite C/V graph: '{word}'")
    plt.savefig(output_path, bbox_inches='tight')
    plt.close()


def visualize_word_set(words: List[str], output_path: str, title: str = "") -> None:
    """Stack each word's consonant-chain graph in its own subplot, for comparing related/colliding/misspelled words."""
    fig, axes = plt.subplots(len(words), 1, figsize=(6, 2 * len(words)))
    if len(words) == 1:
        axes = [axes]
    for ax, word in zip(axes, words):
        g = build_chain_graph(word)
        pos = _path_layout(g)
        labels = {n: g.nodes[n].get('letter', n) for n in g.nodes}
        nx.draw(g, pos, ax=ax, labels=labels, with_labels=True, node_color='lightyellow', node_size=600, arrows=True)
        ax.set_title(f"'{word}' (skeleton: '{consonant_skeleton(word)}')")
    if title:
        fig.suptitle(title)
    plt.tight_layout()
    plt.savefig(output_path)
    plt.close()


def generate_all_figures(output_dir: str) -> List[str]:
    """Generate the full set of example figures required by the design spec's deliverable #4."""
    os.makedirs(output_dir, exist_ok=True)
    paths = []

    p = os.path.join(output_dir, "chain_hello.png")
    visualize_chain_graph("hello", p)
    paths.append(p)

    p = os.path.join(output_dir, "bipartite_hello.png")
    visualize_bipartite_graph("hello", p)
    paths.append(p)

    p = os.path.join(output_dir, "collision_car_care.png")
    visualize_word_set(["car", "care"], p, title="Colliding skeleton: 'cr'")
    paths.append(p)

    p = os.path.join(output_dir, "misspelling_strength_strenght.png")
    visualize_word_set(["strength", "strenght"], p, title="Misspelling (transposition)")
    paths.append(p)

    p = os.path.join(output_dir, "family_run.png")
    visualize_word_set(["run", "running", "runner"], p, title="Morphological family: run/running/runner")
    paths.append(p)

    return paths


if __name__ == "__main__":
    written = generate_all_figures(os.path.join(os.path.dirname(__file__), "figures"))
    print(f"Wrote {len(written)} figures:")
    for p in written:
        print(f"  {p}")
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest wordgraphs/test_visualize.py -v`
Expected: 4 passed

- [ ] **Step 5: Commit**

```bash
git add wordgraphs/visualize.py wordgraphs/test_visualize.py
git commit -m "Add word-graph visualizations"
```

---

### Task 9: Run everything and write the results doc

**Files:**
- Create: `docs/wordgraphs_results.md`
- Create: `wordgraphs/figures/*.png` (generated, then committed as binary files — these are a requested deliverable, not build artifacts to gitignore)

**Interfaces:**
- Consumes: `run_all_experiments()` from `wordgraphs/experiments.py` (Task 7), `generate_all_figures()` from `wordgraphs/visualize.py` (Task 8).

This task has **no decision gate** (unlike the prior RAG probe) — there is no predetermined pass/fail threshold. Your job is to report what the numbers actually show, descriptively, including if the honest conclusion is "nothing here is mathematically interesting." Do not invent a positive result; do not soften a negative or mixed one.

- [ ] **Step 1: Run the experiment suite and record output**

Run: `python wordgraphs/experiments.py`

This will take longer than the RAG probe's experiments (the dictionary has 200k+ entries; trie/DAWG construction and corpus_wide_stats run over all of them). Copy the full printed output verbatim into a scratch note — you need every number for the results doc.

- [ ] **Step 2: Generate the figures**

Run: `python wordgraphs/visualize.py`

Confirm it reports 5 figures written, and that `wordgraphs/figures/` contains 5 non-empty PNG files.

- [ ] **Step 3: Write `docs/wordgraphs_results.md`**

Required sections, in this order:

1. **Methodology** — summarize the dictionary source (`nltk.corpus.words`, filtered/deduplicated count from the actual run), the 8 representations and what each measures, and link to `docs/wordgraphs_survey.md` and the design spec.
2. **Per-word structural stats** (#2, #3, #7, #8) — report the actual numbers from `per_word_structural_stats` on the 500-word sample: chain branching factor (should be exactly 1 — state this plainly as confirming the survey's prediction, not as a novel finding), bipartite strictly-alternating fraction, digraph self-loop fraction (this is the key number for the #7 control — state clearly whether it's close to 0% as the survey predicted, or notably higher), grammar avg rule count and rules-per-letter (state whether this scales 1:1 with word length, confirming "no compression" as the survey predicted for #8).
3. **Corpus-wide stats** (#4, #5) — report skeleton collision rate **alongside** the full-word collision rate control, and state explicitly whether the skeleton collision rate is meaningfully higher than the full-word rate (the real test of whether consonant skeletons collide more than chance/alphabet-size effects alone would predict) or roughly proportional to what shorter-alphabet pigeonhole effects alone would predict. Report `overall_avg_branching_factor` and `max_skeleton_depth`, and the shape of `avg_branching_by_depth` (e.g. does branching peak near the root and taper toward the leaves, or some other pattern). Report DAWG node-count reduction, and note plainly (per the survey's pre-registered skepticism on #5) that this measures storage redundancy, not meaning.
4. **Ambiguity analysis** (#6) — report number of collision groups, average/max group size, and both `related_prefix_fraction` and `related_suffix_fraction`. State directly whether collisions tend to be morphologically related (shared prefix/suffix) or arbitrary.
5. **Misspelling robustness** — report avg raw/chain-token/skeleton distances and `chain_differs_from_raw_fraction`. State plainly whether treating vowel runs as single edit units (chain-token distance) ever diverges from raw character edit distance in this sample, and if so, in which direction.
6. **Homophone and word-family checks** — report the actual `homophone_check` and `family_clustering_check` results verbatim, with a one-line interpretation each.
7. **Visualizations** — list the 5 figures generated with a one-line caption each (what it's an example of, not interpretation).
8. **Novelty analysis** — a direct, evidence-grounded answer to "does anything here appear fundamentally novel," citing the specific numbers from sections 2-6 that support or undercut novelty. If the honest answer is "no," say so without hedging.
9. **Downstream-application analysis** — walk through all 9 named application areas from the design spec (retrieval, indexing, compression, OCR, ASR, spelling correction, morphology, graph search, approximate matching) plus LLM preprocessing, stating for each whether the actual experiment results give support, no support, or are silent. Do not weight LLM preprocessing ahead of the others.

- [ ] **Step 4: Commit**

```bash
git add docs/wordgraphs_results.md wordgraphs/figures/
git commit -m "Record wordgraphs experiment results, novelty and downstream-application analysis"
```
