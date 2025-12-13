"""
Fashion Metadata Generator - Streamlit Application
Streamlit frontend for metadata generation
"""

import streamlit as st
import os
import json
from datetime import datetime
import pandas as pd

# Import ML modules
from models.image_analyzer import ImageAnalyzer
from models.text_generator import TextGenerator
from models.faceted_metadata import FacetedMetadataGenerator
from models.bulk_processor import BulkProcessor
from models.vocabulary_manager import VocabularyManager
from models.confidence_scorer import ConfidenceScorer

# Page config
st.set_page_config(
    page_title="Fashion Metadata Generator",
    page_icon="🛍️",
    layout="wide"
)

# Initialize session state
if 'metadata_store' not in st.session_state:
    st.session_state.metadata_store = {}
if 'current_metadata' not in st.session_state:
    st.session_state.current_metadata = None
if 'current_metadata_id' not in st.session_state:
    st.session_state.current_metadata_id = None

# Initialize models (cached)
@st.cache_resource
def initialize_models():
    """Initialize ML models"""
    try:
        image_analyzer = ImageAnalyzer()
        text_generator = TextGenerator()
        faceted_generator = FacetedMetadataGenerator()
        vocabulary_manager = VocabularyManager()
        confidence_scorer = ConfidenceScorer()
        bulk_processor = BulkProcessor(
            image_analyzer, text_generator, None,  # classifier removed
            None,  # attribute_extractor removed (redundant)
            faceted_generator,
            vocabulary_manager, confidence_scorer
        )
        return {
            'image_analyzer': image_analyzer,
            'text_generator': text_generator,
            'faceted_generator': faceted_generator,
            'vocabulary_manager': vocabulary_manager,
            'confidence_scorer': confidence_scorer,
            'bulk_processor': bulk_processor
        }
    except Exception as e:
        st.error(f"Error initializing models: {str(e)}")
        return None

# Main app
def main():
    st.title("🛍️ Fashion Metadata Generator")
    st.markdown("**Human-in-the-Loop with Controlled Vocabulary**")
    
    # Initialize models
    models = initialize_models()
    if models is None:
        st.stop()
    
    # Sidebar navigation
    page = st.sidebar.radio(
        "Navigation",
        ["Single Product", "Bulk Upload"]
    )
    
    if page == "Single Product":
        single_product_page(models)
    else:
        bulk_upload_page(models)

