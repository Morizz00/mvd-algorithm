# Phase 2 — compression probes

| File | Role |
|---|---|
| `mvd_comp.py` | Synthetic corpora + lossless MVDC + lossy vowel-drop vs gzip/bz2/zlib |
| `fetch_real_corpora.py` | Download frozen real texts into `../data/real/raw/` |
| `real_corpus_probe.py` | Same metrics on real books/RFC |
| `phase2-setup.sh` | Env helper |

Results: root `phase2_output.log`, `phase2_real_corpus_output.log`, and [`../docs/real_corpus_compression.md`](../docs/real_corpus_compression.md).

Beginner explanation: [`../for-dummies/05-phase2-compression-explained.md`](../for-dummies/05-phase2-compression-explained.md).
