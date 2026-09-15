# 09 — Glossary

| Term | Plain meaning in this repo |
|---|---|
| **ASCII** | Simple English letter encoding; one common letter ≈ one byte |
| **Abjad** | Writing system that often omits short vowels (Arabic/Hebrew vibes); mentioned as cultural analogy only |
| **BPE** | Byte-Pair Encoding — how many LLM tokenizers build their vocabulary |
| **Byte** | Smallest size unit we care about for file compression |
| **Catastrophic rate** | Share of sentence pairs with embedding similarity &lt; 0.6 |
| **Consonant (MVD)** | Any character not in `{a,e,i,o,u,A,E,I,O,U}` |
| **Cosine similarity** | Score of how aligned two embedding vectors are (−1…1) |
| **Corpus** | A pile of text used for an experiment |
| **Decision gate** | Pre-written pass/fail rules that decide whether to continue |
| **Embedding** | List of numbers representing meaning for a model |
| **Frozen data** | Dataset locked before looking at scores |
| **gzip / bz2 / zlib** | Standard lossless compressors |
| **Lossless** | Exact original recoverable |
| **Lossy** | Information thrown away on purpose |
| **Mask** | 0/1 list marking vowel positions |
| **MiniLM** | Small sentence embedding model (`all-MiniLM-L6-v2`) |
| **MVDC** | Our binary serialization of consonants+vowels+mask |
| **MVD** | Maharashtran Vowel Disappearance transform |
| **Negative result** | Hypothesis tested and shown false (still useful science) |
| **Phase 0** | Correctness + speed of the split |
| **Phase 1** | Crypto ideas — **not implemented** |
| **Phase 2** | Compression experiments |
| **Phase 3** | Token + embedding probes (Stage A) |
| **Phase 4** | Full RAG — **cancelled** by the gate |
| **RAG** | Retrieval-Augmented Generation |
| **Reduction % (tokens)** | `(old−new)/old×100`; negative means tokens increased |
| **Reversible** | Can rebuild the exact original string |
| **Scenario 4** | Our label for “both Stage A metrics failed” |
| **Seed** | Number that fixes randomness (`42` here) |
| **SHA-256** | Fingerprint hash used to prove a downloaded file matches the manifest |
| **Stage A** | Cheap probes before building RAG |
| **Stage B** | Full retrieval pipeline (not built) |
| **Synthetic corpus** | Computer-made text for reproducible tests |
| **tiktoken** | OpenAI-style tokenizer library |
| **Token** | Chunk of text an LLM reads as one unit |
| **Unweighted mean** | Average of per-corpus scores, each corpus equal |
| **Vowel (MVD)** | `a e i o u` and uppercase versions only |
| **Wordgraphs** | Future idea: treat words as graphs around consonant skeletons |

Back to [README.md](README.md).
