# RAG/Chunking Probe (Stage A) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Empirically test whether MVD vowel-dropping reduces LLM token counts and preserves embedding similarity, to decide whether the RAG/chunking angle merits a full retrieval pipeline (Stage B) or should be written up as a negative/mixed result.

**Architecture:** Two small, independent probe scripts under a new `phase3/` directory. Experiment 1 (token reduction) reuses Phase 2's exact synthetic corpora via a small, behavior-preserving refactor of `phase2/mvd_comp.py`. Experiment 2 (embedding similarity) runs against a new, hand-curated and web-verified sentence dataset frozen in its own commit before any comparison is run. Both experiments produce numbers that feed directly into a results doc and a decision-gate verdict.

**Tech Stack:** Python 3.9, pytest, tiktoken (`cl100k_base`), sentence-transformers (`all-MiniLM-L6-v2`), numpy. All already in `requirements.txt` and confirmed installed/working in this environment (model already cached locally).

## Global Constraints

- Python 3.9 (matches the project's installed interpreter; see `test_output.log` header).
- Reuse `mvd_encode` from `phase2/mvd_comp.py` for vowel/consonant splitting — do not reimplement vowel-dropping logic elsewhere.
- Token counting uses `tiktoken.get_encoding("cl100k_base")`.
- Embedding similarity uses `SentenceTransformer("all-MiniLM-L6-v2")` (local model, no API key).
- `phase3/sentences.json` is frozen once committed in Task 1. No task after Task 1 may edit its sentence text or sources. If a later task finds a defect, the fix and the reason must be recorded explicitly in `docs/probe_results.md` — never a silent edit.
- Decision gate thresholds (from `docs/superpowers/specs/2026-06-28-rag-chunking-probe-design.md`): mean token reduction ≥ 15%, mean cosine similarity ≥ 0.85, catastrophic failure rate (similarity < 0.6) < 10%.
- Follow the existing project import convention: no packages/`__init__.py`, use `sys.path.insert(0, ...)` with paths built from `os.path.dirname(__file__)` (see `tests/test_phase0.py` for the established pattern, adapted to be CWD-independent).

---

### Task 1: Freeze the sentence dataset

**Files:**
- Create: `phase3/sentences.json`
- Create: `phase3/common.py`
- Test: `phase3/test_common.py`

**Interfaces:**
- Produces: `vowel_drop(text: str) -> str` and `load_sentences(path: str) -> dict` (both in `phase3/common.py`), and `REQUIRED_CATEGORIES: set` — later tasks (2, 4, 5) import these directly: `from common import vowel_drop, load_sentences`.
- `load_sentences()` returns `{"frozen_at": str, "categories": {category_name: [{"text": str, "source": str, "synthetic": bool}, ...]}}`.

- [ ] **Step 1: Create the frozen sentence dataset**

Create `phase3/sentences.json` with this exact content. Literary lines are verbatim public-domain text (Project Gutenberg). Technical lines are verbatim or lightly paraphrased (flagged) from public documentation/specs. News lines are verbatim headlines/ledes from a dated, cited source. Vowel-heavy/consonant-heavy lines are hand-constructed because no natural corpus of this kind exists — each is marked `"synthetic": true`.

```json
{
  "frozen_at": "2026-06-28",
  "categories": {
    "literary": [
      {"text": "It is a truth universally acknowledged, that a single man in possession of a good fortune must be in want of a wife.", "source": "Jane Austen, Pride and Prejudice (Project Gutenberg #1342)", "synthetic": false},
      {"text": "Call me Ishmael.", "source": "Herman Melville, Moby-Dick (Project Gutenberg #2701)", "synthetic": false},
      {"text": "It was the best of times, it was the worst of times, it was the age of wisdom, it was the age of foolishness, it was the epoch of belief, it was the epoch of incredulity, it was the season of Light, it was the season of Darkness, it was the spring of hope, it was the winter of despair, we had everything before us, we had nothing before us, we were all going direct to Heaven, we were all going direct the other way--in short, the period was so far like the present period, that some of its noisiest authorities insisted on its being received, for good or for evil, in the superlative degree of comparison only.", "source": "Charles Dickens, A Tale of Two Cities (Project Gutenberg #98)", "synthetic": false},
      {"text": "Alice was beginning to get very tired of sitting by her sister on the bank, and of having nothing to do: once or twice she had peeped into the book her sister was reading, but it had no pictures or conversations in it, \"and what is the use of a book,\" thought Alice \"without pictures or conversations?\"", "source": "Lewis Carroll, Alice's Adventures in Wonderland (Project Gutenberg #11)", "synthetic": false},
      {"text": "You will rejoice to hear that no disaster has accompanied the commencement of an enterprise which you have regarded with such evil forebodings.", "source": "Mary Shelley, Frankenstein (Project Gutenberg #84)", "synthetic": false},
      {"text": "You don't know about me without you have read a book by the name of The Adventures of Tom Sawyer; but that ain't no matter.", "source": "Mark Twain, Adventures of Huckleberry Finn (Project Gutenberg #76)", "synthetic": false}
    ],
    "technical": [
      {"text": "One of Guido's key insights is that code is read much more often than it is written.", "source": "PEP 8 (peps.python.org/pep-0008)", "synthetic": false},
      {"text": "The key words \"MUST\", \"MUST NOT\", \"REQUIRED\", \"SHALL\", \"SHALL NOT\", \"SHOULD\", \"SHOULD NOT\", \"RECOMMENDED\", \"MAY\", and \"OPTIONAL\" in this document are to be interpreted as described in RFC 2119.", "source": "RFC 2119 (rfc-editor.org/rfc/rfc2119)", "synthetic": false},
      {"text": "Python is an easy to learn, powerful programming language.", "source": "Python 3 official tutorial (docs.python.org/3/tutorial/index.html)", "synthetic": false},
      {"text": "JavaScript Object Notation (JSON) is a lightweight, text-based, language-independent data interchange format.", "source": "RFC 8259 abstract (rfc-editor.org/rfc/rfc8259)", "synthetic": false},
      {"text": "A container is a runnable instance of an image.", "source": "Docker documentation, paraphrased (docs.docker.com/get-started/docker-overview)", "synthetic": false},
      {"text": "HTTP is a protocol for fetching resources such as HTML documents.", "source": "MDN Web Docs, HTTP overview (developer.mozilla.org/en-US/docs/Web/HTTP/Overview)", "synthetic": false}
    ],
    "news": [
      {"text": "Over 500 Are Dead and Thousands Remain Missing Following Twin Earthquakes in Venezuela", "source": "Democracy Now! Headlines, June 26, 2026 (democracynow.org/2026/6/26/headlines)", "synthetic": false},
      {"text": "The International Maritime Organization has paused its evacuation of thousands of stranded sailors and hundreds of cargo ships from the Persian Gulf.", "source": "Democracy Now! Headlines, June 26, 2026 (democracynow.org/2026/6/26/headlines)", "synthetic": false},
      {"text": "Israeli airstrikes killed two people and wounded a third in southern Lebanon, while Israeli soldiers bulldozed and burned homes.", "source": "Democracy Now! Headlines, June 26, 2026 (democracynow.org/2026/6/26/headlines)", "synthetic": false},
      {"text": "The Supreme Court has ruled in favor of the Trump administration's policy of denying people at the U.S.-Mexico border a chance to seek asylum.", "source": "Democracy Now! Headlines, June 26, 2026 (democracynow.org/2026/6/26/headlines)", "synthetic": false},
      {"text": "New York City's Rent Guidelines Board has voted to freeze rents for the next two years for nearly 1 million rent-stabilized apartments.", "source": "Democracy Now! Headlines, June 26, 2026 (democracynow.org/2026/6/26/headlines)", "synthetic": false},
      {"text": "The court ruled 7 to 2 to restrict thousands of lawsuits claiming Bayer, the parent company of Monsanto, had a duty to warn consumers about potential cancer risks from its popular weed killer Roundup.", "source": "Democracy Now! Headlines, June 26, 2026 (democracynow.org/2026/6/26/headlines)", "synthetic": false}
    ],
    "vowel_heavy": [
      {"text": "The aerial audio equipment created a beautiful echo in the auditorium.", "source": "hand-constructed for this experiment (no natural vowel-heavy corpus exists)", "synthetic": true},
      {"text": "A queue formed outside the aquarium to see the unique aquatic creatures.", "source": "hand-constructed for this experiment (no natural vowel-heavy corpus exists)", "synthetic": true},
      {"text": "The oasis appeared as an idea too good to be true in the arid area.", "source": "hand-constructed for this experiment (no natural vowel-heavy corpus exists)", "synthetic": true},
      {"text": "An eerie aura surrounded the ancient oak tree near the quiet bayou.", "source": "hand-constructed for this experiment (no natural vowel-heavy corpus exists)", "synthetic": true},
      {"text": "The aviator radioed coordinates while flying over the equatorial ocean.", "source": "hand-constructed for this experiment (no natural vowel-heavy corpus exists)", "synthetic": true},
      {"text": "Audio engineers adjusted the equalizer to remove unwanted feedback noise.", "source": "hand-constructed for this experiment (no natural vowel-heavy corpus exists)", "synthetic": true}
    ],
    "consonant_heavy": [
      {"text": "Strength training strengthens wrists, ankles, and lymph flow through rhythmic stretching.", "source": "hand-constructed for this experiment (no natural consonant-heavy corpus exists)", "synthetic": true},
      {"text": "The cryptographer deciphered glyphs scrawled across crumbling crypts and scrolls.", "source": "hand-constructed for this experiment (no natural consonant-heavy corpus exists)", "synthetic": true},
      {"text": "Nymphs and gypsies danced to rhythmic synth scratches at midnight trysts.", "source": "hand-constructed for this experiment (no natural consonant-heavy corpus exists)", "synthetic": true},
      {"text": "The blacksmith forged scythes, tongs, and sturdy iron clamps by twilight.", "source": "hand-constructed for this experiment (no natural consonant-heavy corpus exists)", "synthetic": true},
      {"text": "Lymphatic dysfunction triggered strength deficits despite strict strength regimens.", "source": "hand-constructed for this experiment (no natural consonant-heavy corpus exists)", "synthetic": true},
      {"text": "Glyphs, scripts, and crypts filled the dusty archive's forgotten shelves.", "source": "hand-constructed for this experiment (no natural consonant-heavy corpus exists)", "synthetic": true}
    ]
  }
}
```

- [ ] **Step 2: Create the shared helper module**

Create `phase3/common.py`:

```python
"""Shared helpers for the Phase 3 RAG/chunking probe."""
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'phase2'))
from mvd_comp import mvd_encode  # noqa: E402

REQUIRED_CATEGORIES = {'literary', 'technical', 'news', 'vowel_heavy', 'consonant_heavy'}
SYNTHETIC_CATEGORIES = {'vowel_heavy', 'consonant_heavy'}


def vowel_drop(text: str) -> str:
    """Return text with all vowels removed (the consonant stream)."""
    consonants, _, _ = mvd_encode(text)
    return consonants


def load_sentences(path: str) -> dict:
    """Load and schema-validate the frozen sentence dataset."""
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    categories = data['categories']
    missing = REQUIRED_CATEGORIES - set(categories.keys())
    if missing:
        raise ValueError(f"Missing categories: {missing}")

    for name, entries in categories.items():
        if not (6 <= len(entries) <= 10):
            raise ValueError(f"Category '{name}' has {len(entries)} entries, expected 6-10")
        expected_synthetic = name in SYNTHETIC_CATEGORIES
        for entry in entries:
            if not entry.get('text'):
                raise ValueError(f"Entry in '{name}' missing non-empty 'text'")
            if not entry.get('source'):
                raise ValueError(f"Entry in '{name}' missing non-empty 'source'")
            if 'synthetic' not in entry:
                raise ValueError(f"Entry in '{name}' missing 'synthetic' flag")
            if expected_synthetic and not entry['synthetic']:
                raise ValueError(f"Entry in '{name}' must be marked synthetic=true")
            if not expected_synthetic and entry['synthetic']:
                raise ValueError(f"Entry in '{name}' must be marked synthetic=false")

    return data
```

- [ ] **Step 3: Write the schema/helper tests**

Create `phase3/test_common.py`:

```python
import json
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(__file__))
from common import vowel_drop, load_sentences, REQUIRED_CATEGORIES  # noqa: E402


def _valid_categories_dict():
    return {
        cat: [
            {
                "text": f"sample {i}",
                "source": "test",
                "synthetic": cat in ("vowel_heavy", "consonant_heavy"),
            }
            for i in range(6)
        ]
        for cat in REQUIRED_CATEGORIES
    }


def test_vowel_drop_removes_vowels():
    assert vowel_drop("Hello World") == "Hll Wrld"


def test_vowel_drop_empty_string():
    assert vowel_drop("") == ""


def test_load_sentences_valid_schema(tmp_path):
    data = {"frozen_at": "2026-06-28", "categories": _valid_categories_dict()}
    p = tmp_path / "sentences.json"
    p.write_text(json.dumps(data), encoding='utf-8')
    loaded = load_sentences(str(p))
    assert set(loaded['categories'].keys()) == REQUIRED_CATEGORIES


def test_load_sentences_rejects_missing_category(tmp_path):
    data = {"frozen_at": "x", "categories": {"literary": []}}
    p = tmp_path / "bad.json"
    p.write_text(json.dumps(data), encoding='utf-8')
    with pytest.raises(ValueError, match="Missing categories"):
        load_sentences(str(p))


def test_load_sentences_rejects_wrong_count(tmp_path):
    cats = _valid_categories_dict()
    cats['literary'] = cats['literary'][:1]  # only 1 entry
    data = {"frozen_at": "x", "categories": cats}
    p = tmp_path / "bad.json"
    p.write_text(json.dumps(data), encoding='utf-8')
    with pytest.raises(ValueError, match="expected 6-10"):
        load_sentences(str(p))


def test_load_sentences_rejects_mislabeled_synthetic_flag(tmp_path):
    cats = _valid_categories_dict()
    cats['vowel_heavy'][0]['synthetic'] = False  # should be True
    data = {"frozen_at": "x", "categories": cats}
    p = tmp_path / "bad.json"
    p.write_text(json.dumps(data), encoding='utf-8')
    with pytest.raises(ValueError, match="synthetic=true"):
        load_sentences(str(p))


def test_real_sentences_file_is_valid():
    """The actual frozen dataset must pass schema validation and have >=30 sentences."""
    path = os.path.join(os.path.dirname(__file__), 'sentences.json')
    data = load_sentences(path)
    total = sum(len(v) for v in data['categories'].values())
    assert total >= 30
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `python -m pytest phase3/test_common.py -v` (from repo root)
Expected: 6 passed

- [ ] **Step 5: Commit — this freezes the sentence dataset**

```bash
git add phase3/sentences.json phase3/common.py phase3/test_common.py
git commit -m "Add frozen Phase 3 sentence dataset and shared probe helpers

Sentence set is frozen as of this commit per the design spec's freeze
rule: no comparison has been run against it yet, and no edits to
sentence text/sources are permitted after this point."
```

---

### Task 2: Expose Phase 2's corpora as a reusable function

**Files:**
- Modify: `phase2/mvd_comp.py:339` (inside `run_all_tests`, replacing the inline block currently at lines 476-513)

**Interfaces:**
- Produces: `get_phase2_corpora() -> dict[str, str]` (top-level function in `phase2/mvd_comp.py`) — Task 3 imports this directly: `from mvd_comp import get_phase2_corpora`.
- Consumes: nothing new: uses only the `random` stdlib module, already used inline at this location.

This is a behavior-preserving refactor: the exact same word lists and `random.seed(42)` call move from being inline in `run_all_tests()` to a standalone function, called from the same place in the same order. Output must be byte-for-byte identical.

- [ ] **Step 1: Add the new function**

In `phase2/mvd_comp.py`, add this function immediately before `def run_all_tests():` (currently at line 339):

```python
def get_phase2_corpora() -> Dict[str, str]:
    """
    Build the same 5 synthetic diverse corpora used in Phase 2's compression
    benchmarks. Deterministic (seed=42) so results are reproducible and
    comparable across phases.
    """
    import random as _rand
    _rand.seed(42)

    def _make_diverse(word_pool, n):
        return ' '.join(_rand.choices(word_pool, k=n))

    literature_words = [
        "the", "and", "of", "to", "a", "in", "that", "was", "he", "for",
        "on", "are", "with", "as", "his", "they", "at", "be", "this", "from",
        "beautiful", "extraordinary", "silence", "whispered", "ancient",
        "mysterious", "shadow", "horizon", "wandering", "forgotten",
    ]
    technical_words = [
        "function", "return", "initialize", "context", "database", "connection",
        "protocol", "encryption", "algorithm", "implementation", "framework",
        "evaluation", "parameter", "configuration", "authentication", "request",
        "response", "buffer", "stream", "processor", "module", "interface",
    ]
    news_words = [
        "government", "officials", "announced", "regulations", "technology",
        "sector", "industry", "market", "economy", "international", "foreign",
        "national", "security", "policy", "committee", "statement", "report",
        "investigation", "legislation", "development", "agreement", "summit",
    ]

    return {
        "diverse_literature (5K)": _make_diverse(literature_words, 900),
        "diverse_technical  (5K)": _make_diverse(technical_words, 700),
        "diverse_news       (5K)": _make_diverse(news_words, 750),
        "vowel_heavy words  (5K)": _make_diverse([
            "beautiful", "audio", "queue", "aura", "idealize", "opaque",
            "oboe", "ukulele", "iodine", "outwit", "aqueous", "aioli",
        ], 400),
        "consonant_heavy    (5K)": _make_diverse([
            "rhythm", "strength", "crypt", "lymph", "glyph", "myths",
            "tryst", "nymph", "psych", "lynch", "gypsy", "pygmy",
        ], 500),
    }
```

- [ ] **Step 2: Replace the inline block inside `run_all_tests()`**

Find this block (currently lines 471-513 inside `run_all_tests()`):

```python
    # Use diverse, non-repetitive text so that gzip does not trivially
    # compress 99% of the source before MVD overhead matters.
    # MVD-COMP's advantage appears in the consonant/vowel stream separation
    # BEFORE the codec runs - but only when the codec can't trivially
    # exploit the raw text's own repetition already.
    import random as _rand
    _rand.seed(42)

    def _make_diverse(word_pool, n):
        return ' '.join(_rand.choices(word_pool, k=n))

    literature_words = [
        "the", "and", "of", "to", "a", "in", "that", "was", "he", "for",
        "on", "are", "with", "as", "his", "they", "at", "be", "this", "from",
        "beautiful", "extraordinary", "silence", "whispered", "ancient",
        "mysterious", "shadow", "horizon", "wandering", "forgotten",
    ]
    technical_words = [
        "function", "return", "initialize", "context", "database", "connection",
        "protocol", "encryption", "algorithm", "implementation", "framework",
        "evaluation", "parameter", "configuration", "authentication", "request",
        "response", "buffer", "stream", "processor", "module", "interface",
    ]
    news_words = [
        "government", "officials", "announced", "regulations", "technology",
        "sector", "industry", "market", "economy", "international", "foreign",
        "national", "security", "policy", "committee", "statement", "report",
        "investigation", "legislation", "development", "agreement", "summit",
    ]

    corpora = {
        "diverse_literature (5K)": _make_diverse(literature_words, 900),
        "diverse_technical  (5K)": _make_diverse(technical_words, 700),
        "diverse_news       (5K)": _make_diverse(news_words, 750),
        "vowel_heavy words  (5K)": _make_diverse([
            "beautiful", "audio", "queue", "aura", "idealize", "opaque",
            "oboe", "ukulele", "iodine", "outwit", "aqueous", "aioli",
        ], 400),
        "consonant_heavy    (5K)": _make_diverse([
            "rhythm", "strength", "crypt", "lymph", "glyph", "myths",
            "tryst", "nymph", "psych", "lynch", "gypsy", "pygmy",
        ], 500),
    }
```

Replace it with:

```python
    # Corpora are built by get_phase2_corpora() so Phase 3's token-reduction
    # probe can reuse the exact same deterministic corpora for continuity.
    corpora = get_phase2_corpora()
```

- [ ] **Step 3: Run the full Phase 2 suite to confirm no regression**

Run: `python phase2/mvd_comp.py`
Expected: last line reads `RESULTS: 38 passed, 0 failed (100% pass rate)` — identical to `phase2_output.log`. If any number differs, the refactor changed behavior; stop and fix before proceeding.

- [ ] **Step 4: Commit**

```bash
git add phase2/mvd_comp.py
git commit -m "Extract Phase 2 corpus generation into get_phase2_corpora()

Behavior-preserving refactor (same seed, same word lists, same call
order) so the Phase 3 token-reduction probe can reuse the exact
corpora Phase 2's compression benchmarks already used."
```

---

### Task 3: Token-reduction experiment

**Files:**
- Create: `phase3/token_probe.py`
- Test: `phase3/test_token_probe.py`

**Interfaces:**
- Consumes: `get_phase2_corpora()` from `phase2/mvd_comp.py` (Task 2), `vowel_drop()` from `phase3/common.py` (Task 1).
- Produces: `count_tokens(text: str, encoding) -> int`, `compute_token_reduction(original: str, encoding) -> dict` with keys `original_tokens`, `dropped_tokens`, `reduction_pct`, and `run_token_experiment() -> dict` (per-corpus results plus `_average_reduction_pct`) — Task 6 imports `run_token_experiment`.

- [ ] **Step 1: Write the failing tests**

Create `phase3/test_token_probe.py`:

```python
import os
import sys

import tiktoken

sys.path.insert(0, os.path.dirname(__file__))
from token_probe import count_tokens, compute_token_reduction, ENCODING_NAME  # noqa: E402


def test_count_tokens_matches_tiktoken_directly():
    encoding = tiktoken.get_encoding(ENCODING_NAME)
    assert count_tokens("hello world", encoding) == len(encoding.encode("hello world"))


def test_compute_token_reduction_known_case():
    encoding = tiktoken.get_encoding(ENCODING_NAME)
    result = compute_token_reduction("Hello World", encoding)
    expected_original = len(encoding.encode("Hello World"))
    expected_dropped = len(encoding.encode("Hll Wrld"))
    assert result['original_tokens'] == expected_original
    assert result['dropped_tokens'] == expected_dropped
    expected_pct = (expected_original - expected_dropped) / expected_original * 100
    assert abs(result['reduction_pct'] - expected_pct) < 1e-9


def test_compute_token_reduction_returns_required_keys():
    encoding = tiktoken.get_encoding(ENCODING_NAME)
    result = compute_token_reduction("The quick brown fox", encoding)
    assert set(result.keys()) == {'original_tokens', 'dropped_tokens', 'reduction_pct'}
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest phase3/test_token_probe.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'token_probe'`

- [ ] **Step 3: Write the implementation**

Create `phase3/token_probe.py`:

```python
"""
Phase 3 Probe — Experiment 1: token reduction from vowel-dropping.

Reuses the exact Phase 2 synthetic corpora (same word lists, same
random.seed(42)) so this experiment is directly comparable to Phase 2's
own compression findings (avg +14.2% gzip savings from vowel-dropping).
"""
import os
import sys

import tiktoken

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'phase2'))
from mvd_comp import get_phase2_corpora  # noqa: E402

