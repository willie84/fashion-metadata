"""
Product Classification Module
Classifies products into hierarchical categories
"""


class ProductClassifier:
    """Classifies fashion products into categories"""
    
    def __init__(self):
        """Initialize classifier with fashion category hierarchy"""
        self.category_hierarchy = {
            "Women's": {
                "Tops": ["Blouses", "T-Shirts", "Tank Tops", "Sweaters", "Hoodies"],
                "Bottoms": ["Jeans", "Pants", "Shorts", "Skirts"],
                "Dresses": ["Casual Dresses", "Formal Dresses", "Maxi Dresses"],
                "Outerwear": ["Jackets", "Coats", "Blazers", "Cardigans"],
                "Shoes": ["Sneakers", "Heels", "Boots", "Sandals", "Flats"],
                "Accessories": ["Handbags", "Jewelry", "Belts", "Hats", "Scarves"]
            },
            "Men's": {
                "Tops": ["Shirts", "T-Shirts", "Polo Shirts", "Sweaters", "Hoodies"],
                "Bottoms": ["Jeans", "Pants", "Shorts", "Chinos"],
                "Outerwear": ["Jackets", "Coats", "Blazers", "Vests"],
                "Shoes": ["Sneakers", "Dress Shoes", "Boots", "Sandals", "Loafers"],
                "Accessories": ["Watches", "Belts", "Hats", "Ties", "Wallets"]
            },
            "Unisex": {
                "Tops": ["T-Shirts", "Hoodies", "Sweaters"],
                "Bottoms": ["Jeans", "Pants", "Shorts"],
                "Shoes": ["Sneakers", "Boots", "Sandals"],
                "Accessories": ["Bags", "Hats", "Belts"]
            }
        }
    
    def classify(self, image_attributes, product_info=None):
        """
        Classify product into hierarchical categories
        
        Args:
            image_attributes: Attributes extracted from image
            product_info: Optional product information
            
        Returns:
            dict: Classification results with hierarchy
        """
        # Extract category hints from image analysis
        category_matches = image_attributes.get("category", [])
        top_category = category_matches[0].get("name", "").lower() if category_matches else ""
        
        # Determine gender category
        gender = self._determine_gender(top_category, product_info)
        
        # Determine main category
        main_category = self._determine_main_category(top_category, gender)
        
        # Determine subcategory
        subcategory = self._determine_subcategory(top_category, main_category, gender)
        
        # Build hierarchy
        hierarchy = {
            "gender": gender,
            "main_category": main_category,
            "subcategory": subcategory,
            "full_path": f"{gender} > {main_category} > {subcategory}"
        }
        
        # Generate tags
        tags = self._generate_tags(hierarchy, image_attributes)
        
        return {
            "hierarchy": hierarchy,
            "tags": tags,
            "product_type": subcategory
        }
    
    def _determine_gender(self, category_text, product_info):
        """Determine gender category"""
        category_text = category_text.lower()
        
        if "women" in category_text or "woman" in category_text:
            return "Women's"
        elif "men" in category_text or "man" in category_text:
            return "Men's"
        elif product_info and product_info.get("gender"):
            gender = product_info["gender"].lower()
            if "women" in gender or "woman" in gender:
                return "Women's"
            elif "men" in gender or "man" in gender:
                return "Men's"
        
        # Default based on category
        if any(word in category_text for word in ["dress", "skirt", "blouse", "heels"]):
            return "Women's"
        elif any(word in category_text for word in ["shirt", "polo", "tie"]):
            return "Men's"
        
        return "Unisex"
    
    def _determine_main_category(self, category_text, gender):
        """Determine main category"""
        category_text = category_text.lower()
        
        # Check for main categories
        if any(word in category_text for word in ["top", "shirt", "blouse", "sweater", "hoodie"]):
            return "Tops"
        elif any(word in category_text for word in ["jean", "pant", "short", "skirt"]):
            return "Bottoms"
        elif "dress" in category_text:
            return "Dresses"
        elif any(word in category_text for word in ["jacket", "coat", "blazer", "cardigan"]):
            return "Outerwear"
        elif any(word in category_text for word in ["shoe", "sneaker", "boot", "heel", "sandal"]):
            return "Shoes"
        elif any(word in category_text for word in ["bag", "handbag", "accessory", "jewelry", "belt", "hat"]):
            return "Accessories"
        
        return "Tops"  # Default
    
    def _determine_subcategory(self, category_text, main_category, gender):
        """Determine subcategory"""
        category_text = category_text.lower()
        subcategories = self.category_hierarchy.get(gender, {}).get(main_category, [])
        
        if not subcategories:
            return main_category
        
        # Try to match subcategory
        for subcat in subcategories:
            if subcat.lower() in category_text or category_text in subcat.lower():
                return subcat
        
        # Return first subcategory as default
        return subcategories[0] if subcategories else main_category
    
    def _generate_tags(self, hierarchy, image_attributes):
        """Generate searchable tags"""
        tags = set()
        
        # Add hierarchy tags
        tags.add(hierarchy["gender"])
        tags.add(hierarchy["main_category"])
        tags.add(hierarchy["subcategory"])
        
        # Add attribute tags
        for attr_type in ["color", "material", "pattern", "style"]:
            for item in image_attributes.get(attr_type, []):
                name = item.get("name", "")
                if name:
                    tags.add(name)
        
        # Add common fashion tags
        tags.update(["fashion", "clothing", "apparel", "style"])
        
        return list(tags)[:15]  # Return top 15 tags

