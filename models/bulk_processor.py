"""
Bulk Processing Module
Processes CSV files and generates metadata for multiple products
"""

import csv
import os
from pathlib import Path


class BulkProcessor:
    """Processes bulk uploads from CSV files"""
    
    def __init__(self, image_analyzer, text_generator, classifier, attribute_extractor, faceted_generator, vocabulary_manager=None, confidence_scorer=None):
        """
        Initialize bulk processor
        
        Args:
            image_analyzer: ImageAnalyzer instance
            text_generator: TextGenerator instance
            classifier: ProductClassifier instance
            attribute_extractor: AttributeExtractor instance
            faceted_generator: FacetedMetadataGenerator instance
            vocabulary_manager: Optional VocabularyManager instance
            confidence_scorer: Optional ConfidenceScorer instance
        """
        self.image_analyzer = image_analyzer
        self.text_generator = text_generator
        self.classifier = classifier
        self.attribute_extractor = attribute_extractor
        self.faceted_generator = faceted_generator
        self.vocabulary_manager = vocabulary_manager
        self.confidence_scorer = confidence_scorer
    
    def process_csv(self, csv_path, images_dir=None, limit=None):
        """
        Process CSV file and generate metadata for all products
        
        Args:
            csv_path: Path to CSV file
            images_dir: Directory containing images (optional)
            limit: Maximum number of products to process (for testing)
            
        Returns:
            list: List of generated metadata dictionaries
        """
        results = []
        
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            for idx, row in enumerate(reader):
                if limit and idx >= limit:
                    break
                
                try:
                    metadata = self.process_single_product(row, images_dir)
                    metadata['csv_row_index'] = idx + 1
                    metadata['csv_data'] = row
                    results.append(metadata)
                except Exception as e:
                    # Error is captured in result dict
                    results.append({
                        'error': str(e),
                        'csv_row_index': idx + 1,
                        'csv_data': row
                    })
        
        return results
    
    def process_single_product(self, csv_row, images_dir=None):
        """
        Process a single product from CSV row
        
        Args:
            csv_row: Dictionary with CSV row data
            images_dir: Directory containing images
            
        Returns:
            dict: Generated metadata
        """
        # Get image path
        image_file = csv_row.get("Image", "")
        image_path = None
        
        if images_dir and image_file:
            image_path = os.path.join(images_dir, image_file)
            if not os.path.exists(image_path):
                # Try current directory
                if os.path.exists(image_file):
                    image_path = image_file
                else:
                    raise FileNotFoundError(f"Image not found: {image_file}")
        elif image_file and os.path.exists(image_file):
            image_path = image_file
        
        # Analyze image if available
        image_attributes = {}
        if image_path and os.path.exists(image_path):
            image_analysis = self.image_analyzer.analyze_image(image_path)
            image_attributes = image_analysis.get('attributes', {})
        
        # Generate faceted metadata
        faceted_metadata = self.faceted_generator.generate_faceted_metadata(
            image_attributes,
            product_info=None,
            csv_data=csv_row
        )
        
        # Generate classification
        classification = self.classifier.classify(image_attributes, csv_row)
        
        # Extract technical attributes
        technical = self.attribute_extractor.extract_attributes(image_attributes, csv_row)
        
        # Generate text (using CSV title if available)
        product_info = {
            'brand': csv_row.get('Brand', ''),
            'gender': csv_row.get('Gender', '')
        }
        
        title = csv_row.get('ProductTitle', '')
        if not title:
            title = self.text_generator.generate_title(product_info, image_attributes)
        
        description = self.text_generator.generate_description(product_info, image_attributes)
        bullets = self.text_generator.generate_bullet_points(product_info, image_attributes)
        keywords = self.text_generator.generate_keywords(product_info, image_attributes)
        
        # Compile complete metadata
        metadata = {
            # Faceted metadata (hierarchical + flat)
            "faceted": faceted_metadata,
            
            # Descriptive metadata
            "descriptive": {
                "title": title,
                "short_description": description[:150] + '...' if len(description) > 150 else description,
                "long_description": description,
                "bullet_points": bullets
            },
            
            # Classification (legacy format for compatibility)
            "classification": classification,
            
            # Technical attributes
            "technical": technical,
            
            # Discovery metadata
            "discovery": {
                "keywords": keywords,
                "related_tags": classification.get('tags', [])[:10]
            },
            
            # Source information
            "source": {
                "product_id": csv_row.get("ProductId", ""),
                "image_file": image_file,
                "image_url": csv_row.get("ImageURL", "")
            }
        }
        
        return metadata
    
    def export_faceted_metadata(self, results, output_format='json'):
        """
        Export faceted metadata in various formats
        
        Args:
            results: List of metadata dictionaries
            output_format: 'json' or 'csv'
            
        Returns:
            str: Path to exported file
        """
        from datetime import datetime
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        if output_format == 'json':
            import json
            filename = f"faceted_metadata_{timestamp}.json"
            filepath = os.path.join('exports', filename)
            os.makedirs('exports', exist_ok=True)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
            
            return filepath
        
        elif output_format == 'csv':
            import csv
            filename = f"faceted_metadata_{timestamp}.csv"
            filepath = os.path.join('exports', filename)
            os.makedirs('exports', exist_ok=True)
            
            # Flatten faceted metadata for CSV
            with open(filepath, 'w', newline='', encoding='utf-8') as f:
                if not results:
                    return filepath
                
                # Get all possible fields
                fieldnames = [
                    'product_id', 'item_type', 'gender',
                    'facet1_level1', 'facet1_level2', 'facet1_level3', 'facet1_path',
                    'facet2_level1', 'facet2_level2', 'facet2_level3', 'facet2_path',
                    'color', 'material', 'pattern', 'size', 'brand',
                    'title', 'category_path', 'tags'
                ]
                
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                
                for result in results:
                    if 'error' in result:
                        continue
                    
                    faceted = result.get('faceted', {}).get('faceted_metadata', {})
                    hierarchical = faceted.get('hierarchical_facets', {})
                    flat = faceted.get('flat_facets', {})
                    
                    row = {
                        'product_id': result.get('source', {}).get('product_id', ''),
                        'item_type': result.get('faceted', {}).get('item_type', ''),
                        'gender': result.get('faceted', {}).get('gender', ''),
                        'facet1_level1': hierarchical.get('facet_1_item_type', {}).get('level_1', ''),
                        'facet1_level2': hierarchical.get('facet_1_item_type', {}).get('level_2', ''),
                        'facet1_level3': hierarchical.get('facet_1_item_type', {}).get('level_3', ''),
                        'facet1_path': hierarchical.get('facet_1_item_type', {}).get('full_path', ''),
                        'facet2_level1': hierarchical.get('facet_2_style_usage', {}).get('level_1', ''),
                        'facet2_level2': hierarchical.get('facet_2_style_usage', {}).get('level_2', ''),
                        'facet2_level3': hierarchical.get('facet_2_style_usage', {}).get('level_3', ''),
                        'facet2_path': hierarchical.get('facet_2_style_usage', {}).get('full_path', ''),
                        'color': flat.get('color', ''),
                        'material': flat.get('material', ''),
                        'pattern': flat.get('pattern', ''),
                        'size': flat.get('size', ''),
                        'brand': flat.get('brand', ''),
                        'title': result.get('descriptive', {}).get('title', ''),
                        'category_path': result.get('classification', {}).get('hierarchy', {}).get('full_path', ''),
                        'tags': ', '.join(result.get('classification', {}).get('tags', [])[:5])
                    }
                    writer.writerow(row)
            
            return filepath
        
        else:
            raise ValueError(f"Unsupported format: {output_format}. Only 'json' and 'csv' are supported.")