sys.path.insert(0, os.path.dirname(__file__))
from common import vowel_drop  # noqa: E402

ENCODING_NAME = "cl100k_base"


def count_tokens(text: str, encoding) -> int:
    return len(encoding.encode(text))


def compute_token_reduction(original: str, encoding) -> dict:
    dropped = vowel_drop(original)
    original_tokens = count_tokens(original, encoding)
    dropped_tokens = count_tokens(dropped, encoding)
    reduction_pct = (original_tokens - dropped_tokens) / original_tokens * 100
    return {
        'original_tokens': original_tokens,
        'dropped_tokens': dropped_tokens,
        'reduction_pct': reduction_pct,
    }


def run_token_experiment() -> dict:
    encoding = tiktoken.get_encoding(ENCODING_NAME)
    corpora = get_phase2_corpora()

    results = {}
    all_reductions = []
    for label, text in corpora.items():
        r = compute_token_reduction(text, encoding)
        results[label] = r
        all_reductions.append(r['reduction_pct'])
        print(f"{label}: {r['original_tokens']} -> {r['dropped_tokens']} tokens "
              f"({r['reduction_pct']:+.2f}%)")

    avg_reduction = sum(all_reductions) / len(all_reductions)
    print(f"\nAverage token reduction across all corpora: {avg_reduction:+.2f}%")
    results['_average_reduction_pct'] = avg_reduction
    return results


