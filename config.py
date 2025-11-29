"""
Configuration constants for PostPros Job Checker.
Centralizes all magic numbers, thresholds, and settings.
"""

# Match percentage thresholds
MATCH_THRESHOLD_HIGH = 90  # Green - excellent match
MATCH_THRESHOLD_LOW = 70   # Red - poor match (between is orange/warning)

# Postal rate thresholds
POSTAL_RATE_THRESHOLD = 0.40  # Above this is considered high

# Display settings
MAX_MISMATCH_DISPLAY = 5  # Maximum mismatched records to display
CARDS_PER_ROW = 3  # Street View cards per row
DEFAULT_NUM_CARDS = 3  # Default number of Street View cards
MAX_NUM_CARDS = 21  # Maximum Street View cards

# IMB validation settings
IMB_CODE_LENGTH = 65  # Valid IMB code length
IMB_VALID_CHARS = 'ADTF'  # Valid characters in IMB codes

# Color palette
COLORS = {
    'success': '#0e8544',      # Green
    'warning': '#ff8c00',      # Orange
    'error': '#ff4b4b',        # Red
    'accuzip': '#0e8544',      # Green for Accuzip
    'client': '#ff9100',       # Orange for Client
    'background': '#f8f9fa',   # Light gray background
}

# Default column mappings (Accuzip -> Client)
DEFAULT_COLUMN_MAPPINGS = {
    'controlno': 'CONTROLNO',
    'yearly_pre': 'YEARLY PREMIUM',
    'NAME': 'name',
    'ADDRESS': 'address',
    'CITY': 'city',
    'STATE': 'state',
    'ZIP': 'zip',
}

# Column detection keywords
ADDRESS_KEYWORDS = ['address', 'addr', 'street']
ZIP_KEYWORDS = ['zip', 'postal']
IMB_KEYWORDS = ['imb', 'barcode', 'intelligent']
DISPLAY_KEYWORDS = ['first', 'dwelling_l', 'yearly_pre']

# Flat rate for postage calculation
FLAT_RATE_PER_RECORD = 0.005
