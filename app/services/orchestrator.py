"""
Main translation orchestrator service.
"""
from typing import Optional
from loguru import logger

from .ner_service import NERService
from .translation_service import TranslationService


class TranslationOrchestrator:
    """Main service that orchestrates the complete translation pipeline."""
    
    def __init__(self):
        """Initialize the orchestrator with NER and translation services."""
        self._ner_service: Optional[NERService] = None
        self._translation_service: Optional[TranslationService] = None
    
    @property
    def ner_service(self) -> NERService:
        """Lazy load NER service."""
        if self._ner_service is None:
            self._ner_service = NERService()
        return self._ner_service
    
    @property
    def translation_service(self) -> TranslationService:
        """Lazy load translation service."""
        if self._translation_service is None:
            self._translation_service = TranslationService()
        return self._translation_service
    
    async def translate(self, japanese_text: str) -> str:
        """
        Translate Japanese text to English with entity handling.
        
        Args:
            japanese_text: Input Japanese text
            
        Returns:
            Translated English text
        """
        logger.info(f"Starting translation orchestration: input_length={len(japanese_text)}")
        
        try:
            # Step 1: Extract entities and create placeholders
            logger.info("Step 1: Extracting entities and creating placeholders")
            text_with_placeholders, ph2ent = self.ner_service.extract_entities_with_placeholders(
                japanese_text
            )
            logger.info(f"Entities extracted: count={len(ph2ent)}, entities={list(ph2ent.values())}")
            
            # Step 2: Translate with entity handling
            logger.info("Step 2: Translating with entity handling")
            result = self.translation_service.translate_with_entity_handling(
                japanese_text, text_with_placeholders, ph2ent
            )
            logger.info("Translation pipeline completed successfully")
            
            return result
            
        except Exception as e:
            logger.error(f"Translation pipeline failed, using fallback: {str(e)}")
            # Fallback to simple translation
            return self.translation_service.translate_text_simple(japanese_text)


# Global instance
translation_orchestrator = TranslationOrchestrator()
