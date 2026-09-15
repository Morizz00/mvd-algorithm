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
