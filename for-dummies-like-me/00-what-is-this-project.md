# 00 — What is this project?

## The elevator pitch

Computers store English as letters. Some letters are **vowels** (`a e i o u`) and the rest we treat as **consonants** (including spaces and punctuation in our code).

**MVD** (“Maharashtran Vowel Disappearance”) is a tiny program that:

1. pulls the vowels out of a string,
2. keeps the leftover consonants in order,
3. remembers *where* the vowels were (a mask),

so you can either:

- put the text back together perfectly (**reversible**), or  
- throw the vowels away on purpose (**lossy**) and see if that helps storage or AI systems.

This repo is a **research lab notebook**: we wrote the transform, ran experiments, and wrote down wins and losses honestly.

## Why anyone would care

Three hopes people sometimes have about vowels:

1. **Compression:** “If I rearrange or drop redundant vowels, files get smaller.”
2. **Encryption preprocessing:** “Messing up language structure might help crypto.” (We designed this; we did **not** finish testing it.)
3. **LLM / RAG cost:** “If I drop vowels, AI models might use fewer tokens and still understand the text.”

We tested (1) carefully and (3) carefully. (2) is still only a design.

## The scoreboard (memorize this)

| Question | Answer |
|---|---|
| Can we split and rebuild text? | **Yes** (Phase 0) |
| Does fancy lossless packing beat normal gzip? | **No** — it gets worse |
| Does deleting vowels then gzip help? | **Yes** — ~14% on toy text, ~20% on real books |
| Does that make ChatGPT-style tokenizers cheaper? | **No** — tokens usually *increase* |
| Do sentence embeddings still match after vowel drop? | **No** — similarity collapses |
| Should we build a full RAG search system on this? | **No** — the early tests already failed |

## What “success” means here

In this project, success is **not** “we built a product.” Success is:

- a clear hypothesis,
- a frozen dataset or fixed random seed,
- a number you can re-run,
- an honest sentence when the hypothesis dies.

Failing an experiment is still a publishable result if you explain *why*.

## Where the “real” docs live

After this folder, the adult versions are:

- `MVD_Progress_Report.md` — full status memo
- `docs/probe_results.md` — token/embedding numbers
- `docs/real_corpus_compression.md` — book-scale gzip numbers
- `docs/paper_draft.md` / `docs/mvd_paper.tex` — paper

## Next

Read [01-cs-basics-words-bytes-tokens.md](01-cs-basics-words-bytes-tokens.md).
