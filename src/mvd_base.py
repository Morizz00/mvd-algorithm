"""
MVD (Masked Vowel Displacement) - Phase 0 Implementation
Baseline reversible transform without cryptographic hardening.
"""

from typing import Tuple, List


def mvd_encode(text: str) -> Tuple[str, List[str], List[int]]:
    """
    Transform text into MVD representation.
    
    Args:
        text: Input string (UTF-8)
    
    Returns:
        (consonants, vowels, mask)
        - consonants: String with vowels removed
        - vowels: List of removed vowels in order
        - mask: List of integers (0=consonant, 1=vowel)
    
    Example:
        >>> mvd_encode("Hello")
        ("Hll", ["e", "o"], [0, 1, 0, 0, 1])
    """
    VOWELS = set('aeiouAEIOU')
    
    consonants = []
    vowels = []
    mask = []
    
    for char in text:
        if char in VOWELS:
            vowels.append(char)
            mask.append(1)
        else:
            consonants.append(char)
            mask.append(0)
    
    return ''.join(consonants), vowels, mask


def mvd_decode(consonants: str, vowels: List[str], mask: List[int]) -> str:
    """
    Reconstruct original text from MVD representation.
    
    Args:
        consonants: Consonant stream
        vowels: Vowel sequence
        mask: Position mask
    
    Returns:
        Original text
    
    Example:
        >>> mvd_decode("Hll", ["e", "o"], [0, 1, 0, 0, 1])
        "Hello"
    """
    result = []
    c_idx = 0
    v_idx = 0
    
    for bit in mask:
        if bit == 1:
            result.append(vowels[v_idx])
            v_idx += 1
        else:
            result.append(consonants[c_idx])
            c_idx += 1
    
    return ''.join(result)


def mask_to_bitstream(mask: List[int]) -> bytes:
    """
    Convert mask list to packed bitstream.
    
    Args:
        mask: List of 0s and 1s
    
    Returns:
        Packed bytes representation
    """
    # Pack 8 bits per byte
    bitstring = ''.join(str(b) for b in mask)
    # Pad to multiple of 8
    padding = (8 - len(bitstring) % 8) % 8
    bitstring += '0' * padding
    
    return int(bitstring, 2).to_bytes(len(bitstring) // 8, 'big')


def bitstream_to_mask(bitstream: bytes, length: int) -> List[int]:
    """
    Reconstruct mask from bitstream.
    
    Args:
        bitstream: Packed bytes
        length: Original mask length
    
    Returns:
        List of 0s and 1s
    """
    bits = bin(int.from_bytes(bitstream, 'big'))[2:].zfill(len(bitstream) * 8)
    return [int(b) for b in bits[:length]]


def encode_vowels(vowels: List[str]) -> bytes:
    """
    Encode vowel sequence with 3-bit mapping.
    
    Mapping:
        a/A -> 000/001
        e/E -> 010/011
        i/I -> 100/101
        o/O -> 110/111
        u/U -> 000/001 (temp: reuse codes)
    
    Args:
        vowels: List of vowel characters
    
    Returns:
        Packed bytes representation
    """
    VOWEL_MAP = {
        'a': 0b000, 'A': 0b001,
        'e': 0b010, 'E': 0b011,
        'i': 0b100, 'I': 0b101,
        'o': 0b110, 'O': 0b111,
        'u': 0b000, 'U': 0b001,  # Temp: reuse codes (will fix in later phases)
    }
    
    # Pack vowels into bitstring
    bitstring = ''
    for vowel in vowels:
        code = VOWEL_MAP.get(vowel, 0b000)
        bitstring += format(code, '03b')
    
    # Pad to byte boundary
    padding = (8 - len(bitstring) % 8) % 8
    bitstring += '0' * padding
    
    # Convert to bytes
    result = int(bitstring, 2).to_bytes(len(bitstring) // 8, 'big')
    return result


def decode_vowels(encoded: bytes, count: int) -> List[str]:
    """
    Decode vowel sequence from bytes.
    
    Args:
        encoded: Packed bytes
        count: Number of vowels to decode
    
    Returns:
        List of vowel characters
    """
    REVERSE_MAP = {
        0b000: 'a', 0b001: 'A',
        0b010: 'e', 0b011: 'E',
        0b100: 'i', 0b101: 'I',
        0b110: 'o', 0b111: 'O',
    }
    
    # Convert bytes to bitstring
    bitstring = bin(int.from_bytes(encoded, 'big'))[2:].zfill(len(encoded) * 8)
    
    vowels = []
    for i in range(count):
        code = int(bitstring[i*3:(i+1)*3], 2)
        vowels.append(REVERSE_MAP.get(code, 'a'))
    
    return vowels


if __name__ == "__main__":
    # Quick test
    test_text = "Hello, World!"
    print(f"Original: {test_text}")
    
    c, v, m = mvd_encode(test_text)
    print(f"Consonants: {c}")
    print(f"Vowels: {v}")
    print(f"Mask: {m}")
    
    reconstructed = mvd_decode(c, v, m)
    print(f"Reconstructed: {reconstructed}")
    print(f"Match: {test_text == reconstructed}")
