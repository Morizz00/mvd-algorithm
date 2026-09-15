# Crypto and other future ideas

## Phase 1 — cryptographic preprocessing (not started)

### The pitch (from the original roadmap)

Use a **key** so that which vowels move/drop depends on a secret. Then treat MVD as a *preprocess* before a real cipher like AES.

Hoped benefits people sometimes claim:

- mess up language-shaped patterns before encryption  
- raise measured entropy a bit  
- confuse naive language detection on the intermediate form

### Why we did not prioritize it

1. MVD alone is **not** a cipher. Reviewers will ask what AES didn’t already give you.  
2. Consonant skeletons still look like language (frequency attacks may survive).  
3. Our other results show the transform is linguistically brittle for ML — not a great omen for “helpful uncertainty.”  
4. Doing crypto *right* needs a threat model and careful stats; easy to overclaim.

### If someone runs a “kill probe” later

Cheapest honesty checks (half-day vibe):

- Shannon entropy of plaintext bytes vs MVD intermediate bytes  
- Off-the-shelf language-ID accuracy on consonants-only text  

If those don’t move in a useful way, close Phase 1 as another clean negative.

Folder `phase1/` is reserved and currently empty on purpose.

---

## Other languages

Current vowel set is English ASCII `aeiou`.  

Future work could define per-language vowel sets (Spanish accents, German umlauts, etc.).  
**Not measured.** Do not imply multilingual wins in the paper.

---

## Partial / adaptive vowel removal

Instead of deleting *all* vowels, delete only “safe” ones (keep first/last, keep diphthongs, learn a predictor).

Phase 3’s gate said: we only chase partial removal if tokens dropped *and* similarity failed.  
**Both failed**, so this follow-on is optional curiosity, not required by the protocol.

---

## Learned codecs / tokenizer training

Ideas from the long README “Future Work” section:

- train a codebook on vowel streams  
- train BPE on vowel-dropped text  
- streaming MVD  
- neural vowel reconstruction (“fill vowels back in”)

All speculative. None have logs in this repo.

---

## Hardware / streaming / cross-modal

README brainstorms CUDA kernels, speech vowel/consonant splits, etc.  
Treat as science fiction relative to the measured paper.

---

## How these relate to the published story

| Idea | Relationship |
|---|---|
| Lossy gzip win | **Measured** — keep |
| RAG token/embedding fail | **Measured** — keep |
| Phase 1 crypto | Unrun — optional appendix |
| Wordgraphs | Unrun — new thread |
| Multilingual / adaptive / learned | Unrun — backlog |

When writing, put these under **Future work** or a separate note like this folder — never under **Results**.
