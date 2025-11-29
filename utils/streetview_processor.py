"""
Google Street View integration for address verification.
Displays Street View images in card format.
"""
import streamlit as st
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional
import urllib.parse
import logging

logger = logging.getLogger(__name__)


def get_streetview_url(address: str, zip_code: str, api_key: str, 
                       size: str = "400x300") -> Optional[str]:
    """
    Generate a Google Street View image URL.
    
    Note: This exposes the API key in the client-side HTML. For production,
    consider implementing a server-side proxy.
    
    Args:
        address: Street address
        zip_code: ZIP code
        api_key: Google API Key
        size: Image size (width x height)
        
    Returns:
        URL to the Google Street View image or None if error
    """
    try:
        # Format the location
        location = f"{address}, {zip_code}"
        
        # Construct the Street View API URL
        base_url = "https://maps.googleapis.com/maps/api/streetview"
        params = {
            "size": size,
            "location": location,
            "key": api_key
        }
        
        # URL-encode parameters
        param_string = "&".join([
            f"{k}={urllib.parse.quote(str(v))}" 
            for k, v in params.items()
        ])
        
        return f"{base_url}?{param_string}"
        
    except Exception as e:
        logger.error(f"Error generating Street View URL: {e}")
        return None


def get_random_sample_indices(total_rows: int, num_samples: int) -> List[int]:
    """
    Get random sample indices from a range.
    
    Args:
        total_rows: Total number of rows available
        num_samples: Number of samples to return
        
    Returns:
        List of sorted random indices
    """
    if total_rows <= num_samples:
        return list(range(total_rows))
    
    # Use NumPy's random choice without fixed seed for new samples each time
    return sorted(np.random.choice(total_rows, size=num_samples, replace=False).tolist())


def display_streetview_cards(df: pd.DataFrame, 
                             address_col: str, 
                             zip_col: str, 
                             display_cols: List[str],
                             api_key: str,
                             num_cards: int = 5) -> None:
    """
    Display Street View image cards with relevant data.
    
    Args:
        df: DataFrame containing the data
        address_col: Column name containing the address
        zip_col: Column name containing the ZIP code
        display_cols: List of column names to display in the card
        api_key: Google API Key
        num_cards: Number of cards to display
    """
    from config import CARDS_PER_ROW
    from utils.html_utils import streetview_card_html, escape
    
    # Validate API key
    if not api_key:
        st.warning("Google Street View API key is required. Please configure it in settings.")
        return
    
    if df.empty:
        st.warning("No data available to display.")
        return
    
    # Validate columns exist
    if address_col not in df.columns:
        st.error(f"Address column '{address_col}' not found in data.")
        return
    
    if zip_col not in df.columns:
        st.error(f"ZIP code column '{zip_col}' not found in data.")
        return
    
    # Get random sample indices
    total_rows = len(df)
    sample_indices = get_random_sample_indices(total_rows, num_cards)
    rows_to_display = len(sample_indices)
    
    logger.info(f"Displaying {rows_to_display} Street View cards from {total_rows} records")
    
    # Create cards in rows
    for i in range(0, rows_to_display, CARDS_PER_ROW):
        cols = st.columns(min(CARDS_PER_ROW, rows_to_display - i))
        
        for j in range(min(CARDS_PER_ROW, rows_to_display - i)):
            card_idx = i + j
            
            if card_idx >= len(sample_indices):
                break
            
            with cols[j]:
                # Get the actual row data
                idx = sample_indices[card_idx]
                row_data = df.iloc[idx]
                
                # Extract address and ZIP
                address = str(row_data.get(address_col, "")).strip()
                zip_code = str(row_data.get(zip_col, "")).strip()
                
                # Truncate for display (FIXED: was using wrong variable)
                display_address = (address[:14] + "...") if len(address) > 14 else address
                display_zip = zip_code[:5] if len(zip_code) > 5 else zip_code
                
                # Get Street View image URL
                image_url = get_streetview_url(address, display_zip, api_key)
                
                if image_url:
                    # Build display data dictionary
                    display_data = {}
                    for col in display_cols:
                        if col in row_data.index:
                            display_data[col] = row_data[col]
                    
                    # Generate and display card HTML
                    card_html = streetview_card_html(
                        record_num=idx + 1,
                        image_url=image_url,
                        address=display_address,
                        zip_code=display_zip,
                        display_data=display_data
                    )
                    
                    st.markdown(card_html, unsafe_allow_html=True)
                else:
                    st.error(f"Could not load Street View for record #{idx + 1}")


def validate_api_key(api_key: str) -> bool:
    """
    Validate that an API key is provided and has reasonable format.
    
    Args:
        api_key: The API key to validate
        
    Returns:
        True if key appears valid, False otherwise
    """
    if not api_key:
        return False
    
    # Basic format check (Google API keys are typically 39 characters)
    if len(api_key) < 30:
        return False
    
    return True
