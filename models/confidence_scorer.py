"""
Confidence Scorer
Calculates confidence scores for auto-generated metadata
"""

from typing import Dict, List, Optional


class ConfidenceScorer:
    """Calculates confidence scores for metadata fields"""
    
    def __init__(self):
        """Initialize confidence scorer"""
        # Base confidence thresholds
        self.base_confidence = {
            'high': 0.8,
            'medium': 0.5,
            'low': 0.3
        }
    
    def calculate_confidence(self, field: str, value: any, source: str, 
                           image_confidence: Optional[float] = None,
                           vocabulary_match: Optional[bool] = None) -> float:
        """
        Calculate confidence score for a field
        
        Args:
            field: Field name
            value: Field value
            source: Source of value ('image', 'csv', 'manual', 'generated')
            image_confidence: Confidence from image analysis (0-1)
            vocabulary_match: Whether value matches vocabulary
            
        Returns:
            Confidence score (0-1)
        """
        # Base confidence by source
        source_confidence = {
            'manual': 1.0,  # Manual input is always 100%
            'csv': 0.9,     # CSV data is highly reliable
            'image': 0.7,   # Image analysis is moderately reliable
            'generated': 0.6  # Generated text is less reliable
        }
        
        base = source_confidence.get(source, 0.5)
        
        # Adjust based on image confidence
        if image_confidence is not None and source == 'image':
            base = (base + image_confidence) / 2
        
        # Adjust based on vocabulary match
        if vocabulary_match is not None:
            if vocabulary_match:
                base = min(1.0, base + 0.1)  # Boost if matches vocabulary
            else:
                base = max(0.0, base - 0.2)  # Reduce if doesn't match
        
        # Field-specific adjustments
        if field in ['gender', 'item_type', 'size']:
            # Core fields are more reliable
            base = min(1.0, base + 0.1)
        elif field in ['color', 'material']:
            # Visual attributes depend on image quality
            if source == 'image' and image_confidence:
                base = image_confidence
        elif field in ['title', 'description']:
            # Generated text is less reliable
            base = max(0.0, base - 0.1)
        
        return round(base, 2)
    
    def score_metadata(self, metadata: Dict, image_attributes: Dict, 
                      vocabulary_manager, product_info: Optional[Dict] = None) -> Dict:
        """
        Score all metadata fields
        
        Args:
            metadata: Generated metadata dictionary
            image_attributes: Attributes from image analysis
            vocabulary_manager: VocabularyManager instance
            product_info: Optional product information
            
        Returns:
            Dictionary with confidence scores for each field
        """
        scores = {}
        
        # Score faceted metadata
        faceted = metadata.get('faceted', {}).get('faceted_metadata', {})
        hierarchical = faceted.get('hierarchical_facets', {})
        flat = faceted.get('flat_facets', {})
        
        # Item Type
        item_type = metadata.get('faceted', {}).get('item_type', '')
        if item_type:
            vocab_match = vocabulary_manager.validate('item_type', item_type)[0]
            scores['item_type'] = self.calculate_confidence(
                'item_type', item_type, 'csv' if product_info else 'image',
                vocabulary_match=vocab_match
            )
        
        # Gender
        gender = metadata.get('faceted', {}).get('gender', '')
        if gender:
            vocab_match = vocabulary_manager.validate('gender', gender)[0]
            scores['gender'] = self.calculate_confidence(
                'gender', gender, 'manual' if product_info and product_info.get('gender') else 'csv',
                vocabulary_match=vocab_match
            )
        
        # Category hierarchy
        facet1 = hierarchical.get('facet_1_item_type', {})
        if facet1:
            category = facet1.get('level_2', '')
            product_type = facet1.get('level_3', '')
            
            if category:
                context = {'item_type': item_type}
                vocab_match = vocabulary_manager.validate('category', category, context)[0]
                scores['category'] = self.calculate_confidence(
                    'category', category, 'csv' if product_info else 'image',
                    vocabulary_match=vocab_match
                )
            
            if product_type:
                context = {'item_type': item_type, 'category': category}
                vocab_match = vocabulary_manager.validate('product_type', product_type, context)[0]
                scores['product_type'] = self.calculate_confidence(
                    'product_type', product_type, 'csv' if product_info else 'image',
                    vocabulary_match=vocab_match
                )
        
        # Flat facets
        if flat.get('color'):
            color = flat['color']
            vocab_match = vocabulary_manager.validate('color', color)[0]
            # Get image confidence for color
            color_confidence = None
            if image_attributes.get('color'):
                color_attrs = image_attributes['color']
                if color_attrs:
                    color_confidence = color_attrs[0].get('confidence', 0.5)
            
            scores['color'] = self.calculate_confidence(
                'color', color, 'image',
                image_confidence=color_confidence,
                vocabulary_match=vocab_match
            )
        
        if flat.get('material'):
            material = flat['material']
            vocab_match = vocabulary_manager.validate('material', material)[0]
            material_confidence = None
            if image_attributes.get('material'):
                material_attrs = image_attributes['material']
                if material_attrs:
                    material_confidence = material_attrs[0].get('confidence', 0.5)
            
            scores['material'] = self.calculate_confidence(
                'material', material, 'image',
                image_confidence=material_confidence,
                vocabulary_match=vocab_match
            )
        
        if flat.get('brand'):
            brand = flat['brand']
            vocab_match = vocabulary_manager.validate('brand', brand)[0]
            scores['brand'] = self.calculate_confidence(
                'brand', brand, 'manual' if product_info and product_info.get('brand') else 'csv',
                vocabulary_match=vocab_match
            )
        
        # Calculate overall confidence
        if scores:
            scores['overall'] = sum(scores.values()) / len(scores)
        else:
            scores['overall'] = 0.5
        
        return scores
    
    def requires_review(self, scores: Dict, threshold: float = 0.7) -> bool:
        """
        Determine if metadata requires human review
        
        Args:
            scores: Confidence scores dictionary
            threshold: Confidence threshold (default 0.7)
            
        Returns:
            True if review is required
        """
        overall = scores.get('overall', 0.5)
        
        # Require review if overall confidence is below threshold
        if overall < threshold:
            return True
        
        # Require review if any critical field is below threshold
        critical_fields = ['item_type', 'gender', 'category', 'product_type']
        for field in critical_fields:
            if field in scores and scores[field] < threshold:
                return True
        
        return False
    
    def get_review_priority(self, scores: Dict) -> str:
        """
        Get review priority level
        
        Args:
            scores: Confidence scores dictionary
            
        Returns:
            Priority: 'high', 'medium', 'low'
        """
        overall = scores.get('overall', 0.5)
        
        if overall < 0.5:
            return 'high'
        elif overall < 0.7:
            return 'medium'
        else:
            return 'low'

