"""
Faceted Metadata Generator
Creates both flat and hierarchical metadata structures
"""

import json
import os


class FacetedMetadataGenerator:
    """Generates faceted metadata with hierarchical structures"""
    
    def __init__(self, vocabulary_path='vocabulary.json'):
        """Initialize faceted metadata generator"""
        self.vocabulary_path = vocabulary_path
        self.vocabulary = self._load_vocabulary()
        
        # Build hierarchical structure from vocabulary
        self.item_type_hierarchy = {}
        item_types = self.vocabulary.get('item_type', [])
        categories = self.vocabulary.get('categories', {})
        product_types = self.vocabulary.get('product_types', {})
        
        for item_type in item_types:
            self.item_type_hierarchy[item_type] = {}
            if item_type in categories:
                for category in categories[item_type]:
                    self.item_type_hierarchy[item_type][category] = []
                    if item_type in product_types and category in product_types[item_type]:
                        self.item_type_hierarchy[item_type][category] = product_types[item_type][category]
    
    def _load_vocabulary(self):
        """Load vocabulary from JSON file"""
        if os.path.exists(self.vocabulary_path):
            with open(self.vocabulary_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            # Return default if file doesn't exist
            return {
                'item_type': ['Apparel', 'Footwear'],
                'categories': {
                    'Apparel': ['Topwear', 'Bottomwear', 'Dress'],
                    'Footwear': ['Shoes', 'Sandals']
                },
                'product_types': {
                    'Apparel': {
                        'Topwear': ['Tops', 'Tshirts'],
                        'Bottomwear': ['Jeans', 'Pants']
                    }
                }
            }
        
    
    def generate_faceted_metadata(self, image_attributes, product_info=None, csv_data=None):
        """
        Generate faceted metadata with both flat and hierarchical structures
        
        Args:
            image_attributes: Attributes from image analysis
            product_info: Optional product information
            csv_data: Optional CSV row data
            
        Returns:
            dict: Faceted metadata structure
        """
        # Determine item type (Apparel or Footwear)
        item_type = self._determine_item_type(image_attributes, csv_data)
        
        # Determine gender
        gender = self._determine_gender(image_attributes, product_info, csv_data)
        
        # Build Hierarchical Facet 1: Item Type Hierarchy
        facet1 = self._build_item_type_hierarchy(item_type, image_attributes, csv_data)
        
        # Build Hierarchical Facet 2: Style/Usage Hierarchy
        facet2 = self._build_style_hierarchy(image_attributes, csv_data)
        
        # Build flat metadata
        flat_metadata = self._build_flat_metadata(image_attributes, product_info, csv_data, item_type, gender)
        
        return {
            "faceted_metadata": {
                "hierarchical_facets": {
                    "facet_1_item_type": facet1,
                    "facet_2_style_usage": facet2
                },
                "flat_facets": flat_metadata
            },
            "item_type": item_type,
            "gender": gender
        }
    
    def _determine_item_type(self, image_attributes, csv_data):
        """Determine if item is Apparel or Footwear"""
        if csv_data and csv_data.get("Category"):
            category = csv_data["Category"]
            if "Footwear" in category or "Shoe" in category:
                return "Footwear"
            return "Apparel"
        
        # From image analysis
        category_matches = image_attributes.get("category", [])
        for match in category_matches:
            name = match.get("name", "").lower()
            if any(word in name for word in ["shoe", "sneaker", "boot", "sandal", "footwear"]):
                return "Footwear"
        
        return "Apparel"
    
    def _determine_gender(self, image_attributes, product_info, csv_data):
        """Determine gender (Men, Women, Unisex)"""
        # From CSV
        if csv_data and csv_data.get("Gender"):
            gender = csv_data["Gender"]
            if "Girl" in gender or "Women" in gender or "Female" in gender:
                return "Women"
            elif "Boy" in gender or "Men" in gender or "Male" in gender:
                return "Men"
            return "Unisex"
        
        # From product info
        if product_info and product_info.get("gender"):
            gender = product_info["gender"]
            if "Women" in gender or "Girl" in gender:
                return "Women"
            elif "Men" in gender or "Boy" in gender:
                return "Men"
            return "Unisex"
        
        # From image
        category_matches = image_attributes.get("category", [])
        for match in category_matches:
            name = match.get("name", "").lower()
            if "women" in name or "woman" in name or "girl" in name:
                return "Women"
            elif "men" in name or "man" in name or "boy" in name:
                return "Men"
        
        return "Unisex"
    
    def _build_item_type_hierarchy(self, item_type, image_attributes, csv_data):
        """
        Build Hierarchical Facet 1: Item Type (3 levels)
        Level 1: Apparel/Footwear
        Level 2: Category (Topwear/Bottomwear/etc)
        Level 3: ProductType (Tops/Tshirts/etc)
        """
        hierarchy = self.item_type_hierarchy.get(item_type, {})
        
        # Determine level 2 (Category)
        level2 = None
        level3 = None
        
        if csv_data:
            # Use CSV data if available
            subcategory = csv_data.get("SubCategory", "")
            product_type = csv_data.get("ProductType", "")
            
            # Map CSV subcategory to hierarchy
            if subcategory in hierarchy:
                level2 = subcategory
                # Find level 3
                if product_type in hierarchy[subcategory]:
                    level3 = product_type
                elif hierarchy[subcategory]:
                    level3 = hierarchy[subcategory][0]  # Default to first
            else:
                # Try to match
                for key in hierarchy.keys():
                    if key.lower() in subcategory.lower() or subcategory.lower() in key.lower():
                        level2 = key
                        if product_type in hierarchy[key]:
                            level3 = product_type
                        elif hierarchy[key]:
                            level3 = hierarchy[key][0]
                        break
        else:
            # Use image analysis - try to match category names
            category_matches = image_attributes.get("category", [])
            
            # First, try direct matching with hierarchy keys
            for match in category_matches:
                name = match.get("name", "").lower()
                # Try to match to hierarchy keys
                for key in hierarchy.keys():
                    key_lower = key.lower()
                    # Check if category name contains hierarchy key or vice versa
                    if (key_lower in name or 
                        any(word in name for word in key_lower.split()) or
                        name in key_lower):
                        level2 = key
                        if hierarchy[key] and len(hierarchy[key]) > 0:
                            level3 = hierarchy[key][0]
                        else:
                            # If hierarchy[key] is empty, we'll set a default later
                            level3 = None
                        break
                if level2:
                    break
            
            # If still not found, try common keyword mappings
            if not level2:
                for match in category_matches:
                    name = match.get("name", "").lower()
                    # Topwear keywords (check most specific first)
                    if any(word in name for word in ["tshirt", "t-shirt", "t shirt"]):
                        if "Topwear" in hierarchy:
                            level2 = "Topwear"
                            # Prefer Tshirts or Tops
                            for pt in hierarchy["Topwear"]:
                                if "tshirt" in pt.lower() or "t-shirt" in pt.lower():
                                    level3 = pt
                                    break
                            if not level3:
                                for pt in hierarchy["Topwear"]:
                                    if "top" in pt.lower():
                                        level3 = pt
                                        break
                            if not level3:
                                level3 = hierarchy["Topwear"][0] if hierarchy["Topwear"] else None
                            break
                    elif any(word in name for word in ["shirt", "blouse", "sweater", "hoodie", "sweatshirt", "polo"]):
                        if "Topwear" in hierarchy:
                            level2 = "Topwear"
                            # Try to match specific product type
                            for pt in hierarchy["Topwear"]:
                                if any(word in name for word in pt.lower().split()):
                                    level3 = pt
                                    break
                            if not level3:
                                # Default to Shirts or Tops
                                for pt in hierarchy["Topwear"]:
                                    if "shirt" in pt.lower():
                                        level3 = pt
                                        break
                                if not level3:
                                    level3 = hierarchy["Topwear"][0] if hierarchy["Topwear"] else None
                            break
                    elif any(word in name for word in ["top", "blazer", "jacket", "waistcoat", "kurta"]):
                        if "Topwear" in hierarchy:
                            level2 = "Topwear"
                            for pt in hierarchy["Topwear"]:
                                if any(word in name for word in pt.lower().split()):
                                    level3 = pt
                                    break
                            if not level3:
                                level3 = hierarchy["Topwear"][0] if hierarchy["Topwear"] else None
                            break
                    # Bottomwear keywords (check most specific first)
                    elif any(word in name for word in ["cargo shorts", "cargo short"]):
                        if "Bottomwear" in hierarchy:
                            level2 = "Bottomwear"
                            for pt in hierarchy["Bottomwear"]:
                                if "short" in pt.lower():
                                    level3 = pt
                                    break
                            if not level3:
                                level3 = hierarchy["Bottomwear"][0] if hierarchy["Bottomwear"] else None
                            break
                    elif any(word in name for word in ["short", "shorts"]):
                        if "Bottomwear" in hierarchy:
                            level2 = "Bottomwear"
                            for pt in hierarchy["Bottomwear"]:
                                if "short" in pt.lower():
                                    level3 = pt
                                    break
                            if not level3:
                                level3 = hierarchy["Bottomwear"][0] if hierarchy["Bottomwear"] else None
                            break
                    elif any(word in name for word in ["jean", "jeans"]):
                        if "Bottomwear" in hierarchy:
                            level2 = "Bottomwear"
                            for pt in hierarchy["Bottomwear"]:
                                if "jean" in pt.lower():
                                    level3 = pt
                                    break
                            if not level3:
                                level3 = hierarchy["Bottomwear"][0] if hierarchy["Bottomwear"] else None
                            break
                    elif any(word in name for word in ["pant", "pants", "trouser", "trousers", "chino", "chinos"]):
                        if "Bottomwear" in hierarchy:
                            level2 = "Bottomwear"
                            for pt in hierarchy["Bottomwear"]:
                                if any(word in pt.lower() for word in ["pant", "trouser"]):
                                    level3 = pt
                                    break
                            if not level3:
                                level3 = hierarchy["Bottomwear"][0] if hierarchy["Bottomwear"] else None
                            break
                    elif any(word in name for word in ["skirt", "legging", "leggings", "capri", "churidar", "salwar"]):
                        if "Bottomwear" in hierarchy:
                            level2 = "Bottomwear"
                            for pt in hierarchy["Bottomwear"]:
                                if any(word in name for word in pt.lower().split()):
                                    level3 = pt
                                    break
                            if not level3:
                                level3 = hierarchy["Bottomwear"][0] if hierarchy["Bottomwear"] else None
                            break
                    # Dress keywords
                    elif "dress" in name or "lehenga" in name:
                        if "Dress" in hierarchy:
                            level2 = "Dress"
                            level3 = hierarchy["Dress"][0] if hierarchy["Dress"] else None
                            break
                    # Footwear keywords
                    elif any(word in name for word in ["shoe", "sneaker", "boot", "sandal", "flip", "flop"]):
                        if item_type == "Footwear":
                            if "Shoes" in hierarchy:
                                level2 = "Shoes"
                                for pt in hierarchy["Shoes"]:
                                    if any(word in name for word in pt.lower().split()):
                                        level3 = pt
                                        break
                                if not level3:
                                    level3 = hierarchy["Shoes"][0] if hierarchy["Shoes"] else None
                            elif "Sandal" in hierarchy:
                                level2 = "Sandal"
                                level3 = hierarchy["Sandal"][0] if hierarchy["Sandal"] else None
                            elif "Flip Flops" in hierarchy:
                                level2 = "Flip Flops"
                                level3 = hierarchy["Flip Flops"][0] if hierarchy["Flip Flops"] else None
                        break
                    # Innerwear keywords
                    elif any(word in name for word in ["vest", "innerwear", "underwear"]):
                        if "Innerwear" in hierarchy:
                            level2 = "Innerwear"
                            level3 = hierarchy["Innerwear"][0] if hierarchy["Innerwear"] else None
                            break
                    # Apparel Set keywords
                    elif any(word in name for word in ["set", "kurta set"]):
                        if "Apparel Set" in hierarchy:
                            level2 = "Apparel Set"
                            level3 = hierarchy["Apparel Set"][0] if hierarchy["Apparel Set"] else None
                            break
        
        # Defaults if not found - use first available option
        if not level2 and hierarchy:
            level2 = list(hierarchy.keys())[0]
        
        # Ensure level3 is always set
        if not level3:
            if level2 and hierarchy.get(level2) and len(hierarchy[level2]) > 0:
                level3 = hierarchy[level2][0]
            else:
                # If no product types available, use a generic default based on level2
                if level2 == "Topwear":
                    level3 = "Tops"
                elif level2 == "Bottomwear":
                    level3 = "Pants"
                elif level2 == "Dress":
                    level3 = "Dresses"
                elif level2 == "Shoes":
                    level3 = "Casual Shoes"
                else:
                    level3 = "Unknown"
        
        return {
            "level_1": item_type,
            "level_2": level2 or "Unknown",
            "level_3": level3 or "Unknown",
            "full_path": f"{item_type} > {level2 or 'Unknown'} > {level3 or 'Unknown'}",
            "hierarchy_tree": hierarchy
        }
    
    def _build_style_hierarchy(self, image_attributes, csv_data):
        """
        Build Hierarchical Facet 2: Style/Usage (3 levels)
        Level 1: Casual/Formal/Sporty/Ethnic
        Level 2: Sub-style (Everyday/Streetwear/etc)
        Level 3: Specific style (Basic/Comfort/etc)
        """
        # Get style hierarchy from vocabulary or use default
        style_hierarchy = self.vocabulary.get('style_hierarchy', self._get_default_style_hierarchy())
        
        # Determine level 1 (Usage/Style)
        level1 = None
        
        if csv_data and csv_data.get("Usage"):
            usage = csv_data["Usage"]
            # Check exact match first
            if usage in style_hierarchy:
                level1 = usage
            # Check partial matches
            elif "Casual" in usage or "Smart Casual" in usage:
                level1 = "Casual"
            elif "Formal" in usage:
                level1 = "Formal"
            elif "Sport" in usage or "Athletic" in usage or "Sports" in usage:
                level1 = "Sporty"
            elif "Ethnic" in usage:
                level1 = "Ethnic"
            else:
                # Try to find closest match
                for key in style_hierarchy.keys():
                    if key.lower() in usage.lower() or usage.lower() in key.lower():
                        level1 = key
                        break
        
        # Default to Casual if not found
        if not level1:
            level1 = "Casual"
        
        hierarchy = style_hierarchy.get(level1, {})
        
        # Determine level 2 and 3
        level2 = None
        level3 = None
        
        if hierarchy and len(hierarchy) > 0:
            # Default to first subcategory
            level2 = list(hierarchy.keys())[0]
            if hierarchy[level2] and len(hierarchy[level2]) > 0:
                level3 = hierarchy[level2][0]
            else:
                # If level2 has no options, use a default
                if level1 == "Casual":
                    level3 = "Basic"
                elif level1 == "Formal":
                    level3 = "Professional"
                elif level1 == "Sporty":
                    level3 = "Performance"
                elif level1 == "Ethnic":
                    level3 = "Classic"
                else:
                    level3 = "Basic"
        else:
            # If no hierarchy for this level1, set defaults
            if level1 == "Casual":
                level2 = "Everyday"
                level3 = "Basic"
            elif level1 == "Formal":
                level2 = "Business"
                level3 = "Professional"
            elif level1 == "Sporty":
                level2 = "Athletic"
                level3 = "Performance"
            elif level1 == "Ethnic":
                level2 = "Traditional"
                level3 = "Classic"
            else:
                level2 = "Everyday"
                level3 = "Basic"
        
        return {
            "level_1": level1,
            "level_2": level2 or "Unknown",
            "level_3": level3 or "Unknown",
            "full_path": f"{level1} > {level2 or 'Unknown'} > {level3 or 'Unknown'}",
            "hierarchy_tree": hierarchy
        }
    
    def _get_default_style_hierarchy(self):
        """Get default style hierarchy if not in vocabulary"""
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
    
    def _build_flat_metadata(self, image_attributes, product_info, csv_data, item_type, gender):
        """Build flat metadata facets"""
        flat = {
            "color": self._extract_flat_value("color", image_attributes, csv_data),
            "material": self._extract_flat_value("material", image_attributes, csv_data),
            "pattern": self._extract_flat_value("pattern", image_attributes, csv_data),
            "size": self._extract_flat_value("size", product_info, csv_data),
            "brand": self._extract_flat_value("brand", product_info, csv_data),
            "product_id": csv_data.get("ProductId", "") if csv_data else "",
            "product_title": csv_data.get("ProductTitle", "") if csv_data else "",
            "image_url": csv_data.get("ImageURL", "") if csv_data else "",
            "image_file": csv_data.get("Image", "") if csv_data else ""
        }
        
        # Add all attributes from image analysis
        for attr_type in ["color", "material", "pattern", "style"]:
            attr_list = image_attributes.get(attr_type, [])
            if attr_list:
                flat[f"{attr_type}_details"] = attr_list
        
        return flat
    
    def _extract_flat_value(self, key, source1, source2):
        """Extract value from multiple sources"""
        # Try source1 first (image_attributes)
        if isinstance(source1, dict):
            if key in source1:
                value = source1[key]
                # Handle list format from Claude (e.g., [{"name": "White", "confidence": 0.9}])
                if isinstance(value, list) and len(value) > 0:
                    # Get the first item's name
                    if isinstance(value[0], dict) and "name" in value[0]:
                        return value[0]["name"]
                    return value[0] if value[0] else None
                # Handle dict format
                elif isinstance(value, dict):
                    if "primary" in value:
                        return value["primary"]
                    if "name" in value:
                        return value["name"]
                    return value
                # Handle string format
                elif isinstance(value, str):
                    return value
        
        # Try source2 (CSV data)
        if source2 and isinstance(source2, dict):
            # Map keys
            key_map = {
                "color": "Colour",
                "material": "Material",
                "pattern": "Pattern",
                "size": "Size",
                "brand": "Brand"
            }
            csv_key = key_map.get(key, key.capitalize())
            if csv_key in source2:
                return source2[csv_key]
        
        return "Unknown"

