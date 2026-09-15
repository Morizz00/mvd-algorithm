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