if __name__ == "__main__":
    run_token_experiment()
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest phase3/test_token_probe.py -v`
Expected: 3 passed

- [ ] **Step 5: Commit**

```bash
git add phase3/token_probe.py phase3/test_token_probe.py
git commit -m "Add token-reduction probe (Experiment 1)"
```

---

### Task 4: Embedding-similarity experiment

**Files:**
- Create: `phase3/embedding_probe.py`
- Test: `phase3/test_embedding_probe.py`

**Interfaces:**
- Consumes: `vowel_drop()` and `load_sentences()` from `phase3/common.py` (Task 1).
- Produces: `cosine_similarity(a, b) -> float` and `run_embedding_experiment() -> dict` with keys `per_category` (dict of `{mean, min, max, n}`), `overall_mean`, `catastrophic_rate_pct`, `n_total` — Task 6 imports `run_embedding_experiment`.

- [ ] **Step 1: Write the failing tests (pure-function tests only — no model load needed here)**

Create `phase3/test_embedding_probe.py`:

```python
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from embedding_probe import cosine_similarity  # noqa: E402


def test_cosine_similarity_identical_vectors():
    assert abs(cosine_similarity([1, 0, 0], [1, 0, 0]) - 1.0) < 1e-9


def test_cosine_similarity_orthogonal_vectors():
    assert abs(cosine_similarity([1, 0], [0, 1])) < 1e-9


