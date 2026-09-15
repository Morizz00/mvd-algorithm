"""
Download and freeze the three public-domain corpora used by real_corpus_probe.py.

Sources (plan-locked):
  austen        — Project Gutenberg #1342 Pride and Prejudice
  rfc8259       — RFC 8259 (JSON) plain text
  frankenstein  — Project Gutenberg #84 Frankenstein

Writes:
  data/real/raw/<id>.txt
  data/real/manifest.json  (URL, retrieval date, byte length, SHA-256)
"""
from __future__ import annotations

import hashlib
import json
import os
import urllib.request
from datetime import datetime, timezone

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
RAW_DIR = os.path.join(ROOT, "data", "real", "raw")
MANIFEST_PATH = os.path.join(ROOT, "data", "real", "manifest.json")

CORPORA = {
    "austen": {
        "title": "Pride and Prejudice",
        "genre": "literary",
        "url": "https://www.gutenberg.org/files/1342/1342-0.txt",
    },
    "rfc8259": {
        "title": "RFC 8259 — The JavaScript Object Notation (JSON) Data Interchange Format",
        "genre": "technical",
        "url": "https://www.rfc-editor.org/rfc/rfc8259.txt",
    },
    "frankenstein": {
        "title": "Frankenstein",
        "genre": "literary/prose",
        "url": "https://www.gutenberg.org/files/84/84-0.txt",
    },
}


def _download(url: str) -> bytes:
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "MVD-research-fetch/1.0 (academic corpus freeze)"},
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        return resp.read()


def main() -> None:
    os.makedirs(RAW_DIR, exist_ok=True)
    retrieved_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    entries = {}

    for corpus_id, meta in CORPORA.items():
        print(f"Fetching {corpus_id}: {meta['url']}")
        data = _download(meta["url"])
        # Normalize newlines to \\n for stable hashing across platforms
        text = data.decode("utf-8", errors="replace")
        text = text.replace("\r\n", "\n").replace("\r", "\n")
        encoded = text.encode("utf-8")

        out_path = os.path.join(RAW_DIR, f"{corpus_id}.txt")
        with open(out_path, "wb") as f:
            f.write(encoded)

        sha = hashlib.sha256(encoded).hexdigest()
        entries[corpus_id] = {
            "title": meta["title"],
            "genre": meta["genre"],
            "url": meta["url"],
            "retrieved_at": retrieved_at,
            "filename": f"raw/{corpus_id}.txt",
            "byte_length": len(encoded),
            "sha256": sha,
        }
        print(f"  wrote {out_path} ({len(encoded):,} bytes, sha256={sha[:12]}...)")

    manifest = {
        "frozen_at": retrieved_at,
        "note": "Full files frozen before real_corpus_probe.py. Slices are built deterministically by the probe.",
        "corpora": entries,
    }
    os.makedirs(os.path.dirname(MANIFEST_PATH), exist_ok=True)
    with open(MANIFEST_PATH, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
        f.write("\n")
    print(f"Wrote manifest: {MANIFEST_PATH}")


if __name__ == "__main__":
    main()
