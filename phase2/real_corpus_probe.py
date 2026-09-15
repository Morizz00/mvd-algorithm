"""
Real-text compression probe — Phase 2 protocol on frozen public-domain corpora.

Reuses mvd_encode / serialize_mvd from mvd_comp.py. Slices are built
deterministically from data/real/manifest.json + raw files.

Claim rule: unweighted mean lossy gzip savings across all samples with
raw size >= 200 KB must be >= 5% for CLAIM HOLDS; otherwise CLAIM WEAKENS.
"""
from __future__ import annotations

import bz2
import gzip
import json
import os
import sys
import zlib
from typing import Dict, List, Tuple

sys.path.insert(0, os.path.dirname(__file__))
from mvd_comp import mvd_encode, serialize_mvd  # noqa: E402

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
MANIFEST_PATH = os.path.join(ROOT, "data", "real", "manifest.json")
REAL_DIR = os.path.join(ROOT, "data", "real")

SIZE_TARGETS = [
    ("50KB", 50 * 1024),
    ("200KB", 200 * 1024),
    ("full", None),  # full file, capped at 1 MB
]
MAX_FULL_BYTES = 1024 * 1024
CLAIM_MIN_BYTES = 200 * 1024
CLAIM_MIN_MEAN_SAVINGS = 5.0


def _utf8_prefix(data: bytes, n: int) -> bytes:
    """Return a valid UTF-8 prefix of at most n bytes."""
    if len(data) <= n:
        return data
    chunk = data[:n]
    while chunk:
        try:
            chunk.decode("utf-8")
            return chunk
        except UnicodeDecodeError:
            chunk = chunk[:-1]
    return b""


def load_samples() -> List[Tuple[str, str, bytes]]:
    """Return list of (label, corpus_id, utf8_bytes)."""
    with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    samples: List[Tuple[str, str, bytes]] = []
    for corpus_id, meta in manifest["corpora"].items():
        path = os.path.join(REAL_DIR, meta["filename"])
        with open(path, "rb") as f:
            full = f.read()
        if len(full) != meta["byte_length"]:
            raise ValueError(
                f"{corpus_id}: on-disk length {len(full)} != manifest {meta['byte_length']}"
            )

        for size_label, size_bytes in SIZE_TARGETS:
            if size_bytes is None:
                slice_bytes = _utf8_prefix(full, MAX_FULL_BYTES)
                label = f"{corpus_id} ({size_label}, {len(slice_bytes):,} B)"
            else:
                if len(full) < size_bytes:
                    # Skip targets larger than the source (e.g. short RFC).
                    continue
                slice_bytes = _utf8_prefix(full, size_bytes)
                label = f"{corpus_id} ({size_label})"
            samples.append((label, corpus_id, slice_bytes))
    return samples


def measure(text_bytes: bytes) -> dict:
    text = text_bytes.decode("utf-8")
    raw_size = len(text_bytes)
    c, v, m = mvd_encode(text)
    blob = serialize_mvd(c, v, m)
    mvd_size = len(blob)
    overhead = (mvd_size - raw_size) / raw_size * 100 if raw_size else 0.0

    codecs = {
        "gzip": gzip.compress,
        "bz2": bz2.compress,
        "zlib": zlib.compress,
    }
    codec_rows = {}
    for name, fn in codecs.items():
        raw_c = len(fn(text_bytes))
        mvd_c = len(fn(blob))
        imp = (raw_c - mvd_c) / raw_c * 100 if raw_c else 0.0
        codec_rows[name] = {
            "raw_compressed": raw_c,
            "mvd_compressed": mvd_c,
            "improvement_pct": imp,
        }

    raw_gzip = len(gzip.compress(text_bytes))
    cons_gzip = len(gzip.compress(c.encode("utf-8")))
    lossy = (raw_gzip - cons_gzip) / raw_gzip * 100 if raw_gzip else 0.0

    return {
        "raw_size": raw_size,
        "mvd_size": mvd_size,
        "overhead_pct": overhead,
        "codecs": codec_rows,
        "lossy_gzip_savings_pct": lossy,
        "consonant_bytes": len(c.encode("utf-8")),
    }


