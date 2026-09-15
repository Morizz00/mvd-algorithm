# 07 — How to run the code (step by step)

Assumes you can open a terminal in the repo root  
`.../research/mvd`.

## 0. Python

You want Python 3.9+ (3.11 is fine). Check:

```bash
python --version
```

## 1. Virtual environment (recommended)

```bash
python -m venv mvd-env
```

Activate:

- Windows PowerShell: `.\mvd-env\Scripts\Activate.ps1`  
- Linux/macOS: `source mvd-env/bin/activate`

Install deps:

```bash
pip install -r requirements.txt
```

`mvd-env/` is gitignored — it stays on your machine only.

## 2. Phase 0 tests

```bash
python -m pytest tests/test_phase0.py -v
```

Optional timing:

```bash
python benchmarks/phase0_perf.py
```

## 3. Phase 2 synthetic compression suite

```bash
python phase2/mvd_comp.py
```

Expect a final line like `38 passed`.

## 4. Real corpora (optional local download)

Large `.txt` files are gitignored. Recreate them:

```bash
python phase2/fetch_real_corpora.py
python phase2/real_corpus_probe.py
```

## 5. Phase 3 probes

```bash
python -m pytest phase3 -v
python phase3/token_probe.py
python phase3/embedding_probe.py
```

First embedding run may download the MiniLM model (needs network once).

## 6. What not to commit

- `.env` (secrets)  
- `mvd-env/`  
- agent folders like `.specstory/`  
- downloaded `data/real/raw/*.txt` (re-fetch instead)

See `.gitignore` and `.env.example`.

## If something fails

| Symptom | Likely fix |
|---|---|
| `No module named pytest` | use the venv; `pip install -r requirements.txt` |
| `No module named tiktoken` | `pip install tiktoken` |
| Embedding download hangs | check network / Hugging Face access |
| Real probe can’t find files | run `fetch_real_corpora.py` first |

## Next

[08-reading-the-paper.md](08-reading-the-paper.md)