def single_product_page(models):
    """Single product upload and metadata generation"""
    st.header("Single Product Upload")
    
    # Upload image
    uploaded_file = st.file_uploader(
        "Upload Product Image",
        type=['png', 'jpg', 'jpeg', 'gif', 'webp'],
        help="Upload a fashion product image"
    )
    
    col1, col2 = st.columns(2)
    
    with col1:
        brand = st.text_input("Brand *", help="Enter product brand", key="brand_input")
        # Gender dropdown from vocabulary
        gender_options = models['vocabulary_manager'].get_valid_options('gender')
        gender = st.selectbox("Gender *", [""] + gender_options, key="gender_select")
    
    with col2:
        # Size dropdown from vocabulary
        size_options = models['vocabulary_manager'].get_valid_options('size')
        size = st.selectbox("Size (Optional)", [""] + size_options, key="size_select")
    
    if st.button("Generate Metadata", type="primary"):
        if not uploaded_file:
            st.error("Please upload an image")
            return
        
        if not brand or not gender:
            st.error("Brand and Gender are required")
            return
        
        with st.spinner("Generating metadata..."):
            try:
                # Save uploaded file temporarily
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                os.makedirs('uploads', exist_ok=True)
                filepath = f"uploads/{timestamp}_{uploaded_file.name}"
                
                with open(filepath, 'wb') as f:
                    f.write(uploaded_file.getbuffer())
                
                # Step 1: Analyze image
                image_analysis = models['image_analyzer'].analyze_image(filepath)
                image_attributes = image_analysis.get('attributes', {})
                
                # Step 2: Generate faceted metadata
                product_info = {
                    'brand': brand,
                    'gender': gender,
                    'size': size
                }
                
                faceted_metadata = models['faceted_generator'].generate_faceted_metadata(
                    image_attributes, product_info, None
                )
                
                # Step 3: Generate text
                title = models['text_generator'].generate_title(product_info, image_attributes)
                description = models['text_generator'].generate_description(product_info, image_attributes)
                bullet_points = models['text_generator'].generate_bullet_points(product_info, image_attributes)
                
                # Step 4: Calculate confidence scores
                temp_metadata = {
                    'faceted': faceted_metadata,
                    'descriptive': {
                        'title': title,
                        'description': description
                    }
                }
                confidence_scores = models['confidence_scorer'].score_metadata(
                    temp_metadata, image_attributes, models['vocabulary_manager'], product_info
                )
                
                # Step 5: Validate against vocabulary
                validation_results = {}
                faceted_data = faceted_metadata.get('faceted_metadata', {})
                flat_facets = faceted_data.get('flat_facets', {})
                hierarchical = faceted_data.get('hierarchical_facets', {})
                
                validation_results['gender'] = models['vocabulary_manager'].validate('gender', faceted_metadata.get('gender', ''))
                validation_results['item_type'] = models['vocabulary_manager'].validate('item_type', faceted_metadata.get('item_type', ''))
                validation_results['color'] = models['vocabulary_manager'].validate('color', flat_facets.get('color', ''))
                validation_results['material'] = models['vocabulary_manager'].validate('material', flat_facets.get('material', ''))
                
                facet1 = hierarchical.get('facet_1_item_type', {})
                if facet1:
                    hierarchy_valid, hierarchy_error = models['vocabulary_manager'].validate_hierarchy(
                        facet1.get('level_1', ''),
                        facet1.get('level_2', ''),
                        facet1.get('level_3', '')
                    )
                    validation_results['hierarchy'] = (hierarchy_valid, hierarchy_error if not hierarchy_valid else None, None)
                
                # Determine if review is required
                
                # Compile all metadata
                metadata = {
                    'faceted': faceted_metadata,
                    'descriptive': {
                        'title': title,
                        'short_description': description[:150] + '...' if len(description) > 150 else description,
                        'long_description': description,
                        'bullet_points': bullet_points
                    },
                    'confidence_scores': confidence_scores,
                    'validation_results': validation_results,
                    'status': 'pending_review',
                    'generated_at': datetime.now().isoformat()
                }
                
                # Store metadata
                metadata_id = f"meta_{timestamp}"
                metadata['id'] = metadata_id
                st.session_state.metadata_store[metadata_id] = metadata
                st.session_state.current_metadata = metadata
                st.session_state.current_metadata_id = metadata_id
                
                st.success("Metadata generated successfully!")
                st.rerun()
                
            except Exception as e:
                st.error(f"Error generating metadata: {str(e)}")
                st.exception(e)
    
    # Display metadata for review if available
    if st.session_state.current_metadata:
        display_review_interface(models, st.session_state.current_metadata)

