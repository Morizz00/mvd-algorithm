#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════════════
#  MVD-COMP Phase 2 — Bash Test Runner
#  Runs the full test suite step by step with explanations.
# ═══════════════════════════════════════════════════════════════

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PY="$SCRIPT_DIR/mvd_comp.py"

# ── Colours ──────────────────────────────────────────────────
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
CYAN='\033[0;36m'; BOLD='\033[1m'; RESET='\033[0m'

banner() {
  echo -e "\n${BOLD}${CYAN}╔══════════════════════════════════════════════════════════╗${RESET}"
  printf "${BOLD}${CYAN}║  %-56s║${RESET}\n" "$1"
  echo -e "${BOLD}${CYAN}╚══════════════════════════════════════════════════════════╝${RESET}\n"
}

section() { echo -e "\n${BOLD}${YELLOW}▶ $1${RESET}"; }
explain() { echo -e "  ${CYAN}ℹ  $1${RESET}"; }
ok()      { echo -e "  ${GREEN}✔  $1${RESET}"; }
fail()    { echo -e "  ${RED}✘  $1${RESET}"; }

# ─────────────────────────────────────────────────────────────
banner "MVD-COMP Phase 2 — Step-by-Step Test Runner"

# ── Step 0: Sanity check environment ─────────────────────────
section "Step 0: Environment Check"
explain "Verifying Python 3 and required stdlib modules are available."

python --version && ok "Python found" || { fail "Python not found"; exit 1; }

python - <<'EOF'
import gzip, bz2, zlib, struct, math
from collections import Counter
print("  stdlib modules: gzip, bz2, zlib, struct, math, collections — all OK")
EOF

# ── Step 1: Explain the architecture ─────────────────────────
section "Step 1: Architecture Overview"
explain "MVD-COMP consists of 8 layers built on top of Phase 0:"
cat <<'EOF'

  Phase 0 Core (base layer)
  │
  ├─ Layer 1: Run-Length Encoding (RLE) for position masks
  │    WHY: Consonant/vowel patterns naturally create long runs
  │         e.g. "strength" → mask=[0,0,0,0,0,0,0,0] — 8 zeros in a row
  │
  ├─ Layer 2: Delta Encoding for vowel positions
  │    WHY: Deltas between vowel positions are small integers → compressible
  │
  ├─ Layer 3: Compact 4-bit vowel encoding
  │    WHY: Only 10 distinct vowels (a/e/i/o/u × 2 cases)
  │         4 bits each vs 8 bits for ASCII = 50% space saving
  │
  ├─ Layer 4: Custom binary serialization format (MVDC)
  │    WHY: Struct packing beats naive string serialization
  │
  └─ Layer 5: Downstream codec comparison (gzip / bz2 / zlib)
       WHY: Separate streams have better compressibility than mixed text

EOF

# ── Step 2: Smoke test — encode a single word ─────────────────
section "Step 2: Smoke Test — Encode  'Hello World'"
explain "Running a quick sanity check before the full suite."

python - <<'EOF'
import sys
sys.path.insert(0, '.')
from mvd_comp import mvd_encode, mvd_decode, rle_encode_mask, delta_encode_positions

text = "Hello World"
c, v, m = mvd_encode(text)
print(f"\n  Input text    : {repr(text)}")
print(f"  Consonants (C): {repr(c)}")
print(f"  Vowels (V)    : {v}")
print(f"  Mask (M)      : {m}")
print(f"  RLE of mask   : {rle_encode_mask(m)}")
print(f"  Vowel deltas  : {delta_encode_positions(m)}")
print(f"  Reconstructed : {repr(mvd_decode(c, v, m))}")
print(f"  Round-trip OK : {mvd_decode(c, v, m) == text}")
EOF

# ── Step 3: Explain RLE math ──────────────────────────────────
section "Step 3: Why RLE Works on MVD Masks"
explain "Demonstrating RLE compression effect on real English text."

python - <<'EOF'
from mvd_comp import mvd_encode, rle_encode_mask

sentence = "The quick brown fox jumps over the lazy dog"
_, _, mask = mvd_encode(sentence)

print(f"\n  Sentence: '{sentence}'")
print(f"  Mask bits ({len(mask)} total): {''.join(str(b) for b in mask)}")
print(f"\n  Raw mask storage  : {len(mask)} bits  = {(len(mask)+7)//8} bytes")

runs = rle_encode_mask(mask)
print(f"  RLE runs          : {runs}")
print(f"  RLE storage       : {len(runs)} runs × 2 bytes = {len(runs)*2} bytes")
print(f"  Space saved       : {(len(mask)+7)//8 - len(runs)*2} bytes  "
      f"({100*(1 - len(runs)*2/((len(mask)+7)//8)):.0f}% reduction)")
