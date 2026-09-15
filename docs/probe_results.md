# Stage A Probe Results: Token Reduction and Embedding Similarity

This report records the Stage A RAG/chunking probes (Phase 3). All numbers
are taken from the run logs in the repository root —
`phase3_token_output.log` and `phase3_embedding_output.log` — not from
projected targets in `README.md`. Design: `docs/superpowers/specs/2026-06-28-rag-chunking-probe-design.md`.

**Code:** `phase3/token_probe.py`, `phase3/embedding_probe.py`, `phase3/common.py`
**Frozen dataset:** `phase3/sentences.json` (`frozen_at`: 2026-06-28)
**Corpora (Experiment 1):** `get_phase2_corpora()` in `phase2/mvd_comp.py` (`random.seed(42)`)

## Methodology

### Experiment 1 — Token reduction

Reuse the five Phase 2 synthetic corpora verbatim (same word lists, same
`random.seed(42)`). Grammaticality does not matter for token counting.
Tokenize original text and vowel-dropped (consonants-only) text with
tiktoken `cl100k_base`. Vowel dropping uses `vowel_drop()` which wraps
`mvd_encode` from Phase 2 — the split is not reimplemented.

Reduction is `(original_tokens - dropped_tokens) / original_tokens * 100`.
The headline average `_average_reduction_pct` is an **unweighted** mean
across the five corpora, not a token-weighted pooled ratio.

### Experiment 2 — Embedding similarity

Uses a purpose-built sentence set, not the Phase 2 word-salad corpora
(those are random word shuffles with no semantic content to preserve).
30 sentences, 6 per category, frozen in `phase3/sentences.json` before
any embedding comparison was run:

- literary / technical / news: real or lightly paraphrased cited text
  (`synthetic: false`)
- vowel_heavy / consonant_heavy: hand-constructed because no natural
  corpus of that kind exists (`synthetic: true`)

Each original sentence is embedded with `all-MiniLM-L6-v2` alongside its
vowel-dropped form; cosine similarity is computed per pair. Per-category
means (n=6) are directional only. The headline numbers are the overall
mean and the catastrophic-failure rate (similarity < 0.6) at n=30.

## Experiment 1 results

**Source log:** `phase3_token_output.log`

| Corpus | Original tokens | Dropped tokens | Reduction % | Interpretation |
|---|---|---|---|---|
| diverse_literature (5K) | 900 | 1492 | -65.78% | Tokens up ~66% |
| diverse_technical (5K) | 700 | 1855 | -165.00% | Tokens more than double |
| diverse_news (5K) | 751 | 2028 | -170.04% | Tokens up ~170% |
| vowel_heavy words (5K) | 691 | 530 | +23.30% | Tokens down 23% — the one win |
| consonant_heavy (5K) | 725 | 773 | -6.62% | Tokens up ~7% |
| **Unweighted average** | — | — | **-76.83%** | **Tokens increase ~77% on average** |

Vowel-dropping increases token count on 4 of 5 corpora. Mechanism: BPE
vocabularies are built from real-word frequency. Common words often
collapse to one or two learned tokens; consonant skeletons ("btfl") are
out-of-vocabulary and fragment into shorter pieces, so token count rises
even as character count falls. Vowel-heavy text is the exception because
it removes the most characters per word.

Gate threshold: mean token reduction ≥ 15%. Actual: **-76.83%**. **FAIL.**

## Experiment 2 results

**Source log:** `phase3_embedding_output.log`

| Category | Mean | Min | Max | n |
|---|---|---|---|---|
| literary | 0.1260 | 0.0077 | 0.1786 | 6 |
| technical | 0.2553 | 0.0251 | 0.4351 | 6 |
| news | 0.0266 | -0.0477 | 0.1146 | 6 |
| vowel_heavy | 0.0451 | -0.0297 | 0.1174 | 6 |
| consonant_heavy | 0.4188 | 0.1985 | 0.6056 | 6 |
| **Overall** | **0.1744** | — | — | **30** |

Catastrophic failure rate (similarity < 0.6): **96.67%** (29 of 30 pairs).
The single pair above 0.6 is in consonant_heavy (max 0.6056).

Per-category numbers are directional only at n=6. The overall mean and
catastrophic rate (n=30) are the headline result. Mechanism: the embedding
model, like the BPE tokenizer, relies on recognizable whole-word and
subword units. Consonant-only strings are opaque to it.

Gate thresholds: mean cosine similarity ≥ 0.85; catastrophic rate < 10%.
Actual: **0.1744** and **96.67%**. **Both FAIL.**

## Decision gate verdict

| Threshold | Required | Actual | Result |
|---|---|---|---|
| Mean token reduction | ≥ 15% | -76.83% (tokens up) | FAIL |
| Mean cosine similarity | ≥ 0.85 | 0.1744 | FAIL |
| Catastrophic failure rate (<0.6) | < 10% | 96.67% | FAIL |

**Scenario 4: Negative result.** Both metric families fail by wide margins.
Per the design spec, Stage B (full chunking/retrieval pipeline) does not
proceed — not as a centerpiece, a tunable knob, or a narrower
structural-only claim. There is no tradeoff to tune.

Tests: 7 `test_common` + 3 `test_token_probe` + 5 `test_embedding_probe` = 15
phase3 tests passed; Phase 2 remains 38/38.

## Implications for the paper

Do not build a RAG pipeline around vowel-dropping. The honest paper is a
negative-results writeup: Phase 0+2 stand as solid empirical work (reversible
transform; lossless MVD+codec loses; lossy vowel-drop + gzip saves ~14.2%
on these corpora). The Phase 3/4 hypothesis — cheaper RAG via vowel-dropping
— was stated, operationalized into two cheap probes, run, and falsified.
The falsification is mechanistic (BPE fragmentation and embedding-model
reliance on recognizable subwords), not an unexplained negative number.

Publication hygiene still open: news-category verbatim third-party
headlines if this dataset is redistributed, and a `load_sentences()` test
for a missing `'categories'` key (current tests cover missing category
*names* inside an otherwise valid object).
