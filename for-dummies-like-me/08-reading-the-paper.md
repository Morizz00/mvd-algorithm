# 08 — Reading the paper

## Files

| File | Form |
|---|---|
| `docs/paper_draft.md` | Markdown draft (easy to read in GitHub) |
| `docs/mvd_paper.tex` | arXiv-style LaTeX (Kour `arxiv` package) |

Same scientific claims; LaTeX is for PDF / arXiv.

## How sections map to this folder

| Paper section | For-dummies guide |
|---|---|
| Abstract / Intro | [00](00-what-is-this-project.md), [03](03-chronology-of-experiments.md) |
| Method: MVD | [02](02-what-is-mvd.md) |
| Phase 0 | [04](04-phase0-explained.md) |
| Compression | [05](05-phase2-compression-explained.md) |
| Tokens / embeddings | [06](06-phase3-rag-tokens-embeddings.md) |
| “Why byte wins invert” | [01](01-cs-basics-words-bytes-tokens.md) §5–6 |
| Limitations / future | [../future-ideas/](../future-ideas/) |

## What the paper is arguing (one paragraph)

We measured a tiny linguistic preprocess. It works as a reversible split. Packing it losslessly for gzip fails. Dropping vowels helps gzip on English prose (~15–20%). The same drop makes BPE token counts worse and wrecks embeddings. Therefore vowel dropping is a **narrow byte trick**, not an LLM/RAG cost lever.

## What the paper is *not* arguing

- “We beat LLMLingua.”  
- “Ship this in production search.”  
- “We invented encryption.”

## Before you submit to arXiv

Checklist from the LaTeX notes (see also paper footer):

- [ ] Add real bibliography citations (LLMLingua, BPE, etc.)  
- [ ] Remove any internal “notes for revision” section from the PDF  
- [ ] Confirm `arxiv.sty` is in the Overleaf/project folder  
- [ ] Decide news-sentence licensing if you publish `phase3/sentences.json`  
- [ ] Fix PDF author metadata if coauthors change  

## Next

Keep [09-glossary.md](09-glossary.md) open while reading the paper, then visit [../future-ideas/](../future-ideas/).