EOF

# ── Step 4: Explain 4-bit vowel packing ───────────────────────
section "Step 4: 4-Bit Vowel Packing Demo"
explain "Showing how packing 2 vowels per byte halves storage cost."

python - <<'EOF'
from mvd_comp import mvd_encode, encode_vowels_compact, decode_vowels_compact

text = "beautiful and extraordinary imagination"
_, vowels, _ = mvd_encode(text)

naive_bytes = len(vowels)                            # 1 char = 1 byte (ASCII)
compact     = encode_vowels_compact(vowels)
compact_len = len(compact)

print(f"\n  Text    : '{text}'")
print(f"  Vowels  : {vowels}")
print(f"  Naive encoding (ASCII) : {naive_bytes} bytes")
print(f"  Compact 4-bit encoding : {compact_len} bytes  ({compact.hex()})")
print(f"  Space saved            : {naive_bytes - compact_len} bytes "
      f"({100*(naive_bytes - compact_len)/naive_bytes:.0f}% reduction)")

# Verify round-trip
decoded = decode_vowels_compact(compact, len(vowels))
print(f"  Round-trip OK          : {decoded == vowels}")
EOF

# ── Step 5: Delta encoding demo ───────────────────────────────
section "Step 5: Delta Encoding of Vowel Positions"
explain "Delta encoding turns absolute positions into small increments."

python - <<'EOF'
from mvd_comp import mvd_encode,delta_encode_positions,delta_decode_positions

text = "The cryptographic strength of this algorithm depends on the pseudorandom distribution of vowels in the input text"
_, _, mask = mvd_encode(text)
vowel_pos = [i for i, b in enumerate(mask) if b == 1]
deltas = delta_encode_positions(mask)
mask_turn=delta_decode_positions(deltas,len(text))

print(f"\n  Text         : '{text}'")
print(f"  Vowel positions (absolute): {vowel_pos}")
print(f"  Deltas (gaps between)     : {deltas}")
print(f"\n  Absolute positions require up to {max(vowel_pos).bit_length()} bits each")
max_delta = max(deltas)
print(f"  Deltas require only up to {max_delta.bit_length()} bits each")
print(f"  (max delta = {max_delta})")
print(f"reconstruct:{[i for i,b in enumerate(mask_turn) if b == 1]}")
print(f"decode elite:{mask_turn==mask}")
EOF

# ── Step 6: Full binary serialization demo ────────────────────
section "Step 6: Binary Serialization Format (MVDC)"
explain "Showing the compact binary layout for storage/transmission."

python - <<'EOF'
from mvd_comp import mvd_encode, serialize_mvd, deserialize_mvd, mvd_decode

text = "The quick brown fox"
c, v, m = mvd_encode(text)
blob = serialize_mvd(c, v, m)

print(f"\n  Input     : {repr(text)}  ({len(text.encode())} bytes UTF-8)")
print(f"  MVDC blob : {len(blob)} bytes")
print(f"  Header    : magic={blob[:4]} | len={int.from_bytes(blob[4:8],'big')} "
      f"| nvowels={int.from_bytes(blob[8:12],'big')}")
print(f"  Hex dump  : {blob.hex()[:80]}...")

c2, v2, m2 = deserialize_mvd(blob)
reconstructed = mvd_decode(c2, v2, m2)
print(f"\n  Deserialised + decoded: {repr(reconstructed)}")
print(f"  Round-trip OK: {reconstructed == text}")
EOF

# ── Step 7: Run the full test suite ───────────────────────────
section "Step 7: Full Test Suite"
explain "Running all 8 test groups (reversibility, RLE, delta, vowels,"
explain "serialization, analysis, compression benchmarks, edge cases)."
echo ""

python "$PY"
STATUS=$?

# ── Step 8: Final summary ─────────────────────────────────────
section "Step 8: Summary"
if [ $STATUS -eq 0 ]; then
  ok "All tests passed. MVD-COMP Phase 2 implementation verified."
  echo ""
  explain "What was validated:"
  echo "  • Core encode/decode reversibility on 10+ text types"
  echo "  • RLE mask encoding — correct runs, bytes round-trip, edge cases"
  echo "  • Delta position encoding — correct deltas, reconstruction"
  echo "  • 4-bit vowel packing — compact encoding with full round-trip"
  echo "  • Binary serialization — MVDC format for 6 diverse texts"
  echo "  • Vowel entropy analysis — Shannon entropy, probability sums"
  echo "  • Compression benchmarks — gzip/bz2/zlib on 6 corpora types"
  echo "  • Edge cases — 45KB text, punctuation, digits, whitespace"
else
  fail "Some tests failed. Review output above for details."
fi

echo ""