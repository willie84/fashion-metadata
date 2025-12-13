# Claude (Anthropic) Vision Setup

This application uses Anthropic's Claude Vision API for accurate image analysis.

## Setup Instructions

### 1. API Key

The API key is already configured in the code. If you need to change it, you can:

**Option A: Set Environment Variable (Recommended)**

```bash
export ANTHROPIC_API_KEY='your-api-key-here'
```

**Option B: Create .env file**

Create a `.env` file in the project root:

```bash
ANTHROPIC_API_KEY=your-api-key-here
```

**Option C: Update in code**

You must set the ANTHROPIC_API_KEY environment variable before running the application.

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

This will install the `anthropic` package.

### 3. Verify Setup

```bash
python3 -c "from models.image_analyzer import ImageAnalyzer; ia = ImageAnalyzer(); print('✅ Claude initialized successfully!')"
```

## Cost Information

- **Claude 3.5 Sonnet**: ~$0.003 per image (input) + ~$0.015 per image (output)
- Very affordable for most use cases
- Check current pricing at https://www.anthropic.com/pricing

## Benefits

- ✅ Excellent product category detection
- ✅ Better understanding of fashion-specific details
- ✅ Handles complex items (cargo shorts, specific shoe types, etc.)
- ✅ More reliable color, material, and pattern detection
- ✅ Better context understanding than CLIP
- ✅ More affordable than GPT-4 Vision

## Model Used

- **Claude 3.5 Sonnet** (`claude-3-5-sonnet-20241022`)
- Latest model with excellent vision capabilities
- Can be changed in `image_analyzer.py` if needed

## Troubleshooting

**Error: "API key not found"**
- Set the `ANTHROPIC_API_KEY` environment variable
- See setup instructions above

**Error: "Rate limit exceeded"**
- Claude has rate limits based on your plan
- Free tier: 5 requests per minute
- Paid tier: Higher limits
- Wait a moment and try again

**Error: "Insufficient quota"**
- Check your Anthropic account balance
- Verify your API key is active
- Check usage limits in Anthropic dashboard

## Testing

Test with an image:

```python
from models.image_analyzer import ImageAnalyzer
from PIL import Image

ia = ImageAnalyzer()
result = ia.analyze_image('path/to/image.jpg')
print(result['attributes']['category'])
```

