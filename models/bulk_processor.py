import csv
import os
from pathlib import Path


class BulkProcessor:
    def __init__(self, image_analyzer, text_generator, faceted_generator, vocabulary_manager=None, confidence_scorer=None):
        self.image_analyzer = image_analyzer
        self.text_generator = text_generator
        self.faceted_generator = faceted_generator
        self.vocabulary_manager = vocabulary_manager
        self.confidence_scorer = confidence_scorer
    
    def process_csv(self, csv_path, images_dir=None, limit=None, progress_callback=None):
        results = []
        
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            total = len(rows) if not limit else min(limit, len(rows))
            
            for idx, row in enumerate(rows):
                if limit and idx >= limit:
                    break
                
                if progress_callback:
                    progress_callback(idx + 1, total)
                
                try:
                    metadata = self.process_single_product(row, images_dir)
                    metadata['csv_row_index'] = idx + 1
                    metadata['csv_data'] = row
                    results.append(metadata)
                except Exception as e:
                    results.append({
                        'error': str(e),
                        'csv_row_index': idx + 1,
                        'csv_data': row
                    })
        
        return results
    
    def process_single_product(self, csv_row, images_dir=None):
        gender = csv_row.get("Gender", "").strip()
        brand = csv_row.get("Brand", "").strip()
        image_file = csv_row.get("Image", "").strip()
        image_url = csv_row.get("ImageURL", "").strip()
        
        if not gender or not brand:
            raise ValueError("Gender and Brand are required in CSV")
        
        image_path = None
        if image_url:
            image_path = image_url
        elif image_file:
            if images_dir:
                image_path = os.path.join(images_dir, image_file)
                if not os.path.exists(image_path):
                    if os.path.exists(image_file):
                        image_path = image_file
                    else:
                        raise FileNotFoundError(f"Image not found: {image_file}")
            elif os.path.exists(image_file):
                image_path = image_file
            else:
                raise FileNotFoundError(f"Image not found: {image_file}")
        else:
            raise ValueError("Either Image or ImageURL must be provided in CSV")
        
        if not image_path:
            raise ValueError("No valid image path or URL found")
        
        image_analysis = self.image_analyzer.analyze_image(image_path)
        image_attributes = image_analysis.get('attributes', {})
        
        product_info = {
            'brand': brand,
            'gender': gender,
            'size': csv_row.get('Size', '').strip()
        }
        
        faceted_metadata = self.faceted_generator.generate_faceted_metadata(
            image_attributes, product_info, None
        )
        
        title = self.text_generator.generate_title(product_info, image_attributes)
        description = self.text_generator.generate_description(product_info, image_attributes)
        bullet_points = self.text_generator.generate_bullet_points(product_info, image_attributes)
        
        temp_metadata = {
            'faceted': faceted_metadata,
            'descriptive': {
                'title': title,
                'description': description
            }
        }
        confidence_scores = {}
        if self.confidence_scorer:
            confidence_scores = self.confidence_scorer.score_metadata(
                temp_metadata, image_attributes, self.vocabulary_manager, product_info
            )
        
        validation_results = {}
        if self.vocabulary_manager:
            faceted_data = faceted_metadata.get('faceted_metadata', {})
            flat_facets = faceted_data.get('flat_facets', {})
            hierarchical = faceted_data.get('hierarchical_facets', {})
            
            validation_results['gender'] = self.vocabulary_manager.validate('gender', faceted_metadata.get('gender', ''))
            validation_results['item_type'] = self.vocabulary_manager.validate('item_type', faceted_metadata.get('item_type', ''))
            validation_results['color'] = self.vocabulary_manager.validate('color', flat_facets.get('color', ''))
            validation_results['material'] = self.vocabulary_manager.validate('material', flat_facets.get('material', ''))
            
            facet1 = hierarchical.get('facet_1_item_type', {})
            if facet1:
                hierarchy_valid, hierarchy_error = self.vocabulary_manager.validate_hierarchy(
                    facet1.get('level_1', ''),
                    facet1.get('level_2', ''),
                    facet1.get('level_3', '')
                )
                validation_results['hierarchy'] = (hierarchy_valid, hierarchy_error if not hierarchy_valid else None, None)
        
        metadata = {
            'faceted': faceted_metadata,
            'descriptive': {
                'title': title,
                'short_description': description[:150] + '...' if len(description) > 150 else description,
                'long_description': description,
                'bullet_points': bullet_points
            },
            'confidence_scores': confidence_scores,
            'validation_results': validation_results,
            'status': 'pending_review',
            'source': {
                'product_id': csv_row.get("ProductId", ""),
                'image_file': image_file,
                'image_url': image_url
            }
        }
        
        return metadata
    
    def export_faceted_metadata(self, results, output_format='json'):
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
            
            with open(filepath, 'w', newline='', encoding='utf-8') as f:
                if not results:
                    return filepath
                
                fieldnames = [
                    'product_id', 'item_type', 'gender',
                    'facet1_level1', 'facet1_level2', 'facet1_level3', 'facet1_path',
                    'facet2_level1', 'facet2_level2', 'facet2_level3', 'facet2_path',
                    'color', 'material', 'pattern', 'size', 'brand',
                    'title', 'short_description', 'long_description', 'bullet_points'
                ]
                
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                
                for result in results:
                    if 'error' in result:
                        continue
                    
                    faceted = result.get('faceted', {}).get('faceted_metadata', {})
                    hierarchical = faceted.get('hierarchical_facets', {})
                    flat = faceted.get('flat_facets', {})
                    descriptive = result.get('descriptive', {})
                    
                    bullets = descriptive.get('bullet_points', [])
                    bullets_str = '; '.join(bullets) if isinstance(bullets, list) else str(bullets)
                    
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
                        'title': descriptive.get('title', ''),
                        'short_description': descriptive.get('short_description', ''),
                        'long_description': descriptive.get('long_description', ''),
                        'bullet_points': bullets_str
                    }
                    writer.writerow(row)
            
            return filepath
        
        else:
            raise ValueError(f"Unsupported format: {output_format}. Only 'json' and 'csv' are supported.")

