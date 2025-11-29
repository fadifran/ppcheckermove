"""
Data validation utilities for comparing Accuzip and Client datasets.
"""
import pandas as pd
import numpy as np
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)


def compare_datasets(df1: pd.DataFrame, df2: pd.DataFrame, 
                     column_mapping: Dict[str, str]) -> Dict[str, Any]:
    """
    Compare datasets to ensure all Accuzip records exist in client files.
    Uses vectorized operations for better performance.
    
    Args:
        df1: Accuzip DataFrame
        df2: Client DataFrame
        column_mapping: Dictionary mapping Accuzip columns to Client columns
        
    Returns:
        Dictionary containing comparison results with keys:
        - total_records: Total records in Accuzip file
        - matching_records: Records that exist in both files
        - missing_records: Records missing from client file
        - mismatches: DataFrame of missing records (limited for display)
    """
    from config import MAX_MISMATCH_DISPLAY
    
    logger.info(f"Comparing datasets: {len(df1)} Accuzip records, {len(df2)} Client records")
    logger.debug(f"Column mapping: {column_mapping}")
    
    # Create copies to avoid modifying original dataframes
    df1_comp = df1.copy()
    df2_comp = df2.copy()
    
    # Add suffixes to all columns for clarity
    df1_comp.columns = [f"{col} (Accuzip)" for col in df1_comp.columns]
    df2_comp.columns = [f"{col} (Client)" for col in df2_comp.columns]
    
    # Get mapped column names with suffixes
    source_cols = [f"{col} (Accuzip)" for col in column_mapping.keys()]
    target_cols = [f"{col} (Client)" for col in column_mapping.values()]
    
    # Select only mapped columns for comparison
    df1_match = df1_comp[source_cols].copy()
    df2_match = df2_comp[target_cols].copy()
    
    # Convert all comparison columns to string type for consistent matching
    # Using vectorized operations instead of iterating
    for col in df1_match.columns:
        df1_match[col] = df1_match[col].astype(str).str.strip().str.lower()
    for col in df2_match.columns:
        df2_match[col] = df2_match[col].astype(str).str.strip().str.lower()
    
    # Create composite match keys using vectorized string concatenation
    df1_match['_match_key'] = df1_match.apply(
        lambda row: '_'.join(row.values.astype(str)), 
        axis=1
    )
    df2_match['_match_key'] = df2_match.apply(
        lambda row: '_'.join(row.values.astype(str)), 
        axis=1
    )
    
    # Find Accuzip records not in client files using set operations (faster)
    client_keys = set(df2_match['_match_key'].values)
    missing_mask = ~df1_match['_match_key'].isin(client_keys)
    
    # Get indices of missing records
    missing_indices = df1_match[missing_mask].index
    
    # Get full records for missing entries (limited for display)
    missing_records = df1_comp.loc[missing_indices].head(MAX_MISMATCH_DISPLAY).copy()
    
    if not missing_records.empty:
        # Add record number column (1-indexed for user-friendliness)
        missing_records.insert(0, 'Record #', missing_records.index + 1)
        missing_records['Status'] = 'Missing in Client Files'
    
    # Calculate statistics
    total_records = len(df1_comp)
    missing_count = len(missing_indices)
    matching_records = total_records - missing_count
    
    logger.info(f"Comparison complete: {matching_records}/{total_records} records matched "
                f"({matching_records/total_records*100:.1f}%)")
    
    return {
        'total_records': total_records,
        'matching_records': matching_records,
        'missing_records': missing_count,
        'mismatches': missing_records
    }


def find_column_by_keywords(df: pd.DataFrame, keywords: list, 
                            default_index: int = 0) -> int:
    """
    Find a column index by searching for keywords in column names.
    
    Args:
        df: DataFrame to search
        keywords: List of keywords to match (case-insensitive)
        default_index: Index to return if no match found
        
    Returns:
        Column index
    """
    for col in df.columns:
        col_lower = col.lower()
        if any(kw.lower() in col_lower for kw in keywords):
            return df.columns.get_loc(col)
    return default_index


def get_default_columns(df: pd.DataFrame, column_type: str) -> list:
    """
    Get default columns based on column type.
    
    Args:
        df: DataFrame to search
        column_type: Type of columns to find ('address', 'zip', 'imb', 'display')
        
    Returns:
        List of matching column names
    """
    from config import ADDRESS_KEYWORDS, ZIP_KEYWORDS, IMB_KEYWORDS, DISPLAY_KEYWORDS
    
    keyword_map = {
        'address': ADDRESS_KEYWORDS,
        'zip': ZIP_KEYWORDS,
        'imb': IMB_KEYWORDS,
        'display': DISPLAY_KEYWORDS
    }
    
    keywords = keyword_map.get(column_type, [])
    matches = []
    
    for col in df.columns:
        col_lower = col.lower()
        if any(kw.lower() in col_lower for kw in keywords):
            matches.append(col)
    
    return matches
