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
