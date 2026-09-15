# Real-Text Compression Probe

This report records the follow-on to Phase 2 that tests whether the surviving
**lossy vowel-drop + gzip** win holds on real public-domain text at longer
lengths. All numbers are from `phase2_real_corpus_output.log`.

**Code:** `phase2/real_corpus_probe.py`, `phase2/fetch_real_corpora.py`
**Frozen corpora:** `data/real/raw/` + `data/real/manifest.json`
**Protocol:** identical to Phase 2 — `mvd_encode`, `serialize_mvd`, gzip/bz2/zlib

## Claim rule

Unweighted mean lossy gzip savings across all samples with raw size **≥ 200 KB**
must be **≥ 5%**.

**Verdict: CLAIM HOLDS** — mean at ≥200 KB = **+20.47%**.

## Corpora (frozen before the run)

| ID | Source | Genre | Full size | SHA-256 (prefix) |
|---|---|---|---|---|
| austen | Project Gutenberg #1342 *Pride and Prejudice* | literary | 738,046 B | `81300b79e8a8…` |
| rfc8259 | RFC 8259 plain text | technical | 28,360 B | `61a5378f4255…` |
| frankenstein | Project Gutenberg #84 *Frankenstein* | literary/prose | 421,633 B | `06c37d2c52d2…` |

Frozen at `2026-09-15T01:36:30Z`. Slices are UTF-8 prefixes of 50 KB, 200 KB,
and full file (capped at 1 MB). RFC 8259 is shorter than 50 KB, so only the
full file is measured for that source. No commercial news text.

## Results

### Per-sample

| Sample | Raw B | MVDC overhead | Lossy gzip savings |
|---|---|---|---|
| austen (50KB) | 51,200 | +79.1% | **+21.32%** |
| austen (200KB) | 204,800 | +86.7% | **+19.89%** |
| austen (full, 738,046 B) | 738,046 | +89.2% | **+19.66%** |
| rfc8259 (full, 28,360 B) | 28,360 | +69.7% | **+17.31%** |
| frankenstein (50KB) | 51,200 | +94.0% | **+22.53%** |
| frankenstein (200KB) | 204,800 | +93.0% | **+21.21%** |
| frankenstein (full, 421,633 B) | 421,633 | +92.8% | **+21.11%** |

### Aggregates

| Metric | Value |
|---|---|
| Samples measured | 7 |
| Samples ≥ 200 KB | 4 |
| Mean lossy gzip savings (all) | **+20.43%** |
| Mean lossy gzip savings (≥200 KB) | **+20.47%** |

Lossless MVDC + gzip/bz2/zlib remains worse than compressing raw text on every
sample (improvements about −45% to −75%), consistent with Phase 2's synthetic
lossless failure. The positive claim is **lossy only**.

## Relation to Phase 2 synthetic result

| Setting | Mean lossy gzip savings |
|---|---|
| Phase 2 synthetic ~3–7 KB word bags | +14.2% |
| This probe, all real samples | +20.43% |
| This probe, real ≥200 KB only | +20.47% |

The synthetic +14.2% was not an artifact of short word-salad. On Austen and
Frankenstein at 200 KB–738 KB, lossy vowel-drop still saves about **20%** of
gzip size versus gzip on the original text.

## Implications for the paper

- Keep the surviving positive claim: **lossy vowel-dropping before gzip
  reduces compressed size on English prose**, measured on real public-domain
  books as well as synthetic corpora.
- Keep lossless MVD+codec as a clean negative (overhead dominates).
- Keep Phase 3 RAG/token/embedding falsification unchanged.
- Caveat still honest: this is character/byte-level compression, not LLM
  token cost; reversibility does not apply to the lossy path.
