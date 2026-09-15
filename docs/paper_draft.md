# When Vowels Don't Help: Empirical Limits of Vowel–Consonant Separation for Compression and LLM Pipelines

**Draft — workshop / short empirical paper**  
**MVD (Maharashtran Vowel Disappearance)**  
**Status:** Measured results only; crypto and full RAG retrieval left out of scope.

---

## Abstract

We study a simple linguistic transform that separates English vowels from consonants—MVD—and ask whether it helps three common goals: reversible representation, lossless compression with standard codecs, and cheaper LLM/RAG pipelines via lossy vowel dropping. The reversible split works. Lossless MVD serialization plus gzip/bz2/zlib is *worse* than compressing raw text (about −120% relative improvement on short synthetic corpora; still strongly negative on real books). Lossy vowel dropping before gzip *does* help: about +14% mean savings on synthetic text and **+20.5%** mean savings on real public-domain prose at ≥200 KB. The same lossy transform fails for RAG-relevant proxies: tiktoken (`cl100k_base`) token counts *increase* by 76.8% on average, and sentence-transformer cosine similarity collapses to 0.17 (96.7% of pairs below 0.6). We conclude that vowel dropping is a narrow byte-level compression trick, not a path to LLM token or embedding efficiency. Byte savings do not transfer to BPE tokenizers or pretrained embedders that rely on recognizable subword units.

---

## 1. Introduction

Natural language is redundant. Vowels are frequent, often predictable, and—under a naïve reading—candidates for removal or relocation. That intuition appears in shorthand systems, abjad scripts, and informal “disemvoweling.” In systems research it reappears as a hope that a language-aware preprocess might:

1. reorganize text for better lossless compression,
2. reduce LLM token counts (and thus RAG cost), or
3. preserve enough semantics for embedding-based retrieval after aggressive shortening.

We implement a minimal, auditable transform—**MVD**—and test these hopes with fixed protocols and frozen data. We do *not* claim a new cipher, a production compressor, or a RAG system. We claim measurements.

**Contributions.**

1. A reversible vowel/consonant/mask transform with full round-trip tests and microbenchmarks.
2. Evidence that **lossless** stream separation + standard codecs fails under our MVDC serialization (header/structure overhead dominates).
3. Evidence that **lossy** vowel dropping before gzip yields consistent savings on both synthetic and real English text (~20% at book scale).
4. A decisive **negative** result for LLM/RAG proxies: token counts rise; embedding similarity collapses—with a shared mechanism (BPE / subword opacity of consonant skeletons).

---

## 2. Method: MVD

### 2.1 Reversible transform

For ASCII vowels `{a,e,i,o,u}` (both cases), MVD maps a string \(S\) to:

- \(C\): consonant stream (all non-vowels, order preserved),
- \(V\): ordered vowel sequence,
- \(M\): position mask (\(1\) = vowel removed).

Reconstruction is exact given \((C,V,M)\). Accented characters and non-Latin scripts are treated as consonants under the current vowel set—an intentional limitation for this study.

### 2.2 Lossless packaging (MVDC)

For lossless experiments we serialize \((C,V,M)\) as an MVDC blob: fixed header, UTF-8 consonants, 4-bit packed vowels, RLE-encoded mask. Downstream codecs: gzip, bz2, zlib.

### 2.3 Lossy variant

For lossy experiments we discard \(V\) and \(M\) and keep only \(C\) (consonants-only text), then compress with gzip. This is **not** reversible.

### 2.4 LLM / embedding probes

- **Tokens:** tiktoken `cl100k_base` on original vs consonants-only text.
- **Embeddings:** `all-MiniLM-L6-v2`, cosine similarity of original vs consonants-only pairs.

Decision thresholds (set before measuring Stage A): mean token reduction ≥15%; mean cosine ≥0.85; rate of pairs with similarity <0.6 under 10%. Failure of both metric families ends further RAG pipeline work.

---

## 3. Experiments

### 3.1 Phase 0 — Correctness and speed

Eight unit tests (reversibility, edges, case, punctuation, bitstream, vowel packing) all pass. Encode/decode at 10 KB is sub-millisecond; ~1 MB round-trip is ~230 ms on our test machine. The transform is space-neutral: it reorganizes characters, it does not shrink them.

### 3.2 Phase 2 — Compression (synthetic)

Five deterministic synthetic corpora (`random.seed(42)`), roughly 3–7 KB each: literature-, technical-, and news-like word bags, plus vowel-heavy and consonant-heavy bags.

**Lossless.** Mean improvement of MVDC+codec vs raw+codec across all corpora and codecs: **−119.78%** (negative = worse). MVDC size overhead before compression ranges from +5.8% to +116.8%. Modern codecs already exploit mixed-ASCII redundancy; relocating vowels into a verbose container does not help on these lengths.

**Lossy.** Gzip on consonants-only vs gzip on raw text:

| Corpus | Gzip savings |
|---|---|
| literature-like | +18.9% |
| technical-like | +12.8% |
| news-like | +10.8% |
| vowel-heavy | +27.2% |
| consonant-heavy | +1.4% |
| **Mean** | **+14.2%** |

