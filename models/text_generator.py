"""
Text Generation Module
Uses free Hugging Face models (GPT-2 or T5) for generating product descriptions
"""

from transformers import GPT2LMHeadModel, GPT2Tokenizer, pipeline
import torch


class TextGenerator:
    """Generates product descriptions using GPT-2 or T5"""
    
    def __init__(self, model_name="gpt2"):
        """
        Initialize text generation model
        
        Args:
            model_name: Hugging Face model name (default: "gpt2")
        """
        # Model loading (GPT-2 for text generation)
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        
        try:
            # Try GPT-2 first (smaller, faster)
            self.tokenizer = GPT2Tokenizer.from_pretrained(model_name)
            self.model = GPT2LMHeadModel.from_pretrained(model_name)
            self.model.to(self.device)
            self.model.eval()
            
            # Set padding token
            if self.tokenizer.pad_token is None:
                self.tokenizer.pad_token = self.tokenizer.eos_token
            
            self.generator = pipeline(
                "text-generation",
                model=self.model,
                tokenizer=self.tokenizer,
                device=0 if self.device == "cuda" else -1
            )
            pass  # Model loaded successfully
        except Exception as e:
            raise RuntimeError(f"Failed to load text generation model: {e}")
            self.generator = None
    
    def generate_title(self, product_info, image_attributes):
        """
        Generate SEO-optimized product title
        
        Args:
            product_info: Dict with product info (name, brand, etc.)
            image_attributes: Attributes extracted from image
            
        Returns:
            str: Generated product title
        """
        if not self.generator:
            return self._fallback_title(product_info, image_attributes)
        
        # Build prompt
        category_list = image_attributes.get("category", [])
        category = category_list[0].get("name", "clothing") if category_list else "clothing"
        
        color_list = image_attributes.get("color", [])
        color = color_list[0].get("name", "") if color_list else ""
        
        brand = product_info.get("brand", "")
        
        prompt = f"Product title for {brand} {color} {category}:"
        
        try:
            # Use fallback for better quality (GPT-2 base model not great for product titles)
            # This avoids vocabulary issues with terms like "tshirt", "shirt", "crew neck", etc.
            return self._fallback_title(product_info, image_attributes)
        except Exception as e:
            # Return fallback title
            return self._fallback_title(product_info, image_attributes)
    
    def generate_description(self, product_info, image_attributes):
        """
        Generate product description
        
        Args:
            product_info: Dict with product info
            image_attributes: Attributes extracted from image
            
        Returns:
            str: Generated product description
        """
        if not self.generator:
            return self._fallback_description(product_info, image_attributes)
        
        # Build prompt
        category_list = image_attributes.get("category", [])
        category = category_list[0].get("name", "clothing item") if category_list else "clothing item"
        
        color_list = image_attributes.get("color", [])
        color = color_list[0].get("name", "") if color_list else ""
        
        material_list = image_attributes.get("material", [])
        material = material_list[0].get("name", "") if material_list else ""
        
        style_list = image_attributes.get("style", [])
        style = style_list[0].get("name", "") if style_list else ""
        
        prompt = f"Product description for a {color} {material} {category} with {style} features:"
        
        try:
            # Use fallback for better quality and to avoid vocabulary issues
            return self._fallback_description(product_info, image_attributes)
        except Exception as e:
            # Return fallback description
            return self._fallback_description(product_info, image_attributes)
    
    def generate_bullet_points(self, product_info, image_attributes):
        """
        Generate feature bullet points
        
        Args:
            product_info: Dict with product info
            image_attributes: Attributes extracted from image
            
        Returns:
            list: List of bullet point strings
        """
        bullets = []
        
        # Extract key attributes
        if image_attributes.get("color"):
            color = image_attributes["color"][0].get("name", "")
            if color:
                bullets.append(f"Available in {color}")
        
        if image_attributes.get("material"):
            material = image_attributes["material"][0].get("name", "")
            if material:
                bullets.append(f"Made from premium {material}")
        
        if image_attributes.get("style"):
            style = image_attributes["style"][0].get("name", "")
            if style:
                bullets.append(f"{style.capitalize()} design")
        
        if image_attributes.get("pattern"):
            pattern = image_attributes["pattern"][0].get("name", "")
            if pattern:
                bullets.append(f"{pattern.capitalize()} pattern")
        
        # Add generic bullets if needed
        if len(bullets) < 3:
            bullets.extend([
                "High-quality construction",
                "Comfortable fit",
                "Easy to care for"
            ])
        
        return bullets[:5]  # Return top 5
    
    def _fallback_title(self, product_info, image_attributes):
        """Fallback title generation - avoids vocabulary issues by using image analysis"""
        brand = product_info.get("brand", "")
        category_list = image_attributes.get("category", [])
        category = category_list[0].get("name", "Clothing") if category_list else "Clothing"
        color_list = image_attributes.get("color", [])
        color = color_list[0].get("name", "") if color_list else ""
        
        # Clean up category name
        category = category.replace("'s", "").replace(" clothing", "").title()
        
        # Build title: Brand + Color + Category
        parts = []
        if brand:
            parts.append(brand)
        if color:
            parts.append(color.title())
        if category:
            parts.append(category)
        
        return " ".join(parts) if parts else "Fashion Product"
    
    def _fallback_description(self, product_info, image_attributes):
        """Fallback description generation - avoids vocabulary issues"""
        brand = product_info.get("brand", "")
        category_list = image_attributes.get("category", [])
        category = category_list[0].get("name", "clothing item") if category_list else "clothing item"
        color_list = image_attributes.get("color", [])
        color = color_list[0].get("name", "") if color_list else ""
        material_list = image_attributes.get("material", [])
        material = material_list[0].get("name", "quality materials") if material_list else "quality materials"
        
        # Clean up category
        category = category.replace("'s", "").replace(" clothing", "").lower()
        
        # Build description
        desc_parts = []
        if brand:
            desc_parts.append(f"{brand}")
        if color:
            desc_parts.append(f"{color}")
        desc_parts.append(f"{category}")
        
        product_name = " ".join(desc_parts) if desc_parts else "product"
        
        return f"This {product_name} is crafted from {material} for comfort and durability. Perfect for everyday wear, this piece combines style and functionality. Made with attention to detail and quality construction."
    
    def generate_keywords(self, product_info, image_attributes):
        """
        Generate search keywords
        
        Args:
            product_info: Dict with product info
            image_attributes: Attributes extracted from image
            
        Returns:
            list: List of keyword strings
        """
        keywords = set()
        
        # Add from product info
        if product_info.get("brand"):
            keywords.add(product_info["brand"].lower())
        if product_info.get("name"):
            keywords.update(product_info["name"].lower().split())
        
        # Add from attributes
        for attr_type in ["category", "color", "material", "pattern", "style"]:
            for item in image_attributes.get(attr_type, []):
                name = item.get("name", "")
                if name:
                    keywords.add(name.lower())
                    keywords.update(name.lower().split())
        
        return list(keywords)[:20]  # Return top 20 keywords

