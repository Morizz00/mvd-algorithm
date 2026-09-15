"""
MVD-COMP Phase 2 — compression-oriented encoding on top of the Phase 0 transform.

Layers: RLE masks, delta-encoded vowel positions, 4-bit vowel packing,
MVDC binary serialization, and gzip/bz2/zlib comparison (lossless + lossy).
"""
from __future__ import annotations

import bz2
import gzip
import math
import struct
import sys
import zlib
from collections import Counter
from typing import Dict, List, Sequence, Tuple

VOWELS = set("aeiouAEIOU")
MAGIC = b"MVDC"

VOWEL_TO_NIBBLE = {
    "a": 0x0, "A": 0x1,
    "e": 0x2, "E": 0x3,
    "i": 0x4, "I": 0x5,
    "o": 0x6, "O": 0x7,
    "u": 0x8, "U": 0x9,
}
NIBBLE_TO_VOWEL = {v: k for k, v in VOWEL_TO_NIBBLE.items()}


def mvd_encode(text: str) -> Tuple[str, List[str], List[int]]:
    consonants: List[str] = []
    vowels: List[str] = []
    mask: List[int] = []
    for char in text:
        if char in VOWELS:
            vowels.append(char)
            mask.append(1)
        else:
            consonants.append(char)
            mask.append(0)
    return "".join(consonants), vowels, mask


def mvd_decode(consonants: str, vowels: Sequence[str], mask: Sequence[int]) -> str:
    result: List[str] = []
    c_idx = 0
    v_idx = 0
    for bit in mask:
        if bit == 1:
            result.append(vowels[v_idx])
            v_idx += 1
        else:
            result.append(consonants[c_idx])
            c_idx += 1
    return "".join(result)


def rle_encode_mask(mask: Sequence[int]) -> List[Tuple[int, int]]:
    if not mask:
        return []
    runs: List[Tuple[int, int]] = []
    current = mask[0]
    count = 1
    for bit in mask[1:]:
        if bit == current:
            count += 1
        else:
            runs.append((current, count))
            current = bit
            count = 1
    runs.append((current, count))
    return runs


def rle_decode_mask(runs: Sequence[Tuple[int, int]]) -> List[int]:
    mask: List[int] = []
    for val, count in runs:
        mask.extend([val] * count)
    return mask


def rle_to_bytes(runs: Sequence[Tuple[int, int]]) -> bytes:
    out = bytearray()
    for val, count in runs:
        remaining = count
        while remaining > 0:
            chunk = min(remaining, 255)
            out.append(val & 0xFF)
            out.append(chunk)
            remaining -= chunk
    return bytes(out)


def rle_from_bytes(data: bytes) -> List[Tuple[int, int]]:
    if len(data) % 2 != 0:
        raise ValueError("RLE byte length must be even")
    runs: List[Tuple[int, int]] = []
    for i in range(0, len(data), 2):
        val = data[i]
        count = data[i + 1]
        if runs and runs[-1][0] == val:
            prev_val, prev_count = runs[-1]
            runs[-1] = (prev_val, prev_count + count)
        else:
            runs.append((val, count))
    return runs


def delta_encode_positions(mask: Sequence[int]) -> List[int]:
    positions = [i for i, bit in enumerate(mask) if bit == 1]
    if not positions:
        return []
    deltas = [positions[0]]
    for i in range(1, len(positions)):
        deltas.append(positions[i] - positions[i - 1])
    return deltas


def delta_decode_positions(deltas: Sequence[int], length: int) -> List[int]:
    mask = [0] * length
    if not deltas:
        return mask
    pos = 0
    for i, d in enumerate(deltas):
        pos = d if i == 0 else pos + d
        if 0 <= pos < length:
            mask[pos] = 1
    return mask


def encode_vowels_compact(vowels: Sequence[str]) -> bytes:
    if not vowels:
        return b""
    nibbles = [VOWEL_TO_NIBBLE.get(v, 0) for v in vowels]
    if len(nibbles) % 2 == 1:
        nibbles.append(0)
    out = bytearray()
    for i in range(0, len(nibbles), 2):
        out.append((nibbles[i] << 4) | nibbles[i + 1])
    return bytes(out)