def test_cosine_similarity_opposite_vectors():
    assert abs(cosine_similarity([1, 0], [-1, 0]) - (-1.0)) < 1e-9


def test_cosine_similarity_zero_vector_returns_zero():
    assert cosine_similarity([0, 0], [1, 1]) == 0.0
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest phase3/test_embedding_probe.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'embedding_probe'`

- [ ] **Step 3: Write the implementation**

Create `phase3/embedding_probe.py`:

```python
"""
Phase 3 Probe — Experiment 2: embedding similarity under vowel-dropping.

Runs only on the frozen real-sentence dataset (sentences.json), never the
Phase 2 word-salad corpora, since those are random word shuffles with no
semantic content for an embedding model to preserve.
"""
import os
import sys

import numpy as np
from sentence_transformers import SentenceTransformer

sys.path.insert(0, os.path.dirname(__file__))
from common import vowel_drop, load_sentences  # noqa: E402

MODEL_NAME = "all-MiniLM-L6-v2"
SENTENCES_PATH = os.path.join(os.path.dirname(__file__), 'sentences.json')


def cosine_similarity(a, b) -> float:
    a = np.asarray(a, dtype=float)
    b = np.asarray(b, dtype=float)
    denom = np.linalg.norm(a) * np.linalg.norm(b)
    if denom == 0:
        return 0.0
    return float(np.dot(a, b) / denom)


