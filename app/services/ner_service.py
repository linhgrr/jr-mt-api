"""
Named Entity Recognition service for Japanese railway entities.
"""
import torch
from transformers import AutoTokenizer, AutoModelForTokenClassification
from typing import List, Tuple, Dict
import MeCab

from ..core.config import get_settings
from ..utils.text_processing import setup_mecab, tokenize_japanese_text, normalize_entity


class NERService:
    """Named Entity Recognition service for Japanese railway entities."""
    
    def __init__(self):
        """Initialize NER service with model and tokenizer."""
        self.settings = get_settings()
        self.device = torch.device('cuda' if torch.cuda.is_available() and self.settings.use_cuda else 'cpu')
        self.id_to_label = {0: 'O', 1: 'B-STATION', 2: 'I-STATION', 3: 'B-LINE', 4: 'I-LINE'}
        
        # Initialize models
        self._load_models()
        
        # Initialize MeCab
        self.mecab = setup_mecab()
    
    def _load_models(self) -> None:
        """Load NER model and tokenizer."""
        try:
            self.tokenizer = AutoTokenizer.from_pretrained(self.settings.ner_model_name)
            self.model = AutoModelForTokenClassification.from_pretrained(
                self.settings.ner_model_name
            ).to(self.device)
            self.model.eval()
        except Exception as e:
            raise RuntimeError(f"Failed to load NER models: {e}")
    
    def predict_entities(self, text_tokens: List[str]) -> List[Tuple[str, str]]:
        """
        Predict entities from tokenized text.
        
        Args:
            text_tokens: List of text tokens
            
        Returns:
            List of (token, label) tuples
        """
        try:
            inputs = self.tokenizer(
                text_tokens,
                return_tensors="pt",
                truncation=True,
                padding=True,
                is_split_into_words=True
            ).to(self.device)
            
            with torch.no_grad():
                outputs = self.model(**inputs)
                predictions = torch.argmax(outputs.logits, dim=2)
            
            word_ids = inputs.word_ids()
            predicted_labels = []
            seen_words = set()
            
            for i, word_id in enumerate(word_ids):
                if word_id is not None and word_id not in seen_words:
                    predicted_labels.append(self.id_to_label[predictions[0][i].item()])
                    seen_words.add(word_id)
            
            min_len = min(len(text_tokens), len(predicted_labels))
            return list(zip(text_tokens[:min_len], predicted_labels[:min_len]))
            
        except Exception as e:
            raise RuntimeError(f"Failed to predict entities: {e}")
    
    def extract_and_normalize_entities(self, predicted: List[Tuple[str, str]]) -> List[str]:
        """
        Extract and normalize entities from predictions.
        
        Args:
            predicted: List of (token, label) tuples
            
        Returns:
            List of normalized entities
        """
        entities = []
        i = 0
        
        while i < len(predicted):
            token, label = predicted[i]
            
            if label.startswith("B-"):
                ent_type = label.split("-", 1)[1]
                ent_tokens = [token]
                i += 1
                
                while i < len(predicted) and predicted[i][1] == f"I-{ent_type}":
                    ent_tokens.append(predicted[i][0])
                    i += 1
                
                entity_text = "".join(ent_tokens)
                normalized_entities = normalize_entity(entity_text)
                entities.extend(normalized_entities)
            else:
                i += 1
        
        return entities
    
    def create_placeholder_mapping(self, text: str, entities: List[str]) -> Tuple[Dict[str, str], Dict[str, str]]:
        """
        Create mapping between entities and placeholders.
        
        Args:
            text: Original text
            entities: List of entities
            
        Returns:
            Tuple of (placeholder_to_entity, entity_to_placeholder) mappings
        """
        offsets = []
        for ent in entities:
            pos = text.find(ent)
            if pos != -1:
                offsets.append((pos, ent))
        
        offsets.sort()
        
        ph2ent = {}
        ent2ph = {}
        ph_counter = 0
        
        for pos, ent in offsets:
            if ent not in ent2ph:
                ph = f"[PH{ph_counter}]"
                ent2ph[ent] = ph
                ph2ent[ph] = ent
                ph_counter += 1
        
        return ph2ent, ent2ph
    
    def mask_text_with_placeholders(self, text: str, ent2ph: Dict[str, str]) -> str:
        """
        Replace entities in text with placeholders.
        
        Args:
            text: Original text
            ent2ph: Entity to placeholder mapping
            
        Returns:
            Text with entities replaced by placeholders
        """
        result_text = text
        sorted_entities = sorted(ent2ph.keys(), key=len, reverse=True)
        
        for ent in sorted_entities:
            result_text = result_text.replace(ent, ent2ph[ent])
        
        return result_text
    
    def extract_entities_with_placeholders(self, text: str) -> Tuple[str, Dict[str, str]]:
        """
        Extract entities and replace with placeholders.
        
        Args:
            text: Input Japanese text
            
        Returns:
            Tuple of (text_with_placeholders, placeholder_to_entity_mapping)
        """
        try:
            # Tokenize
            tokens = tokenize_japanese_text(text, self.mecab)
            
            # Predict entities
            predicted = self.predict_entities(tokens)
            
            # Extract and normalize entities
            normalized_entities = self.extract_and_normalize_entities(predicted)
            
            # Create placeholder mapping
            ph2ent, ent2ph = self.create_placeholder_mapping(text, normalized_entities)
            
            # Mask text
            final_text = self.mask_text_with_placeholders(text, ent2ph)
            
            return final_text, ph2ent
            
        except Exception as e:
            # Return original text if processing fails
            return text, {}
