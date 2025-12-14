import os
import csv
import json
import pandas as pd
from datetime import datetime
from typing import Dict, List, Optional


class AIAccuracyEvaluator:
    def __init__(self):
        pass
    
    def evaluate_batch(self, gold_standard_csv: str, ai_csv: str, 
                       limit: Optional[int] = None) -> Dict:
        print(f"\n📊 Loading CSVs...")
        print(f"  Gold Standard: {gold_standard_csv}")
        print(f"  AI Generated: {ai_csv}")
        
        gold_data = self._load_csv(gold_standard_csv)
        ai_data = self._load_csv(ai_csv)
        
        print(f"  Gold Standard rows: {len(gold_data)}")
        print(f"  AI Generated rows: {len(ai_data)}")
        
        if limit:
            gold_data = gold_data[:limit]
            ai_data = ai_data[:limit]
        
        print(f"\n🔍 Comparing {len(gold_data)} products...")
        
        results = []
        errors = []
        missing_products = []
        
        gold_dict = {self._get_product_id(row): row for row in gold_data}
        ai_dict = {self._get_product_id(row): row for row in ai_data}
        
        for product_id in gold_dict.keys():
            if product_id not in ai_dict:
                missing_products.append(product_id)
                continue
            
            try:
                comparison = self._compare_rows(gold_dict[product_id], ai_dict[product_id])
                comparison['product_id'] = product_id
                results.append(comparison)
            except Exception as e:
                error_info = {
                    'product_id': product_id,
                    'error': str(e)
                }
                errors.append(error_info)
                print(f"  ❌ Error processing {product_id}: {str(e)}")
        
        if missing_products:
            print(f"\n⚠️  Warning: {len(missing_products)} products in gold standard not found in AI CSV")
        
        metrics = self._calculate_metrics(results)
        
        return {
            'summary': metrics,
            'detailed_results': results,
            'errors': errors,
            'missing_products': missing_products,
            'total_processed': len(results),
            'total_errors': len(errors),
            'timestamp': datetime.now().isoformat()
        }
    
    def _load_csv(self, csv_path: str) -> List[Dict]:
        data = []
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                data.append(row)
        return data
    
    def _compare_rows(self, gold: Dict, ai: Dict) -> Dict:
        comparison = {}
        
        gold_item_type = self._get_value(gold, ['Item-type', 'ItemType', 'Category', 'item_type', 'Item Type'])
        gold_category = self._get_value(gold, ['Category', 'SubCategory', 'Itemcategory', 'ItemCategory', 'Item-category'])
        gold_product_type = self._get_value(gold, ['ProductType', 'product_type', 'Product Type', 'Product-Type'])
        gold_color = self._get_value(gold, ['Colour', 'Color', 'colour', 'color'])
        gold_material = self._get_value(gold, ['Material', 'material'])
        gold_pattern = self._get_value(gold, ['Pattern', 'pattern'])
        gold_usage = self._get_value(gold, ['Usage', 'usage', 'Style', 'style'])
        gold_substyle = self._get_value(gold, ['substyle', 'SubStyle', 'Sub-Style', 'Substyle', 'Sub Style'])
        gold_specific_style = self._get_value(gold, ['specific-style', 'SpecificStyle', 'specific_style', 'Specific Style', 'SpecificStyle'])
        
        ai_item_type = self._get_value(ai, ['Item-type', 'ItemType', 'item_type'])
        ai_category = self._get_value(ai, ['Itemcategory', 'ItemCategory', 'Category', 'category'])
        ai_product_type = self._get_value(ai, ['ProductType', 'product_type'])
        ai_color = self._get_value(ai, ['Colour', 'Color', 'color'])
        ai_material = self._get_value(ai, ['Material', 'material'])
        ai_pattern = self._get_value(ai, ['Pattern', 'pattern'])
        ai_usage = self._get_value(ai, ['Usage', 'usage'])
        ai_substyle = self._get_value(ai, ['substyle', 'Sub-Style', 'SubStyle', 'Substyle'])
        ai_specific_style = self._get_value(ai, ['specific-style', 'Specific Style', 'SpecificStyle', 'specific_style'])
        
        comparison['item_type'] = {
            'gold': gold_item_type,
            'ai': ai_item_type,
            'match': self._normalize_compare(gold_item_type, ai_item_type)
        }
        
        comparison['facet1_level1'] = {
            'gold': gold_item_type,
            'ai': ai_item_type,
            'match': self._normalize_compare(gold_item_type, ai_item_type)
        }
        
        comparison['facet1_level2'] = {
            'gold': gold_category,
            'ai': ai_category,
            'match': self._normalize_compare(gold_category, ai_category)
        }
        
        comparison['facet1_level3'] = {
            'gold': gold_product_type,
            'ai': ai_product_type,
            'match': self._normalize_compare(gold_product_type, ai_product_type)
        }
        
        comparison['facet2_level1'] = {
            'gold': gold_usage,
            'ai': ai_usage,
            'match': self._normalize_compare(gold_usage, ai_usage)
        }
        
        comparison['facet2_level2'] = {
            'gold': gold_substyle,
            'ai': ai_substyle,
            'match': self._normalize_compare(gold_substyle, ai_substyle)
        }
        
        comparison['facet2_level3'] = {
            'gold': gold_specific_style,
            'ai': ai_specific_style,
            'match': self._normalize_compare(gold_specific_style, ai_specific_style)
        }
        
        comparison['color'] = {
            'gold': gold_color,
            'ai': ai_color,
            'match': self._normalize_compare(gold_color, ai_color)
        }
        
        comparison['material'] = {
            'gold': gold_material,
            'ai': ai_material,
            'match': self._normalize_compare(gold_material, ai_material)
        }
        
        comparison['pattern'] = {
            'gold': gold_pattern,
            'ai': ai_pattern,
            'match': self._normalize_compare(gold_pattern, ai_pattern)
        }
        
        return comparison
    
    def _get_value(self, row: Dict, possible_keys: List[str]) -> str:
        for key in possible_keys:
            if key in row:
                value = row[key]
                if isinstance(value, str):
                    value = value.strip()
                else:
                    value = str(value).strip() if value else ''
                if value and value.lower() not in ['nan', 'none', 'null', '']:
                    return value
        return ''
    
    def _get_product_id(self, row: Dict) -> str:
        return self._get_value(row, ['ProductId', 'product_id', 'Product ID', 'product_id'])
    
    def _normalize_compare(self, val1: str, val2: str) -> bool:
        if not val1 or not val2:
            return False
        return val1.lower().strip() == val2.lower().strip()
    
    def _calculate_metrics(self, results: List[Dict]) -> Dict:
        if not results:
            return {}
        
        metrics = {}
        
        attributes = [
            'item_type', 'facet1_level1', 'facet1_level2', 'facet1_level3',
            'facet2_level1', 'facet2_level2', 'facet2_level3',
            'color', 'material', 'pattern'
        ]
        
        for attr in attributes:
            valid_results = [r for r in results if r.get(attr, {}).get('gold', '')]
            if not valid_results:
                continue
            
            matches = sum(1 for r in valid_results if r.get(attr, {}).get('match', False))
            total = len(valid_results)
            accuracy = (matches / total * 100) if total > 0 else 0
            
            metrics[attr] = {
                'accuracy': accuracy,
                'matches': matches,
                'total': total
            }
        
        if metrics:
            overall_accuracy = sum(m['accuracy'] for m in metrics.values()) / len(metrics)
            
            metrics['overall'] = {
                'accuracy': overall_accuracy
            }
        
        return metrics
    
    def export_results(self, results: Dict, output_dir: str = 'evaluation_results'):
        """Export evaluation results to files"""
        os.makedirs(output_dir, exist_ok=True)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Export summary JSON
        summary_path = os.path.join(output_dir, f'evaluation_summary_{timestamp}.json')
        with open(summary_path, 'w', encoding='utf-8') as f:
            json.dump(results['summary'], f, indent=2, ensure_ascii=False)
        print(f"\n✅ Summary exported: {summary_path}")
        
        # Export detailed results CSV
        detailed_path = os.path.join(output_dir, f'evaluation_detailed_{timestamp}.csv')
        self._export_detailed_csv(results['detailed_results'], detailed_path)
        print(f"✅ Detailed results exported: {detailed_path}")
        
        # Export errors CSV
        if results['errors']:
            errors_path = os.path.join(output_dir, f'evaluation_errors_{timestamp}.csv')
            self._export_errors_csv(results['errors'], errors_path)
            print(f"✅ Errors exported: {errors_path}")
        
        # Print summary
        self._print_summary(results['summary'])
        
        return {
            'summary': summary_path,
            'detailed': detailed_path,
            'errors': errors_path if results['errors'] else None
        }
    
    def _export_detailed_csv(self, results: List[Dict], filepath: str):
        rows = []
        for r in results:
            row = {
                'ProductId': r.get('product_id', ''),
            }
            
            for attr in ['item_type', 'facet1_level1', 'facet1_level2', 'facet1_level3',
                        'facet2_level1', 'facet2_level2', 'facet2_level3',
                        'color', 'material', 'pattern']:
                comp = r.get(attr, {})
                row[f'{attr}_gold'] = comp.get('gold', '')
                row[f'{attr}_ai'] = comp.get('ai', '')
                row[f'{attr}_match'] = 'YES' if comp.get('match') else 'NO'
            
            rows.append(row)
        
        df = pd.DataFrame(rows)
        df.to_csv(filepath, index=False)
    
    def _export_errors_csv(self, errors: List[Dict], filepath: str):
        df = pd.DataFrame(errors)
        df.to_csv(filepath, index=False)
    
    def _print_summary(self, metrics: Dict):
        print("\n" + "="*60)
        print("📊 AI ACCURACY EVALUATION SUMMARY")
        print("="*60)
        
        print("\nAttribute Accuracy:")
        for attr, m in metrics.items():
            if attr != 'overall':
                print(f"  {attr:20s}: {m['accuracy']:5.1f}% ({m['matches']}/{m['total']})")
        
        if 'overall' in metrics:
            print(f"\n{'Overall Accuracy':20s}: {metrics['overall']['accuracy']:5.1f}%")
        
        print("="*60)


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Evaluate AI metadata generation accuracy')
    parser.add_argument('gold_standard_csv', help='Path to gold standard CSV file')
    parser.add_argument('ai_csv', help='Path to AI-generated CSV file')
    parser.add_argument('--limit', type=int, help='Limit number of products to process (for testing)')
    parser.add_argument('--output-dir', default='evaluation_results', help='Output directory for results')
    
    args = parser.parse_args()
    
    evaluator = AIAccuracyEvaluator()
    
    results = evaluator.evaluate_batch(
        args.gold_standard_csv,
        args.ai_csv,
        limit=args.limit
    )
    
    evaluator.export_results(results, output_dir=args.output_dir)
    
    print("\n✅ Evaluation complete!")


if __name__ == "__main__":
    main()

