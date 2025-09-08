"""
Translation service for Japanese to English translation.
"""
import torch
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
from typing import Dict, Tuple

from ..core.config import get_settings
from ..utils.text_processing import remove_adjacent_duplicate_phrases
from ..utils.entity_mapping import load_entity_mapping_from_csv, translate_entity_with_fallback


class TranslationService:
    """Translation service for Japanese to English text."""
    
    def __init__(self):
        """Initialize translation service with model and entity mappings."""
        self.settings = get_settings()
        self.device = torch.device('cuda' if torch.cuda.is_available() and self.settings.use_cuda else 'cpu')
        
        # Load models
        self._load_models()
        
        # Load entity mapping
        self.entity_mapping = load_entity_mapping_from_csv(self.settings.entity_csv_path)
    
    def _load_models(self) -> None:
        """Load translation model and tokenizer."""
        try:
            self.tokenizer = AutoTokenizer.from_pretrained(self.settings.translation_model_name)
            self.model = AutoModelForSeq2SeqLM.from_pretrained(
                self.settings.translation_model_name
            ).to(self.device)
            self.model.eval()
        except Exception as e:
            raise RuntimeError(f"Failed to load translation models: {e}")
    
    def translate_text_simple(self, text: str) -> str:
        """
        Translate text using machine translation model.
        
        Args:
            text: Japanese text to translate
            
        Returns:
            Translated English text
        """
        if not text.strip():
            return ""
        
        try:
            inputs = self.tokenizer(
                [text],
                return_tensors="pt",
                padding=True,
                truncation=True,
                max_length=128
            ).to(self.device)
            
            with torch.no_grad():
                generated = self.model.generate(
                    **inputs,
                    max_length=128,
                    num_beams=6,
                    length_penalty=0.8,
                    early_stopping=True,
                    do_sample=False
                )
            
            result = self.tokenizer.decode(generated[0], skip_special_tokens=True).strip()
            return result
            
        except Exception as e:
            # Return original text if translation fails
            return text
    
    def translate_entities_with_fallback(self, ph2ent: Dict[str, str]) -> Tuple[Dict[str, str], Dict[str, str]]:
        """
        Translate entities using CSV mapping and Wikidata fallback.
        
        Args:
            ph2ent: Placeholder to entity mapping
            
        Returns:
            Tuple of (translated_entities, entities_to_restore)
        """
        updated_ph2ent = {}
        entities_to_restore = {}
        
        for placeholder, entity in ph2ent.items():
            translated = translate_entity_with_fallback(entity, self.entity_mapping)
            
            # If translation is different from original, it was successfully translated
            if translated != entity:
                updated_ph2ent[placeholder] = translated
            else:
                # Entity couldn't be translated, restore it later
                entities_to_restore[placeholder] = entity
        
        return updated_ph2ent, entities_to_restore
    
    def restore_entities_and_translate(
        self,
        text_with_placeholders: str,
        entities_to_restore: Dict[str, str],
        translated_entities: Dict[str, str]
    ) -> Tuple[str, str, Dict[str, str]]:
        """
        Restore untranslated entities and translate the text.
        
        Args:
            text_with_placeholders: Text with placeholders
            entities_to_restore: Entities that couldn't be translated
            translated_entities: Successfully translated entities
            
        Returns:
            Tuple of (final_text, translated_text, final_ph2ent)
        """
        # Restore untranslated entities
        final_text = text_with_placeholders
        for placeholder, original_entity in entities_to_restore.items():
            final_text = final_text.replace(placeholder, original_entity)
        
        # Translate the text
        translated_text = self.translate_text_simple(final_text)
        
        return final_text, translated_text, translated_entities
    
    def merge_translation_with_entities(
        self,
        translated_text: str,
        final_ph2ent: Dict[str, str]
    ) -> str:
        """
        Merge translated text with translated entities.
        
        Args:
            translated_text: Translated text with placeholders
            final_ph2ent: Final placeholder to entity mapping
            
        Returns:
            Final translated text with entities replaced
        """
        final_result = translated_text
        
        # Replace placeholders with translated entities
        for placeholder, translated_entity in final_ph2ent.items():
            if placeholder in final_result:
                final_result = final_result.replace(placeholder, translated_entity)
        
        # Clean up duplicates and formatting
        final_result = remove_adjacent_duplicate_phrases(final_result)
        
        return final_result
    
    def translate_with_entity_handling(
        self,
        text: str,
        text_with_placeholders: str,
        ph2ent: Dict[str, str]
    ) -> str:
        """
        Complete translation pipeline with entity handling.
        
        Args:
            text: Original Japanese text
            text_with_placeholders: Text with entity placeholders
            ph2ent: Placeholder to entity mapping
            
        Returns:
            Final translated English text
        """
        try:
            if not ph2ent:
                # No entities found, translate directly
                return self.translate_text_simple(text)
            
            # Translate entities
            translated_entities, entities_to_restore = self.translate_entities_with_fallback(ph2ent)
            
            # Restore untranslated entities and translate text
            final_text, translated_text, final_ph2ent = self.restore_entities_and_translate(
                text_with_placeholders, entities_to_restore, translated_entities
            )
            
            # Merge results
            final_result = self.merge_translation_with_entities(translated_text, final_ph2ent)
            
            return final_result
            
        except Exception:
            # Fallback to simple translation
            return self.translate_text_simple(text)