def display_review_interface(models, metadata):
    """Display review and edit interface"""
    st.divider()
    st.header("Review & Edit Metadata")
    
    # Status and confidence
    col1, col2, col3 = st.columns(3)
    with col1:
        status = metadata.get('status', 'pending_review')
        if status == 'approved':
            st.success("✅ Approved")
        elif metadata.get('requires_review', False):
            st.warning("⚠️ Needs Review")
        else:
            st.info("📝 Ready to Approve")
    
    with col2:
        overall_conf = metadata.get('confidence_scores', {}).get('overall', 0)
        st.metric("Overall Confidence", f"{int(overall_conf * 100)}%")
    
    
    # Faceted Metadata Editor
    st.subheader("🏗️ Faceted Metadata")
    
    faceted = metadata.get('faceted', {}).get('faceted_metadata', {})
    hierarchical = faceted.get('hierarchical_facets', {})
    flat = faceted.get('flat_facets', {})
    
    # Hierarchical Facet 1: Item Type
    st.markdown("**Hierarchical Facet 1: Item Type**")
    col1, col2, col3 = st.columns(3)
    
    facet1 = hierarchical.get('facet_1_item_type', {})
    with col1:
        current_item_type = facet1.get('level_1', '')
        item_type = st.selectbox(
            "Level 1: Item Type",
            ["", "Apparel", "Footwear"],
            index=0 if not current_item_type else (1 if current_item_type == 'Apparel' else 2),
            key="item_type_edit"
        )
    
    with col2:
        # Get categories for selected item type using vocabulary_manager
        category_options = []
        if item_type:
            vocab = models['vocabulary_manager'].vocabulary
            category_options = vocab.get('categories', {}).get(item_type, [])
        
        current_category = facet1.get('level_2', '')
        category_index = 0
        if current_category and current_category in category_options:
            category_index = category_options.index(current_category) + 1
        
        category = st.selectbox(
            "Level 2: Category",
            [""] + category_options,
            index=category_index,
            key="category_edit"
        )
    
    with col3:
        # Get product types for selected category using vocabulary_manager
        product_type_options = []
        if item_type and category:
            vocab = models['vocabulary_manager'].vocabulary
            product_type_options = vocab.get('product_types', {}).get(item_type, {}).get(category, [])
        
        current_product_type = facet1.get('level_3', '')
        product_type_index = 0
        if current_product_type and current_product_type in product_type_options:
            product_type_index = product_type_options.index(current_product_type) + 1
        
        product_type = st.selectbox(
            "Level 3: Product Type",
            [""] + product_type_options,
            index=product_type_index,
            key="product_type_edit"
        )
    
    # Hierarchical Facet 2: Style/Usage
    st.markdown("**Hierarchical Facet 2: Style/Usage**")
    col1, col2, col3 = st.columns(3)
    
    facet2 = hierarchical.get('facet_2_style_usage', {})
    vocab = models['vocabulary_manager'].vocabulary
    style_hierarchy = vocab.get('style_hierarchy', {})
    
    with col1:
        style_level1 = st.selectbox(
            "Level 1: Style",
            [""] + list(style_hierarchy.keys()),
            index=0 if not facet2.get('level_1') else (list(style_hierarchy.keys()).index(facet2.get('level_1')) + 1 if facet2.get('level_1') in style_hierarchy else 0),
            key="style_level1_edit"
        )
    
    with col2:
        style_level2_options = []
        if style_level1:
            style_level2_options = list(style_hierarchy.get(style_level1, {}).keys())
        
        style_level2 = st.selectbox(
            "Level 2: Sub-Style",
            [""] + style_level2_options,
            index=0 if not facet2.get('level_2') else (style_level2_options.index(facet2.get('level_2')) + 1 if facet2.get('level_2') in style_level2_options else 0),
            key="style_level2_edit"
        )
    
    with col3:
        style_level3_options = []
        if style_level1 and style_level2:
            style_level3_options = style_hierarchy.get(style_level1, {}).get(style_level2, [])
        
        style_level3 = st.selectbox(
            "Level 3: Specific Style",
            [""] + style_level3_options,
            index=0 if not facet2.get('level_3') else (style_level3_options.index(facet2.get('level_3')) + 1 if facet2.get('level_3') in style_level3_options else 0),
            key="style_level3_edit"
        )
    
    # Flat Facets
    st.subheader("Flat Facets")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # Gender dropdown from vocabulary
        gender_options = models['vocabulary_manager'].get_valid_options('gender')
        current_gender = metadata.get('faceted', {}).get('gender', '')
        gender_index = 0
        if current_gender and current_gender in gender_options:
            gender_index = gender_options.index(current_gender) + 1
        edit_gender = st.selectbox(
            "Gender",
            [""] + gender_options,
            index=gender_index,
            key="edit_gender"
        )
        # Brand - use text input (more flexible for custom brands)
        current_brand = flat.get('brand', '')
        edit_brand = st.text_input(
            "Brand",
            value=current_brand,
            key="edit_brand",
            help="Enter brand name"
        )
        # Size dropdown from vocabulary
        size_options = models['vocabulary_manager'].get_valid_options('size')
        current_size = flat.get('size', '')
        size_index = 0
        if current_size and current_size in size_options:
            size_index = size_options.index(current_size) + 1
        edit_size = st.selectbox(
            "Size",
            [""] + size_options,
            index=size_index,
            key="edit_size"
        )
    
    with col2:
        # Color dropdown from vocabulary
        color_options = models['vocabulary_manager'].get_valid_options('color')
        current_color = flat.get('color', '')
        color_index = 0
        if current_color and current_color in color_options:
            color_index = color_options.index(current_color) + 1
        edit_color = st.selectbox(
            "Color",
            [""] + color_options,
            index=color_index,
            key="edit_color"
        )
        
        # Material dropdown from vocabulary
        material_options = models['vocabulary_manager'].get_valid_options('material')
        current_material = flat.get('material', '')
        material_index = 0
        if current_material and current_material in material_options:
            material_index = material_options.index(current_material) + 1
        edit_material = st.selectbox(
            "Material",
            [""] + material_options,
            index=material_index,
            key="edit_material"
        )
        
        # Pattern dropdown from vocabulary
        pattern_options = models['vocabulary_manager'].get_valid_options('pattern')
        current_pattern = flat.get('pattern', '')
        pattern_index = 0
        if current_pattern and current_pattern in pattern_options:
            pattern_index = pattern_options.index(current_pattern) + 1
        edit_pattern = st.selectbox(
            "Pattern",
            [""] + pattern_options,
            index=pattern_index,
            key="edit_pattern"
        )
    
    # Descriptive Metadata
    st.subheader("Descriptive Metadata")
    desc = metadata.get('descriptive', {})
    
    edit_title = st.text_input("Title", value=desc.get('title', ''), key="edit_title")
    edit_short_desc = st.text_area("Short Description", value=desc.get('short_description', ''), key="edit_short_desc")
    edit_long_desc = st.text_area("Long Description", value=desc.get('long_description', ''), height=150, key="edit_long_desc")
    
    # Bullet points
    st.markdown("**Bullet Points**")
    bullets = desc.get('bullet_points', [])
    bullet_inputs = []
    for i, bullet in enumerate(bullets):
        bullet_inputs.append(st.text_input(f"Bullet {i+1}", value=bullet, key=f"bullet_{i}"))
    
    # Store bullet points in session state for update
    st.session_state['bullet_points'] = [b for b in bullet_inputs if b]
    
    # Save changes button (updates and re-validates)
    if st.button("💾 Save Changes", help="Save your edits and re-validate"):
        updated_metadata = update_metadata_from_ui(metadata, models)
        st.session_state.metadata_store[updated_metadata['id']] = updated_metadata
        st.session_state.current_metadata = updated_metadata
        st.success("Changes saved! Validation updated.")
        st.rerun()
    
    # Validation Status (use current metadata)
    current_meta = st.session_state.current_metadata
    validation = current_meta.get('validation_results', {})
    
    st.subheader("Validation Status")
    all_valid = True
    for field, result in validation.items():
        is_valid = result[0] if isinstance(result, tuple) else result
        if is_valid:
            st.success(f"✅ {field}: Valid")
        else:
            st.error(f"❌ {field}: Invalid")
            all_valid = False
            if isinstance(result, tuple) and len(result) > 2:
                suggestions = result[2]
                if suggestions:
                    st.caption(f"Suggestions: {', '.join(suggestions[:3])}")
    
    # Action buttons
    action_col1, action_col2 = st.columns(2)
    
    with action_col1:
        approve_disabled = not all_valid or current_meta.get('status') == 'approved'
        if st.button("✓ Approve", type="primary", disabled=approve_disabled):
            if not all_valid:
                st.error("Cannot approve: Some fields have validation errors. Please fix them first.")
            else:
                # Update metadata with edited values
                updated_metadata = update_metadata_from_ui(current_meta, models)
                
                # Mark as approved
                updated_metadata['status'] = 'approved'
                updated_metadata['approved_at'] = datetime.now().isoformat()
                
                st.session_state.metadata_store[updated_metadata['id']] = updated_metadata
                st.session_state.current_metadata = updated_metadata
                
                st.success("Metadata approved successfully! You can now download it.")
                st.rerun()
    
    with action_col2:
        if current_meta.get('status') == 'approved':
            download_metadata_json(st.session_state.current_metadata)

