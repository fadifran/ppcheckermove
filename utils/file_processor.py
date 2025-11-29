"""
File processing utilities for CSV and ZIP files.
Handles file upload, validation, and merging of dataframes.
"""
import pandas as pd
import zipfile
import io
import logging
from typing import List, Tuple, Optional
import streamlit as st

# Configure logging
logger = logging.getLogger(__name__)


class FileProcessingError(Exception):
    """Custom exception for file processing errors."""
    pass


def write_debug_info(message: str) -> None:
    """
    Write debug information to the debug container if available.
    
    Args:
        message: Debug message to write
    """
    logger.debug(message)
    try:
        if 'debug_container' in st.session_state and st.session_state.debug_container is not None:
            st.session_state.debug_container.write(message)
    except Exception:
        # Silently fail if debug container is not available
        pass


def read_csv_file(file_obj) -> pd.DataFrame:
    """
    Read a CSV file object and return a pandas DataFrame.
    
    Args:
        file_obj: File-like object containing CSV data
        
    Returns:
        Pandas DataFrame with the CSV contents
        
    Raises:
        FileProcessingError: If the file cannot be read or is invalid
    """
    file_name = getattr(file_obj, 'name', 'unknown')
    
    try:
        write_debug_info(f"Processing CSV file: {file_name}")
        
        # Try to read the CSV file
        df = pd.read_csv(file_obj)
        
        # Validate the DataFrame
        if df.empty:
            raise FileProcessingError(f"The CSV file '{file_name}' is empty")
        
        write_debug_info(f"Successfully read CSV file with {len(df)} rows")
        return df
        
    except pd.errors.EmptyDataError:
        error_msg = f"The file '{file_name}' is empty"
        logger.error(error_msg)
        st.error(error_msg)
        raise FileProcessingError(error_msg)
        
    except pd.errors.ParserError as e:
        error_msg = f"Error parsing CSV file '{file_name}': File may be corrupted or not a valid CSV"
        logger.error(f"{error_msg}: {e}")
        st.error(error_msg)
        raise FileProcessingError(error_msg)
        
    except UnicodeDecodeError as e:
        error_msg = f"Encoding error in file '{file_name}': Try saving the file as UTF-8"
        logger.error(f"{error_msg}: {e}")
        st.error(error_msg)
        raise FileProcessingError(error_msg)
        
    except Exception as e:
        error_msg = f"Error reading CSV file '{file_name}': {str(e)}"
        logger.error(error_msg)
        st.error(error_msg)
        raise FileProcessingError(error_msg)


def process_zip_file(zip_file) -> List[pd.DataFrame]:
    """
    Extract and process CSV files from a ZIP archive.
    
    Args:
        zip_file: File-like object containing ZIP archive
        
    Returns:
        List of DataFrames extracted from CSV files in the ZIP
        
    Raises:
        FileProcessingError: If the ZIP file is invalid or contains no valid CSVs
    """
    dataframes = []
    file_name = getattr(zip_file, 'name', 'unknown')
    
    try:
        write_debug_info(f"Processing ZIP file: {file_name}")
        
        with zipfile.ZipFile(zip_file) as z:
            # List all files in the ZIP
            all_files = z.namelist()
            write_debug_info(f"Found {len(all_files)} files in ZIP archive")
            
            # Filter CSV files (excluding hidden files and macOS metadata)
            csv_files = [
                f for f in all_files 
                if f.lower().endswith('.csv') 
                and not f.startswith('__MACOSX')
                and not f.startswith('.')
            ]
            
            if not csv_files:
                raise FileProcessingError(f"No CSV files found in ZIP file '{file_name}'")
            
            write_debug_info(f"Found {len(csv_files)} CSV files in ZIP archive")
            
            for filename in csv_files:
                try:
                    write_debug_info(f"Extracting and processing: {filename}")
                    with z.open(filename) as f:
                        df = pd.read_csv(io.BytesIO(f.read()))
                        if not df.empty:
                            dataframes.append(df)
                            write_debug_info(f"Successfully processed {filename} with {len(df)} rows")
                        else:
                            st.warning(f"Skipping empty CSV file: {filename}")
                except Exception as e:
                    st.warning(f"Error processing {filename} in ZIP: {str(e)}")
                    logger.warning(f"Error processing {filename}: {e}")
                    continue
                    
    except zipfile.BadZipFile:
        error_msg = f"Invalid ZIP file: {file_name}"
        logger.error(error_msg)
        st.error(error_msg)
        raise FileProcessingError(error_msg)
        
    except Exception as e:
        error_msg = f"Error processing ZIP file '{file_name}': {str(e)}"
        logger.error(error_msg)
        st.error(error_msg)
        raise FileProcessingError(error_msg)
    
    if not dataframes:
        raise FileProcessingError(f"No valid data found in ZIP file '{file_name}'")
    
    return dataframes


def process_uploaded_files(files) -> Tuple[pd.DataFrame, int]:
    """
    Process uploaded files (CSV or ZIP) and return a merged DataFrame.
    
    Args:
        files: List of uploaded file objects
        
    Returns:
        Tuple of (merged DataFrame, count of processed files)
        
    Raises:
        FileProcessingError: If no valid files could be processed
    """
    if not files:
        raise FileProcessingError("No files were uploaded. Please upload CSV files or ZIP files containing CSVs.")
    
    dataframes = []
    processed_files = 0
    
    with st.spinner("Processing uploaded files..."):
        # Create a debug expander
        with st.expander("📋 View File Processing Details", expanded=False) as debug_expander:
            st.session_state.debug_container = debug_expander
            write_debug_info("Starting file processing...")
            
            for uploaded_file in files:
                try:
                    file_name = uploaded_file.name.lower()
                    
                    # Validate file extension
                    if not (file_name.endswith('.csv') or file_name.endswith('.zip')):
                        st.warning(f"Skipping unsupported file: {uploaded_file.name} (Only .csv and .zip files are supported)")
                        continue
                    
                    # Process based on file type
                    if file_name.endswith('.zip'):
                        dfs = process_zip_file(uploaded_file)
                        dataframes.extend(dfs)
                        processed_files += len(dfs)
                    else:
                        df = read_csv_file(uploaded_file)
                        dataframes.append(df)
                        processed_files += 1
                        
                except FileProcessingError:
                    # Already logged and displayed, continue with next file
                    continue
                except Exception as e:
                    st.error(f"Unexpected error processing '{uploaded_file.name}': {str(e)}")
                    logger.exception(f"Unexpected error processing {uploaded_file.name}")
                    continue
            
            if not dataframes:
                raise FileProcessingError("""
                    No valid CSV files were processed. Please ensure:
                    1. You've uploaded either .csv files or .zip files containing .csv files
                    2. The CSV files are not empty
                    3. The CSV files are properly formatted
                    4. The ZIP files contain valid CSV files
                """)
            
            write_debug_info(f"Successfully processed {processed_files} files")
            
            # Merge all dataframes
            merged_df = pd.concat(dataframes, ignore_index=True, sort=False)
            
            # Remove duplicate rows if any
            initial_rows = len(merged_df)
            merged_df.drop_duplicates(inplace=True)
            duplicates_removed = initial_rows - len(merged_df)
            
            if duplicates_removed > 0:
                write_debug_info(f"Removed {duplicates_removed} duplicate rows")
            
            write_debug_info(f"Final dataset contains {len(merged_df)} rows")
            
            return merged_df, processed_files
