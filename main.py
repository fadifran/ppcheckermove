"""
PostPros Job Checker - Main Application
A Streamlit application for comparing mailing list data between Accuzip and client files.

Features:
- File upload and processing (CSV/ZIP)
- Dataset comparison with column mapping
- Seed record search
- Postal rate statistics
- IMB (Intelligent Mail Barcode) validation
- Google Street View integration
"""
import streamlit as st
import pandas as pd
import numpy as np
import os
import logging
from typing import Dict, List, Tuple, Optional, Any

# Local imports
from config import (
    COLORS, DEFAULT_COLUMN_MAPPINGS, MATCH_THRESHOLD_HIGH, MATCH_THRESHOLD_LOW,
    FLAT_RATE_PER_RECORD, DEFAULT_NUM_CARDS, MAX_NUM_CARDS,
    ADDRESS_KEYWORDS, ZIP_KEYWORDS, IMB_KEYWORDS, DISPLAY_KEYWORDS
)
from utils.file_processor import process_uploaded_files, FileProcessingError
from utils.data_validator import compare_datasets, find_column_by_keywords, get_default_columns
from utils.imb_validator import validate_imb_column
from utils.streetview_processor import display_streetview_cards
from utils.html_utils import (
    record_counts_html, match_results_html, seed_results_container_html,
    seed_result_html, postal_rate_metrics_html, imb_validation_metrics_html,
    escape
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_css() -> None:
    """Load custom CSS from external file."""
    css_path = '.streamlit/style.css'
    try:
        if os.path.exists(css_path):
            with open(css_path) as f:
                st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
    except Exception as e:
        logger.warning(f"Could not load CSS: {e}")


def render_file_upload_section() -> Tuple[Optional[List], Optional[List]]:
    """
    Render the file upload section with two columns.
    
    Returns:
        Tuple of (source_files, compare_files) or (None, None) if not uploaded
    """
    col1, col2 = st.columns(2)
    
    with col1:
        st.header("🗂️ Accuzip File(s)")
        source_files = st.file_uploader(
            "Upload Accuzip CSV, or ZIP file(s)",
            accept_multiple_files=True,
            type=['csv', 'zip'],
            key="accuzip_uploader"
        )
    
    with col2:
        st.header("👨‍💼 Client File(s)")
        compare_files = st.file_uploader(
            "Upload Client CSV, or ZIP file(s)",
            accept_multiple_files=True,
            type=['csv', 'zip'],
            key="client_uploader"
        )
    
    return source_files, compare_files


def render_dataset_info(df1: pd.DataFrame, df2: pd.DataFrame) -> None:
    """
    Render dataset information section.
    
    Args:
        df1: Accuzip DataFrame
        df2: Client DataFrame
    """
    # Display record counts
    st.markdown(record_counts_html(len(df1), len(df2)), unsafe_allow_html=True)
    
    # Dataset details in expander
    with st.expander("📊 Dataset Information", expanded=False):
        col1, col2 = st.columns(2)
        with col1:
            st.write("**Accuzip File(s):**")
            st.write("Columns:", ", ".join(df1.columns))
        with col2:
            st.write("**Client File(s):**")
            st.write("Columns:", ", ".join(df2.columns))


def render_column_mapping(df1: pd.DataFrame, df2: pd.DataFrame) -> Dict[str, str]:
    """
    Render column mapping configuration section.
    
    Args:
        df1: Accuzip DataFrame
        df2: Client DataFrame
        
    Returns:
        Dictionary mapping Accuzip columns to Client columns
    """
    mapping = {}
    
    with st.expander("⚙️ Configure Column Mapping", expanded=False):
        st.write("Select the columns to compare between datasets:")
        
        cols = st.columns(2)
        
        with cols[0]:
            st.subheader("Accuzip Columns")
            # Find default columns that exist
            default_source_cols = [
                col for col in DEFAULT_COLUMN_MAPPINGS.keys() 
                if col in df1.columns
            ]
            source_cols = st.multiselect(
                "Select Accuzip columns",
                df1.columns,
                default=default_source_cols,
                key="source_cols_select"
            )
        
        with cols[1]:
            st.subheader("Client Columns")
            if source_cols:
                # Find corresponding default target columns
                default_target_cols = [
                    DEFAULT_COLUMN_MAPPINGS[src] 
                    for src in source_cols
                    if src in DEFAULT_COLUMN_MAPPINGS 
                    and DEFAULT_COLUMN_MAPPINGS[src] in df2.columns
                ]
                compare_cols = st.multiselect(
                    "Select matching Client columns",
                    df2.columns,
                    default=default_target_cols,
                    max_selections=len(source_cols),
                    key="compare_cols_select"
                )
                
                if len(source_cols) == len(compare_cols):
                    mapping = dict(zip(source_cols, compare_cols))
    
    return mapping


def render_comparison_results(comparison_results: Dict[str, Any]) -> None:
    """
    Render the comparison results section.
    
    Args:
        comparison_results: Dictionary with comparison results
    """
    st.header("Match Results")
    
    total_records = comparison_results['total_records']
    matching_records = comparison_results['matching_records']
    match_percentage = (matching_records / total_records * 100) if total_records > 0 else 0
    
    # Display metrics
    st.markdown(
        match_results_html(total_records, matching_records, match_percentage),
        unsafe_allow_html=True
    )
    
    # Display mismatches table if any
    if not comparison_results['mismatches'].empty:
        st.dataframe(
            comparison_results['mismatches'],
            use_container_width=True,
            hide_index=True
        )


def render_seed_search_section(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """
    Render the seed record search section.
    
    Args:
        df: DataFrame to search
        
    Returns:
        List of search results
    """
    search_results = []
    
    with st.expander("⚙️ Configure Seed Search", expanded=False):
        # Default search configurations
        default_columns = ["first", "first", "last", None]
        default_terms = ["Post", "Current", "Job", ""]
        
        for i in range(4):
            cols = st.columns([1, 1])
            
            with cols[0]:
                # Get default index
                default_idx = 0
                if default_columns[i] and default_columns[i] in df.columns:
                    default_idx = df.columns.get_loc(default_columns[i])
                
                selected_col = st.selectbox(
                    f"Field {i+1}",
                    options=df.columns,
                    label_visibility="hidden",
                    index=default_idx,
                    key=f"seed_col_{i}"
                )
            
            with cols[1]:
                search_term = st.text_input(
                    f"Search term {i+1}",
                    value=default_terms[i],
                    label_visibility="hidden",
                    key=f"seed_term_{i}"
                )
                
                if selected_col and search_term:
                    # Perform search
                    filtered_df = df[
                        df[selected_col].astype(str).str.contains(
                            search_term, case=False, na=False
                        )
                    ]
                    search_results.append({
                        'column': selected_col,
                        'term': search_term,
                        'count': len(filtered_df)
                    })
        
        # Postal rate column selection
        st.markdown("#### Postal Rate Column")
        rate_col_idx = next(
            (i for i, col in enumerate(df.columns) if 'rate_' in col.lower()), 
            0
        )
        rate_col = st.selectbox(
            "Rate Column",
            options=df.columns,
            label_visibility="hidden",
            index=rate_col_idx,
            key="postal_rate_col"
        )
        
        # Store rate column in session state
        st.session_state.rate_col = rate_col
    
    return search_results


def render_seed_results(search_results: List[Dict[str, Any]]) -> None:
    """
    Render seed search results.
    
    Args:
        search_results: List of search result dictionaries
    """
    if not search_results:
        return
    
    # CSS for seed results (loaded from style.css, but inline fallback)
    st.markdown("""
    <style>
    .seed-container { background-color: white; border-radius: 8px; padding: 5px 0px 5px 10px;
                      box-shadow: 0 2px 4px rgba(0,0,0,0.1); margin-bottom: 10px; }
    .seed-title { color: #000; font-size: 1.2em; font-weight: bold; margin-bottom: 15px;
                  display: flex; align-items: center; gap: 8px; }
    .seed-record { padding: 12px; border-radius: 6px; margin-bottom: 10px;
                   display: flex; align-items: center; gap: 10px; }
    .seed-found { background-color: #e6f4ea; border: 1px solid #137333; }
    .seed-not-found { background-color: #fce8e6; border: 1px solid #c5221f; }
    .seed-count { font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)
    
    # Build results HTML
    html = seed_results_container_html()
    for result in search_results:
        html += seed_result_html(result['column'], result['term'], result['count'])
    html += "</div>"
    
    st.markdown(html, unsafe_allow_html=True)


def render_postal_rate_statistics(df: pd.DataFrame, rate_col: str) -> None:
    """
    Render postal rate statistics section.
    
    Args:
        df: DataFrame containing rate data
        rate_col: Column name containing postal rates
    """
    if not rate_col:
        return
    
    try:
        # CSS for metrics
        st.markdown("""
        <style>
        .metric-container { background-color: white; border-radius: 8px; padding: 5px 0px 5px 10px;
                           box-shadow: 0 2px 4px rgba(0,0,0,0.1); margin: 35px 0 10px 0; }
        .metric-title { color: #000; font-size: 1.2em; font-weight: bold; margin-bottom: 15px;
                       display: flex; align-items: center; gap: 8px; }
        .metric-grid { display: flex; flex-wrap: wrap; gap: 15px; justify-content: space-between; }
        .metric-item { flex: 1; min-width: 150px; padding: 12px; background-color: #f8f9fa;
                      border-radius: 6px; text-align: center; }
        .metric-value { font-size: 1.8em; font-weight: bold; margin: 5px 0; }
        .metric-label { color: #5f6368; font-size: 0.9em; }
        </style>
        """, unsafe_allow_html=True)
        
        # Calculate statistics
        rate_data = pd.to_numeric(df[rate_col], errors='coerce')
        total_sum = rate_data.sum()
        total_records = rate_data.count()
        flat_rate = total_records * FLAT_RATE_PER_RECORD
        postage = flat_rate - total_sum
        avg_rate = rate_data.mean()
        
        # Display container
        st.markdown("""
        <div class="metric-container">
            <div class="metric-title">
                <span>📮 Postal Rate Statistics</span>
            </div>
        """, unsafe_allow_html=True)
        
        # Display metrics
        st.markdown(
            postal_rate_metrics_html(avg_rate, rate_data.min(), rate_data.max(), postage),
            unsafe_allow_html=True
        )
        
    except Exception as e:
        st.warning(f"Unable to calculate rate statistics: {str(e)}")
        logger.exception("Error calculating postal rate statistics")


def render_imb_validation_section(df1: pd.DataFrame, df2: pd.DataFrame) -> None:
    """
    Render IMB validation section.
    
    Args:
        df1: Accuzip DataFrame
        df2: Client DataFrame
    """
    st.markdown("---")
    
    # CSS for IMB section
    st.markdown("""
    <style>
    .imb-container { background-color: white; border-radius: 8px; padding: 5px 0px 5px 10px;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1); margin: 15px 0 10px 0; }
    .imb-title { color: #000; font-size: 1.2em; font-weight: bold; margin-bottom: 15px;
                display: flex; align-items: center; gap: 8px; }
    .imb-results-container { background-color: white; border-radius: 8px; padding: 5px 0px 5px 10px;
                            box-shadow: 0 2px 4px rgba(0,0,0,0.1); margin: 15px 0; }
    .imb-metric-grid { display: flex; flex-wrap: wrap; gap: 15px; justify-content: space-between;
                      margin-bottom: 15px; }
    .imb-metric-item { flex: 1; min-width: 150px; padding: 12px; background-color: #f8f9fa;
                      border-radius: 6px; text-align: center; }
    .imb-metric-value { font-size: 1.8em; font-weight: bold; margin: 5px 0; }
    .imb-metric-label { color: #5f6368; font-size: 0.9em; }
    </style>
    """, unsafe_allow_html=True)
    
    # Container header
    st.markdown("""
    <div class="imb-container">
        <div class="imb-title">
            <span>💌 IMB Code Validation</span>
        </div>
    """, unsafe_allow_html=True)
    
    # Configuration expander
    with st.expander("⚙️ Configure IMB Validation", expanded=False):
        # Initialize session state
        if 'imb_validation_results' not in st.session_state:
            st.session_state.imb_validation_results = None
        
        cols = st.columns(2)
        
        with cols[0]:
            dataset_choice = st.radio(
                "Select Dataset",
                ["Accuzip Files", "Client Files"],
                index=0,
                key="imb_dataset_choice"
            )
            active_df = df1 if dataset_choice == "Accuzip Files" else df2
            
            # Find default IMB column
            imb_cols = get_default_columns(active_df, 'imb')
            if 'imbarcode' in active_df.columns:
                default_imb_idx = active_df.columns.get_loc('imbarcode')
            elif imb_cols:
                default_imb_idx = active_df.columns.get_loc(imb_cols[0])
            else:
                default_imb_idx = 0
            
            imb_col = st.selectbox(
                "Select IMB Code Column",
                options=active_df.columns,
                index=default_imb_idx,
                key="imb_col_select"
            )
        
        with cols[1]:
            # Find default ZIP column
            zip_cols = get_default_columns(active_df, 'zip')
            default_zip_idx = active_df.columns.get_loc(zip_cols[0]) if zip_cols else 0
            
            zip_col = st.selectbox(
                "Select ZIP Code Column",
                options=active_df.columns,
                index=default_zip_idx,
                key="imb_zip_col_select"
            )
        
        # Store selections in session state
        st.session_state.imb_col = imb_col
        st.session_state.zip_col = zip_col
        st.session_state.imb_dataset_choice = dataset_choice
    
    # Close container
    st.markdown("</div>", unsafe_allow_html=True)
    
    # Validate button
    if st.button("Validate IMB Codes", type="primary", key="validate_imb_btn"):
        with st.spinner("Validating IMB codes..."):
            active_df = df1 if st.session_state.imb_dataset_choice == "Accuzip Files" else df2
            results = validate_imb_column(
                active_df, 
                st.session_state.imb_col, 
                st.session_state.zip_col
            )
            st.session_state.imb_validation_results = results
    
    # Display results if available
    if st.session_state.get('imb_validation_results'):
        render_imb_validation_results(
            st.session_state.imb_validation_results,
            df1 if st.session_state.get('imb_dataset_choice') == "Accuzip Files" else df2
        )


def render_imb_validation_results(results: Dict[str, Any], active_df: pd.DataFrame) -> None:
    """
    Render IMB validation results.
    
    Args:
        results: Validation results dictionary
        active_df: The active DataFrame being validated
    """
    if not results.get('success'):
        st.error(f"Error during IMB validation: {results.get('error', 'Unknown error')}")
        return
    
    # Results container
    st.markdown("""
    <div class="imb-results-container">
        <div class="imb-results-title" style="color: #000; font-size: 1.2em; font-weight: bold; 
                                              margin-bottom: 15px; display: flex; align-items: center; gap: 8px;">
            <span>📊 IMB Validation Results</span>
        </div>
    """, unsafe_allow_html=True)
    
    # Display metrics
    st.markdown(
        imb_validation_metrics_html(
            results['total_records'],
            results['valid_imbs'],
            results['valid_percent'],
            results['matching_zips'],
            results['match_percent']
        ),
        unsafe_allow_html=True
    )
    
    # Display mismatches if any
    if 'zip_match' in results['results_df'].columns:
        mismatched_df = results['results_df'][results['results_df']['zip_match'] == False].copy()
        
        if len(mismatched_df) > 0:
            # Truncate IMB codes for display
            imb_col = st.session_state.get('imb_col', '')
            if imb_col and imb_col in mismatched_df.columns:
                mismatched_df[imb_col] = mismatched_df[imb_col].astype(str).apply(
                    lambda x: x[:15] + "..." if len(x) > 15 else x
                )
            
            # Add CSV ZIP column for comparison
            zip_col = st.session_state.get('zip_col', '')
            if zip_col and zip_col in active_df.columns:
                mismatched_df['csv_zip'] = active_df.loc[mismatched_df.index, zip_col].astype(str)
            
            st.markdown("""
            <div style="background-color: white; padding: 10px; border-radius: 6px; 
                        margin: 15px 0; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                <span style="font-size: 1.1em; font-weight: bold;">⚠️ Mismatched ZIP Codes</span>
            </div>
            """, unsafe_allow_html=True)
            
            st.dataframe(mismatched_df, use_container_width=True)
        else:
            st.success("No mismatched ZIP codes found! All decoded IMB ZIP codes match the data.")
    else:
        st.info("No ZIP code column was selected for comparison.")
        st.dataframe(results['results_df'].head(10), use_container_width=True)


def render_streetview_section(df1: pd.DataFrame, df2: pd.DataFrame) -> None:
    """
    Render Google Street View section.
    
    Args:
        df1: Accuzip DataFrame
        df2: Client DataFrame
    """
    st.markdown("---")
    
    # Container header
    st.markdown("""
    <div class="streetview-container" style="background-color: white; border-radius: 8px; 
                padding: 5px 0px 5px 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); margin: 15px 0;">
        <div class="streetview-title" style="color: #000; font-size: 1.2em; font-weight: bold; 
                                            margin-bottom: 15px; display: flex; align-items: center; gap: 8px;">
            <span>📡 Google Street View Images</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Get API key from environment
    if 'google_api_key' not in st.session_state:
        st.session_state.google_api_key = os.environ.get('GOOGLE_MAPS_API_KEY', "")
    
    # Configuration expander
    with st.expander("⚙️ Configure Street View Settings", expanded=False):
        streetview_dataset = st.radio(
            "Select Dataset for Street View",
            ["Accuzip Files", "Client Files"],
            index=0,
            key="streetview_dataset"
        )
        
        sv_active_df = df1 if streetview_dataset == "Accuzip Files" else df2
        
        col1, col2 = st.columns(2)
        
        with col1:
            addr_cols = get_default_columns(sv_active_df, 'address')
            default_addr_idx = sv_active_df.columns.get_loc(addr_cols[0]) if addr_cols else 0
            
            address_col = st.selectbox(
                "Address Column",
                options=sv_active_df.columns,
                index=default_addr_idx,
                key="streetview_address_col"
            )
        
        with col2:
            zip_cols = get_default_columns(sv_active_df, 'zip')
            default_zip_idx = sv_active_df.columns.get_loc(zip_cols[0]) if zip_cols else 0
            
            zip_col = st.selectbox(
                "ZIP Code Column",
                options=sv_active_df.columns,
                index=default_zip_idx,
                key="streetview_zip_col"
            )
        
        # Additional display columns
        display_default = get_default_columns(sv_active_df, 'display')[:4]
        display_cols = st.multiselect(
            "Select columns to display on Street View cards",
            options=sv_active_df.columns,
            default=display_default,
            key="streetview_display_cols"
        )
        
        num_cards = st.slider(
            "Number of Street View cards to display",
            min_value=1,
            max_value=MAX_NUM_CARDS,
            value=DEFAULT_NUM_CARDS,
            key="streetview_num_cards"
        )
        
        # Save config to session state
        st.session_state.streetview_config = {
            'dataset': streetview_dataset,
            'address_col': address_col,
            'zip_col': zip_col,
            'display_cols': display_cols,
            'num_cards': num_cards
        }
    
    # Generate button
    if st.session_state.google_api_key:
        if st.button("Generate Street View Images", type="primary", key="generate_streetview"):
            with st.spinner("Fetching Street View images..."):
                config = st.session_state.streetview_config
                active_df = df1 if config['dataset'] == "Accuzip Files" else df2
                
                display_streetview_cards(
                    df=active_df,
                    address_col=config['address_col'],
                    zip_col=config['zip_col'],
                    display_cols=config['display_cols'],
                    api_key=st.session_state.google_api_key,
                    num_cards=config['num_cards']
                )
    else:
        st.warning("""
        The GOOGLE_MAPS_API_KEY is required to display street view images.
        
        Please add it to your environment variables or Replit Secrets.
        """)


def main() -> None:
    """Main application entry point."""
    # Page configuration
    st.set_page_config(
        page_title="Post Pros Job Checker",
        page_icon="📬",
        layout="centered"
    )
    
    # Load custom CSS
    load_css()
    
    # Header
    st.title("💼 Post Pros Job Checker")
    st.markdown("For Post Pros Internal Use Only.")
    
    # File upload section
    source_files, compare_files = render_file_upload_section()
    
    # Process files if both are uploaded
    if source_files and compare_files:
        try:
            # Process files
            df1, processed_files1 = process_uploaded_files(source_files)
            df2, processed_files2 = process_uploaded_files(compare_files)
            
            st.success(f"""
            Files processed successfully!
            - Processed {processed_files1} Accuzip file(s)
            - Processed {processed_files2} Client file(s)
            """)
            
            # Store in session state
            st.session_state.df1 = df1
            st.session_state.df2 = df2
            
            # Render sections
            render_dataset_info(df1, df2)
            
            # Column mapping and comparison
            mapping = render_column_mapping(df1, df2)
            
            if mapping:
                comparison_results = compare_datasets(df1, df2, mapping)
                st.session_state.comparison_results = comparison_results
                render_comparison_results(comparison_results)
            
            # Data analysis section
            st.markdown("---")
            st.header("Data Analysis")
            
            # Seed search
            search_results = render_seed_search_section(df1)
            render_seed_results(search_results)
            
            # Postal rate statistics
            if 'rate_col' in st.session_state:
                render_postal_rate_statistics(df1, st.session_state.rate_col)
            
            # IMB validation
            render_imb_validation_section(df1, df2)
            
            # Street View
            render_streetview_section(df1, df2)
            
        except FileProcessingError as e:
            st.error(str(e))
        except Exception as e:
            st.error(f"Error processing files: {str(e)}")
            logger.exception("Unexpected error in main")


if __name__ == "__main__":
    main()
