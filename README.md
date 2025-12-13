# Fashion Metadata Generator

A Streamlit web application that automatically generates comprehensive metadata for fashion products using AI vision analysis (Claude Vision API) and controlled vocabulary.

## Features

- **AI-Powered Image Analysis**: Uses Claude Vision API to analyze product images
- **Faceted Metadata**: Generates both hierarchical and flat metadata structures
- **Controlled Vocabulary**: Validates metadata against predefined vocabulary
- **Human-in-the-Loop**: Review and edit interface with confidence scoring
- **Bulk Processing**: Upload CSV files for batch metadata generation
- **Export Options**: Export metadata as JSON or CSV

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Claude API Key

You need to set your Anthropic API key as an environment variable:

**Option A: Environment Variable**
```bash
export ANTHROPIC_API_KEY='your-api-key-here'
```

**Option B: Create `.env` file**
```bash
ANTHROPIC_API_KEY=your-api-key-here
```

**Important:** Never commit API keys to version control. Always use environment variables.

### 3. Run the Application

```bash
streamlit run app_streamlit.py
```

The application will open automatically in your browser at `http://localhost:8501`

## Usage

### Single Product Upload

1. Navigate to "Single Product" tab
2. Upload a product image
3. Enter Brand and Gender (required)
4. Optionally enter Size
5. Click "Generate Metadata"
6. Review and edit the generated metadata
7. Approve (only if all fields are valid)
8. Download as JSON

### Bulk Upload

1. Navigate to "Bulk Upload" tab
2. Prepare a CSV file with columns:
   - ProductId, Gender, Category, SubCategory, ProductType, Colour, Usage, ProductTitle, Image, ImageURL
3. Upload CSV file
4. Optionally specify images directory
5. Click "Process CSV"
6. Review results and download

## Project Structure

```
fasion-metadata/
├── app_streamlit.py          # Streamlit application
├── models/                    # Core modules
│   ├── image_analyzer.py    # Claude Vision API integration
│   ├── faceted_metadata.py  # Faceted metadata generation
│   ├── text_generator.py     # Text generation (titles, descriptions)
│   ├── bulk_processor.py    # Bulk CSV processing
│   ├── vocabulary_manager.py # Controlled vocabulary
│   └── confidence_scorer.py  # Confidence scoring
├── vocabulary.json           # Controlled vocabulary definitions
├── requirements.txt          # Python dependencies
└── README.md                 # This file
```

## Metadata Structure

### Hierarchical Facets

**Facet 1: Item Type**
- Level 1: Apparel / Footwear
- Level 2: Category (Topwear, Bottomwear, etc.)
- Level 3: Product Type (Shirts, Tshirts, Jeans, etc.)

**Facet 2: Style/Usage**
- Level 1: Casual / Formal / Sporty / Ethnic
- Level 2: Sub-Style (Everyday, Business, etc.)
- Level 3: Specific Style (Basic, Professional, etc.)

### Flat Facets

- Gender (Men, Women, Unisex)
- Brand
- Size
- Color
- Material
- Pattern

### Descriptive Metadata

- Product Title
- Short Description
- Long Description
- Bullet Points
- Keywords

## Deployment

### Streamlit Cloud (Recommended)

1. Push your code to GitHub
2. Go to https://streamlit.io/cloud
3. Connect your GitHub repository
4. Deploy!

### Other Platforms

Streamlit apps can be deployed on:
- Heroku
- AWS
- Google Cloud
- Azure
- Any platform that supports Python

## Cost Information

- **Claude 3 Haiku**: ~$0.003 per image (input) + ~$0.015 per image (output)
- Very affordable for most use cases
- Check current pricing at https://www.anthropic.com/pricing

## License

This project is for educational purposes.
