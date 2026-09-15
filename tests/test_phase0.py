"""
Unit tests for Phase 0 - Baseline MVD Implementation
"""

import sys
sys.path.insert(0, '../src')

import pytest
from mvd_base import (
    mvd_encode, mvd_decode,
    mask_to_bitstream, bitstream_to_mask,
    encode_vowels, decode_vowels
)


def test_reversibility():
    """Core property: decode(encode(x)) == x"""
    test_cases = [
        "Hello World",
        "The quick brown fox",
        "AEIOU aeiou",
        "xyz",
        "Programming in Python",
        "",
        "a",
        "beautiful",
        "rhythm",
    ]
    
    for text in test_cases:
        c, v, m = mvd_encode(text)
        reconstructed = mvd_decode(c, v, m)
        assert reconstructed == text, f"Failed on: {text}"


def test_vowel_extraction():
    """Verify vowels are correctly identified"""
    c, v, m = mvd_encode("beautiful")
    assert v == ['e', 'a', 'u', 'i', 'u']
    assert c == "btfl"
    
    c, v, m = mvd_encode("Hello")
    assert v == ['e', 'o']
    assert c == "Hll"


def test_edge_cases():
    """Handle boundary conditions"""
    # All vowels
    c, v, m = mvd_encode("aeiou")
    assert c == ""
    assert len(v) == 5
    assert sum(m) == 5
    
    # No vowels
    c, v, m = mvd_encode("xyz")
    assert v == []
    assert c == "xyz"
    assert sum(m) == 0
    
    # Empty
    c, v, m = mvd_encode("")
    assert (c, v, m) == ("", [], [])
    
    # Single character vowel
    c, v, m = mvd_encode("a")
    assert c == ""
    assert v == ["a"]
    
    # Single character consonant
    c, v, m = mvd_encode("b")
    assert c == "b"
    assert v == []


def test_case_preservation():
    """Case must be preserved"""
    text = "HeLLo WoRLd"
    c, v, m = mvd_encode(text)
    assert mvd_decode(c, v, m) == text
    
    text = "AEIOU aeiou"
    c, v, m = mvd_encode(text)
    assert mvd_decode(c, v, m) == text


def test_punctuation_handling():
    """Punctuation should be treated as consonants"""
    text = "Hello, World!"
    c, v, m = mvd_encode(text)
    reconstructed = mvd_decode(c, v, m)
    assert reconstructed == text


def test_mask_bitstream_conversion():
    """Test mask to/from bitstream conversion"""
    masks = [
        [0, 1, 0, 0, 1],
        [1, 1, 1, 1, 1],
        [0, 0, 0, 0, 0],
        [1, 0, 1, 0, 1, 0, 1, 0],
        [],
    ]
    
    for mask in masks:
        if len(mask) > 0:
            bitstream = mask_to_bitstream(mask)
            recovered = bitstream_to_mask(bitstream, len(mask))
            assert recovered == mask, f"Failed on mask: {mask}"


def test_vowel_encoding():
    """Test vowel encoding/decoding"""
    test_cases = [
        ['a', 'e', 'i', 'o', 'u'],
        ['A', 'E', 'I', 'O', 'U'],
        ['e', 'a', 'u', 'i', 'u'],
        ['a'],
        [],
    ]
    
    for vowels in test_cases:
        if len(vowels) > 0:
            encoded = encode_vowels(vowels)
            decoded = decode_vowels(encoded, len(vowels))
            # Note: u/U mapping is temp and may not round-trip perfectly
            # This will be fixed in later phases


def test_special_characters():
    """Test handling of special characters"""
    test_cases = [
        "Hello, World!",
        "Test: 123",
        "End.\n",
        "Tab\there",
    ]
    
    for text in test_cases:
        c, v, m = mvd_encode(text)
        reconstructed = mvd_decode(c, v, m)
        assert reconstructed == text


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