def update_metadata_from_ui(metadata, models):
    """Update metadata with values from UI"""
    # Get values from session state
    item_type = st.session_state.get('item_type_edit', '')
    category = st.session_state.get('category_edit', '')
    product_type = st.session_state.get('product_type_edit', '')
    style_level1 = st.session_state.get('style_level1_edit', '')
    style_level2 = st.session_state.get('style_level2_edit', '')
    style_level3 = st.session_state.get('style_level3_edit', '')
    edit_gender = st.session_state.get('edit_gender', '')
    edit_brand = st.session_state.get('edit_brand', '')
    edit_size = st.session_state.get('edit_size', '')
    edit_color = st.session_state.get('edit_color', '')
    edit_material = st.session_state.get('edit_material', '')
    edit_pattern = st.session_state.get('edit_pattern', '')
    edit_title = st.session_state.get('edit_title', '')
    edit_short_desc = st.session_state.get('edit_short_desc', '')
    edit_long_desc = st.session_state.get('edit_long_desc', '')
    bullet_points = st.session_state.get('bullet_points', [])
    
    # Update hierarchical facets
    metadata['faceted']['faceted_metadata']['hierarchical_facets']['facet_1_item_type'] = {
        'level_1': item_type,
        'level_2': category,
        'level_3': product_type,
        'full_path': f"{item_type} > {category} > {product_type}" if all([item_type, category, product_type]) else ""
    }
    
    metadata['faceted']['faceted_metadata']['hierarchical_facets']['facet_2_style_usage'] = {
        'level_1': style_level1,
        'level_2': style_level2,
        'level_3': style_level3,
        'full_path': f"{style_level1} > {style_level2} > {style_level3}" if all([style_level1, style_level2, style_level3]) else ""
    }
    
    # Update flat facets
    metadata['faceted']['faceted_metadata']['flat_facets'].update({
        'brand': edit_brand,
        'size': edit_size,
        'color': edit_color,
        'material': edit_material,
        'pattern': edit_pattern
    })
    
    # Update gender and item_type
    metadata['faceted']['gender'] = edit_gender
    metadata['faceted']['item_type'] = item_type
    
    # Update descriptive
    metadata['descriptive'].update({
        'title': edit_title,
        'short_description': edit_short_desc,
        'long_description': edit_long_desc,
        'bullet_points': bullet_points
    })
    
    # Re-validate
    faceted_data = metadata['faceted'].get('faceted_metadata', {})
    flat_facets = faceted_data.get('flat_facets', {})
    hierarchical = faceted_data.get('hierarchical_facets', {})
    
    validation_results = {}
    validation_results['gender'] = models['vocabulary_manager'].validate('gender', edit_gender)
    validation_results['item_type'] = models['vocabulary_manager'].validate('item_type', item_type)
    validation_results['color'] = models['vocabulary_manager'].validate('color', edit_color)
    validation_results['material'] = models['vocabulary_manager'].validate('material', edit_material)
    
    facet1 = hierarchical.get('facet_1_item_type', {})
    if facet1:
        hierarchy_valid, hierarchy_error = models['vocabulary_manager'].validate_hierarchy(
            facet1.get('level_1', ''),
            facet1.get('level_2', ''),
            facet1.get('level_3', '')
        )
        validation_results['hierarchy'] = (hierarchy_valid, hierarchy_error if not hierarchy_valid else None, None)
    
    metadata['validation_results'] = validation_results
    metadata['updated_at'] = datetime.now().isoformat()
    
    return metadata

