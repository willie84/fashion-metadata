import json
import os
from difflib import get_close_matches
from typing import Dict, List, Tuple, Optional


class VocabularyManager:
    def __init__(self, vocabulary_path='vocabulary.json'):
        self.vocabulary_path = vocabulary_path
        self.vocabulary = self._load_vocabulary()
        self.custom_terms = {}
    
    def _load_vocabulary(self) -> Dict:
        if os.path.exists(self.vocabulary_path):
            with open(self.vocabulary_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            return self._get_default_vocabulary()
    
    def _get_default_vocabulary(self) -> Dict:
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
            'colors': ["red", "pink", "black", "white", "brown", "green", "blue", "gold",  "purple", "orange", "grey", "maroon", "yellow", "navy blue", "khaki", "magenta", "mushroom brown", "silver", "olive", "beige", "nude", "lavender", "tan"],
            'materials': ["cotton", "denim", "leather", "silk", "polyester", "wool", "linen", "rayon", "spandex", "nylon", "canvas"],
            'patterns': ['Solid', 'Striped', 'Floral', 'Geometric', 'Animal Print', 'Paisley', 'Polka Dot', 'Check', 'Stripes', 'Tartan', 'Houndstooth', 'Checkered', 'Gingham', 'Tartan', 'Houndstooth', 'Checkered', 'Gingham', 'Tartan', 'Houndstooth', 'Checkered', 'Gingham'],
            'usages': ['Casual', 'Formal', 'Sporty'],
            'brands': [
                'Adidas', 'Aeropostale', 'Allen', 'Allen Solly', 'American Eagle', 'Ant',
                'Arrow', 'ASICS', 'Avengers', 'Banana Republic', 'Basics', 'Bata', 'Batman',
                'Ben', 'Benetton', 'Btwin', 'Buckaroo', 'Calvin Klein', 'Carlton', 'Catwalk',
                'Chhota Bheem', 'Clarks', 'Cobblerz', 'Converse', 'Coolers', 'Crocs', 'DC',
                'Decathlon', 'Disney', 'Do', 'Doodle', 'Enroute', 'Estd.', 'Fabindia', 'FILA',
                'Filac', 'Flying Machine', 'Force', 'Forever 21', 'Fortune', 'Franco', 'Ganuchi',
                'Gap', 'GAS', 'Gini & Jony', 'Giny', 'Gliders', 'Globalite', 'Grendha', 'Guess',
                'H&M', 'Hannah', 'Hollister', 'ID', 'Inc', 'Jockey', 'Kappa', 'Lacoste',
                'Levi\'s', 'Marks & Spencer', 'Mufti', 'Nike', 'Old Navy', 'Pepe Jeans',
                'Peter England', 'Provogue', 'Puma', 'Red Tape', 'Reebok', 'Skechers', 'Sparx',
                'Tommy Hilfiger', 'UCB', 'Under Armour', 'Uniqlo', 'US Polo Assn', 'Van Heusen',
                'Vans', 'Versace', 'Woodland', 'Wrangler', 'Yonex', 'Zara'
            ]
        }
    
    def validate(self, field: str, value: str, context: Optional[Dict] = None) -> Tuple[bool, Optional[str], Optional[List[str]]]:
        value = str(value).strip()
        if not value:
            return False, None, None
        
        normalized = self._normalize(value)
        vocab_list = self._get_vocabulary_list(field, context)
        
        if not vocab_list:
            return True, normalized, None
        
        for term in vocab_list:
            if term.lower() == normalized.lower():
                return True, term, None
        
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
        if field in ['gender', 'item_type', 'size']:
            return self.vocabulary.get(field, [])
        
        if field == 'category' and context:
            item_type = context.get('item_type')
            if item_type:
                return self.vocabulary.get('categories', {}).get(item_type, [])
        
        if field == 'product_type' and context:
            item_type = context.get('item_type')
            category = context.get('category')
            if item_type and category:
                return self.vocabulary.get('product_types', {}).get(item_type, {}).get(category, [])
        
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
        value = ' '.join(value.split())
        return value.title()
    
    def get_suggestions(self, field: str, value: str, context: Optional[Dict] = None, limit: int = 5) -> List[str]:
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
        normalized = self._normalize(value)
        
        if field not in self.custom_terms:
            self.custom_terms[field] = []
        
        if normalized not in self.custom_terms[field]:
            self.custom_terms[field].append(normalized)
        
        return True
    
    def get_custom_terms(self, field: str) -> List[str]:
        return self.custom_terms.get(field, [])
    
    def validate_hierarchy(self, item_type: str, category: str, product_type: str) -> Tuple[bool, str]:
        if item_type not in self.vocabulary.get('item_type', []):
            return False, f"Invalid item_type: {item_type}"
        
        valid_categories = self.vocabulary.get('categories', {}).get(item_type, [])
        if category not in valid_categories:
            return False, f"Category '{category}' not valid for item_type '{item_type}'"
        
        valid_product_types = self.vocabulary.get('product_types', {}).get(item_type, {}).get(category, [])
        if product_type and product_type not in valid_product_types:
            return False, f"Product type '{product_type}' not valid for category '{category}'"
        
        return True, ""
    
    def get_valid_options(self, field: str, context: Optional[Dict] = None) -> List[str]:
        vocab_list = self._get_vocabulary_list(field, context)
        custom_list = self.get_custom_terms(field)
        return sorted(list(set(vocab_list + custom_list)))
    
    def get_category_keyword_mappings(self) -> Dict[str, List[str]]:
        return self.vocabulary.get('category_keyword_mappings', {})
    
    def get_color_keyword_mappings(self) -> Dict[str, List[str]]:
        return self.vocabulary.get('color_keyword_mappings', {})
    
    def get_material_keyword_mappings(self) -> Dict[str, List[str]]:
        return self.vocabulary.get('material_keyword_mappings', {})
    
    def get_pattern_keyword_mappings(self) -> Dict[str, List[str]]:
        return self.vocabulary.get('pattern_keyword_mappings', {})
    
    def get_item_type_hierarchy(self) -> Dict:
        hierarchy = {}
        item_types = self.vocabulary.get('item_type', [])
        categories = self.vocabulary.get('categories', {})
        product_types = self.vocabulary.get('product_types', {})
        
        for item_type in item_types:
            hierarchy[item_type] = {}
            if item_type in categories:
                for category in categories[item_type]:
                    hierarchy[item_type][category] = []
                    if item_type in product_types and category in product_types[item_type]:
                        hierarchy[item_type][category] = product_types[item_type][category]
        
        return hierarchy
    
    def get_style_hierarchy(self) -> Dict:
        return self.vocabulary.get('style_hierarchy', self._get_default_style_hierarchy())
    
    def _get_default_style_hierarchy(self) -> Dict:
        return {
            "Casual": {
                "Everyday": ["Basic", "Comfort", "Relaxed"],
                "Streetwear": ["Urban", "Trendy", "Athletic"],
                "Weekend": ["Leisure", "Outdoor", "Active"],
                "Smart Casual": ["Polished", "Refined", "Elevated"]
            },
            "Formal": {
                "Business": ["Professional", "Corporate", "Office"],
                "Evening": ["Elegant", "Sophisticated", "Dressy"],
                "Special Occasion": ["Party", "Wedding", "Event"]
            },
            "Sporty": {
                "Athletic": ["Performance", "Training", "Gym"],
                "Active": ["Outdoor", "Hiking", "Running"],
                "Athleisure": ["Comfort", "Stylish", "Versatile"]
            },
            "Ethnic": {
                "Traditional": ["Classic", "Cultural", "Heritage"],
                "Fusion": ["Modern", "Contemporary", "Blended"]
            }
        }
    
    def save_vocabulary(self):
        with open(self.vocabulary_path, 'w', encoding='utf-8') as f:
            json.dump(self.vocabulary, f, indent=2, ensure_ascii=False)