def run() -> dict:
    samples = load_samples()
    print("=" * 70)
    print("  MVD Real-Text Compression Probe")
    print("  Protocol locked to Phase 2 (mvd_encode + serialize_mvd + gzip/bz2/zlib)")
    print("=" * 70)
    print()

    results = []
    lossy_all: List[float] = []
    lossy_ge_200: List[float] = []

    bar = "─" * 70
    for label, corpus_id, text_bytes in samples:
        r = measure(text_bytes)
        results.append({"label": label, "corpus_id": corpus_id, **r})
        lossy_all.append(r["lossy_gzip_savings_pct"])
        if r["raw_size"] >= CLAIM_MIN_BYTES:
            lossy_ge_200.append(r["lossy_gzip_savings_pct"])

        print(bar)
        print(f"  Sample: {label}")
        print(bar)
        print(f"  Raw size:         {r['raw_size']:10,} bytes")
        print(f"  MVD binary size:  {r['mvd_size']:10,} bytes  "
              f"(overhead: {r['overhead_pct']:+.1f}%)")
        print(f"  Consonant stream: {r['consonant_bytes']:10,} bytes")
        print()
        print("  Codec      Raw→Compressed   MVD→Compressed  Improvement")
        print("  " + "─" * 8 + " " + "─" * 16 + " " + "─" * 16 + " " + "─" * 12)
        for name, row in r["codecs"].items():
            print(
                f"  {name:<8} {row['raw_compressed']:8,} "
                f"({row['raw_compressed'] / r['raw_size'] * 100:5.1f}%)  "
                f"{row['mvd_compressed']:8,} "
                f"({row['mvd_compressed'] / r['raw_size'] * 100:5.1f}%)   "
                f"{row['improvement_pct']:+.2f}%"
            )
        print(f"  Lossy vowel-drop + gzip savings: {r['lossy_gzip_savings_pct']:+.2f}%")
        print()

    mean_all = sum(lossy_all) / len(lossy_all) if lossy_all else 0.0
    mean_ge_200 = sum(lossy_ge_200) / len(lossy_ge_200) if lossy_ge_200 else 0.0

    print("=" * 70)
    print("  SUMMARY")
    print("=" * 70)
    print(f"  Samples measured:              {len(results)}")
    print(f"  Samples ≥ 200 KB:              {len(lossy_ge_200)}")
    print(f"  Mean lossy gzip savings (all): {mean_all:+.2f}%")
    print(f"  Mean lossy gzip savings (≥200 KB): {mean_ge_200:+.2f}%")
    print()
    print("  CLAIM RULE: unweighted mean lossy gzip savings for samples")
    print(f"  with raw size ≥ {CLAIM_MIN_BYTES:,} B must be ≥ {CLAIM_MIN_MEAN_SAVINGS:.0f}%.")
    print()

    if not lossy_ge_200:
        verdict = "CLAIM WEAKENS"
        reason = "no samples ≥ 200 KB (cannot evaluate rule)"
    elif mean_ge_200 >= CLAIM_MIN_MEAN_SAVINGS:
        verdict = "CLAIM HOLDS"
        reason = (
            f"mean lossy gzip savings at ≥200 KB = {mean_ge_200:+.2f}% "
            f"(≥ {CLAIM_MIN_MEAN_SAVINGS:.0f}%)"
        )
    else:
        verdict = "CLAIM WEAKENS"
        reason = (
            f"mean lossy gzip savings at ≥200 KB = {mean_ge_200:+.2f}% "
            f"(< {CLAIM_MIN_MEAN_SAVINGS:.0f}%)"
        )

    print(f"  >>> {verdict}: {reason}")
    print("=" * 70)

    return {
        "results": results,
        "mean_all": mean_all,
        "mean_ge_200": mean_ge_200,
        "n_ge_200": len(lossy_ge_200),
        "verdict": verdict,
        "reason": reason,
    }


if __name__ == "__main__":
    run()
    sys.exit(0)