def download_metadata_json(metadata):
    """Download clean metadata as JSON (only essential fields)"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"metadata_{timestamp}.json"
    
    # Create clean metadata structure - only essential product metadata
    clean_metadata = {
        "faceted": {
            "item_type": metadata.get('faceted', {}).get('item_type', ''),
            "gender": metadata.get('faceted', {}).get('gender', ''),
            "hierarchical_facets": metadata.get('faceted', {}).get('faceted_metadata', {}).get('hierarchical_facets', {}),
            "flat_facets": {
                "brand": metadata.get('faceted', {}).get('faceted_metadata', {}).get('flat_facets', {}).get('brand', ''),
                "size": metadata.get('faceted', {}).get('faceted_metadata', {}).get('flat_facets', {}).get('size', ''),
                "color": metadata.get('faceted', {}).get('faceted_metadata', {}).get('flat_facets', {}).get('color', ''),
                "material": metadata.get('faceted', {}).get('faceted_metadata', {}).get('flat_facets', {}).get('material', ''),
                "pattern": metadata.get('faceted', {}).get('faceted_metadata', {}).get('flat_facets', {}).get('pattern', '')
            }
        },
        "descriptive": {
            "title": metadata.get('descriptive', {}).get('title', ''),
            "short_description": metadata.get('descriptive', {}).get('short_description', ''),
            "long_description": metadata.get('descriptive', {}).get('long_description', ''),
            "bullet_points": metadata.get('descriptive', {}).get('bullet_points', [])
        }
    }
    
    json_str = json.dumps(clean_metadata, indent=2, ensure_ascii=False)
    
    st.download_button(
        label="📥 Download JSON File",
        data=json_str,
        file_name=filename,
        mime="application/json",
        key="download_json"
    )

def bulk_upload_page(models):
    """Bulk CSV upload and processing"""
    st.header("Bulk Upload")
    
    st.info("Upload a CSV file with product data. Columns: ProductId, Gender, Category, SubCategory, ProductType, Colour, Usage, ProductTitle, Image, ImageURL")
    
    uploaded_csv = st.file_uploader(
        "Upload CSV File",
        type=['csv'],
        help="Upload CSV file with product data"
    )
    
    images_dir = st.text_input("Images Directory (Optional)", help="Path to directory containing product images")
    limit = st.number_input("Limit (Optional)", min_value=1, value=None, help="Process only first N rows")
    
    if st.button("Process CSV", type="primary"):
        if not uploaded_csv:
            st.error("Please upload a CSV file")
            return
        
        with st.spinner("Processing CSV..."):
            try:
                # Save CSV
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                os.makedirs('uploads', exist_ok=True)
                csv_path = f"uploads/{timestamp}_{uploaded_csv.name}"
                
                with open(csv_path, 'wb') as f:
                    f.write(uploaded_csv.getbuffer())
                
                # Process CSV
                results = models['bulk_processor'].process_csv(csv_path, images_dir, limit)
                
                # Store results in session state for display
                st.session_state.bulk_results = results
                
                # Display results
                st.success(f"Processed {len(results)} products")
                
                # Show summary
                successful = sum(1 for r in results if 'error' not in r)
                errors = len(results) - successful
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total", len(results))
                with col2:
                    st.metric("Successful", successful)
                with col3:
                    st.metric("Errors", errors)
                
                # Display detailed results table for validation
                if successful > 0:
                    st.subheader("📊 Detailed Results for Validation")
                    
                    # Create comparison table
                    display_results_table(results)
                
                # Export options
                if successful > 0:
                    st.subheader("Export Results")
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        if st.button("📥 Download as JSON"):
                            download_bulk_json(results)
                    
                    with col2:
                        if st.button("📥 Download Validation CSV"):
                            download_validation_csv(results, models)
                
            except Exception as e:
                st.error(f"Error processing CSV: {str(e)}")
                st.exception(e)

def display_results_table(results):
    """Display detailed results table for manual validation"""
    import pandas as pd
    
    # Prepare data for table
    table_data = []
    for result in results:
        if 'error' in result:
            table_data.append({
                'Product ID': result.get('csv_data', {}).get('ProductId', 'N/A'),
                'Status': '❌ Error',
                'Error': result.get('error', 'Unknown error'),
                'Original Title': result.get('csv_data', {}).get('ProductTitle', 'N/A'),
                'Generated Title': 'N/A',
                'Original Color': result.get('csv_data', {}).get('Colour', 'N/A'),
                'Generated Color': 'N/A',
                'Original Category': result.get('csv_data', {}).get('Category', 'N/A'),
                'Generated Item Type': 'N/A'
            })
        else:
            csv_data = result.get('csv_data', {})
            faceted = result.get('faceted', {}).get('faceted_metadata', {})
            flat = faceted.get('flat_facets', {})
            hierarchical = faceted.get('hierarchical_facets', {})
            facet1 = hierarchical.get('facet_1_item_type', {})
            
            table_data.append({
                'Product ID': csv_data.get('ProductId', 'N/A'),
                'Status': '✅ Success',
                'Error': '',
                'Original Title': csv_data.get('ProductTitle', 'N/A'),
                'Generated Title': result.get('descriptive', {}).get('title', 'N/A'),
                'Original Color': csv_data.get('Colour', 'N/A'),
                'Generated Color': flat.get('color', 'N/A'),
                'Original Category': csv_data.get('Category', 'N/A'),
                'Generated Item Type': facet1.get('level_1', 'N/A'),
                'Generated Category': facet1.get('level_2', 'N/A'),
                'Generated Product Type': facet1.get('level_3', 'N/A'),
                'Generated Gender': result.get('faceted', {}).get('gender', 'N/A'),
                'Original Gender': csv_data.get('Gender', 'N/A')
            })
    
    if table_data:
        df = pd.DataFrame(table_data)
        st.dataframe(df, use_container_width=True, hide_index=True)

def download_bulk_json(results):
    """Download bulk results as JSON"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"bulk_metadata_{timestamp}.json"
    
    json_str = json.dumps(results, indent=2, ensure_ascii=False)
    
    st.download_button(
        label="📥 Download JSON File",
        data=json_str,
        file_name=filename,
        mime="application/json",
        key="download_bulk_json"
    )

