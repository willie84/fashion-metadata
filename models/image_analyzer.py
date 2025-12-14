"""
Image Analysis Module using Anthropic Claude Vision
Uses Claude's vision API for accurate image understanding
"""

import os
import base64
from PIL import Image
import io
from anthropic import Anthropic
import requests
from urllib.parse import urlparse


class ImageAnalyzer:
    """Analyzes fashion product images using Anthropic Claude Vision"""
    
    def __init__(self):
        """Initialize Anthropic client"""
        api_key = os.getenv('ANTHROPIC_API_KEY')
        if not api_key:
            raise ValueError(
                "ANTHROPIC_API_KEY environment variable is required. "
                "Please set it using: export ANTHROPIC_API_KEY='your-key-here'"
            )
        
        self.client = Anthropic(api_key=api_key)
        self.model = "claude-3-haiku-20240307"  # Claude 3 Haiku with vision
    
    def analyze_image(self, image_input):
        """
        Analyze fashion product image and extract visual features using Claude Vision
        
        Args:
            image_input: Path to the image file (str), image URL (str starting with http:// or https://), or PIL Image object
            
        Returns:
            dict: Extracted visual features and descriptions
        """
        try:
            # Load and preprocess image
            image_path = None
            if isinstance(image_input, str):
                # Check if it's a URL
                parsed = urlparse(image_input)
                if parsed.scheme in ('http', 'https'):
                    # Download image from URL
                    response = requests.get(image_input, timeout=30)
                    response.raise_for_status()
                    image = Image.open(io.BytesIO(response.content)).convert("RGB")
                    # Extract extension from URL for media type
                    image_path = image_input
                else:
                    # Local file path
                    image = Image.open(image_input).convert("RGB")
                    image_path = image_input
            elif isinstance(image_input, Image.Image):
                image = image_input.convert("RGB")
                image_path = None
            else:
                raise ValueError(f"Unsupported image input type: {type(image_input)}")
            
            # Convert image to base64 for API
            # Determine format from file extension or URL, default to JPEG
            if image_path:
                # Check if it's a URL
                parsed = urlparse(image_path) if isinstance(image_path, str) else None
                if parsed and parsed.scheme in ('http', 'https'):
                    # Extract extension from URL path
                    path_part = parsed.path.lower()
                    ext = path_part.split('.')[-1] if '.' in path_part else 'jpg'
                else:
                    # Local file path
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
            
            # Create detailed prompt for fashion product analysis
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

            # Call Claude Vision API
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
            
            # Parse the response
            analysis_text = message.content[0].text
            
            # Extract structured attributes from the response
            attributes = self._parse_claude_response(analysis_text)
            
            return {
                "top_matches": [(attributes.get("category", [{}])[0].get("name", "unknown"), 1.0)],
                "attributes": attributes,
                "raw_analysis": analysis_text,
                "model": self.model
            }
            
        except Exception as e:
            # Error will be raised to caller
            return {
                "top_matches": [],
                "attributes": {},
                "error": str(e)
            }
    
    def _parse_claude_response(self, analysis_text):
        """Parse Claude Vision response into structured attributes"""
        attributes = {
            "category": [],
            "color": [],
            "material": [],
            "pattern": [],
            "style": []
        }
        
        analysis_lower = analysis_text.lower()
        
        # First, try to extract from structured format (Product Category line)
        found_category = None
        
        # Look for "Product Category" line
        lines = analysis_text.split('\n')
        for i, line in enumerate(lines):
            line_lower = line.lower()
            if 'product category' in line_lower or ('category' in line_lower and ':' in line):
                # Get the category from this line
                if ':' in line:
                    category_text = line.split(':', 1)[1].strip()
                elif i + 1 < len(lines):
                    category_text = lines[i + 1].strip()
                else:
                    category_text = line
                
                category_text_lower = category_text.lower()
                
                # Extract category (most specific first)
                category_keywords = {
                    # Bottoms (check first, but exclude "short sleeves")
                    "cargo shorts": ["cargo shorts", "cargo short"],
                    "shorts": ["shorts", "short pants", "pair of shorts"],
                    "jeans": ["jeans", "jean", "denim pants"],
                    "pants": ["pants", "trousers", "trouser", "pant"],
                    "skirt": ["skirt"],
                    "leggings": ["leggings", "legging"],
                    "capris": ["capris", "capri"],
                    
                    # Tops
                    "tshirt": ["t-shirt", "tshirt", "t shirt", "tee"],
                    "shirt": ["shirt", "collared shirt", "button-down", "button down", "dress shirt"],
                    "top": ["top", "blouse"],
                    "sweater": ["sweater", "pullover"],
                    "hoodie": ["hoodie", "hooded"],
                    "polo": ["polo", "polo shirt"],
                    
                    # Dresses
                    "dress": ["dress"],
                    
                    # Footwear
                    "sneakers": ["sneakers", "sneaker", "athletic shoes", "running shoes"],
                    "shoes": ["shoes", "shoe"],
                    "boots": ["boots", "boot"],
                    "sandals": ["sandals", "sandal"],
                    
                    # Outerwear
                    "jacket": ["jacket"],
                    "blazer": ["blazer"],
                    "coat": ["coat"]
                }
                
                # Find matching category (check most specific first)
                for category, keywords in category_keywords.items():
                    if any(keyword in category_text_lower for keyword in keywords):
                        found_category = category
                        break
                
                if found_category:
                    break
        
        # If not found in structured format, search entire text (but avoid "short sleeves")
        if not found_category:
            category_keywords = {
                # Bottoms (check first, but exclude "short sleeves")
                "cargo shorts": ["cargo shorts", "cargo short"],
                "shorts": ["shorts", "short pants", "pair of shorts"],
                "jeans": ["jeans", "jean", "denim pants"],
                "pants": ["pants", "trousers", "trouser", "pant"],
                "skirt": ["skirt"],
                "leggings": ["leggings", "legging"],
                "capris": ["capris", "capri"],
                
                # Tops
                "tshirt": ["t-shirt", "tshirt", "t shirt", "tee"],
                "shirt": ["shirt", "collared shirt", "button-down", "button down", "dress shirt"],
                "top": ["top", "blouse"],
                "sweater": ["sweater", "pullover"],
                "hoodie": ["hoodie", "hooded"],
                "polo": ["polo", "polo shirt"],
                
                # Dresses
                "dress": ["dress"],
                
                # Footwear
                "sneakers": ["sneakers", "sneaker", "athletic shoes", "running shoes"],
                "shoes": ["shoes", "shoe"],
                "boots": ["boots", "boot"],
                "sandals": ["sandals", "sandal"],
                
                # Outerwear
                "jacket": ["jacket"],
                "blazer": ["blazer"],
                "coat": ["coat"]
            }
            
            # Find matching category, but exclude "short sleeves" context
            for category, keywords in category_keywords.items():
                for keyword in keywords:
                    # Check if keyword appears but not in "short sleeves" context
                    if keyword in analysis_lower:
                        # Make sure it's not "short sleeves" or "short sleeve"
                        idx = analysis_lower.find(keyword)
                        if idx >= 0:
                            # Check context around the keyword
                            context_start = max(0, idx - 10)
                            context_end = min(len(analysis_lower), idx + len(keyword) + 10)
                            context = analysis_lower[context_start:context_end]
                            # Skip if it's "short sleeves" or "short sleeve"
                            if "short sleeve" not in context:
                                found_category = category
                                break
                if found_category:
                    break
        
        if found_category:
            attributes["category"].append({
                "name": found_category,
                "confidence": 0.95  # High confidence from Claude
            })
        
        # Extract color
        color_keywords = ["red", "blue", "black", "white", "green", "yellow", "pink", 
                         "purple", "brown", "gray", "grey", "beige", "khaki", "navy", 
                         "olive", "orange", "tan", "maroon", "burgundy", "charcoal"]
        for color in color_keywords:
            if color in analysis_lower:
                attributes["color"].append({
                    "name": color.capitalize(),
                    "confidence": 0.9
                })
                break
        
        # Extract material
        material_keywords = ["cotton", "denim", "leather", "silk", "polyester", 
                            "wool", "linen", "rayon", "spandex", "nylon", "canvas"]
        for material in material_keywords:
            if material in analysis_lower:
                attributes["material"].append({
                    "name": material.capitalize(),
                    "confidence": 0.9
                })
                break
        
        # Extract pattern
        if "solid" in analysis_lower or "plain" in analysis_lower:
            attributes["pattern"].append({"name": "Solid", "confidence": 0.9})
        elif "striped" in analysis_lower or "stripe" in analysis_lower:
            attributes["pattern"].append({"name": "Striped", "confidence": 0.9})
        elif "floral" in analysis_lower:
            attributes["pattern"].append({"name": "Floral", "confidence": 0.9})
        elif "geometric" in analysis_lower:
            attributes["pattern"].append({"name": "Geometric", "confidence": 0.9})
        
        # Extract style details
        if "long sleeve" in analysis_lower:
            attributes["style"].append({"name": "Long Sleeve", "confidence": 0.9})
        elif "short sleeve" in analysis_lower:
            attributes["style"].append({"name": "Short Sleeve", "confidence": 0.9})
        elif "sleeveless" in analysis_lower:
            attributes["style"].append({"name": "Sleeveless", "confidence": 0.9})
        
        return attributes
