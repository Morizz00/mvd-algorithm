# 02 — What is MVD?

## Name

**MVD** = Maharashtran Vowel Disappearance.

Ignore the fancy name. Mechanically it is:

> Split a string into consonants, vowels, and a position mask.

## The three outputs

For input `S = "Hello"`:

| Piece | Value | Meaning |
|---|---|---|
| `C` (consonants) | `"Hll"` | Everything that is not an ASCII vowel, in order |
| `V` (vowels) | `['e','o']` | Vowels in the order they appeared |
| `M` (mask) | `[0,1,0,0,1]` | `1` means “this position was a vowel” |

### Rebuild (decode)

Walk the mask. When you see `0`, take the next consonant. When you see `1`, take the next vowel.

```text
M: 0 1 0 0 1
   H e l l o
```

You get `"Hello"` back. That is **reversibility**.

## Two ways to use the split

### A. Lossless path (keep everything)

Pack `C`, `V`, and `M` into a binary blob we call **MVDC**, then run gzip/bz2/zlib on that blob.

Hope: separated streams compress better than mixed text.  
Reality in our tests: the packaging overhead is so large that **raw text + gzip wins**.

### B. Lossy path (throw vowels away)

Keep only `C` (`"Hll"`). Compress that with gzip.

Hope: fewer letters → smaller compressed file.  
Reality: **yes**, on both toy corpora and real books (~14% to ~20% gzip savings).  
Cost: you can no longer recover the original spelling.

## What the code looks like (conceptual)

```python
VOWELS = set("aeiouAEIOU")

def mvd_encode(text):
    consonants, vowels, mask = [], [], []
    for ch in text:
        if ch in VOWELS:
            vowels.append(ch)
            mask.append(1)
        else:
            consonants.append(ch)
            mask.append(0)
    return "".join(consonants), vowels, mask
```

Real code:

- Phase 0: `src/mvd_base.py`
- Phase 2 (same idea + compression): `phase2/mvd_comp.py`
- Phase 3 vowel-drop helper: `phase3/common.py` → `vowel_drop()` returns only `C`

## Tiny worked examples

### All vowels

```text
"aeiou" → C="", V=[a,e,i,o,u], M=[1,1,1,1,1]
```

### No vowels

```text
"rhythm" → C="rhythm", V=[], M=[0,0,0,0,0,0]
```

(Wait: `y` is **not** in our vowel set, so `rhythm` is all consonants for MVD.)

### Mixed case

```text
"HeLLo" → vowels keep case: e, o
```

### Spaces and punctuation

```text
"Hi!" → C="H!", V=['i'], M=[0,1,0]
```

Space/punctuation stay in `C`.

## What MVD is not

- Not AES encryption  
- Not a general “make AI smarter” algorithm  
- Not multilingual as implemented (ASCII `aeiou` only)  
- Not magic: lossy mode literally deletes information

## Mental model

Think of English words as **skeletons** (consonants) plus **glue** (vowels).

- Skeletons alone are shorter → sometimes compress better as bytes.  
- Skeletons alone look weird to tokenizers/embedders trained on full spelling → AI proxies break.

That single tension is the whole paper.

## Next

Read [03-chronology-of-experiments.md](03-chronology-of-experiments.md).