def run_embedding_experiment() -> dict:
    data = load_sentences(SENTENCES_PATH)
    model = SentenceTransformer(MODEL_NAME)

    per_category = {}
    all_similarities = []
    catastrophic = 0

    for category, entries in data['categories'].items():
        sims = []
        for entry in entries:
            original = entry['text']
            dropped = vowel_drop(original)
            emb_original, emb_dropped = model.encode([original, dropped])
            sim = cosine_similarity(emb_original, emb_dropped)
            sims.append(sim)
            all_similarities.append(sim)
            if sim < 0.6:
                catastrophic += 1
        per_category[category] = {
            'mean': sum(sims) / len(sims),
            'min': min(sims),
            'max': max(sims),
            'n': len(sims),
        }
        print(f"{category}: mean={per_category[category]['mean']:.4f} "
              f"min={per_category[category]['min']:.4f} n={len(sims)}")

    overall_mean = sum(all_similarities) / len(all_similarities)
    catastrophic_rate = catastrophic / len(all_similarities) * 100
    print(f"\nOverall mean similarity: {overall_mean:.4f}")
    print(f"Catastrophic failure rate (<0.6): {catastrophic_rate:.2f}%")

    return {
        'per_category': per_category,
        'overall_mean': overall_mean,
        'catastrophic_rate_pct': catastrophic_rate,
        'n_total': len(all_similarities),
    }


