from typing import Dict, Optional
from models.vocabulary_manager import VocabularyManager


class FacetedMetadataGenerator:
    def __init__(self, vocabulary_manager: VocabularyManager = None):
        if vocabulary_manager is None:
            vocabulary_manager = VocabularyManager()
        self.vocab_manager = vocabulary_manager
        self.item_type_hierarchy = self.vocab_manager.get_item_type_hierarchy()
        
    def generate_faceted_metadata(self, image_attributes, product_info=None, csv_data=None):
        item_type = self._determine_item_type(image_attributes, csv_data)
        gender = self._determine_gender(image_attributes, product_info, csv_data)
        facet1 = self._build_item_type_hierarchy(item_type, image_attributes, csv_data)
        facet2 = self._build_style_hierarchy(image_attributes, csv_data)
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
        if csv_data and csv_data.get("Category"):
            category = csv_data["Category"]
            if "Footwear" in category or "Shoe" in category:
                return "Footwear"
            return "Apparel"
        
        category_matches = image_attributes.get("category", [])
        for match in category_matches:
            name = match.get("name", "").lower()
            if any(word in name for word in ["shoe", "sneaker", "boot", "sandal", "footwear"]):
                return "Footwear"
        
        return "Apparel"
    
    def _determine_gender(self, image_attributes, product_info, csv_data):
        if csv_data and csv_data.get("Gender"):
            gender = csv_data["Gender"]
            if "Girl" in gender or "Women" in gender or "Female" in gender:
                return "Women"
            elif "Boy" in gender or "Men" in gender or "Male" in gender:
                return "Men"
                return "Unisex"
        
        if product_info and product_info.get("gender"):
            gender = product_info["gender"]
            if "Women" in gender or "Girl" in gender:
                return "Women"
            elif "Men" in gender or "Boy" in gender:
                return "Men"
                return "Unisex"
        
        category_matches = image_attributes.get("category", [])
        for match in category_matches:
            name = match.get("name", "").lower()
            if "women" in name or "woman" in name or "girl" in name:
                return "Women"
            elif "men" in name or "man" in name or "boy" in name:
                return "Men"
        
        return "Unisex"
    
    def _build_item_type_hierarchy(self, item_type, image_attributes, csv_data):
        hierarchy = self.item_type_hierarchy.get(item_type, {})
        level2 = None
        level3 = None
        
        if csv_data:
            subcategory = csv_data.get("SubCategory", "")
            product_type = csv_data.get("ProductType", "")
            
            if subcategory in hierarchy:
                level2 = subcategory
                if product_type in hierarchy[subcategory]:
                    level3 = product_type
                elif hierarchy[subcategory]:
                    level3 = hierarchy[subcategory][0]
            else:
                for key in hierarchy.keys():
                    if key.lower() in subcategory.lower() or subcategory.lower() in key.lower():
                        level2 = key
                        if product_type in hierarchy[key]:
                            level3 = product_type
                        elif hierarchy[key]:
                            level3 = hierarchy[key][0]
                        break
        else:
            category_matches = image_attributes.get("category", [])
            
            for match in category_matches:
                name = match.get("name", "").lower()
                for key in hierarchy.keys():
                    key_lower = key.lower()
                    if (key_lower in name or 
                        any(word in name for word in key_lower.split()) or
                        name in key_lower):
                        level2 = key
                        if hierarchy[key] and len(hierarchy[key]) > 0:
                            level3 = hierarchy[key][0]
                        else:
                            level3 = None
                        break
                if level2:
                    break
            
            if not level2:
                category_mappings = self.vocab_manager.get_category_keyword_mappings()
                for match in category_matches:
                    name = match.get("name", "").lower()
                    for category_key, keywords in category_mappings.items():
                        if any(keyword in name for keyword in keywords):
                            mapped_category = self._map_category_key_to_hierarchy(category_key, item_type, hierarchy)
                            if mapped_category:
                                level2 = mapped_category
                                if hierarchy.get(level2):
                                    for pt in hierarchy[level2]:
                                        if any(word in name for word in pt.lower().split()) or any(word in category_key for word in pt.lower().split()):
                                            level3 = pt
                                            break
                                    if not level3 and hierarchy[level2]:
                                        level3 = hierarchy[level2][0]
                                break
                    if level2:
                        break
        
        if not level2 and hierarchy:
            level2 = list(hierarchy.keys())[0]
        
        if not level3:
            if level2 and hierarchy.get(level2) and len(hierarchy[level2]) > 0:
                level3 = hierarchy[level2][0]
            else:
                level3 = "Unknown"
        
        return {
            "level_1": item_type,
            "level_2": level2 or "Unknown",
            "level_3": level3 or "Unknown",
            "full_path": f"{item_type} > {level2 or 'Unknown'} > {level3 or 'Unknown'}",
            "hierarchy_tree": hierarchy
        }
    
    def _map_category_key_to_hierarchy(self, category_key: str, item_type: str, hierarchy: Dict) -> str:
        categories = self.vocab_manager.vocabulary.get('categories', {}).get(item_type, [])
        category_mappings = self.vocab_manager.get_category_keyword_mappings()
        
        if category_key in category_mappings:
            for cat in categories:
                if cat in hierarchy:
                    product_types = hierarchy[cat]
                    for pt in product_types:
                        if category_key in pt.lower() or any(word in pt.lower() for word in category_key.split()):
                            return cat
                    if category_key in cat.lower():
                        return cat
        
        for cat in categories:
            if cat.lower() in category_key or category_key in cat.lower():
                if cat in hierarchy:
                    return cat
        
        return None
    
    def _build_style_hierarchy(self, image_attributes, csv_data):
        style_hierarchy = self.vocab_manager.get_style_hierarchy()
        level1 = None
        
        if csv_data and csv_data.get("Usage"):
            usage = csv_data["Usage"]
            if usage in style_hierarchy:
                level1 = usage
            elif "Casual" in usage or "Smart Casual" in usage:
                level1 = "Casual"
            elif "Formal" in usage:
                level1 = "Formal"
            elif "Sport" in usage or "Athletic" in usage or "Sports" in usage:
                level1 = "Sporty"
            elif "Ethnic" in usage:
                level1 = "Ethnic"
            else:
                for key in style_hierarchy.keys():
                    if key.lower() in usage.lower() or usage.lower() in key.lower():
                        level1 = key
                        break
        
        if not level1:
            level1 = "Casual"
        
        hierarchy = style_hierarchy.get(level1, {})
        level2 = None
        level3 = None
        
        if hierarchy and len(hierarchy) > 0:
            level2 = list(hierarchy.keys())[0]
            if hierarchy[level2] and len(hierarchy[level2]) > 0:
                level3 = hierarchy[level2][0]
            else:
                level3 = "Unknown"
        else:
            default_hierarchy = self.vocab_manager._get_default_style_hierarchy()
            if level1 in default_hierarchy and default_hierarchy[level1]:
                level2 = list(default_hierarchy[level1].keys())[0]
                if default_hierarchy[level1][level2] and len(default_hierarchy[level1][level2]) > 0:
                    level3 = default_hierarchy[level1][level2][0]
                else:
                    level3 = "Unknown"
            else:
                level2 = "Unknown"
                level3 = "Unknown"
        
        return {
            "level_1": level1,
            "level_2": level2 or "Unknown",
            "level_3": level3 or "Unknown",
            "full_path": f"{level1} > {level2 or 'Unknown'} > {level3 or 'Unknown'}",
            "hierarchy_tree": hierarchy
        }
    
    def _build_flat_metadata(self, image_attributes, product_info, csv_data, item_type, gender):
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
        
        for attr_type in ["color", "material", "pattern", "style"]:
            attr_list = image_attributes.get(attr_type, [])
            if attr_list:
                flat[f"{attr_type}_details"] = attr_list
        
        return flat
    
    def _extract_flat_value(self, key, source1, source2):
        if isinstance(source1, dict):
            if key in source1:
                value = source1[key]
                if isinstance(value, list) and len(value) > 0:
                    if isinstance(value[0], dict) and "name" in value[0]:
                        return value[0]["name"]
                    return value[0] if value[0] else None
                elif isinstance(value, dict):
                    if "primary" in value:
                        return value["primary"]
                    if "name" in value:
                        return value["name"]
                    return value
                elif isinstance(value, str):
                    return value
        
        if source2 and isinstance(source2, dict):
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

