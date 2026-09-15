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
