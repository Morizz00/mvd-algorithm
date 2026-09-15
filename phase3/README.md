# Phase 3 — LLM / RAG Stage A probes

Cheap proxies **before** building a full RAG stack. Gate said: do not build Phase 4.

| File | Role |
|---|---|
| `common.py` | Shared sentence loading / helpers |
| `token_probe.py` | tiktoken counts: original vs vowel-dropped |
| `embedding_probe.py` | Cosine similarity of sentence embeddings |
| `sentences.json` | Fixed probe sentences |
| `test_*.py` | Unit tests for the probes |

Results: root `phase3_token_output.log`, `phase3_embedding_output.log`, and [`../docs/probe_results.md`](../docs/probe_results.md).

Beginner explanation: [`../for-dummies/06-phase3-rag-tokens-embeddings.md`](../for-dummies/06-phase3-rag-tokens-embeddings.md).
