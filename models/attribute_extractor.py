"""
Attribute Extraction Module
Extracts structured technical attributes from images
"""


class AttributeExtractor:
    """Extracts technical attributes from fashion product images"""
    
    def __init__(self):
        """Initialize attribute extractor"""
        self.color_map = {
            "red": ["red", "crimson", "burgundy", "maroon"],
            "blue": ["blue", "navy", "cyan", "azure"],
            "black": ["black", "charcoal", "ebony"],
            "white": ["white", "ivory", "cream", "beige"],
            "green": ["green", "emerald", "olive", "lime"],
            "yellow": ["yellow", "gold", "amber"],
            "pink": ["pink", "rose", "magenta"],
            "purple": ["purple", "violet", "lavender"],
            "brown": ["brown", "tan", "khaki"],
            "gray": ["gray", "grey", "silver"]
        }
        
        self.material_map = {
            "cotton": ["cotton", "cotton blend"],
            "denim": ["denim", "jean"],
            "leather": ["leather", "genuine leather"],
            "silk": ["silk", "silk blend"],
            "polyester": ["polyester", "poly blend"],
            "wool": ["wool", "woolen"],
            "linen": ["linen"],
            "synthetic": ["synthetic", "polyester", "nylon"]
        }
        
        self.size_categories = ["XS", "S", "M", "L", "XL", "XXL"]
        self.pattern_types = ["solid", "striped", "floral", "geometric", "polka dot", "plaid", "abstract"]
        self.style_types = ["casual", "formal", "sporty", "vintage", "modern", "classic", "trendy"]
    
    def extract_attributes(self, image_attributes, product_info=None):
        """
        Extract structured technical attributes
        
        Args:
            image_attributes: Attributes from image analysis
            product_info: Optional product information
            
        Returns:
            dict: Structured attributes
        """
        attributes = {
            "color": self._extract_color(image_attributes),
            "material": self._extract_material(image_attributes),
            "size": self._extract_size(product_info),
            "pattern": self._extract_pattern(image_attributes),
            "style": self._extract_style(image_attributes),
            "sleeve_length": self._extract_sleeve_length(image_attributes),
            "neck_type": self._extract_neck_type(image_attributes),
            "fit_type": self._extract_fit_type(),
            "care_instructions": self._generate_care_instructions(image_attributes)
        }
        
        return attributes
    
    def _extract_color(self, image_attributes):
        """Extract color information"""
        color_data = image_attributes.get("color", [])
        if color_data:
            color_name = color_data[0].get("name", "").lower()
            # Map to standard color
            for standard_color, variants in self.color_map.items():
                if any(variant in color_name for variant in variants):
                    return {
                        "primary": standard_color.capitalize(),
                        "variants": [standard_color],
                        "confidence": color_data[0].get("confidence", 0.5)
                    }
            return {
                "primary": color_data[0].get("name", "Unknown").capitalize(),
                "variants": [color_data[0].get("name", "")],
                "confidence": color_data[0].get("confidence", 0.5)
            }
        return {"primary": "Unknown", "variants": [], "confidence": 0.0}
    
    def _extract_material(self, image_attributes):
        """Extract material information"""
        material_data = image_attributes.get("material", [])
        if material_data:
            material_name = material_data[0].get("name", "").lower()
            # Map to standard material
            for standard_material, variants in self.material_map.items():
                if any(variant in material_name for variant in variants):
                    return {
                        "primary": standard_material.capitalize(),
                        "composition": f"{standard_material.capitalize()} blend",
                        "confidence": material_data[0].get("confidence", 0.5)
                    }
            return {
                "primary": material_data[0].get("name", "Unknown").capitalize(),
                "composition": material_data[0].get("name", ""),
                "confidence": material_data[0].get("confidence", 0.5)
            }
        return {"primary": "Unknown", "composition": "Unknown", "confidence": 0.0}
    
    def _extract_size(self, product_info):
        """Extract size information"""
        if product_info and product_info.get("size"):
            size = product_info["size"].upper()
            if size in self.size_categories:
                return {
                    "available_sizes": [size],
                    "size_range": size,
                    "fit_guide": "Standard sizing"
                }
        return {
            "available_sizes": self.size_categories,
            "size_range": "XS-XXL",
            "fit_guide": "Standard sizing - refer to size chart"
        }
    
    def _extract_pattern(self, image_attributes):
        """Extract pattern information"""
        pattern_data = image_attributes.get("pattern", [])
        if pattern_data:
            pattern_name = pattern_data[0].get("name", "").lower()
            for pattern_type in self.pattern_types:
                if pattern_type in pattern_name:
                    return {
                        "type": pattern_type.capitalize(),
                        "description": f"{pattern_type.capitalize()} pattern design",
                        "confidence": pattern_data[0].get("confidence", 0.5)
                    }
            return {
                "type": pattern_data[0].get("name", "Solid").capitalize(),
                "description": pattern_data[0].get("name", ""),
                "confidence": pattern_data[0].get("confidence", 0.5)
            }
        return {"type": "Solid", "description": "Solid color", "confidence": 0.5}
    
    def _extract_style(self, image_attributes):
        """Extract style information"""
        style_data = image_attributes.get("style", [])
        if style_data:
            style_name = style_data[0].get("name", "").lower()
            for style_type in self.style_types:
                if style_type in style_name:
                    return {
                        "primary": style_type.capitalize(),
                        "secondary": ["Everyday", "Versatile"],
                        "confidence": style_data[0].get("confidence", 0.5)
                    }
        return {"primary": "Casual", "secondary": ["Everyday"], "confidence": 0.5}
    
    def _extract_sleeve_length(self, image_attributes):
        """Extract sleeve length"""
        style_data = image_attributes.get("style", [])
        for item in style_data:
            style_name = item.get("name", "").lower()
            if "long sleeve" in style_name:
                return "Long Sleeve"
            elif "short sleeve" in style_name:
                return "Short Sleeve"
            elif "sleeveless" in style_name:
                return "Sleeveless"
        return "Unknown"
    
    def _extract_neck_type(self, image_attributes):
        """Extract neck type"""
        style_data = image_attributes.get("style", [])
        for item in style_data:
            style_name = item.get("name", "").lower()
            if "v-neck" in style_name:
                return "V-Neck"
            elif "round neck" in style_name or "crew neck" in style_name:
                return "Round Neck"
        return "Standard"
    
    def _extract_fit_type(self):
        """Extract fit type (default)"""
        return {
            "type": "Regular Fit",
            "description": "Standard fit for comfort"
        }
    
    def _generate_care_instructions(self, image_attributes):
        """Generate care instructions based on material"""
        material_data = image_attributes.get("material", [])
        if material_data:
            material = material_data[0].get("name", "").lower()
            if "cotton" in material:
                return ["Machine wash cold", "Tumble dry low", "Iron if needed"]
            elif "denim" in material:
                return ["Machine wash cold", "Hang dry", "Do not bleach"]
            elif "silk" in material:
                return ["Dry clean only", "Do not wring", "Iron on low heat"]
            elif "leather" in material:
                return ["Professional cleaning recommended", "Keep away from water", "Condition regularly"]
        return ["Machine wash cold", "Tumble dry low", "Follow care label instructions"]

