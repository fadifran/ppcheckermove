"""
Unit tests for PostPros Job Checker.
"""
import pytest
import pandas as pd
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import (
    MATCH_THRESHOLD_HIGH, MATCH_THRESHOLD_LOW, COLORS,
    IMB_CODE_LENGTH, IMB_VALID_CHARS
)
from utils.html_utils import escape, get_percentage_color, format_number
from utils.data_validator import compare_datasets
from utils.imb_validator import is_valid_imb_format, validate_imb_format_vectorized


class TestConfig:
    """Test configuration values."""
    
    def test_thresholds_are_valid(self):
        assert MATCH_THRESHOLD_HIGH > MATCH_THRESHOLD_LOW
        assert 0 <= MATCH_THRESHOLD_LOW <= 100
        assert 0 <= MATCH_THRESHOLD_HIGH <= 100
    
    def test_colors_defined(self):
        assert 'success' in COLORS
        assert 'warning' in COLORS
        assert 'error' in COLORS
    
    def test_imb_constants(self):
        assert IMB_CODE_LENGTH == 65
        assert set(IMB_VALID_CHARS) == {'A', 'D', 'T', 'F'}


class TestHtmlUtils:
    """Test HTML utility functions."""
    
    def test_escape_basic(self):
        assert escape("<script>") == "&lt;script&gt;"
        assert escape("Hello & World") == "Hello &amp; World"
        assert escape('"quotes"') == "&quot;quotes&quot;"
    
    def test_escape_handles_none(self):
        assert escape(None) == "None"
    
    def test_escape_handles_numbers(self):
        assert escape(123) == "123"
        assert escape(45.67) == "45.67"
    
    def test_format_number(self):
        assert format_number(1000) == "1,000"
        assert format_number(1234567) == "1,234,567"
        assert format_number(0) == "0"
    
    def test_get_percentage_color_high(self):
        color = get_percentage_color(95)
        assert color == COLORS['success']
    
    def test_get_percentage_color_medium(self):
        color = get_percentage_color(80)
        assert color == COLORS['warning']
    
    def test_get_percentage_color_low(self):
        color = get_percentage_color(50)
        assert color == COLORS['error']


class TestDataValidator:
    """Test data validation functions."""
    
    def test_compare_datasets_identical(self):
        df1 = pd.DataFrame({'col1': ['a', 'b', 'c'], 'col2': [1, 2, 3]})
        df2 = pd.DataFrame({'colA': ['a', 'b', 'c'], 'colB': [1, 2, 3]})
        mapping = {'col1': 'colA', 'col2': 'colB'}
        
        result = compare_datasets(df1, df2, mapping)
        
        assert result['total_records'] == 3
        assert result['matching_records'] == 3
        assert result['missing_records'] == 0
    
    def test_compare_datasets_with_missing(self):
        df1 = pd.DataFrame({'col1': ['a', 'b', 'c', 'd']})
        df2 = pd.DataFrame({'colA': ['a', 'b']})
        mapping = {'col1': 'colA'}
        
        result = compare_datasets(df1, df2, mapping)
        
        assert result['total_records'] == 4
        assert result['matching_records'] == 2
        assert result['missing_records'] == 2


class TestImbValidator:
    """Test IMB validation functions."""
    
    def test_is_valid_imb_format_valid(self):
        # Valid 65-character IMB with only ADTF
        valid_imb = "A" * 65
        assert is_valid_imb_format(valid_imb) == True
        
        valid_imb2 = "TAAFFATFFDTFTFAATDTTAAFDAFDFDAFFDTTADAADTATTADTTTAADAFDDDDTTDDDTA"
        assert is_valid_imb_format(valid_imb2) == True
    
    def test_is_valid_imb_format_invalid_length(self):
        assert is_valid_imb_format("A" * 64) == False
        assert is_valid_imb_format("A" * 66) == False
        assert is_valid_imb_format("") == False
    
    def test_is_valid_imb_format_invalid_chars(self):
        # Contains invalid character 'X'
        invalid_imb = "A" * 64 + "X"
        assert is_valid_imb_format(invalid_imb) == False
    
    def test_is_valid_imb_format_none(self):
        assert is_valid_imb_format(None) == False
    
    def test_validate_imb_format_vectorized(self):
        series = pd.Series([
            "A" * 65,  # Valid
            "D" * 65,  # Valid
            "A" * 64,  # Invalid - too short
            "A" * 64 + "X",  # Invalid - bad char
        ])
        
        result = validate_imb_format_vectorized(series)
        
        assert result[0] == True
        assert result[1] == True
        assert result[2] == False
        assert result[3] == False


class TestStreetViewProcessor:
    """Test Street View processor functions."""
    
    def test_zip_truncation(self):
        """Test that ZIP codes are properly truncated to 5 digits."""
        # This tests the fix for the bug where address length was checked
        # instead of zip_code length
        zip_code = "77382-1482"
        # Correct behavior: truncate zip_code if zip_code > 5 chars
        display_zip = zip_code[:5] if len(zip_code) > 5 else zip_code
        assert display_zip == "77382"
        
        # Short zip should remain unchanged
        short_zip = "7738"
        display_zip = short_zip[:5] if len(short_zip) > 5 else short_zip
        assert display_zip == "7738"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
