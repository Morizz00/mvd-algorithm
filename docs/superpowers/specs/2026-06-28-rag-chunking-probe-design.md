# MVD RAG/Chunking Probe — Design (Stage A)

## Context

MVD (vowel/consonant separation transform) has two completed, empirically
verified phases:

- **Phase 0** — reversible vowel/consonant/mask transform. 8/8 tests pass,
  sub-ms round-trip at 10KB. See `docs/progress_report_pre_rag.md`.
- **Phase 2** — compression-optimized encoding (RLE masks, delta-encoded
  positions, compact vowel bits, binary serialization). 38/38 tests pass.
  Key finding: **lossless** MVD+gzip is worse than raw gzip (avg -119.78%,
  header overhead too costly on short text). **Lossy** vowel-dropping +
  gzip gives a real average **+14.2%** size reduction.

Phase 3 Stage A is **complete**. Results: `docs/probe_results.md`.
Token reduction **−76.83%** (tokens increased); embedding mean **0.1744**;
catastrophic rate **96.67%**. Decision gate: **Scenario 4** — do not build
Stage B / Phase 4. The README's 15–25% token-cut and 0.85 similarity
figures were projections; they are now measured and rejected.

## Problem being solved

RAG pipelines pay recurring cost per token (embedding compute, vector
storage, LLM context/API cost). If MVD's lossy vowel-drop reduces tokens
without degrading retrieval-relevant semantic content, it's a viable
compression lever for RAG specifically. This is a narrow, contested claim —
prompt/context-compression methods (e.g. LLMLingua) already attack the same
problem, often more aggressively. The paper's contribution is determining
whether this specific linguistic-structure-based lever holds up empirically,
not assuming it does.

## Scope of this phase (Stage A only)

Test the two cheapest, most decisive RAG-relevant hypotheses before
committing to a full retrieval pipeline (Stage B, out of scope here):

1. Does vowel-dropping meaningfully reduce **LLM token counts** (not just
   character counts — BPE tokenizers may not realize character-level
   savings, since "hll" is not a vocabulary token the way "hello" is)?
2. Does vowel-dropping preserve **embedding similarity** well enough that
   a downstream retrieval system would still find the right content?

Stage B (full chunking-strategy + retrieval-quality pipeline with
recall@k/NDCG) is explicitly deferred. Whether it's worth building depends
on Stage A's results — see Decision Gate below.

## Methodology

### Experiment 1 — Token reduction

- **Corpus**: reuse the exact Phase 2 synthetic corpora verbatim — same
  word lists (`literature_words`, `technical_words`, `news_words`,
  vowel-heavy words, consonant-heavy words) and same `random.seed(42)`,
  from `phase2/mvd_comp.py`. Grammaticality doesn't matter for token
  counting, and reusing the exact corpora keeps continuity with Phase 2's
  established narrative.
- **Method**: tokenize original text and vowel-dropped (consonants-only)
  text with `tiktoken` (cl100k_base or equivalent). Compare token counts.
- **Output**: % token reduction (or increase) per corpus, plus distribution
  of per-token-length effects if reduction is negative (to explain *why*,
  if BPE fragmentation is the cause).

### Experiment 2 — Embedding similarity

- **Corpus**: a new, purpose-built sentence set — **not** the Phase 2
  word-salad corpora, which have no semantic content for an embedding
  model to preserve (random word shuffles, not sentences).
- **Construction rule, split by category**:
  - **Literary / technical / news** (~6–10 sentences each): real or
    lightly-adapted text — public-domain literary openings, real
    documentation-style lines, wire-style ledes — sourced via web search,
    not authored for this experiment. Avoids both the "why didn't you use
    real text" objection and the subtler bias of unconsciously writing
    easy-for-the-hypothesis sentences.
  - **Vowel-heavy / consonant-heavy** (~6–10 sentences each): hand
    -constructed. These are not natural genres — no real corpus of this
    kind exists — so hand-construction is the only honest option, not a
    shortcut. Documented plainly as synthetic-by-necessity.
  - Total ~30–50 sentences across 5 categories.
- **Freeze rule**: the sentence set is finalized and saved to a data file
  (with source citations for the three natural categories) **before** any
  tiktoken or embedding comparison is run. No edits after seeing results.
  This is stated explicitly in the paper's methodology section to preempt
  cherry-picking objections.
- **Method**: embed original vs. vowel-dropped sentence with
  `sentence-transformers` (local model, e.g. `all-MiniLM-L6-v2`, no API
  key needed). Compute cosine similarity per pair.
- **Output**: aggregate mean + spread (headline number). Per-category
  means reported but explicitly flagged as **directional only** — n≈6–10
  per category is too thin for confident category-level claims.

## Decision gate

| Threshold | Value | Rationale |
|---|---|---|
| Mean token reduction | ≥ 15% | Anchors to Phase 2's lossy-gzip finding of +14.2%, so the two experiments corroborate or contradict each other |
| Mean cosine similarity | ≥ 0.85 | Matches the (previously unverified) figure asserted in README's Phase 3 spec |
| Catastrophic failure rate | < 10% of pairs below 0.6 similarity | Guards against a high mean masking a long tail of broken cases |

### Four outcome scenarios

| Scenario | Condition | Paper narrative | Next step |
|---|---|---|---|
| Strong result | Both thresholds met | MVD vowel-dropping is a viable token-efficiency lever for RAG | Proceed to Stage B (full retrieval pipeline) as centerpiece |
| Efficiency/quality tradeoff | Tokens drop, similarity doesn't | Tunable knob with a real cost; explore partial vowel removal as bounded follow-on | No full pipeline; small follow-on sweep only |
| Limited token benefit | Similarity holds, tokens don't drop | Likely cause: BPE tokenizers fragment vowel-dropped non-words into more tokens, not fewer; pivot to structural/chunking-only claim | No pipeline; explain mechanism via tokenizer analysis |
| Negative result | Both fail | Honest negative-results paper: Phase 0+2 stand as solid empirical work; Phase 3/4 hypothesis stated, tested, falsified — consistent with Phase 2's own honesty about lossless compression | No pipeline; paper scope = phases 0+2+falsified hypothesis |

## Deliverables

- Frozen sentence dataset file (with sources) for Experiment 2, committed
  before any run.
- Probe script(s) producing both experiments' results (reduction %s,
  similarity stats), no full RAG/vector-DB pipeline.
- A results writeup (numbers + methodology) feeding directly into the
  paper draft, analogous to `docs/progress_report_pre_rag.md`.

## Out of scope (explicitly deferred)

- Stage B: chunking-strategy comparison, vector indexing, retrieval
  recall@k/NDCG evaluation. Only pursued if the decision gate is met.
- Phase 1 (cryptographic hardening) — unrelated to RAG/chunking angle.
- Any claim about retrieval/answer quality — Stage A measures proxies
  (tokens, embedding similarity), not actual retrieval performance.
