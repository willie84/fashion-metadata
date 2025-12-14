from transformers import GPT2LMHeadModel, GPT2Tokenizer, pipeline
import torch


class TextGenerator:
    def __init__(self, model_name="gpt2"):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        
        try:
            self.tokenizer = GPT2Tokenizer.from_pretrained(model_name)
            self.model = GPT2LMHeadModel.from_pretrained(model_name)
            self.model.to(self.device)
            self.model.eval()
            
            if self.tokenizer.pad_token is None:
                self.tokenizer.pad_token = self.tokenizer.eos_token
            
            self.generator = pipeline(
                "text-generation",
                model=self.model,
                tokenizer=self.tokenizer,
                device=0 if self.device == "cuda" else -1
            )
        except Exception as e:
            raise RuntimeError(f"Failed to load text generation model: {e}")
            self.generator = None
    
    def generate_title(self, product_info, image_attributes):
        if not self.generator:
            return self._fallback_title(product_info, image_attributes)
        
        return self._fallback_title(product_info, image_attributes)
    
    def generate_description(self, product_info, image_attributes):
        if not self.generator:
            return self._fallback_description(product_info, image_attributes)
        
        return self._fallback_description(product_info, image_attributes)
    
    def generate_bullet_points(self, product_info, image_attributes):
        bullets = []
        
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
        
        if len(bullets) < 3:
            bullets.extend([
                "High-quality construction",
                "Comfortable fit",
                "Easy to care for"
            ])
        
        return bullets[:5]
    
    def _fallback_title(self, product_info, image_attributes):
        brand = product_info.get("brand", "")
        category_list = image_attributes.get("category", [])
        category = category_list[0].get("name", "Clothing") if category_list else "Clothing"
        color_list = image_attributes.get("color", [])
        color = color_list[0].get("name", "") if color_list else ""
        category = category.replace("'s", "").replace(" clothing", "").title()
        
        parts = []
        if brand:
            parts.append(brand)
        if color:
            parts.append(color.title())
        if category:
            parts.append(category)
        
        return " ".join(parts) if parts else "Fashion Product"
    
    def _fallback_description(self, product_info, image_attributes):
        brand = product_info.get("brand", "")
        category_list = image_attributes.get("category", [])
        category = category_list[0].get("name", "clothing item") if category_list else "clothing item"
        color_list = image_attributes.get("color", [])
        color = color_list[0].get("name", "") if color_list else ""
        material_list = image_attributes.get("material", [])
        material = material_list[0].get("name", "quality materials") if material_list else "quality materials"
        category = category.replace("'s", "").replace(" clothing", "").lower()
        
        desc_parts = []
        if brand:
            desc_parts.append(f"{brand}")
        if color:
            desc_parts.append(f"{color}")
        desc_parts.append(f"{category}")
        
        product_name = " ".join(desc_parts) if desc_parts else "product"
        
        return f"This {product_name} is crafted from {material} for comfort and durability. Perfect for everyday wear, this piece combines style and functionality. Made with attention to detail and quality construction."
    
    def generate_keywords(self, product_info, image_attributes):
        keywords = set()
        
        if product_info.get("brand"):
            keywords.add(product_info["brand"].lower())
        if product_info.get("name"):
            keywords.update(product_info["name"].lower().split())
        
        for attr_type in ["category", "color", "material", "pattern", "style"]:
            for item in image_attributes.get(attr_type, []):
                name = item.get("name", "")
                if name:
                    keywords.add(name.lower())
                    keywords.update(name.lower().split())
        
        return list(keywords)[:20]

