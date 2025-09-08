"""
Text preprocessing utilities for Japanese text.
"""
import re
import MeCab
from typing import List


def setup_mecab() -> MeCab.Tagger:
    """Initialize MeCab tokenizer."""
    try:
        mecab = MeCab.Tagger("-Owakati")
        return mecab
    except Exception as e:
        raise RuntimeError(f"Failed to initialize MeCab: {e}")


def tokenize_japanese_text(text: str, mecab: MeCab.Tagger) -> List[str]:
    """
    Tokenize Japanese text using MeCab.
    
    Args:
        text: Japanese text to tokenize
        mecab: MeCab tagger instance
        
    Returns:
        List of tokens
    """
    try:
        tokens = mecab.parse(text).strip().split()
        return tokens
    except Exception as e:
        raise ValueError(f"Failed to tokenize text: {e}")


def normalize_entity(entity_text: str) -> List[str]:
    """
    Normalize entity: strip suffix + split number.
    
    Args:
        entity_text: Entity text to normalize
        
    Returns:
        List of normalized entities
    """
    suffixes_to_strip = ["方面行き", "方面", "行き"]
    num_split_pattern = re.compile(r"^(.+?)(\d+号)$")
    
    # Strip suffixes
    for suffix in suffixes_to_strip:
        if entity_text.endswith(suffix):
            entity_text = entity_text[:-len(suffix)]
            break
    
    # Split numbers
    match = num_split_pattern.match(entity_text)
    if match:
        base, suffix = match.groups()
        return [base, suffix]
    else:
        return [entity_text]


def remove_adjacent_duplicate_phrases(text: str, max_phrase_len: int = 5) -> str:
    """
    Remove adjacent duplicate phrases in text.
    
    Args:
        text: Text to process
        max_phrase_len: Maximum phrase length to check
        
    Returns:
        Text with duplicates removed
    """
    # Remove extra spaces around commas
    text = re.sub(r'\s+,', ',', text)
    
    # Process phrase repetitions, decreasing from longest to single words
    for n in range(max_phrase_len, 0, -1):
        pattern = re.compile(
            r'(\b(?:[\w\-\'ōū]+(?:\s+|, ?)){%d}[\w\-\'ōū]+\b)'
            r'(,? \1\b)'
            % (n-1),
            flags=re.IGNORECASE
        )
        while pattern.search(text):
            text = pattern.sub(r'\1', text)
    
    # Handle single word repetitions
    text = re.sub(r'\b(\w+)(,? \1\b)', r'\1', text, flags=re.IGNORECASE)
    
    # Fix punctuation and spacing
    text = re.sub(r'\s{2,}', ' ', text)
    text = re.sub(r'\s+([.,;:!?])', r'\1', text)
    
    return text.strip()
