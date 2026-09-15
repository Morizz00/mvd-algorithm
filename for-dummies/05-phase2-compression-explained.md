# 05 — Phase 2 explained (compression)

## Goal

Ask the practical storage question:

> If I use MVD before gzip/bz2/zlib, do I get a smaller file?

We tested **two** answers:

1. **Lossless:** keep vowels + mask in an MVDC binary container, then compress.  
2. **Lossy:** delete vowels, compress consonants only.

## Where the code lives

| File | Job |
|---|---|
| `phase2/mvd_comp.py` | RLE masks, delta positions, 4-bit vowels, MVDC, benchmarks, `get_phase2_corpora()` |
| `phase2/phase2-setup.sh` | Guided bash runner |
| `phase2/real_corpus_probe.py` | Same metrics on real books |
| `phase2/fetch_real_corpora.py` | Download Austen / Frankenstein / RFC |
| `phase2_output.log` | Synthetic benchmark transcript |
| `phase2_real_corpus_output.log` | Real-text transcript |
| `docs/real_corpus_compression.md` | Human writeup |

## Synthetic corpora (toy but fair)

Five bags of words, built with `random.seed(42)` so every machine gets the same text:

- literature-like, technical-like, news-like  
- vowel-heavy, consonant-heavy  

Sizes ~3–7 KB. Not pretty English paragraphs — that’s OK for compression/token counting continuity.

## Result A — Lossless fails

Average improvement of “MVDC then codec” vs “raw then codec”:

**−119.78%**

Negative means **worse**. The MVDC blob is often much larger than the original *before* gzip (overheads from +5.8% up to +116.8% in the synthetic run). gzip cannot earn that tax back on short/diverse text.

**Plain English:** We paid a packaging fee larger than the prize.

## Result B — Lossy wins (synthetic)

Gzip(consonants) vs gzip(original):

| Corpus | Savings |
|---|---|
| literature-like | +18.9% |
| technical-like | +12.8% |
| news-like | +10.8% |
| vowel-heavy | +27.2% |
| consonant-heavy | +1.4% |
| **Mean** | **+14.2%** |

**Plain English:** If you are willing to destroy the vowels, the leftover skeleton often gzip-compresses smaller.

## Result C — Real books (the claim that survives review)

Same protocol on frozen public-domain files:

- Pride and Prejudice (Gutenberg)  
- Frankenstein (Gutenberg)  
- RFC 8259 (technical)

Slices at 50 KB, 200 KB, and full (RFC is only ~28 KB so “full” only).

| Setting | Mean lossy gzip savings |
|---|---|
| Synthetic | +14.2% |
| Real, all samples | **+20.43%** |
| Real, ≥200 KB only | **+20.47%** |

Pre-set rule: if ≥200 KB mean savings ≥ 5%, **CLAIM HOLDS**. It held.

Lossless still loses on every real sample.

## What you should take away

1. **Do not** sell “MVD lossless container beats gzip.”  
2. **Do** report “lossy vowel-drop before gzip helps English prose ~15–20% in our setup.”  
3. Remember the cost: text becomes hard for humans *and* for LLMs.

## Next

[06-phase3-rag-tokens-embeddings.md](06-phase3-rag-tokens-embeddings.md)