if __name__ == "__main__":
    run_embedding_experiment()
```

- [ ] **Step 4: Run the pure-function tests to verify they pass**

Run: `python -m pytest phase3/test_embedding_probe.py -v`
Expected: 4 passed

- [ ] **Step 5: Add an integration smoke test (loads the real model — slower, run separately)**

Append to `phase3/test_embedding_probe.py`:

```python
def test_run_embedding_experiment_smoke():
    """Integration smoke test: loads the real model, runs on frozen sentences."""
    from embedding_probe import run_embedding_experiment
    result = run_embedding_experiment()
    assert -1.0 <= result['overall_mean'] <= 1.0
    assert result['n_total'] == 30
    assert set(result['per_category'].keys()) == {
        'literary', 'technical', 'news', 'vowel_heavy', 'consonant_heavy'
    }
```

Run: `python -m pytest phase3/test_embedding_probe.py -v`
Expected: 5 passed (model load takes a few seconds; already confirmed working in this environment)

- [ ] **Step 6: Commit**

```bash
git add phase3/embedding_probe.py phase3/test_embedding_probe.py
git commit -m "Add embedding-similarity probe (Experiment 2)"
```

---

### Task 5: Run both experiments and write the results doc

**Files:**
- Create: `docs/probe_results.md`

**Interfaces:**
- Consumes: `run_token_experiment()` (Task 3) and `run_embedding_experiment()` (Task 4).

- [ ] **Step 1: Run the token-reduction experiment and record output**

Run: `python phase3/token_probe.py`

Copy the full printed output verbatim into a scratch note — you will need the exact per-corpus numbers and the average for the results doc.

- [ ] **Step 2: Run the embedding-similarity experiment and record output**

Run: `python phase3/embedding_probe.py`

Copy the full printed output verbatim (per-category means/mins and overall mean + catastrophic rate).

- [ ] **Step 3: Apply the decision gate**

Using the actual numbers from Steps 1-2, compare against the thresholds in the Global Constraints section (mean token reduction ≥15%, mean similarity ≥0.85, catastrophic rate <10%), and determine which of the four scenarios from `docs/superpowers/specs/2026-06-28-rag-chunking-probe-design.md` applies:
- Strong result (both pass)
- Efficiency/quality tradeoff (tokens pass, similarity fails)
- Limited token benefit (similarity passes, tokens fail)
- Negative result (both fail)

- [ ] **Step 4: Write `docs/probe_results.md`**

Follow the structure of `docs/progress_report_pre_rag.md` (numbers-first, sourced directly from the actual run output, no projected/theoretical figures). Required sections:
1. **Methodology** — summarize Experiment 1 (Phase 2 corpora reuse) and Experiment 2 (frozen sentence dataset, freeze date, sourcing rule), with a link to the design spec.
2. **Experiment 1 results** — per-corpus token counts and % reduction, plus the average, in a table.
3. **Experiment 2 results** — per-category mean/min/max/n, overall mean, catastrophic failure rate, in a table. Explicitly flag per-category numbers as directional only (n≈6 per category).
4. **Decision gate verdict** — state plainly which of the 4 scenarios applies and why, quoting the actual numbers against the thresholds.
5. **Implications for the paper** — one paragraph on what this means for Stage B (build it, defer it, or skip it) per the scenario.

- [ ] **Step 5: Commit**

```bash
git add docs/probe_results.md
git commit -m "Record Stage A probe results and decision-gate verdict"
```
