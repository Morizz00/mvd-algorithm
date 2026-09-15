# For dummies (like me)

Welcome. This folder explains the **entire MVD research project** as if you have never taken a CS course. After you finish the reading order below, you should understand:

- what the project tried to do,
- what a “byte,” “token,” and “embedding” are (in plain language),
- what MVD actually does to text,
- what we measured, in what order, and what won vs failed,
- how to find the code and the paper,
- what ideas we *didn’t* run yet (wordgraphs, crypto, etc.).

Nothing here replaces the measured writeups. Those live in `docs/` and `MVD_Progress_Report.md`. This folder is the **gentle path**.

## Reading order (do this in order)

| # | File | Time | Goal |
|---|---|---|---|
| 1 | [00-what-is-this-project.md](00-what-is-this-project.md) | 10 min | Big picture and the one-sentence scoreboard |
| 2 | [01-cs-basics-words-bytes-tokens.md](01-cs-basics-words-bytes-tokens.md) | 25 min | The vocabulary the rest of the repo assumes |
| 3 | [02-what-is-mvd.md](02-what-is-mvd.md) | 20 min | The transform, with a worked example |
| 4 | [03-chronology-of-experiments.md](03-chronology-of-experiments.md) | 20 min | What we did when, and why that order |
| 5 | [04-phase0-explained.md](04-phase0-explained.md) | 15 min | “Does the split even work?” |
| 6 | [05-phase2-compression-explained.md](05-phase2-compression-explained.md) | 25 min | Lossless fail, lossy win, real books |
| 7 | [06-phase3-rag-tokens-embeddings.md](06-phase3-rag-tokens-embeddings.md) | 25 min | Why RAG/token hopes died |
| 8 | [07-how-to-run-the-code.md](07-how-to-run-the-code.md) | 15 min | Commands to reproduce |
| 9 | [08-reading-the-paper.md](08-reading-the-paper.md) | 10 min | How the paper maps to these docs |
| 10 | [09-glossary.md](09-glossary.md) | reference | Look up any word |

Then optionally:

- [../future-ideas/](../future-ideas/) — wordgraphs, crypto, and other unrun directions
- [../docs/REPO_MAP.md](../docs/REPO_MAP.md) — which folder is which

## One-sentence results (spoiler)

MVD can **split** English text into consonants and vowels perfectly; **lossy** “delete the vowels then gzip” shrinks files ~14–20%; **lossless** packaging for gzip fails; trying to make **LLMs/RAG cheaper** by dropping vowels makes tokens *worse* and wrecks embeddings.

## What this folder is not

- Not a substitute for `docs/mvd_paper.tex`
- Not a claim that MVD is a breakthrough product
- Not crypto advice (we never finished that phase)
