# Wordgraphs — future idea (not run)

## Status

**Design only.** There is no `wordgraphs/` code folder with results yet.  
Full engineer specs:

- `docs/superpowers/specs/2026-06-28-wordgraphs-design.md`  
- `docs/superpowers/plans/2026-06-28-wordgraphs.md`

This page explains the idea for a fresher.

## Why this idea exists

Phase 3 showed: if you **delete vowels and feed the leftovers to LLMs/embedders**, things go badly.

So we stopped using MVD as an “LLM cost hack.”

Wordgraphs asks a *different* question that does **not** care about tokens or RAG:

> If consonants are a stable “skeleton” of a word, is there a **graph / tree / automaton** view of that skeleton that is mathematically interesting on a dictionary?

Interesting might mean: shared structure across words, collision rates, morphology-ish patterns, etc.  
**Negative answers are allowed.** “These graphs are boring” is a valid outcome.

## Intuition with an example

Word: `hello`

- Letters: `h e l l o`  
- MVD consonants: `hll`  
- Vowels between them: `e` between `h` and first `l`, empty between the two `l`s, `o` after…

One proposed representation (**consonant chain with vowel-labeled edges**):

```text
[START] --e--> (h) --e--> (l) --""--> (l) --o--> [END]
```

(Exact START/END rules are in the design spec; this is the vibe.)

Another representation is just the boring string pattern `CVCCV` as a **baseline**. If fancy graphs can’t beat `CVCCV` on any metric, the fancy graphs aren’t earning their keep.

## The eight prototype families (names only)

The design consolidates many doodles into eight prototypes to implement and compare:

1. CV-pattern baseline (`hello` → `CVCCV`)  
2. Consonant-chain with vowel-labeled edges  
3. Alternating bipartite C/V character graph  
4. Corpus-wide trie over consonant skeletons  
5. DAWG (suffix-merged trie) over skeletons  
6. Ambiguity automata for colliding skeletons  
7. Unrestricted directed-graph builder (control)  
8. Toy graph-grammar encoding (control)

Data would come from NLTK word lists, with `random.seed(42)` for samples — same reproducibility habit as Phase 2.

## Explicitly out of scope for wordgraphs

- LLMs  
- Tokenizers  
- Embeddings  
- “Make compression better” as the goal  

Those belong to the old RAG hypothesis, which already failed.

## What “done” would look like

A `wordgraphs/` package, a results markdown with tables (branching factors, collision rates, etc.), and a clear sentence:

- either “representation X shows Y structure,” or  
- “none of these beat the CV baseline; idea closed.”

## Should you do this before the paper?

**No.** The paper does not need wordgraphs. This is a sequel research thread.