def decode_vowels_compact(data: bytes, count: int) -> List[str]:
    if count == 0:
        return []
    vowels: List[str] = []
    for byte in data:
        hi = (byte >> 4) & 0xF
        lo = byte & 0xF
        vowels.append(NIBBLE_TO_VOWEL.get(hi, "a"))
        vowels.append(NIBBLE_TO_VOWEL.get(lo, "a"))
    return vowels[:count]


def serialize_mvd(consonants: str, vowels: Sequence[str], mask: Sequence[int]) -> bytes:
    """
    MVDC layout (16-byte header + payload):
      magic[4] orig_len[4] n_vowels[4] c_len[4]
      consonants utf-8
      compact vowels (ceil(n_vowels/2) bytes)
      RLE-encoded mask (2 bytes per run, counts split at 255)
    """
    orig_len = len(mask)
    n_vowels = len(vowels)
    c_bytes = consonants.encode("utf-8")
    v_bytes = encode_vowels_compact(vowels)
    rle_bytes = rle_to_bytes(rle_encode_mask(mask))
    header = MAGIC + struct.pack(">III", orig_len, n_vowels, len(c_bytes))
    return header + c_bytes + v_bytes + rle_bytes


def deserialize_mvd(blob: bytes) -> Tuple[str, List[str], List[int]]:
    if blob[:4] != MAGIC:
        raise ValueError("bad MVDC magic")
    orig_len, n_vowels, c_len = struct.unpack(">III", blob[4:16])
    offset = 16
    c_bytes = blob[offset:offset + c_len]
    offset += c_len
    v_nbytes = (n_vowels + 1) // 2
    v_bytes = blob[offset:offset + v_nbytes]
    offset += v_nbytes
    rle_bytes = blob[offset:]
    consonants = c_bytes.decode("utf-8")
    vowels = decode_vowels_compact(v_bytes, n_vowels)
    mask = rle_decode_mask(rle_from_bytes(rle_bytes))
    if orig_len and len(mask) != orig_len:
        raise ValueError(f"mask length {len(mask)} != orig_len {orig_len}")
    return consonants, vowels, mask


def analyze_vowel_distribution(vowels: Sequence[str]) -> dict:
    freq = Counter(vowels)
    total = len(vowels)
    if total == 0:
        return {"frequencies": freq, "probabilities": {}, "entropy": 0.0}
    probabilities = {v: c / total for v, c in freq.items()}
    entropy = -sum(p * math.log2(p) for p in probabilities.values())
    return {"frequencies": freq, "probabilities": probabilities, "entropy": entropy}


def get_phase2_corpora() -> Dict[str, str]:
    """
    Build the same 5 synthetic diverse corpora used in Phase 2's compression
    benchmarks. Deterministic (seed=42) so results are reproducible and
    comparable across phases.
    """
    import random as _rand
    _rand.seed(42)

    def _make_diverse(word_pool, n):
        return " ".join(_rand.choices(word_pool, k=n))

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


