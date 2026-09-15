# 03 — Chronology of experiments

This is the story in time order. Phase numbers look weird on purpose: we did the **cheap measurable** work before crypto and before a full RAG system.

```text
Phase 0  →  Phase 2  →  Phase 3 Stage A  →  Real-text compression follow-on
                ↘
              Phase 1 (crypto) never started
              Phase 4 (full RAG) cancelled by Phase 3 gate
```

## Timeline table

| When (logical) | Name | Question | Verdict | Evidence |
|---|---|---|---|---|
| 1 | **Phase 0** | Can we split/rebuild text correctly and fast? | **WIN** | `test_output.log`, `benchmark_output.log`, `src/mvd_base.py` |
| 2 | **Phase 2 lossless** | Does MVDC + gzip beat raw + gzip? | **LOSS** (~−120% avg) | `phase2_output.log` |
| 3 | **Phase 2 lossy** | Does consonants-only + gzip beat raw + gzip? | **WIN** (+14.2% avg) | same log |
| 4 | **Phase 3 tokens** | Does vowel-drop reduce tiktoken counts ≥15%? | **LOSS** (−76.8% mean) | `phase3_token_output.log` |
| 5 | **Phase 3 embeddings** | Does similarity stay ≥0.85? | **LOSS** (0.17 mean) | `phase3_embedding_output.log` |
| 6 | **Decision gate** | Build full RAG? | **No** (Scenario 4) | `docs/probe_results.md` |
| 7 | **Real corpus probe** | Does +14% survive on real ≥200 KB text? | **CLAIM HOLDS** (+20.47%) | `phase2_real_corpus_output.log` |
| — | **Phase 1 crypto** | Does keyed MVD help entropy / language detection? | **Not run** | design only in README |
| — | **Wordgraphs** | Are consonant graphs mathematically interesting? | **Not run** | `future-ideas/` + design specs |

## Why this order?

### Phase 0 first

If encode/decode is buggy, every later number is garbage. Prove the toy works.

### Phase 2 before Phase 1 (crypto)

Compression gives an objective score (file size). Crypto needs threat models and careful stats. We wanted a clear metric early.

### Phase 3 before Phase 4 (full RAG)

Full RAG means vector DBs, chunking strategies, recall@k, maybe paid LLM APIs. Expensive.

Instead we asked two **proxies**:

1. Do tokens drop?  
2. Do embeddings survive?

Both failed hard → building Phase 4 would have been theater.

### Real-text probe near the end

The +14.2% lossy win was on **synthetic** ~5 KB bags. Reviewers would say “toy data.” So we re-ran the same protocol on Austen / Frankenstein / RFC. The win held (~20%). That is the surviving positive claim for the paper.

## Decision gate (Phase 3), in plain English

Before running Stage A we wrote rules:

| Rule | Need | Got |
|---|---|---|
| Token reduction | ≥ +15% | −76.8% |
| Mean cosine | ≥ 0.85 | 0.1744 |
| Catastrophic rate | &lt; 10% | 96.67% |

All three failed → **Scenario 4: negative result** → do not proceed to Stage B / Phase 4.

## What we wrote along the way

| Doc | Role in the chronology |
|---|---|
| `docs/phase0_report.md` | Early Phase 0 note |
| `docs/progress_report_pre_rag.md` | Snapshot after Phase 2, before probes |
| `docs/probe_results.md` | Stage A official writeup |
| `docs/real_corpus_compression.md` | Book-scale compression writeup |
| `MVD_Progress_Report.md` | Combined status memo |
| `docs/paper_draft.md` / `docs/mvd_paper.tex` | Paper |

## Next

[04-phase0-explained.md](04-phase0-explained.md)
