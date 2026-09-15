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