def run_all_tests() -> bool:
    passed = 0
    failed = 0

    def check(name: str, cond: bool, extra: str = "") -> None:
        nonlocal passed, failed
        status = "PASS" if cond else "FAIL"
        mark = "✔" if cond else "✘"
        print(f"  {mark} {status}  {name}")
        if extra:
            print(f"          {extra}")
        if cond:
            passed += 1
        else:
            failed += 1

    print("=" * 60)
    print("  MVD-COMP Phase 2 — Full Test Suite")
    print("=" * 60)

    print("\n[TEST GROUP 1] Core MVD Encode/Decode Reversibility")
    group1 = [
        "Hello World",
        "The quick brown fox jumps over",
        "AEIOU aeiou",
        "xyz bcdfg",
        "aeiou",
        "",
        "a",
        "b",
        "Café",
        "Programming in Python is fun!",
    ]
    for text in group1:
        c, v, m = mvd_encode(text)
        reconstructed = mvd_decode(c, v, m)
        check(f"Reversibility: {repr(text[:30])}", reconstructed == text)

    print("\n[TEST GROUP 2] Run-Length Encoding of Masks")
    sample_mask = [0, 0, 0, 1, 1, 0, 0]
    runs = rle_encode_mask(sample_mask)
    expected_runs = [(0, 3), (1, 2), (0, 2)]
    check(
        "RLE encodes [0,0,0,1,1,0,0] -> [(0,3),(1,2),(0,2)]",
        runs == expected_runs,
        f"Got: {runs}",
    )
    decoded = rle_decode_mask(runs)
    check("RLE round-trip", decoded == sample_mask, f"Got: {decoded}")
    long_mask = ([0] * 100) + ([1] * 50) + ([0] * 100)
    check("RLE round-trip on 250-element mask", rle_decode_mask(rle_encode_mask(long_mask)) == long_mask)
    check("RLE of empty mask", rle_encode_mask([]) == [])
    rle_bytes = rle_to_bytes(runs)
    check("RLE bytes round-trip", rle_from_bytes(rle_bytes) == expected_runs, f"Got: {rle_from_bytes(rle_bytes)}")

    print("\n[TEST GROUP 3] Delta Encoding of Vowel Positions")
    _, _, hello_mask = mvd_encode("Hello")
    hello_deltas = delta_encode_positions(hello_mask)
    check(
        "Delta encode 'Hello' vowels [1,4] -> [1,3]",
        hello_deltas == [1, 3],
        f"Got: {hello_deltas}",
    )
    hello_back = delta_decode_positions(hello_deltas, len("Hello"))
    check(
        "Delta decode round-trip for 'Hello'",
        hello_back == [0, 1, 0, 0, 1],
        f"Got: {hello_back}",
    )
    _, _, no_vowel_mask = mvd_encode("xyz")
    check("Delta encode no-vowel mask returns []", delta_encode_positions(no_vowel_mask) == [])

    print("\n[TEST GROUP 4] Compact Vowel Encoding")
    sample_vowels = ["e", "a", "o", "I", "U", "e"]
    compact = encode_vowels_compact(sample_vowels)
    decoded_v = decode_vowels_compact(compact, len(sample_vowels))
    check(
        "Vowel compact encode/decode round-trip",
        decoded_v == sample_vowels,
        f"Got: {decoded_v}",
    )
    check("Empty vowel list encodes to b''", encode_vowels_compact([]) == b"")

    print("\n[TEST GROUP 5] MVD-COMP Binary Serialization")
    ser_texts = [
        "Hello World",
        "The quick brown fox",
        "xyz",
        "aeiou",
        "aaaaaaaaaaaaaaaaaaaaaaaaa",
        "The The The The The The T",
    ]
    for text in ser_texts:
        c, v, m = mvd_encode(text)
        blob = serialize_mvd(c, v, m)
        c2, v2, m2 = deserialize_mvd(blob)
        reconstructed = mvd_decode(c2, v2, m2)
        check(f"Serialize→Deserialize→Decode: {repr(text[:24])}", reconstructed == text)

    print("\n[TEST GROUP 6] Vowel Distribution Analysis")
    _, fox_vowels, _ = mvd_encode("quick brown fox")
    fox_stats = analyze_vowel_distribution(fox_vowels)
    check(
        "Entropy of 'quick brown fox' vowels > 0",
        fox_stats["entropy"] > 0,
        f"entropy={fox_stats['entropy']:.4f}",
    )
    _, dist_vowels, _ = mvd_encode("The quick brown fox jumps over the lazy dog")
    dist_stats = analyze_vowel_distribution(dist_vowels)
    check("Frequencies sum to vowel count", sum(dist_stats["frequencies"].values()) == len(dist_vowels))
    check("All probabilities sum to ~1.0", abs(sum(dist_stats["probabilities"].values()) - 1.0) < 1e-9)
    empty_stats = analyze_vowel_distribution([])
    check("Empty vowel list entropy = 0", empty_stats["entropy"] == 0)

    print("\n[TEST GROUP 7] Compression Benchmarks (Real Corpora)")
    corpora = get_phase2_corpora()
    codecs = [
        ("gzip", gzip.compress),
        ("bz2", bz2.compress),
        ("zlib", zlib.compress),
    ]
    improvements: List[float] = []
    lossy_savings: List[float] = []
    first_label = None
    first_text = None

    bar = "─" * 60
    for label, text in corpora.items():
        raw = text.encode("utf-8")
        raw_size = len(raw)
        c, v, m = mvd_encode(text)
        blob = serialize_mvd(c, v, m)
        mvd_size = len(blob)
        overhead = (mvd_size - raw_size) / raw_size * 100 if raw_size else 0.0

        print()
        print(bar)
        print(f"  Corpus: {label}")
        print(bar)
        print(f"  Raw size:         {raw_size:8,} bytes")
        print(f"  MVD binary size:  {mvd_size:8,} bytes  (overhead: {overhead:+.1f}%)")
        print()
        print("  Codec      Raw→Compressed   MVD→Compressed  Improvement")
        print("  " + "─" * 8 + " " + "─" * 16 + " " + "─" * 16 + " " + "─" * 12)

        for name, fn in codecs:
            raw_c = len(fn(raw))
            mvd_c = len(fn(blob))
            imp = (raw_c - mvd_c) / raw_c * 100 if raw_c else 0.0
            improvements.append(imp)
            print(
                f"  {name:<8} {raw_c:8,} ({raw_c / raw_size * 100:4.1f}%)  "
                f"{mvd_c:8,} ({mvd_c / raw_size * 100:4.1f}%)   {imp:+.2f}%"
            )

        raw_gzip = len(gzip.compress(raw))
        cons_gzip = len(gzip.compress(c.encode("utf-8")))
        savings = (raw_gzip - cons_gzip) / raw_gzip * 100 if raw_gzip else 0.0
        lossy_savings.append(savings)

        if first_label is None:
            first_label = label
            first_text = text

    avg_imp = sum(improvements) / len(improvements) if improvements else 0.0
    print()
    print(f"  Average improvement across all corpora/codecs: {avg_imp:+.2f}%")
    print()
    print("  ┌" + "─" * 58 + "┐")
    print("  │  HONEST COMPRESSION ANALYSIS                             │")
    print("  │  MVD binary format adds header overhead that modern      │")
    print("  │  codecs (gzip/bz2) cannot recoup for short texts.        │")
    print("  │  The real MVD-COMP payoff is LOSSY mode (vowel drop)     │")
    print("  │  and stream-separation for custom/neural compressors.    │")
    print("  └" + "─" * 58 + "┘")
    print()
    print("  VOWEL-DROP (lossy) — consonants-only vs raw text, then gzip:")
    for (label, _text), sav in zip(corpora.items(), lossy_savings):
        print(f"    {label:<32}: {sav:+.1f}%")

    avg_lossy = sum(lossy_savings) / len(lossy_savings) if lossy_savings else 0.0
    check(
        "Consonant-only (vowel-drop) gzip beats full-text gzip on average",
        avg_lossy > 0,
        f"avg savings = {avg_lossy:+.1f}%",
    )

    lit = corpora["diverse_literature (5K)"]
    lit_c, _, _ = mvd_encode(lit)
    check(
        "Consonant stream is smaller than full text (core MVD insight)",
        len(lit_c.encode("utf-8")) < len(lit.encode("utf-8")),
        f"full={len(lit.encode('utf-8'))}B  consonants={len(lit_c.encode('utf-8'))}B",
    )

    for key in ("diverse_literature (5K)", "diverse_technical  (5K)"):
        text = corpora[key]
        c, v, m = mvd_encode(text)
        blob = serialize_mvd(c, v, m)
        c2, v2, m2 = deserialize_mvd(blob)
        check(f"Lossless round-trip: {key}", mvd_decode(c2, v2, m2) == text)

    print("\n[TEST GROUP 8] Edge Cases & Stress Tests")
    big = ("The quick brown fox jumps over the lazy dog. ") * 1000
    # ~45 characters * 1000 ≈ 45KB
    c, v, m = mvd_encode(big)
    blob = serialize_mvd(c, v, m)
    c2, v2, m2 = deserialize_mvd(blob)
    check("45KB text serialization round-trip", mvd_decode(c2, v2, m2) == big)

    punct = "!!!???...,,,"
    pc, pv, pm = mvd_encode(punct)
    check("Punctuation-only: no vowels extracted", pv == [] and mvd_decode(pc, pv, pm) == punct)

    digits = "1234567890"
    dc, dv, dm = mvd_encode(digits)
    check(
        "Digits-only: no vowels extracted, consonants=digits",
        dv == [] and dc == digits and mvd_decode(dc, dv, dm) == digits,
    )

    ws = "Hello   World\n\tTab"
    wc, wv, wm = mvd_encode(ws)
    check("Whitespace preserved in reconstruction", mvd_decode(wc, wv, wm) == ws)

    print()
    print("=" * 60)
    print(f"  RESULTS: {passed} passed, {failed} failed  ({100 * passed / (passed + failed):.0f}% pass rate)")
    print("=" * 60)
    return failed == 0


if __name__ == "__main__":
    ok = run_all_tests()
    sys.exit(0 if ok else 1)
