# MVD Progress Report

**Maharashtran Vowel Disappearance — Final Status: Phases 0–3 Complete, Decision Gate Applied**

This report summarizes verified results to date for MVD, a reversible text transformation that separates consonant structure from vowel information. It was explored across compression, cryptographic preprocessing, and LLM/RAG token-efficiency use cases. Key-dependence is a Phase 1 (MVD-ENC) design, not a property of the implemented transform; that phase was never started. Numbers below are from completed test/probe runs in this tree (`test_output.log`, `benchmark_output.log`, `phase2_output.log`, `phase2_real_corpus_output.log`, `phase3_token_output.log`, `phase3_embedding_output.log`) and re-verified arithmetic, not from projected targets in the original design spec. Stage A writeup: `docs/probe_results.md`. Real-text compression writeup: `docs/real_corpus_compression.md`. Two remaining open items are publication-hygiene decisions (news-text licensing; one unrun schema test), not pending experimental results.

## Where We Won, Where We Lost

All five probe tasks are now complete and independently verified end to end. The short answer:

| Result | Metric | Verdict |
|---|---|---|
| Phase 0 — reversibility | 100% round-trip accuracy | WIN |
| Phase 2 — lossy compression (synthetic) | +14.2% avg gzip savings (up to +27.2%) | WIN |
| Phase 2 — lossy compression (real ≥200 KB) | +20.47% mean gzip savings | WIN — CLAIM HOLDS |
| Phase 2 — lossless compression | -119.78% avg vs. raw + codec | LOSS |
| Phase 3 — token count (the RAG cost driver) | -76.83% avg (tokens INCREASED) | LOSS |
| Phase 3 — embedding similarity | 0.1744 mean vs. 0.85 target | LOSS |

The project's central motivating claim — cheaper RAG via vowel-dropping — is dead, on both legs that would have supported it. Token count and embedding similarity were the two decision-gate metrics chosen specifically because they are cheap, decisive, and directly tied to real RAG cost. Both failed by wide margins, not borderline ones: vowel-dropping made text more expensive to tokenize on 4 of 5 corpora (up to +170% more tokens on news text), and destroyed embedding similarity almost entirely (96.67% of all 30 sentence pairs fell below the catastrophic-failure line). This is Scenario 4 from the decision gate: a clean, mechanistically-explained negative result, not a tuning problem.