def download_bulk_csv(results, models):
    """Download bulk results as CSV"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"bulk_metadata_{timestamp}.csv"
    
    filepath = models['bulk_processor'].export_faceted_metadata(results, 'csv')
    
    with open(filepath, 'rb') as f:
        csv_data = f.read()
    
    st.download_button(
        label="📥 Download CSV File",
        data=csv_data,
        file_name=filename,
        mime="text/csv",
        key="download_bulk_csv"
    )

def download_validation_csv(results, models):
    """Download validation CSV with original vs generated comparison"""
    import csv
    from io import StringIO
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"validation_results_{timestamp}.csv"
    
    # Create CSV in memory
    output = StringIO()
    
    # Define columns for validation
    fieldnames = [
        'ProductId',
        'Status',
        'Original_Title',
        'Generated_Title',
        'Title_Match',
        'Original_Gender',
        'Generated_Gender',
        'Gender_Match',
        'Original_Color',
        'Generated_Color',
        'Color_Match',
        'Original_Category',
        'Generated_Item_Type',
        'Generated_Category',
        'Generated_Product_Type',
        'Category_Match',
        'Original_Usage',
        'Generated_Style_Level1',
        'Generated_Style_Level2',
        'Generated_Style_Level3',
        'Notes'
    ]
    
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    
    for result in results:
        csv_data = result.get('csv_data', {})
        product_id = csv_data.get('ProductId', '')
        
        if 'error' in result:
            writer.writerow({
                'ProductId': product_id,
                'Status': 'ERROR',
                'Notes': result.get('error', 'Unknown error')
            })
        else:
            faceted = result.get('faceted', {}).get('faceted_metadata', {})
            flat = faceted.get('flat_facets', {})
            hierarchical = faceted.get('hierarchical_facets', {})
            facet1 = hierarchical.get('facet_1_item_type', {})
            facet2 = hierarchical.get('facet_2_style_usage', {})
            
            # Get original values
            orig_title = csv_data.get('ProductTitle', '')
            orig_gender = csv_data.get('Gender', '')
            orig_color = csv_data.get('Colour', '')
            orig_category = csv_data.get('Category', '')
            orig_usage = csv_data.get('Usage', '')
            
            # Get generated values
            gen_title = result.get('descriptive', {}).get('title', '')
            gen_gender = result.get('faceted', {}).get('gender', '')
            gen_color = flat.get('color', '')
            gen_item_type = facet1.get('level_1', '')
            gen_category = facet1.get('level_2', '')
            gen_product_type = facet1.get('level_3', '')
            gen_style_l1 = facet2.get('level_1', '')
            gen_style_l2 = facet2.get('level_2', '')
            gen_style_l3 = facet2.get('level_3', '')
            
            # Simple matching (case-insensitive)
            title_match = 'YES' if orig_title.lower() in gen_title.lower() or gen_title.lower() in orig_title.lower() else 'NO'
            gender_match = 'YES' if orig_gender.lower() == gen_gender.lower() else 'NO'
            color_match = 'YES' if orig_color.lower() == gen_color.lower() else 'NO'
            category_match = 'YES' if orig_category.lower() == gen_category.lower() or orig_category.lower() == gen_item_type.lower() else 'NO'
            
            writer.writerow({
                'ProductId': product_id,
                'Status': 'SUCCESS',
                'Original_Title': orig_title,
                'Generated_Title': gen_title,
                'Title_Match': title_match,
                'Original_Gender': orig_gender,
                'Generated_Gender': gen_gender,
                'Gender_Match': gender_match,
                'Original_Color': orig_color,
                'Generated_Color': gen_color,
                'Color_Match': color_match,
                'Original_Category': orig_category,
                'Generated_Item_Type': gen_item_type,
                'Generated_Category': gen_category,
                'Generated_Product_Type': gen_product_type,
                'Category_Match': category_match,
                'Original_Usage': orig_usage,
                'Generated_Style_Level1': gen_style_l1,
                'Generated_Style_Level2': gen_style_l2,
                'Generated_Style_Level3': gen_style_l3,
                'Notes': ''
            })
    
    csv_str = output.getvalue()
    
    st.download_button(
        label="📥 Download Validation CSV",
        data=csv_str,
        file_name=filename,
        mime="text/csv",
        key="download_validation_csv"
    )

if __name__ == "__main__":
    main()

