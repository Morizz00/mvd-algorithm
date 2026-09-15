"""
Performance benchmarks for Phase 0 - Baseline MVD Implementation
"""

import sys
sys.path.insert(0, '../src')

import time
import random
import string
from mvd_base import mvd_encode, mvd_decode


def generate_text(size_kb: int) -> str:
    """Generate random text of specified size."""
    chars = string.ascii_letters + ' ' * 10  # Add spaces for realism
    return ''.join(random.choice(chars) for _ in range(size_kb * 1024))


def benchmark_encode_decode():
    """Measure transformation speed at different scales."""
    print("=" * 60)
    print("MVD Phase 0 - Performance Benchmark")
    print("=" * 60)
    print()
    
    sizes = [1, 10, 100, 1000]  # KB
    
    print(f"{'Size':>8} | {'Encode (ms)':>12} | {'Decode (ms)':>12} | {'Total (ms)':>12}")
    print("-" * 60)
    
    for size in sizes:
        text = generate_text(size)
        
        # Encode
        start = time.perf_counter()
        c, v, m = mvd_encode(text)
        encode_time = time.perf_counter() - start
        
        # Decode
        start = time.perf_counter()
        reconstructed = mvd_decode(c, v, m)
        decode_time = time.perf_counter() - start
        
        # Verify correctness
        assert reconstructed == text, f"Reversibility check failed at {size}KB"
        
        total_time = encode_time + decode_time
        
        print(f"{size:>6}KB | {encode_time*1000:>11.2f}  | {decode_time*1000:>11.2f}  | {total_time*1000:>11.2f}")
    
    print()
    print("✓ All reversibility checks passed")


def benchmark_compression_ratio():
    """Measure space efficiency."""
    print()
    print("=" * 60)
    print("Compression Analysis")
    print("=" * 60)
    print()
    
    test_texts = [
        ("English prose", "The quick brown fox jumps over the lazy dog. " * 20),
        ("All vowels", "aeiouAEIOU" * 100),
        ("No vowels", "bcdfghjklmnpqrstvwxyz" * 50),
        ("Mixed", "Hello World! Programming in Python is fun." * 25),
    ]
    
    print(f"{'Text Type':>15} | {'Original':>10} | {'Consonants':>12} | {'Vowels':>10} | {'Mask':>10}")
    print("-" * 70)
    
    for name, text in test_texts:
        c, v, m = mvd_encode(text)
        
        original_size = len(text)
        consonants_size = len(c)
        vowels_size = len(v)
        mask_size = len(m)
        
        print(f"{name:>15} | {original_size:>10} | {consonants_size:>12} | {vowels_size:>10} | {mask_size:>10}")
    
    print()


def benchmark_edge_cases():
    """Test performance on edge cases."""
    print("=" * 60)
    print("Edge Case Performance")
    print("=" * 60)
    print()
    
    edge_cases = [
        ("Empty string", ""),
        ("Single char", "a"),
        ("All vowels (1KB)", "aeiou" * 204),
        ("No vowels (1KB)", "bcdfg" * 204),
        ("Long word", "z" * 10000),
    ]
    
    print(f"{'Case':>20} | {'Time (ms)':>12} | {'Status':>10}")
    print("-" * 50)
    
    for name, text in edge_cases:
        try:
            start = time.perf_counter()
            c, v, m = mvd_encode(text)
            reconstructed = mvd_decode(c, v, m)
            elapsed = time.perf_counter() - start
            
            status = "✓ PASS" if reconstructed == text else "✗ FAIL"
            print(f"{name:>20} | {elapsed*1000:>11.3f}  | {status:>10}")
        except Exception as e:
            print(f"{name:>20} | {'N/A':>11}  | {'✗ ERROR':>10}")
            print(f"  Error: {e}")
    
    print()


if __name__ == "__main__":
    random.seed(42)  # For reproducibility
    
    benchmark_encode_decode()
    benchmark_compression_ratio()
    benchmark_edge_cases()
    
    print("=" * 60)
    print("Benchmark complete!")
    print("=" * 60)
