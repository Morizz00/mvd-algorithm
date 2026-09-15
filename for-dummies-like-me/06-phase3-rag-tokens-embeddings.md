# 06 — Phase 3 explained (RAG hopes vs reality)

## Goal

Phase 2 showed: **lossy vowel-drop helps gzip (bytes).**

Phase 3 asked: **does that help the things RAG actually pays for?**

1. **Token count** (LLM context / API cost)  
2. **Embedding similarity** (can a retriever still recognize the text?)

If either fails badly, building a full RAG stack (Phase 4) is pointless.

## Where the code lives

| File | Job |
|---|---|
| `phase3/sentences.json` | 30 frozen sentences for embeddings |
| `phase3/common.py` | `vowel_drop`, `load_sentences` |
| `phase3/token_probe.py` | tiktoken experiment |
| `phase3/embedding_probe.py` | MiniLM cosine experiment |
| `phase3/test_*.py` | 15 tests |
| `phase3_token_output.log` | token run |
| `phase3_embedding_output.log` | embedding run |
| `docs/probe_results.md` | official writeup |

## Experiment 1 — Tokens

**Input:** same five synthetic corpora as Phase 2.  
**Tool:** tiktoken `cl100k_base`.  
**Compare:** original vs consonants-only.

| Corpus | Reduction % | Meaning |
|---|---|---|
| literature-like | −65.8% | tokens **up** ~66% |
| technical-like | −165.0% | more than double |
| news-like | −170.0% | tokens **up** ~170% |
| vowel-heavy | **+23.3%** | only win |
| consonant-heavy | −6.6% | slight increase |
| **Unweighted mean** | **−76.8%** | tokens up ~77% |

Gate needed ≥ **+15%** mean reduction. We got the opposite.

### Why (fresher version)

Imagine a dictionary the tokenizer memorized:

- page for `beautiful` → short code  
- no page for `btfl` → spell it out with many tiny codes  

Deleting vowels removes letters but **destroys dictionary hits**. Cost goes up.

## Experiment 2 — Embeddings

**Input:** 30 sentences frozen *before* any scoring:

- literary / technical / news (cited real lines)  
- vowel-heavy / consonant-heavy (hand-made stress tests)

**Model:** `all-MiniLM-L6-v2`  
**Score:** cosine(original, vowel-dropped)

| Metric | Needed | Got |
|---|---|---|
| Mean cosine | ≥ 0.85 | **0.1744** |
| Share of pairs &lt; 0.6 | &lt; 10% | **96.67%** (29/30) |

Nearly every sentence becomes a stranger to the embedder after vowel drop.

## Decision gate → Scenario 4

Both families failed by huge margins → **do not build Phase 4 RAG**.

That is not cowardice. That is the protocol we wrote in advance.

## The deep lesson (say this in interviews)

> A trick that saves **bytes** can still waste **tokens** and destroy **embeddings**, because those systems don’t operate on letters—they operate on learned pieces of normally spelled text.

## Publication hygiene still open

- Some news lines in `sentences.json` are third-party headlines — decide licensing before redistributing that file widely.  
- One extra schema test for a fully malformed JSON object was listed as optional.

## Next

[07-how-to-run-the-code.md](07-how-to-run-the-code.md)
