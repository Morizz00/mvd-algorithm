# Repository map

How folders relate. Start here if you are lost; start at [`../for-dummies/`](../for-dummies/) if you are new to CS.

## Public story (read in this order)

| Path | What it is |
|---|---|
| [`../for-dummies/`](../for-dummies/) | Beginner explanations (start with its README) |
| [`../MVD_Progress_Report.md`](../MVD_Progress_Report.md) | Measured results scoreboard |
| [`probe_results.md`](probe_results.md) | Phase 3 token + embedding writeup |
| [`real_corpus_compression.md`](real_corpus_compression.md) | Real-text compression claim |
| [`paper_draft.md`](paper_draft.md) / [`mvd_paper.tex`](mvd_paper.tex) | Paper drafts |
| [`../future-ideas/`](../future-ideas/) | Wordgraphs, crypto, and other unrun ideas |

## Code by phase

| Path | Role |
|---|---|
| [`../src/mvd_base.py`](../src/mvd_base.py) | Phase 0 core encode/decode |
| [`../tests/test_phase0.py`](../tests/test_phase0.py) | Phase 0 unit tests |
| [`../benchmarks/phase0_perf.py`](../benchmarks/phase0_perf.py) | Phase 0 timing |
| [`../phase2/mvd_comp.py`](../phase2/mvd_comp.py) | Compression + MVDC + synthetic corpora |
| [`../phase2/real_corpus_probe.py`](../phase2/real_corpus_probe.py) | Real Gutenberg/RFC compression probe |
| [`../phase2/fetch_real_corpora.py`](../phase2/fetch_real_corpora.py) | Download frozen real corpora |
| [`../phase3/`](../phase3/) | Token + embedding Stage A probes |
| [`../phase1/`](../phase1/) | Empty — crypto never started |

## Data and logs

| Path | Role |
|---|---|
| [`../data/test/`](../data/test/) | Tiny unit/edge fixtures |
| [`../data/real/manifest.json`](../data/real/manifest.json) | Frozen real-corpus metadata (SHA-256, URLs) |
| [`../data/real/raw/`](../data/real/raw/) | Downloaded `.txt` (gitignored; re-fetch locally) |
| `*_output.log` at repo root | Local console transcripts (**gitignored**; numbers are in the writeups above) |

## Design / agent plans (advanced)

| Path | Role |
|---|---|
| [`superpowers/specs/`](superpowers/specs/) | Design specs (RAG probe, wordgraphs) |
| [`superpowers/plans/`](superpowers/plans/) | Step-by-step implementation plans |
| [`phase0_report.md`](phase0_report.md) | Early Phase 0 note |
| [`progress_report_pre_rag.md`](progress_report_pre_rag.md) | Pre–Phase-3 snapshot |

## Root entry points

| Path | Role |
|---|---|
| [`../README.md`](../README.md) | Landing page + long original roadmap |
| [`../requirements.txt`](../requirements.txt) | Python deps |
| `SETUP_INSTRUCTIONS.md`, `setup.sh`, `run_*.sh` | Local convenience (gitignored) |