### 3.3 Real-text compression follow-on

To check that +14.2% was not an artifact of short word salad, we froze three public-domain sources (Pride and Prejudice, Frankenstein, RFC 8259), sliced UTF-8 prefixes at 50 KB / 200 KB / full (RFC is only ~28 KB), and reused the Phase 2 protocol.

| Setting | Mean lossy gzip savings |
|---|---|
| Synthetic (Phase 2) | +14.2% |
| Real, all samples (n=7) | **+20.43%** |
| Real, ≥200 KB (n=4) | **+20.47%** |

Pre-registered claim rule: mean lossy savings at ≥200 KB ≥ 5%. **Claim holds.** Lossless MVDC+codec remains worse on every real sample (roughly −45% to −75% relative to raw+codec).

### 3.4 Stage A — Tokens and embeddings

**Tokens** (same synthetic corpora as Phase 2):

| Corpus | Reduction % |
|---|---|
| literature-like | −65.8% (tokens up) |
| technical-like | −165.0% |
| news-like | −170.0% |
| vowel-heavy | +23.3% (only win) |
| consonant-heavy | −6.6% |
| **Unweighted mean** | **−76.8%** |

**Embeddings** (30 frozen sentences, 6×5 categories; literary/technical/news cited; vowel-/consonant-heavy synthetic):

| Metric | Target | Actual |
|---|---|---|
| Mean cosine | ≥ 0.85 | **0.1744** |
| Catastrophic rate (sim < 0.6) | < 10% | **96.67%** (29/30) |

Both Stage A families fail by wide margins. We do not build a retrieval pipeline.

---

## 4. Why byte wins invert at the tokenizer

BPE vocabularies (and the MiniLM tokenizer stack) are trained on natural orthography. Common words map to few tokens; consonant skeletons (`btfl` for `beautiful`) are out-of-vocabulary and fragment into more pieces. Character count falls while token count rises. The same opacity destroys embedding geometry: mean similarity is near orthogonal, with some negative pairs.

The vowel-heavy synthetic bag is the exception for tokens: enough characters disappear that even fragmented pieces can net fewer tokens—still not a general RAG strategy.

---

## 5. Related work (positioning)

- **Classical compression** already models English redundancy; language-aware preprocessors rarely beat gzip/zstd on plain text without loss or domain-specific codecs.
- **Prompt/context compression** (e.g. LLMLingua-style methods) targets LLM cost with learned or extractive deletion—far more aggressive, and evaluated on task metrics. MVD is a weaker, linguistics-naive baseline that fails the cheap proxies those systems must still beat.
- **Abjad / shorthand** traditions show humans can read reduced vowels in context; pretrained BPE models are not those humans.

We do not claim superiority over any production system. We report where a minimal linguistic prior helps and where it does not.

---

## 6. Limitations

- English ASCII vowels only; no multilingual evaluation.
- Lossy path is irreversible and unsuitable when exact text matters.
- Token study uses one encoding (`cl100k_base`); one embedding model.
- Synthetic bags for token counting are not grammatical prose (by design, for continuity with Phase 2); embedding sentences are small-n per category.
- Cryptographic preprocessing was specified but not measured.
- ~20% gzip savings is real but modest: gzip is already cheap, and dropping vowels changes the artifact.

---

## 7. Conclusion

MVD teaches a sharp lesson about transferring linguistic redundancy across layers of the stack:

| Layer | Outcome |
|---|---|
| Reversible representation | Works |
| Lossless + gzip/bz2/zlib | Fails (overhead) |
| Lossy + gzip (bytes) | Helps (~14–20%) |
| BPE token count | Fails (tokens increase) |
| Embedding similarity | Fails (near collapse) |

**Byte-level savings do not imply token-level or semantic-level savings.** A transform that removes predictable letters can help a byte compressor and simultaneously harm models whose units are learned subwords. For RAG cost, vowel dropping is not a viable lever under our probes. For archival or bandwidth settings that tolerate irreversible, unreadable text, consonants-only gzip remains a small, reproducible win on English prose.

---

## Reproducibility

| Artifact | Path |
|---|---|
| Core transform | `src/mvd_base.py`, `phase2/mvd_comp.py` |
| Synthetic compression log | `phase2_output.log` |
| Real compression | `phase2/real_corpus_probe.py`, `phase2_real_corpus_output.log`, `data/real/` |
| Token / embedding probes | `phase3/`, `phase3_token_output.log`, `phase3_embedding_output.log` |
| Internal writeups | `docs/probe_results.md`, `docs/real_corpus_compression.md`, `MVD_Progress_Report.md` |

---

## Acknowledgments / notes for revision

- Replace author block; add license for redistributed Gutenberg/RFC files.
- Optional: one extra tokenizer ablation (same corpora) before camera-ready.
- News sentences in `phase3/sentences.json` need a licensing decision before open release.
- Target venues: workshop on negative results, empirical NLP, or compression—not a RAG systems oral.
