# Automating Fashion E-commerce Metadata Creation Using Machine Learning

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://fashion-store-metadata-generator.streamlit.app/)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**Live Application:** https://fashion-store-metadata-generator.streamlit.app/

**GitHub Repository:** https://github.com/willie84/fashion-metadata

---

## Table of Contents

- [Introduction](#introduction)
- [The Problem](#the-problem)
- [The Solution](#the-solution)
- [System Architecture](#system-architecture)
- [Results](#results)
- [AI Use and Transparency](#ai-use-and-transparency)
- [Installation](#installation)
- [Usage](#usage)
- [Dataset](#dataset)
- [Links](#links)

---

## Introduction

When building e-commerce web applications, it is important to have good metadata for the items present on the website to be discoverable by the customers. Metadata also helps with search engine optimizations and also with inventory analytics. 

This project demonstrates how machine learning, specifically Claude Vision API, can automate the creation of fashion product metadata while maintaining quality through human-in-the-loop validation and controlled vocabularies.

---

## The Problem

The problem comes when a store has thousands of products with different colors, styles, materials, and patterns - things can get messy very quickly. 

**Common issues with manual metadata creation:**

- **Inconsistent terminology**: If one person labels a product as "Red" and another uses "Crimson" or "Cherry," filters stop working properly
- **Failed searches**: A customer searching for "striped T-shirts" might miss items labeled as "stripe" or "lined," even though they're basically the same thing
- **Lost sales**: When people can't find what they're looking for, they leave the website, and that affects sales
- **Operational challenges**: Messy metadata makes inventory tracking and reporting much harder and hurts the overall shopping experience
- **Scale**: Manually tagging thousands of products takes weeks of human effort

---

## The Solution

Machine learning can help speed up the process of creating metadata. What would normally take a team weeks to tag can be done in just a few hours.

### Key Components

**1. AI-Powered Generation**
- Uses Anthropic's Claude Vision API to analyze product images
- Automatically extracts attributes like color, pattern, material, style
- Processes hundreds of products in hours instead of weeks

**2. Human-in-the-Loop Validation**

However, AI isn't perfect. It can make bad mistakes, like tagging a floral pattern as geometric or calling heels "casual shoes." This is why human-in-the-loop validation is important. Having people review and correct AI-generated metadata helps catch these errors before products go live. The value here is that rather than the humans having to create or generate the whole metadata, AI can do part of it.

**3. Controlled Vocabulary**

Using a controlled vocabulary—basically a fixed list of allowed terms for things like color, pattern, and style—helps keep everything consistent. When AI generates tags, human reviewers can quickly check whether the terms match the approved list. This makes it easier to spot mistakes and ensures consistency across the entire dataset, whether it's 250 products or 250,000.

**4. Continuous Improvement Loop**

Over time, this also helps improve the AI itself. Instead of learning from inconsistent or messy data, the model learns the exact terms the business wants to use. This creates a feedback loop where AI works faster and humans keep quality in check. This helps to keep the metadata consistent, and customers can actually find the products they're searching for.

---

## System Architecture

The system architecture combines automated AI metadata generation with human validation. The system is built using several Python classes that work together in a structured pipeline.

### Core Components

**1. ImageAnalyzer Class**
- Uses Anthropic's Claude Vision API to extract visual attributes from product images
- Analyzes product category, color, material, and pattern
- Processes images and returns structured attribute data

**2. FacetedMetadataGenerator Class**
- Creates both hierarchical and flat metadata structures
- Builds a two-level hierarchical facet system:
  - **Facet 1**: Item type hierarchy (Apparel/Footwear → Category → Product Type)
  - **Facet 2**: Style/usage hierarchy (Casual/Formal → Sub-style → Specific Style)
- Generates flat facets for attributes like color, material, pattern, brand, and size

**3. VocabularyManager Class**
- Maintains the controlled vocabulary stored in JSON format
- Validates AI-generated terms against approved lists
- Suggests closest matching terms when mismatches occur
- Ensures consistency across all metadata generation

**4. ConfidenceScorer Class**
- Calculates confidence scores for each AI-generated attribute
- Helps reviewers prioritize which items need closer inspection
- Flags low-confidence predictions for human review

**5. BulkProcessor Class**
- Handles CSV uploads for batch processing
- Processes multiple products while maintaining validation workflow
- Exports validated metadata in JSON format

### Workflow Pipeline

```
Product Image → ImageAnalyzer (Claude Vision API) 
              → FacetedMetadataGenerator 
              → VocabularyManager (Validation) 
              → Human Review (Streamlit Interface) 
              → Validated Metadata Export (JSON)
```

### Human-in-the-Loop Interface

Human validation happens through a Streamlit-based interface where reviewers can:
- View AI-generated metadata alongside original product images
- See confidence scores for each attribute
- Correct misclassifications before approval
- Validate terms against controlled vocabulary
- Process items in priority order based on confidence scores

The final validated metadata is exported in JSON format, making it easy to integrate with e-commerce platforms.

---

## Results

### Evaluation Methodology

To evaluate how well the AI performed, I manually created a gold standard dataset with 250 images.

**Gold Standard Dataset:** https://docs.google.com/spreadsheets/d/1ZQflidcyfjmxpznGaY39QdIIiXdMJCqs-J7qq13Y-Dk/edit?usp=drive_link

**Base Dataset Source:** https://www.kaggle.com/datasets/vikashrajluhaniwal/fashion-images

Some of the metadata came directly from the Kaggle source, but I manually created the pattern and material metadata to ensure quality.

### Testing Process

**1. Input CSV for AI Generation:**
https://raw.githubusercontent.com/willie84/fashion-metadata/refs/heads/main/data-of-250-fashion-images/fashion_gold_standard_250%20-%20csv-to-generator.csv

**2. AI-Generated Output:**
https://raw.githubusercontent.com/willie84/fashion-metadata/refs/heads/main/data-of-250-fashion-images/ai_generated_metadata_20251213_181150.csv

**3. Evaluation Process:**

I used the `evaluate_ai_accuracy.py` class to compare AI-generated metadata against the gold standard. Both CSV files were uploaded to the Streamlit application at https://fashion-store-metadata-generator.streamlit.app/ under the AI evaluation section.

**Files evaluated:**
- Gold Standard: https://raw.githubusercontent.com/willie84/fashion-metadata/refs/heads/main/data-of-250-fashion-images/fashion_gold_standard_250%20-%20fashion_gold_standard_250.csv
- AI Generated: https://raw.githubusercontent.com/willie84/fashion-metadata/refs/heads/main/data-of-250-fashion-images/ai_generated_metadata_20251213_181150.csv

### Performance Results

**Overall Weighted Accuracy: 62.4%**

#### Field-by-Field Performance

| Metadata Field | Accuracy | Performance |
|---------------|----------|-------------|
| Item-type | >80% | ✅ High accuracy |
| Style | >80% | ✅ High accuracy |
| Gender | ~70-80% | 🟡 Good |
| Pattern | ~60-70% | 🟡 Moderate |
| **Colour** | <60% | ⚠️ **Needs human review** |
| **Material** | <60% | ⚠️ **Needs human review** |

### Key Findings

**Strengths:**
- AI excels at identifying high-level categories (item-type, style)
- Consistent performance on structural attributes
- Fast processing time (250 images in ~15 minutes)

**Weaknesses:**
- Struggles with specific color identification (confuses similar shades)
- Material detection is challenging from images alone
- These fields require careful human review

**Recommendation:**
Human reviewers should focus validation efforts on:
1. Color accuracy (primary concern)
2. Material verification (secondary concern)
3. Spot-checking other fields for quality assurance

This targeted approach allows humans to add value where AI is weakest while leveraging AI's speed for initial generation.

---

## AI Use and Transparency

### Project Development Process

**Initial Planning (Manual)**
- Analyzed the Kaggle dataset to understand structure
- Designed the faceted metadata system
- Created the `vocabulary.json` file with controlled vocabularies

**Code Development (Hybrid Approach)**

I used both manual and automated coding throughout this project:

**Fully Manual Implementation:**
- `FacetedMetadataGenerator` class
- `VocabularyManager` class  
- `TextGenerator` class
- Core business logic and metadata structure

**AI-Assisted Implementation:**
- `ImageAnalyzer` class (prompt engineering with AI assistance)
- `app_streamlit.py` (fully generated by Claude Code)
- Debugging and connection issues (AI-assisted troubleshooting)

### Tools Used

**Development:**
- **Claude Code**: Code generation and debugging assistance
- **Streamlit**: Frontend interface (AI-generated)
- **Python**: Core implementation language

**Testing:**
- Started with command-line testing in Python shell
- Transitioned to Streamlit frontend for better UX (AI-generated)

### Workflow Evolution

1. **Initial testing**: Command-line Python shell
2. **Recognition**: Needed user-friendly interface for practical use
3. **Solution**: Claude Code generated Streamlit frontend
4. **Outcome**: Accessible web application for non-technical users

### Example AI Prompts Used

Some of the AI prompts I used with Claude during development:

```
"Generate a Streamlit interface for uploading CSV files and displaying metadata results"

"Help debug the Claude API connection issue with image analysis"

"Create a class for managing controlled vocabulary with JSON storage"

"Write a function to calculate confidence scores for AI-generated attributes"
```

### Transparency Statement

This project demonstrates a realistic AI-assisted development workflow:
- Core architecture and business logic designed manually
- AI assisted with implementation details and interface generation
- Human oversight maintained throughout for quality and correctness
- Final system combines human expertise with AI efficiency

The goal was to create a practical tool that shows how AI can augment (not replace) human work in both software development and metadata creation.

---

## Installation

### Prerequisites

- Python 3.8 or higher
- Anthropic API key ([Get one here](https://console.anthropic.com/))

### Setup

1. **Clone the repository**
```bash
git clone https://github.com/willie84/fashion-metadata.git
cd fashion-metadata
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Configure API key**

Create a `.env` file:
```bash
ANTHROPIC_API_KEY=your_api_key_here
```

4. **Run the application**
```bash
streamlit run app.py
```

5. **Open in browser**
Navigate to `http://localhost:8501`

---

## Usage

### 1. Bulk Metadata Generation

1. Navigate to "🤖 Bulk Metadata Generation"
2. Enter your Anthropic API key
3. Upload CSV with columns: `ProductId`, `ImageURL`, `Image`
4. Click "Generate Metadata"
5. Download results as CSV

### 2. AI Accuracy Evaluation

1. Navigate to "📊 AI Accuracy Evaluation"
2. Upload two CSV files:
   - Gold Standard (manually verified)
   - AI-Generated (from bulk generation)
3. Click "Evaluate Accuracy"
4. Review field-by-field accuracy metrics
5. Download evaluation report

### 3. Human Review

1. Review AI-generated metadata in the interface
2. Check confidence scores
3. Focus on low-accuracy fields (Colour, Material)
4. Validate against controlled vocabulary
5. Approve or correct before export

---

## Dataset

### Original Source
Kaggle Fashion Images Dataset: https://www.kaggle.com/datasets/vikashrajluhaniwal/fashion-images

### Gold Standard (250 Images)
Manually created and verified: https://docs.google.com/spreadsheets/d/1ZQflidcyfjmxpznGaY39QdIIiXdMJCqs-J7qq13Y-Dk/edit?usp=drive_link

### CSV Format

**Required columns:**
- `ProductId`: Unique identifier
- `ImageURL`: Direct URL to product image
- `Image`: Filename

**Generated metadata columns:**
- Gender, Item-type, Itemcategory, ProductType
- Colour, Pattern, Material
- Brand, Style, Sub-Style, Specific Style
- ProductTitle

---

## Links

### Application
- **Live App**: https://fashion-store-metadata-generator.streamlit.app/
- **GitHub Repository**: https://github.com/willie84/fashion-metadata

### Datasets
- **Kaggle Source**: https://www.kaggle.com/datasets/vikashrajluhaniwal/fashion-images
- **Gold Standard**: https://docs.google.com/spreadsheets/d/1ZQflidcyfjmxpznGaY39QdIIiXdMJCqs-J7qq13Y-Dk/edit?usp=drive_link

### Evaluation Files
- **Input CSV**: https://raw.githubusercontent.com/willie84/fashion-metadata/refs/heads/main/data-of-250-fashion-images/fashion_gold_standard_250%20-%20csv-to-generator.csv
- **AI Generated**: https://raw.githubusercontent.com/willie84/fashion-metadata/refs/heads/main/data-of-250-fashion-images/ai_generated_metadata_20251213_181150.csv
- **Gold Standard CSV**: https://raw.githubusercontent.com/willie84/fashion-metadata/refs/heads/main/data-of-250-fashion-images/fashion_gold_standard_250%20-%20fashion_gold_standard_250.csv

---

## Project Structure

```
fashion-metadata/
├── app.py                          # Main Streamlit application
├── evaluate_ai_accuracy.py         # Evaluation module
├── image_analyzer.py               # Claude Vision API integration
├── faceted_metadata_generator.py   # Metadata structure generator
├── vocabulary_manager.py           # Controlled vocabulary manager
├── text_generator.py               # Text generation utilities
├── confidence_scorer.py            # Confidence scoring
├── bulk_processor.py               # Batch processing
├── vocabulary.json                 # Controlled vocabulary definitions
├── requirements.txt                # Python dependencies
├── data-of-250-fashion-images/     # Dataset and results
│   ├── fashion_gold_standard_250.csv
│   └── ai_generated_metadata_20251213_181150.csv
└── README.md                       # This file
```

---

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

---

## License

This project is licensed under the MIT License - see the LICENSE file for details.

---

## Acknowledgments

- **Anthropic** for Claude Vision API
- **Kaggle** for the fashion images dataset
- **Streamlit** for the web framework
- **UC Berkeley I 202** course for project inspiration

---

## Contact

For questions or feedback, please open an issue on GitHub or contact the project maintainer.

---

**Built with ❤️ for better fashion e-commerce metadata**
