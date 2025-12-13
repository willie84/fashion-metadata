"""
Create a test subset CSV with 10 images for validation testing
"""

import csv
import os

def create_test_subset(input_csv='fashion.csv', output_csv='test_subset_10.csv', num_rows=10):
    """Create a test subset CSV with specified number of rows"""
    
    if not os.path.exists(input_csv):
        print(f"Error: {input_csv} not found!")
        return
    
    with open(input_csv, 'r', encoding='utf-8') as f_in:
        reader = csv.DictReader(f_in)
        rows = list(reader)
        
        if len(rows) < num_rows:
            print(f"Warning: Only {len(rows)} rows available, using all rows")
            num_rows = len(rows)
        
        # Take first N rows
        test_rows = rows[:num_rows]
        
        # Write to output CSV
        with open(output_csv, 'w', encoding='utf-8', newline='') as f_out:
            if test_rows:
                fieldnames = test_rows[0].keys()
                writer = csv.DictWriter(f_out, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(test_rows)
        
        print(f"✅ Created {output_csv} with {len(test_rows)} rows")
        print(f"\nProducts in test subset:")
        for i, row in enumerate(test_rows, 1):
            product_id = row.get('ProductId', 'N/A')
            title = row.get('ProductTitle', 'N/A')
            image = row.get('Image', 'N/A')
            print(f"  {i}. ID: {product_id}, Title: {title[:50]}, Image: {image}")

if __name__ == "__main__":
    create_test_subset(num_rows=10)

