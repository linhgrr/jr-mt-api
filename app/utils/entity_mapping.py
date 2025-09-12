"""
Entity mapping utilities for loading and accessing entity translations.
"""
import pandas as pd
import requests
import re
from typing import Dict, Optional
from functools import lru_cache
from loguru import logger


def load_entity_mapping_from_csv(file_path: str) -> Dict[str, str]:
    """
    Load entity mapping from CSV file.
    
    Args:
        file_path: Path to CSV file containing entity mappings
        
    Returns:
        Dictionary mapping Japanese entities to English
    """
    logger.info(f"Loading entity mapping from CSV: {file_path}")
    
    try:
        df = pd.read_csv(file_path, encoding='utf-8')
        
        # Clean data
        df_clean = df.dropna(subset=['kanji', 'english'])
        df_clean = df_clean[(df_clean['kanji'] != '') & (df_clean['english'] != '')]
        
        # Create mapping dictionary
        entity_mapping = dict(zip(df_clean['kanji'], df_clean['english']))
        logger.info(f"Entity mapping loaded successfully: {len(entity_mapping)} mappings")
        
        return entity_mapping
        
    except Exception as e:
        logger.error(f"Failed to load entity mapping from {file_path}: {e}")
        raise FileNotFoundError(f"Failed to load entity mapping from {file_path}: {e}")


@lru_cache(maxsize=1000)
def get_entity_from_wikidata(japanese_name: str) -> Optional[str]:
    """
    Get English entity name from Wikidata.
    
    Args:
        japanese_name: Japanese entity name
        
    Returns:
        English entity name if found, None otherwise
    """
    # Input validation
    if not japanese_name or len(japanese_name.strip()) < 2:
        return None
    
    japanese_name = japanese_name.strip()
    
    # Filter out punctuation and particles
    punctuation_chars = {'。', '、', '，', '．', '！', '？', '：', '；'}
    if japanese_name in punctuation_chars:
        return None
    
    japanese_particles = {
        'は', 'を', 'が', 'に', 'で', 'と', 'の', 'か', 'から', 'まで', 'も', 'へ', 'より', 'だけ', 'ばかり',
        'くらい', 'ほど', 'など', 'しか', 'でも', 'だって', 'って', 'なら', 'たら', 'れば', 'けれど',
        'が', 'けど', 'のに', 'ので', 'から', 'ため', 'ように', 'ために', 'として', 'について',
        'によって', 'に関して', 'に対して', 'について', 'として', 'において', 'において'
    }
    if japanese_name in japanese_particles:
        return None
    
    # Check for railway indicators
    railway_indicators = ['駅', '線', 'メトロ', 'Metro', '鉄道', '電車', '新幹線', 'JR', '方面', '地下鉄']
    has_railway_indicator = any(indicator in japanese_name for indicator in railway_indicators)
    
    # Check reasonable length
    is_reasonable_length = len(japanese_name) >= 2 and len(japanese_name) <= 25
    
    if not (has_railway_indicator and is_reasonable_length):
        return None
    
    try:
        # Search Wikidata
        search_url = "https://www.wikidata.org/w/api.php"
        search_params = {
            "action": "wbsearchentities",
            "language": "ja",
            "format": "json",
            "search": japanese_name,
            "limit": 5
        }
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(search_url, params=search_params, timeout=8, headers=headers)
        response.raise_for_status()
        results = response.json().get("search", [])
        
        if not results:
            return None
        
        # Get first result
        entity_id = results[0]["id"]
        description = results[0].get("description", "").lower()
        
        # Check if railway-related
        railway_keywords = ['station', 'railway', 'train', 'metro', 'line', 'subway', 'transit']
        is_railway_related = any(keyword in description for keyword in railway_keywords) if description else True
        
        if description and not is_railway_related and not has_railway_indicator:
            return None
        
        # Get entity data
        data_url = f"https://www.wikidata.org/wiki/Special:EntityData/{entity_id}.json"
        response = requests.get(data_url, timeout=8, headers=headers)
        response.raise_for_status()
        
        entity_data = response.json()
        en_label = entity_data.get("entities", {}).get(entity_id, {}).get("labels", {}).get("en", {}).get("value")
        
        return en_label
        
    except Exception:
        return None


def translate_entity_with_fallback(
    japanese_entity: str,
    csv_mapping: Dict[str, str]
) -> str:
    """
    Translate Japanese entity to English using multiple methods.
    
    Args:
        japanese_entity: Japanese entity to translate
        csv_mapping: CSV entity mapping dictionary
        
    Returns:
        Translated entity or original if not found
    """
    japanese_entity = japanese_entity.strip()
    if not japanese_entity:
        return ""
    
    logger.debug(f"Translating entity: {japanese_entity}")
    
    # Try CSV mapping first
    if japanese_entity in csv_mapping:
        result = csv_mapping[japanese_entity]
        logger.debug(f"Entity found in CSV mapping: {japanese_entity} -> {result}")
        return result
    
    # Try Wikidata
    logger.debug(f"Entity not in CSV, trying Wikidata: {japanese_entity}")
    wikidata_result = get_entity_from_wikidata(japanese_entity)
    if wikidata_result:
        logger.info(f"Entity translated via Wikidata: {japanese_entity} -> {wikidata_result}")
        return wikidata_result
    
    # Return original if no translation found
    logger.debug(f"Entity translation not found, keeping original: {japanese_entity}")
    return japanese_entity
