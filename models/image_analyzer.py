import os
import base64
from PIL import Image
import io
from anthropic import Anthropic
import requests
from urllib.parse import urlparse
from models.vocabulary_manager import VocabularyManager


class ImageAnalyzer:
    def __init__(self, vocabulary_manager: VocabularyManager = None):
        api_key = os.getenv('ANTHROPIC_API_KEY')
        if not api_key:
            raise ValueError(
                "ANTHROPIC_API_KEY environment variable is required. "
                "Please set it using: export ANTHROPIC_API_KEY='your-key-here'"
            )
        
        self.client = Anthropic(api_key=api_key)
        self.model = "claude-3-haiku-20240307"
        
        if vocabulary_manager is None:
            vocabulary_manager = VocabularyManager()
        self.vocab_manager = vocabulary_manager
    
    def analyze_image(self, image_input):
        try:
            image_path = None
            if isinstance(image_input, str):
                parsed = urlparse(image_input)
                if parsed.scheme in ('http', 'https'):
                    response = requests.get(image_input, timeout=30)
                    response.raise_for_status()
                    image = Image.open(io.BytesIO(response.content)).convert("RGB")
                    image_path = image_input
                else:
                    image = Image.open(image_input).convert("RGB")
                    image_path = image_input
            elif isinstance(image_input, Image.Image):
                image = image_input.convert("RGB")
                image_path = None
            else:
                raise ValueError(f"Unsupported image input type: {type(image_input)}")
            
            if image_path:
                parsed = urlparse(image_path) if isinstance(image_path, str) else None
                if parsed and parsed.scheme in ('http', 'https'):
                    path_part = parsed.path.lower()
                    ext = path_part.split('.')[-1] if '.' in path_part else 'jpg'
                else:
                    ext = image_path.lower().split('.')[-1]
                
                if ext in ['jpg', 'jpeg']:
                    format_type = "JPEG"
                    media_type = "image/jpeg"
                elif ext == 'png':
                    format_type = "PNG"
                    media_type = "image/png"
                elif ext == 'webp':
                    format_type = "WEBP"
                    media_type = "image/webp"
                else:
                    format_type = "JPEG"
                    media_type = "image/jpeg"
            else:
                format_type = "JPEG"
                media_type = "image/jpeg"
            
            buffered = io.BytesIO()
            image.save(buffered, format=format_type)
            image_base64 = base64.b64encode(buffered.getvalue()).decode('utf-8')
            
            prompt = """Analyze this fashion product image and provide detailed information in the following format:

1. **Product Category** (most important - be very specific):
   - Is it a t-shirt, shirt, pants, jeans, shorts, cargo shorts, dress, shoes, sneakers, jacket, etc.?
   - Be very specific about the product type (e.g., "cargo shorts" not just "shorts", "t-shirt" not just "shirt")

2. **Gender**: Men, Women, or Unisex

3. **Color**: Primary color of the item (be specific: khaki, navy blue, etc.)

4. **Material/Fabric**: What material does it appear to be made of? (cotton, denim, leather, etc.)

5. **Pattern**: Solid, striped, floral, geometric, etc.

6. **Style Details**: 
   - For tops: sleeve length, neck type, etc.
   - For bottoms: length, fit type, etc.
   - For shoes: type, style, etc.

7. **Usage/Style**: Casual, Formal, Sporty, Ethnic, etc.

Provide your analysis in a structured format focusing on accurately identifying the product category first. Be very specific about the product type."""

            message = self.client.messages.create(
                model=self.model,
                max_tokens=500,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": media_type,
                                    "data": image_base64
                                }
                            },
                            {
                                "type": "text",
                                "text": prompt
                            }
                        ]
                    }
                ]
            )
            
            analysis_text = message.content[0].text
            attributes = self._parse_claude_response(analysis_text)
            
            return {
                "top_matches": [(attributes.get("category", [{}])[0].get("name", "unknown"), 1.0)],
                "attributes": attributes,
                "raw_analysis": analysis_text,
                "model": self.model
            }
            
        except Exception as e:
            return {
                "top_matches": [],
                "attributes": {},
                "error": str(e)
            }
    
    def _parse_claude_response(self, analysis_text):
        attributes = {
            "category": [],
            "color": [],
            "material": [],
            "pattern": [],
            "style": []
        }
        
        analysis_lower = analysis_text.lower()
        
        category_mappings = self.vocab_manager.get_category_keyword_mappings()
        color_mappings = self.vocab_manager.get_color_keyword_mappings()
        material_mappings = self.vocab_manager.get_material_keyword_mappings()
        pattern_mappings = self.vocab_manager.get_pattern_keyword_mappings()
        
        found_category = None
        lines = analysis_text.split('\n')
        for i, line in enumerate(lines):
            line_lower = line.lower()
            if 'product category' in line_lower or ('category' in line_lower and ':' in line):
                if ':' in line:
                    category_text = line.split(':', 1)[1].strip()
                elif i + 1 < len(lines):
                    category_text = lines[i + 1].strip()
                else:
                    category_text = line
                
                category_text_lower = category_text.lower()
                
                for category, keywords in category_mappings.items():
                    if any(keyword in category_text_lower for keyword in keywords):
                        found_category = category
                        break
                
                if found_category:
                    break
        
        if not found_category:
            for category, keywords in category_mappings.items():
                for keyword in keywords:
                    if keyword in analysis_lower:
                        idx = analysis_lower.find(keyword)
                        if idx >= 0:
                            context_start = max(0, idx - 10)
                            context_end = min(len(analysis_lower), idx + len(keyword) + 10)
                            context = analysis_lower[context_start:context_end]
                            if "short sleeve" not in context:
                                found_category = category
                                break
                if found_category:
                    break
        
        if found_category:
            attributes["category"].append({
                "name": found_category,
                "confidence": 0.95
            })
        
        for color_name, keywords in color_mappings.items():
            if any(keyword in analysis_lower for keyword in keywords):
                vocab_colors = self.vocab_manager.get_valid_options('color')
                matched_color = next((c for c in vocab_colors if color_name.lower() in c.lower()), color_name.capitalize())
                attributes["color"].append({
                    "name": matched_color,
                    "confidence": 0.9
                })
                break
        
        for material_name, keywords in material_mappings.items():
            if any(keyword in analysis_lower for keyword in keywords):
                vocab_materials = self.vocab_manager.get_valid_options('material')
                matched_material = next((m for m in vocab_materials if material_name.lower() in m.lower()), material_name.capitalize())
                attributes["material"].append({
                    "name": matched_material,
                    "confidence": 0.9
                })
                break
        
        for pattern_name, keywords in pattern_mappings.items():
            if any(keyword in analysis_lower for keyword in keywords):
                vocab_patterns = self.vocab_manager.get_valid_options('pattern')
                matched_pattern = next((p for p in vocab_patterns if pattern_name.lower() in p.lower()), pattern_name.title())
                attributes["pattern"].append({
                    "name": matched_pattern,
                    "confidence": 0.9
                })
                break
        if "long sleeve" in analysis_lower:
            attributes["style"].append({"name": "Long Sleeve", "confidence": 0.9})
        elif "short sleeve" in analysis_lower:
            attributes["style"].append({"name": "Short Sleeve", "confidence": 0.9})
        elif "sleeveless" in analysis_lower:
            attributes["style"].append({"name": "Sleeveless", "confidence": 0.9})
        
        return attributes
