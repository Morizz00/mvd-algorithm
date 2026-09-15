# 01 — CS basics: words, bytes, tokens, embeddings, compression

You do not need a degree. You need a few pictures in your head.

## 1. Text is just a list of characters

`"Hello"` is five characters: `H e l l o`.

In our MVD code, a **vowel** is one of:

```text
a e i o u A E I O U
```

Everything else (letters like `H`, spaces, commas, digits, emoji, accented letters like `é`) is treated as a **consonant** for this project. That is a design choice, not a linguistics exam answer.

**Example**

```text
Hello World
H e l l o   W o r l d
C V C C V C C V C C V
```

Consonant stream: `Hll Wrld`  
Vowels in order: `e, o, o`  
Mask (1 = vowel): `0,1,0,0,1, 0, 0,1,0,0,1`

## 2. Bytes: how disks count size

Computers store text as **bytes** (8-bit chunks). For simple English ASCII, one letter ≈ one byte.

- `"Hi"` ≈ 2 bytes  
- A 200 KB file ≈ 200 × 1024 bytes of text

When we say “gzip savings +20%,” we mean:

> After gzip, the vowel-dropped version uses about 20% *fewer bytes* than gzip of the original.

We are talking about **file size**, not “how smart the AI is.”

## 3. Compression (gzip) in one paragraph

**Compression** tries to store the same information with fewer bytes by noticing patterns (“the” appears a lot, long runs of spaces, etc.).

**gzip** is a common compressor. You give it bytes; it gives back fewer bytes (usually). To read the file again you decompress.

Important:

- Compressing **already random** data barely helps.
- Compressing **English** usually helps a lot.
- If your preprocess adds a big header, gzip may not recover that cost → net **worse** file. That is what happened to our **lossless** MVD packaging.

## 4. Lossy vs lossless

| Word | Meaning | Everyday analogy |
|---|---|---|
| **Lossless** | You can get the exact original back | ZIP of a document |
| **Lossy** | You throw information away on purpose | JPEG that blurs fine detail |

MVD has both modes:

- **Lossless MVD:** keep consonants + vowels + mask → can rebuild `"Hello World"` exactly.
- **Lossy vowel-drop:** keep only consonants → `"Hll Wrld"` — you **cannot** know the original vowels for sure.

Our only strong compression win is the **lossy** path.

## 5. Tokens: how LLMs bill and think

Large language models (ChatGPT-style systems) do not read letters one-by-one the way you do. They chop text into **tokens** — little pieces of words.

Example (simplified intuition, not exact):

```text
beautiful   →  maybe 1–2 tokens
btfl        →  maybe many tiny pieces, because the model never “learned” btfl as a word
```

**tiktoken** with encoding `cl100k_base` is the tokenizer family used around GPT-4-class models. We count:

```text
reduction % = (tokens_original - tokens_dropped) / tokens_original × 100
```

- Positive reduction → fewer tokens (cheaper / shorter context) — **good for the RAG hope**  
- Negative reduction → *more* tokens — **bad**

Our average was about **−76.8%** (tokens went **up** ~77%).

### Why that happens (the key insight)

Tokenizers are trained on **normal spelling**.  
`beautiful` is common → short token ID.  
`btfl` looks alien → split into awkward scraps → **more** IDs, even though fewer letters.

So: **fewer characters ≠ fewer tokens.**

## 6. Embeddings: turning sentences into arrows

An **embedding** is a list of numbers that represents “what this sentence is about” for a model. Similar meanings → arrows pointing similar directions.

We used `all-MiniLM-L6-v2` (a small local model). For each sentence we compute:

```text
cosine similarity( original_embedding , vowel_dropped_embedding )
```

- `1.0` = identical direction  
- `0.0` = unrelated (orthogonal)  
- negative = somewhat opposite

We hoped similarity would stay ≥ **0.85**.  
We got about **0.17** on average. Almost nothing useful left for retrieval.

**Catastrophic** in our gate: similarity &lt; 0.6. That happened for **29 of 30** pairs.

## 7. RAG in one paragraph

**RAG** = Retrieval-Augmented Generation.

1. Chop documents into chunks.  
2. Embed chunks into a vector database.  
3. On a question, embed the question, find nearest chunks.  
4. Stuff those chunks into an LLM prompt.

Cost drivers include **token counts** (LLM fees / context limits) and **embedding quality** (did you retrieve the right chunk?).

We never built the full RAG system. We tested the two cheapest make-or-break questions first (tokens + embedding similarity). Both failed → **stop**; don’t build Stage B.

## 8. Synthetic vs real text

| Kind | What we used it for |
|---|---|
| **Synthetic** | Computer-generated bags of words with a fixed random seed (`42`) so runs match forever |
| **Real** | Public-domain books (Austen, Frankenstein) and an RFC technical document |

Synthetic text is allowed for compression/token counting continuity. Embeddings need real(ish) sentences, so we froze a 30-sentence file before measuring.

## 9. Seeds and “frozen” data

- **`random.seed(42)`** — same fake corpora every time.  
- **Frozen `sentences.json`** — we promised not to edit sentences after seeing scores (anti-cherry-picking).  
- **`data/real/manifest.json`** — records URLs and SHA-256 hashes of downloaded books.

## Next

Read [02-what-is-mvd.md](02-what-is-mvd.md).
