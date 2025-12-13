"""
Vocabulary Manager
Manages controlled vocabulary and validation
"""

import json
import os
from difflib import get_close_matches
from typing import Dict, List, Tuple, Optional


class VocabularyManager:
    """Manages controlled vocabulary and provides validation"""
    
    def __init__(self, vocabulary_path='vocabulary.json'):
        """
        Initialize vocabulary manager
        
        Args:
            vocabulary_path: Path to vocabulary JSON file
        """
        self.vocabulary_path = vocabulary_path
        self.vocabulary = self._load_vocabulary()
        self.custom_terms = {}  # Track custom terms added by users
    
    def _load_vocabulary(self) -> Dict:
        """Load vocabulary from JSON file"""
        if os.path.exists(self.vocabulary_path):
            with open(self.vocabulary_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            # Return default vocabulary if file doesn't exist
            return self._get_default_vocabulary()
    
    def _get_default_vocabulary(self) -> Dict:
        """Get default vocabulary structure"""
        return {
            'gender': ['Men', 'Women', 'Unisex'],
            'item_type': ['Apparel', 'Footwear'],
            'size': ['XS', 'S', 'M', 'L', 'XL', 'XXL'],
            'categories': {
                'Apparel': ['Topwear', 'Bottomwear', 'Dress', 'Outerwear', 'Innerwear'],
                'Footwear': ['Shoes', 'Sandals', 'Flip Flops', 'Boots', 'Socks']
            },
            'product_types': {
                'Apparel': {
                    'Topwear': ['Tops', 'Tshirts', 'Shirts', 'Blouses'],
                    'Bottomwear': ['Jeans', 'Pants', 'Shorts', 'Skirts']
                },
                'Footwear': {
                    'Shoes': ['Casual Shoes', 'Formal Shoes', 'Sports Shoes']
                }
            },
            'colors': ['Black', 'White', 'Blue', 'Red', 'Green', 'Yellow', 'Pink', 'Purple'],
            'materials': ['Cotton', 'Polyester', 'Denim', 'Leather'],
            'patterns': ['Solid', 'Striped', 'Floral', 'Geometric'],
            'usages': ['Casual', 'Formal', 'Sporty'],
            'brands': []
        }
    
    def validate(self, field: str, value: str, context: Optional[Dict] = None) -> Tuple[bool, Optional[str], Optional[List[str]]]:
        """
        Validate a value against vocabulary
        
        Args:
            field: Field name (e.g., 'gender', 'color', 'category')
            value: Value to validate
            context: Optional context (e.g., parent category for product_type)
            
        Returns:
            Tuple of (is_valid, normalized_value, suggestions)
        """
        value = str(value).strip()
        if not value:
            return False, None, None
        
        # Normalize value
        normalized = self._normalize(value)
        
        # Get vocabulary list for field
        vocab_list = self._get_vocabulary_list(field, context)
        
        if not vocab_list:
            return True, normalized, None  # No vocabulary for this field
        
        # Check exact match (case-insensitive)
        for term in vocab_list:
            if term.lower() == normalized.lower():
                return True, term, None
        
        # Check fuzzy match
        suggestions = get_close_matches(
            normalized,
            vocab_list,
            n=3,
            cutoff=0.6
        )
        
        if suggestions:
            return False, normalized, suggestions
        
        return False, normalized, None
    
    def _get_vocabulary_list(self, field: str, context: Optional[Dict] = None) -> List[str]:
        """Get vocabulary list for a field"""
        # Core fields
        if field in ['gender', 'item_type', 'size']:
            return self.vocabulary.get(field, [])
        
        # Context-dependent fields
        if field == 'category' and context:
            item_type = context.get('item_type')
            if item_type:
                return self.vocabulary.get('categories', {}).get(item_type, [])
        
        if field == 'product_type' and context:
            item_type = context.get('item_type')
            category = context.get('category')
            if item_type and category:
                return self.vocabulary.get('product_types', {}).get(item_type, {}).get(category, [])
        
        # Extended fields
        if field == 'color':
            return self.vocabulary.get('colors', [])
        if field == 'material':
            return self.vocabulary.get('materials', [])
        if field == 'pattern':
            return self.vocabulary.get('patterns', [])
        if field == 'usage':
            return self.vocabulary.get('usages', [])
        if field == 'brand':
            return self.vocabulary.get('brands', [])
        
        return []
    
    def _normalize(self, value: str) -> str:
        """Normalize value for comparison"""
        # Remove extra spaces
        value = ' '.join(value.split())
        # Title case
        return value.title()
    
    def get_suggestions(self, field: str, value: str, context: Optional[Dict] = None, limit: int = 5) -> List[str]:
        """Get vocabulary suggestions for a value"""
        vocab_list = self._get_vocabulary_list(field, context)
        if not vocab_list:
            return []
        
        normalized = self._normalize(value)
        suggestions = get_close_matches(
            normalized,
            vocab_list,
            n=limit,
            cutoff=0.5
        )
        return suggestions
    
    def add_custom_term(self, field: str, value: str, context: Optional[Dict] = None) -> bool:
        """
        Add a custom term (not in vocabulary)
        
        Args:
            field: Field name
            value: Custom value
            context: Optional context
            
        Returns:
            True if added successfully
        """
        normalized = self._normalize(value)
        
        if field not in self.custom_terms:
            self.custom_terms[field] = []
        
        if normalized not in self.custom_terms[field]:
            self.custom_terms[field].append(normalized)
        
        return True
    
    def get_custom_terms(self, field: str) -> List[str]:
        """Get custom terms for a field"""
        return self.custom_terms.get(field, [])
    
    def validate_hierarchy(self, item_type: str, category: str, product_type: str) -> Tuple[bool, str]:
        """
        Validate hierarchical relationship
        
        Args:
            item_type: Level 1 (Apparel/Footwear)
            category: Level 2 (Topwear/Bottomwear/etc)
            product_type: Level 3 (Tops/Tshirts/etc)
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Validate item_type
        if item_type not in self.vocabulary.get('item_type', []):
            return False, f"Invalid item_type: {item_type}"
        
        # Validate category belongs to item_type
        valid_categories = self.vocabulary.get('categories', {}).get(item_type, [])
        if category not in valid_categories:
            return False, f"Category '{category}' not valid for item_type '{item_type}'"
        
        # Validate product_type belongs to category
        valid_product_types = self.vocabulary.get('product_types', {}).get(item_type, {}).get(category, [])
        if product_type and product_type not in valid_product_types:
            return False, f"Product type '{product_type}' not valid for category '{category}'"
        
        return True, ""
    
    def get_valid_options(self, field: str, context: Optional[Dict] = None) -> List[str]:
        """Get all valid options for a field"""
        vocab_list = self._get_vocabulary_list(field, context)
        custom_list = self.get_custom_terms(field)
        return sorted(list(set(vocab_list + custom_list)))
    
    def save_vocabulary(self):
        """Save vocabulary to file"""
        with open(self.vocabulary_path, 'w', encoding='utf-8') as f:
            json.dump(self.vocabulary, f, indent=2, ensure_ascii=False)

