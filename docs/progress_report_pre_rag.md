# MVD Progress Report: Phase 0 + Phase 2 (Pre-RAG)

This report summarizes everything completed and empirically verified before the
RAG/chunking exploration (Phase 3/4). All numbers below are taken directly from
the run logs in the repository root — `test_output.log`, `benchmark_output.log`,
and `phase2_output.log` — not from the design spec in README.md. Nothing here is
projected or theoretical; it is what the code actually did when run.

## Phase 0 — Baseline Reversible Transform

**Source log:** `test_output.log`, `benchmark_output.log`
**Code:** `src/mvd_base.py`

### What it does
Splits text into three reversible streams:
- **Consonants** — all non-vowel characters, in order
- **Vowels** — all vowel characters, in order, case preserved
- **Mask** — binary array marking vowel (1) vs consonant (0) position

### Test results (`test_output.log`)
8/8 tests passed in 0.03s:

| Test | Result |
|---|---|
| `test_reversibility` | PASS |
| `test_vowel_extraction` | PASS |
| `test_edge_cases` | PASS |
| `test_case_preservation` | PASS |
| `test_punctuation_handling` | PASS |
| `test_mask_bitstream_conversion` | PASS |
| `test_vowel_encoding` | PASS |
| `test_special_characters` | PASS |

### Performance (`benchmark_output.log`)

| Size | Encode (ms) | Decode (ms) | Total (ms) |
|---|---|---|---|
| 1 KB | 0.07 | 0.06 | 0.13 |
| 10 KB | 0.58 | 0.49 | 1.07 |
| 100 KB | 8.32 | 10.01 | 18.33 |
| 1000 KB | 107.91 | 121.66 | 229.57 |

Edge cases (empty string, single char, all-vowels 1KB, no-vowels 1KB, long word) all passed, ranging 0.004–1.683 ms.

### Space breakdown (byte counts, not compression)

| Text type | Original | Consonants | Vowels | Mask |
|---|---|---|---|---|
| English prose | 900 | 680 | 220 | 900 |
| All vowels | 1000 | 0 | 1000 | 1000 |
| No vowels | 1050 | 1050 | 0 | 1050 |
| Mixed | 1050 | 800 | 250 | 1050 |

**Conclusion:** the transform is reversible, correct on all tested edge cases, and fast (sub-millisecond at 10KB, ~230ms total round-trip at 1MB). It is space-neutral by design — it reorganizes bytes, it does not shrink them.

## Phase 2 — Compression-Optimized Encoding

**Source log:** `phase2_output.log`
**Code:** `phase2/mvd_comp.py`

Adds five optimizations on top of Phase 0: run-length encoding of the mask, delta-encoded vowel positions, 4-bit compact vowel codes, a binary serialization format (MVDC), and direct benchmarking against gzip/bz2/zlib on real corpora.

### Test results
**38/38 tests passed (100% pass rate)** across 8 groups: core reversibility (10 cases), RLE mask encoding (5), delta encoding (3), compact vowel encoding (2), binary serialization round-trips (6), vowel-distribution entropy checks (4), compression benchmarks (real corpora), and edge/stress cases (4, including a 45KB round-trip).

### Compression benchmark results (5 real corpora, ~5KB each)

**Lossless MVD binary format vs. raw text, then compressed:**

| Corpus | Raw size | MVD binary size | Header overhead | gzip improvement | bz2 improvement | zlib improvement |
|---|---|---|---|---|---|---|
| diverse_literature | 5,188 B | 10,240 B | +97.4% | -98.19% | -113.18% | -99.13% |
| diverse_technical | 6,971 B | 14,508 B | +108.1% | -153.20% | -159.37% | -154.83% |
| diverse_news | 7,181 B | 14,731 B | +105.1% | -152.20% | -152.10% | -153.76% |
| vowel_heavy_words | 2,769 B | 6,003 B | +116.8% | -154.49% | -172.49% | -158.12% |
| consonant_heavy | 3,182 B | 3,368 B | +5.8% | -21.81% | -31.54% | -22.26% |

**Average improvement across all corpora/codecs: -119.78%** — i.e., lossless MVD + standard codec is worse than just compressing the raw text. The logged "honest compression analysis" states the reason directly: the MVD binary format's header overhead is larger than what gzip/bz2 can recoup on short, diverse text, because those codecs already exploit structure in ordinary mixed-ASCII text.

**Lossy mode (vowel-drop, consonants-only) vs. raw text, then gzip:**

| Corpus | gzip savings |
|---|---|
| diverse_literature | +18.9% |
| diverse_technical | +12.8% |
| diverse_news | +10.8% |
| vowel_heavy_words | +27.2% |
| consonant_heavy | +1.4% |

**Average savings: +14.2%** (logged as PASS — "consonant-only gzip beats full-text gzip on average"). The log also confirms the core MVD insight directly: on the literature corpus, consonant stream (3,524 B) is smaller than full text (5,188 B).

### Conclusion
Phase 2 is fully implemented and tested, and its own benchmark honestly falsifies the lossless-compression hypothesis: separating vowels from consonants does not help general-purpose codecs on short/diverse text — it hurts, due to serialization overhead. The only verified win is the **lossy** path (dropping vowels entirely before compressing), which gives a real, consistent ~14% average reduction, ranging from +1.4% (consonant-heavy text, little to gain) to +27.2% (vowel-heavy text, most to gain).

## What This Means Going Into the RAG/Chunking Phase

Two verified facts carry forward into Phase 3/4 planning:

1. **Lossless separation has a real, measured cost** (+5.8% to +116.8% size overhead before compression) — any RAG/chunking design that stores vowels and consonants as separate lossless streams inherits this overhead unless serialization is redesigned.
2. **Lossy vowel-dropping has a real, measured benefit** (+14.2% average gzip savings) — this is the only empirically supported lever so far, and it is the one the RAG/chunking probe (token reduction + embedding similarity) is designed to test against, since RAG can tolerate lossy text if retrieval/embedding quality holds up.

No claim about token reduction or embedding similarity under vowel-dropping has been tested yet — those numbers in README.md's Phase 3 spec are projections, not results. That is the gap this phase is meant to close.

## Status at end of Phase 2

| Item | Status |
|---|---|
| Phase 0 implementation, tests, benchmarks | Done, verified |
| Phase 2 implementation, tests, benchmarks | Done, verified |
| `docs/phase2_analysis.md` | Not written (this report supersedes the need for it) |
| Phase 1 (crypto hardening) | Not started — spec only |
| Phase 3 (token reduction / LLM) | Not started — spec only |
| Phase 4 (RAG integration) | Not started — spec only |