What survives is narrower than the original pitch: a real, consistent byte-level compression win (Phase 2's lossy mode) that has nothing to do with LLMs, tokenizers, or RAG. On synthetic ~5 KB corpora that win was +14.2% avg gzip; on frozen real public-domain text at ≥200 KB it is **+20.47%** mean (`docs/real_corpus_compression.md`, CLAIM HOLDS). Phase 0 and Phase 2 are solid, publishable empirical work either way; Phase 1 (crypto) was never started, and Phase 4 (full RAG/chunking pipeline) does not proceed, per the decision gate's own rule for a Scenario 4 outcome.

## Status Summary

| Phase | Component | Status |
|---|---|---|
| Phase 0 | Reversible baseline transform | DONE — WIN |
| Phase 2 | Lossless compression (separate streams) | DONE — LOSS |
| Phase 2 | Lossy compression (vowel-drop + gzip, synthetic) | DONE — WIN (+14.2%) |
| Phase 2 | Lossy compression (real text, ≥200 KB) | DONE — CLAIM HOLDS (+20.47%) |
| Phase 3 | Sentence dataset (sourcing + freeze) | DONE — 2 publication items open |
| Phase 3 | Token-reduction probe (tiktoken) | DONE — LOSS |
| Phase 3 | Embedding-similarity probe | DONE — LOSS |
| Phase 3 | Decision gate verdict | SCENARIO 4: NEGATIVE RESULT |
| Phase 1 | Cryptographic hardening (MVD-ENC) | NOT STARTED — spec only |
| Phase 4 | RAG integration (Stage B) | NOT PROCEEDING — gate failed |

*Note: phase numbering follows the original design doc's intentional out-of-order sequencing (0 → 2 → 3 → 1 → 4), chosen so that cheaper, more measurable validation happens before cryptographic and end-to-end work.*

## Phase 0 — Baseline Reversible Transform

Splits text into a consonant stream, an ordered vowel sequence, and a binary position mask. Fully reversible by construction.

### Results

8/8 unit tests passed (reversibility, vowel extraction, edge cases, case preservation, punctuation, mask bitstream conversion, vowel encoding, special characters). Performance: sub-millisecond round-trip at 10 KB, ~230 ms total round-trip at 1 MB. The transform is space-neutral by design — it reorganizes bytes rather than shrinking them.

| Size | Encode (ms) | Decode (ms) | Total (ms) |
|---|---|---|---|
| 1 KB | 0.07 | 0.06 | 0.13 |
| 10 KB | 0.58 | 0.49 | 1.07 |
| 100 KB | 8.32 | 10.01 | 18.33 |
| 1000 KB | 107.91 | 121.66 | 229.57 |

## Phase 2 — Compression-Optimized Encoding

Adds run-length mask encoding, delta-encoded vowel positions, compact 4-bit vowel codes, a binary serialization format, and direct benchmarking against gzip/bz2/zlib on five ~5 KB synthetic corpora (diverse_literature, diverse_technical, diverse_news, vowel_heavy_words, consonant_heavy). 38/38 tests passed.

**Key finding 1 — lossless mode hurts compression.** Serializing consonants, vowels, and mask as separate lossless streams adds 5.8%–116.8% size overhead before any compressor runs. Average effect across all corpora/codecs: -119.78% (i.e. worse than compressing raw text directly). This is a clean, reported negative result, not a bug — general-purpose codecs already exploit the redundancy MVD tries to relocate, and the format overhead outweighs any gain on short/diverse text.

**Key finding 2 — lossy mode helps, consistently.** Dropping vowels entirely (not storing them) before gzip gives a real, consistent average of +14.2% size reduction on the synthetic corpora, ranging from +1.4% (consonant-heavy, little to gain) to +27.2% (vowel-heavy, most to gain). This is the only empirically supported lever going into Phase 3, and it is lossy — the reversibility property MVD was originally framed around does not apply to the variant that actually works.

**Key finding 2b — the lossy win survives on real, longer text.** The same Phase 2 protocol on frozen Austen / Frankenstein / RFC 8259 (`phase2/real_corpus_probe.py`, log `phase2_real_corpus_output.log`) yields **+20.43%** mean lossy gzip savings across all 7 samples and **+20.47%** on the 4 samples ≥200 KB (Austen 200 KB / full, Frankenstein 200 KB / full). Claim rule (≥5% at ≥200 KB): **CLAIM HOLDS**. Full writeup: `docs/real_corpus_compression.md`. Lossless MVDC+codec remains worse on every real sample.

| Corpus | Lossless MVD vs raw (avg codec overhead) | Lossy vowel-drop (gzip savings) |
|---|---|---|
| diverse_literature | +97.4% to +99–113% worse | +18.9% |
| diverse_technical | +108.1% / ~150–159% worse | +12.8% |
| diverse_news | +105.1% / ~152–154% worse | +10.8% |
| vowel_heavy_words | +116.8% / ~154–172% worse | +27.2% |
| consonant_heavy | +5.8% / ~22–32% worse | +1.4% |

*"Worse" figures are the logged negative percentage improvements vs. gzip/bz2/zlib on raw text (e.g. -98.19% to -113.18% for literature). Lossy savings are gzip-on-consonants-only vs. gzip-on-raw-text.*

## Phase 3 — Token Reduction & Embedding Similarity (Complete)

Goal: test whether the lossy vowel-drop lever (proven at the byte/gzip level in Phase 2) also holds at the level that actually drives RAG cost — LLM tokenizer token count — and whether semantic similarity survives well enough for retrieval to remain usable. That was the central question the README's original Phase 3 projections had not yet tested. Both probes are complete; the decision gate is Scenario 4.

### 3.1 — Frozen Sentence Dataset

30 sentences across 5 categories (6 each), frozen before any probe was run to avoid post-hoc cherry-picking. Synthetic bag-of-words corpora from Phase 2 were judged unsuitable for the embedding-similarity test (no grammatical meaning to preserve), so this dataset uses real or adapted text for the three natural categories and necessarily hand-constructed text for the two artificial stress categories.

| Category | n | Sourcing | synthetic flag |
|---|---|---|---|
| literary | 6 | Real public-domain quotes (Austen, Melville, Dickens, Carroll, Shelley, Twain) — Gutenberg-cited | False |
| technical | 6 | Real lines from PEP 8, RFC 2119, RFC 8259, Python docs, Docker docs, MDN — cited | False |
| news | 6 | Real verbatim headlines/ledes, single news source, dated June 2026 — source URL recorded | False |
| vowel_heavy | 6 | Hand-constructed for this experiment | True |
| consonant_heavy | 6 | Hand-constructed for this experiment | True |

Independent verification (vowel-letter ratio, computed directly from the frozen file, not from labels): literary 0.401, technical 0.381, news 0.392, vowel_heavy 0.518, consonant_heavy 0.228. The three natural categories cluster tightly around real-English baseline (~0.38–0.40); the two artificial categories separate cleanly in the intended direction. Zero duplicate sentences across the set.

**OPEN ITEM — news sourcing licensing.**
The news category currently stores real verbatim headlines/ledes from a single named outlet. If this dataset is published as part of an open-source repository (per the project's stated release plan), verbatim third-party text in a redistributed data file is a different exposure than quoting a fragment in conversation. Decision needed: confirm attribution/fair-use is sufficient, or replace with public-domain wire text / style-matched constructed sentences (the same approach already used for the two artificial categories).

**OPEN ITEM — schema robustness test not run.**
A planned test for `load_sentences()`'s error handling on a malformed file (missing `'categories'` key) was attempted in a sandboxed temp file but the tool call was declined before it ran. Still outstanding — needs an explicit decision on whether to run it, skip it as out of scope, or fold it into the existing test suite.

### 3.2 — Token-Reduction Probe

Implemented in `phase3/token_probe.py` using tiktoken's `cl100k_base` encoding exclusively, reusing `vowel_drop()` and the Phase 2 corpus generator (no reimplemented logic). **Source log:** `phase3_token_output.log`.

Result: this is the central risk flagged before the probe ran, and it materialized. Vowel-dropping increases token count on 4 of 5 corpora — sometimes sharply — with vowel-heavy text as the sole exception.

| Corpus | Original → dropped | Token reduction % | Interpretation |
|---|---|---|---|
| diverse_literature | 900 → 1492 | -65.78% | Tokens UP ~66% |
| diverse_technical | 700 → 1855 | -165.00% | Tokens UP ~165% (more than double) |
| diverse_news | 751 → 2028 | -170.04% | Tokens UP ~170% |
| vowel_heavy | 691 → 530 | +23.30% | Tokens DOWN 23% — the one corpus where it works |
| consonant_heavy | 725 → 773 | -6.62% | Tokens UP ~7% |
| **Average (unweighted)** | — | **-76.83%** | **Net: tokens increase, on average, by ~77%** |

Mechanism: BPE tokenizer vocabularies are built from real-word frequency. Common words ("beautiful") often collapse to one or two learned tokens; their consonant skeletons ("btfl") are out-of-vocabulary and fall back to shorter byte/subword pieces, increasing token count even as character count drops. This matches the failure mode predicted before the probe was run, and explains why vowel-heavy text is the exception — it has the most characters to remove per word, and even fragmented tokens can still net fewer pieces than the longer original.

*Note on the averaging: `_average_reduction_pct` is an unweighted mean across the five corpora, not a token-weighted pooled ratio. This matches the task specification and is not a defect, but it is worth stating explicitly in any write-up, since corpora of different sizes contribute equally to the average regardless of their token counts.*

### 3.3 — Embedding-Similarity Probe

Implemented in `phase3/embedding_probe.py` using sentence-transformers' `all-MiniLM-L6-v2` model (local, no API key), reusing `vowel_drop()` and `load_sentences()` from Task 1 with no reimplemented logic. **Source log:** `phase3_embedding_output.log`.

Result: embedding similarity collapses almost entirely. Mean cosine similarity across all 30 sentence pairs is 0.1744, against a target of 0.85 — barely above orthogonal, with some pairs slightly negative. 96.67% of all 30 pairs (29 of 30) fall below the 0.6 catastrophic-failure threshold. No category exceeds a mean of ~0.42.

| Category | Mean similarity | Min | Max | n |
|---|---|---|---|---|
| literary | 0.1260 | 0.0077 | 0.1786 | 6 |
| technical | 0.2553 | 0.0251 | 0.4351 | 6 |
| news | 0.0266 | -0.0477 | 0.1146 | 6 |
| vowel_heavy | 0.0451 | -0.0297 | 0.1174 | 6 |
| consonant_heavy | 0.4188 | 0.1985 | 0.6056 | 6 |
| **Overall mean (n=30)** | **0.1744** | — | — | 30 |
| **Catastrophic failure rate (<0.6)** | **96.67%** | — | — | 30 |

*Per-category numbers (n=6 each) are directional only, not statistically robust at this sample size; the overall mean and catastrophic rate (n=30) are the headline result.* Mechanism: all-MiniLM-L6-v2, like the BPE tokenizer, relies on recognizable whole-word and subword units from pretraining. Stripped of vowels, the input is opaque to the model in the same way it is opaque to the tokenizer — both failures share the same root cause.

### 3.4 — Decision Gate Verdict

| Threshold | Required | Actual | Result |
|---|---|---|---|
| Mean token reduction | ≥ 15% | -76.83% (tokens up) | FAIL |
| Mean cosine similarity | ≥ 0.85 | 0.1744 | FAIL |
| Catastrophic failure rate (<0.6) | < 10% | 96.67% | FAIL |

All three thresholds fail, and by wide margins in every case — this is Scenario 4: Negative result from the design spec's four-scenario decision table. Per the spec's own rule for this scenario, the project does not proceed to Stage B (the full chunking/retrieval pipeline) in any form — not as a centerpiece, a tunable knob, or a narrower structural-only claim. There is no tradeoff to tune: neither metric came close enough to passing to justify further investment. Full writeup: `docs/probe_results.md`. Logs: `phase3_token_output.log`, `phase3_embedding_output.log`. All 15 phase3 tests plus all 38 Phase 2 tests passed.

## What the Verified Results Mean

All probes are complete and the picture is now settled, not provisional:

- **Character/byte-level reduction from vowel-dropping is solid.** Phase 2 measured +14.2% average gzip savings on synthetic corpora; the real-text probe measured **+20.47%** mean at ≥200 KB (CLAIM HOLDS). Both results stand.
- **Token-level reduction — the metric that actually drives RAG cost — failed.** Tokens increased on 4 of 5 corpora, up to +170% on news text. A byte-level win does not imply a token-level win, and for this lever it inverts.
- **Embedding similarity failed even more decisively.** Mean 0.1744 against a 0.85 target, 96.67% catastrophic failure rate. The transform does not just degrade semantic preservation — it destroys it for nearly every sentence tested.
- **The RAG/LLM cost-savings motivation for Phases 3–4 is falsified, not merely unsupported.** Both decision-gate metrics chosen specifically to test this claim failed by wide margins. Per the design spec's own rule, Phase 4 (the full RAG pipeline) does not proceed.

This is consistent with how Phase 2 was reported: a clean, mechanistically explained negative result is a publishable finding, not a failed project. The honest framing for the paper is that MVD's vowel-drop produces a real, narrow byte-level compression win with no relationship to LLM token cost or embedding-based retrieval — and that the project's central hypothesis was stated, operationalized into two cheap and decisive probes, run, and falsified, with the falsification mechanistically explained (BPE fragmentation and embedding-model reliance on recognizable subword units, both defeated by consonant-only strings) rather than left as an unexplained negative number.

## Immediate Next Steps

- Resolve the two still-open Phase 3 dataset items before any publication: the news-sourcing licensing decision (verbatim third-party text in a dataset intended for open-source release), and the missing schema-robustness test for `load_sentences()`.
- Write the paper as an honest negative-results paper: Phase 0+2 as solid positive empirical work; Phase 3/4's RAG-cost hypothesis as clearly stated, tested, and falsified.
- Do not build Stage B / Phase 4 (the full RAG/chunking pipeline) — the decision gate failed decisively, with no tunable tradeoff to chase.
- Position against existing context-compression baselines (e.g. LLMLingua) in the writeup, framing MVD's surviving contribution as the narrow, real Phase 2 compression result plus a mechanistically-explained falsification of the LLM-cost angle.

---

*Report generated from logged test/benchmark/probe output in this tree. Phase 0–3 experimental results are final. Phase 1 (crypto) remains unstarted; Phase 4 (RAG integration) does not proceed per the Scenario 4 decision-gate outcome above.*
