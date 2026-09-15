# 04 — Phase 0 explained (does the split work?)

## Goal

Prove the boring foundation:

1. `decode(encode(text)) == text` always (on our tests).  
2. It is fast enough that later experiments aren’t bottlenecked.  
3. Edge cases don’t explode (empty string, all vowels, punctuation…).

## Where the code lives

| File | Job |
|---|---|
| `src/mvd_base.py` | `mvd_encode`, `mvd_decode`, mask packing, early vowel packing |
| `tests/test_phase0.py` | pytest suite |
| `benchmarks/phase0_perf.py` | timing script |
| `test_output.log` | saved test run |
| `benchmark_output.log` | saved timings |

## What we measured

**Correctness:** 8/8 tests passed (reversibility, vowel extraction, edges, case, punctuation, bitstream, vowel encoding, special characters).

**Speed (from the log):**

| Size | Encode | Decode | Total |
|---|---|---|---|
| 1 KB | 0.07 ms | 0.06 ms | 0.13 ms |
| 10 KB | 0.58 ms | 0.49 ms | 1.07 ms |
| 100 KB | 8.32 ms | 10.01 ms | 18.33 ms |
| 1000 KB | 107.91 ms | 121.66 ms | 229.57 ms |

For 10 KB we are far under a 100 ms “feels fine” budget.

## Important: Phase 0 does not compress

Encode turns one string into three pieces whose total information is the same. Disk size is not supposed to shrink here. Shrinkage only appears later when we **drop** vowels or when a compressor exploits structure.

## Known limitations called out early

- Only ASCII `aeiou` / `AEIOU`.  
- Early 3-bit vowel packing in Phase 0 temporarily reused codes for `u`/`U` (Phase 2 moves to cleaner 4-bit codes).  
- No security claims.

## Verdict

**WIN.** Foundation is solid. Everything else builds on this.

## Next

[05-phase2-compression-explained.md](05-phase2-compression-explained.md)
