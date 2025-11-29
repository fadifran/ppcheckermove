"""
HTML utilities for safe rendering in Streamlit.
Provides HTML escaping and template functions.
"""
import html
from typing import Any, Dict, List, Optional
from config import COLORS


def escape(value: Any) -> str:
    """
    Safely escape a value for HTML rendering.
    
    Args:
        value: Any value to escape
        
    Returns:
        HTML-escaped string
    """
    return html.escape(str(value))


def format_number(value: int) -> str:
    """Format a number with comma separators."""
    return f"{value:,}"


def get_percentage_color(percentage: float, high_threshold: float = 90, low_threshold: float = 70) -> str:
    """
    Get color based on percentage value.
    
    Args:
        percentage: The percentage value
        high_threshold: Threshold for success color
        low_threshold: Threshold for error color
        
    Returns:
        Hex color string
    """
    if percentage >= high_threshold:
        return COLORS['success']
    elif percentage < low_threshold:
        return COLORS['error']
    else:
        return COLORS['warning']


def record_counts_html(accuzip_count: int, client_count: int) -> str:
    """
    Generate HTML for record counts display.
    
    Args:
        accuzip_count: Number of Accuzip records
        client_count: Number of client records
        
    Returns:
        HTML string
    """
    return f"""
    <div style='display: flex; justify-content: space-around; padding: 20px; 
                background-color: {COLORS['background']}; border-radius: 10px; margin: 20px 0;'>
        <div style='text-align: center;'>
            <h3>Accuzip File(s) Records</h3>
            <p style="color:{COLORS['accuzip']}; font-size:35pt; font-weight:bold;">{format_number(accuzip_count)}</p>
        </div>
        <div style='text-align: center;'>
            <h3>Client File(s) Records</h3>
            <p style="color:{COLORS['client']}; font-size:35pt; font-weight:bold;">{format_number(client_count)}</p>
        </div>
    </div>
    """


def match_results_html(total_records: int, matching_records: int, match_percentage: float) -> str:
    """
    Generate HTML for match results display.
    
    Args:
        total_records: Total number of records
        matching_records: Number of matching records
        match_percentage: Match percentage
        
    Returns:
        HTML string
    """
    percentage_color = get_percentage_color(match_percentage)
    
    return f"""
    <div style='display: flex; justify-content: space-around; padding: 10px; 
                background-color: {COLORS['background']}; border-radius: 10px; margin: 10px 0;'>
        <div style='text-align: center; flex: 1;'>
            <h3 style='font-weight: normal;'>Total Records</h3>
            <h4>{format_number(total_records)}</h4>
        </div>
        <div style='text-align: center; flex: 1;'>
            <h3 style='font-weight: normal;'>Matching Records</h3>
            <h4 style='color: {COLORS["success"]};'>{format_number(matching_records)}</h4>
        </div>
        <div style='text-align: center; flex: 1;'>
            <h3 style='font-weight: normal;'>Match Rate</h3>
            <h4 style='color: {percentage_color};'>{match_percentage:.1f}%</h4>
        </div>
    </div>
    """


def seed_results_container_html() -> str:
    """Generate opening HTML for seed results container."""
    return """
    <div class="seed-container">
        <div class="seed-title">
            <span>🌱 Seed Record Results</span>
        </div>
    """


def seed_result_html(column: str, term: str, count: int) -> str:
    """
    Generate HTML for a single seed result.
    
    Args:
        column: Column name searched
        term: Search term used
        count: Number of records found
        
    Returns:
        HTML string
    """
    # Escape user-provided values
    column_escaped = escape(column)
    term_escaped = escape(term)
    
    if count > 0:
        return f"""
        <div class="seed-record seed-found">
            <div class="seed-icon">✅</div>
            <div class="seed-content">
                Found <span class="seed-count">{format_number(count)}</span> records where 
                <strong>{column_escaped}</strong> contains '{term_escaped}'
            </div>
        </div>
        """
    else:
        return f"""
        <div class="seed-record seed-not-found">
            <div class="seed-icon">❌</div>
            <div class="seed-content">
                No records found where <strong>{column_escaped}</strong> contains '{term_escaped}'
            </div>
        </div>
        """


def postal_rate_metrics_html(avg_rate: float, min_rate: float, max_rate: float, postage: float) -> str:
    """
    Generate HTML for postal rate statistics.
    
    Args:
        avg_rate: Average postal rate
        min_rate: Minimum postal rate
        max_rate: Maximum postal rate
        postage: Calculated postage
        
    Returns:
        HTML string
    """
    from config import POSTAL_RATE_THRESHOLD
    
    avg_color = 'red' if avg_rate > POSTAL_RATE_THRESHOLD else 'green'
    avg_icon = '⛔' if avg_rate > POSTAL_RATE_THRESHOLD else '✅'
    postage_color = 'green' if postage >= 0 else 'red'
    
    return f"""
    <div class="metric-grid">
        <div class="metric-item">
            <div class="metric-label">Average Rate</div>
            <div class="metric-value" style="color: {avg_color};">
                {avg_icon} ${avg_rate:.3f}
            </div>
        </div>
        <div class="metric-item">
            <div class="metric-label">Minimum Rate</div>
            <div class="metric-value">${min_rate:.3f}</div>
        </div>
        <div class="metric-item">
            <div class="metric-label">Maximum Rate</div>
            <div class="metric-value">${max_rate:.3f}</div>
        </div>
        <div class="metric-item">
            <div class="metric-label">Postage</div>
            <div class="metric-value" style="color: {postage_color}">
                ${abs(postage):.2f}
            </div>
        </div>
    </div>
    </div>
    """


def imb_validation_metrics_html(total_records: int, valid_imbs: int, valid_percent: float,
                                 matching_zips: int, match_percent: float) -> str:
    """
    Generate HTML for IMB validation results.
    
    Args:
        total_records: Total number of records
        valid_imbs: Number of valid IMB codes
        valid_percent: Percentage of valid IMBs
        matching_zips: Number of matching ZIP codes
        match_percent: ZIP match percentage
        
    Returns:
        HTML string
    """
    valid_color = get_percentage_color(valid_percent)
    match_color = get_percentage_color(match_percent)
    
    return f"""
    <div class="imb-metric-grid">
        <div class="imb-metric-item">
            <div class="imb-metric-label">Total Records</div>
            <div class="imb-metric-value">{format_number(total_records)}</div>
        </div>
        <div class="imb-metric-item">
            <div class="imb-metric-label">Valid IMB Codes</div>
            <div class="imb-metric-value" style="color: {valid_color};">
                {format_number(valid_imbs)} ({valid_percent:.1f}%)
            </div>
        </div>
        <div class="imb-metric-item">
            <div class="imb-metric-label">ZIP Code Matches</div>
            <div class="imb-metric-value" style="color: {match_color};">
                {format_number(matching_zips)} ({match_percent:.1f}%)
            </div>
        </div>
    </div>
    </div>
    """


def streetview_card_html(record_num: int, image_url: str, address: str, 
                         zip_code: str, display_data: Dict[str, Any]) -> str:
    """
    Generate HTML for a Street View card.
    
    Args:
        record_num: Record number for display
        image_url: URL to Street View image
        address: Display address
        zip_code: ZIP code
        display_data: Dictionary of additional fields to display
        
    Returns:
        HTML string
    """
    # Escape all user-provided values
    address_escaped = escape(address)
    zip_escaped = escape(zip_code)
    
    card_html = f"""
    <div class="streetview-card">
        <div class="streetview-card-title">📇 Record #{record_num}</div>
        <img src="{image_url}" alt="Street View of {address_escaped}">
        <div class="streetview-address">{address_escaped} {zip_escaped}</div>
    """
    
    # Add data fields
    for col, value in display_data.items():
        col_escaped = escape(col)
        value_escaped = escape(value)
        card_html += f"""
        <div><span class="streetview-addcol">{col_escaped}:</span>
             <span class="streetview-addinfo"> {value_escaped}</span></div>
        """
    
    # Close the card div
    card_html += "</div>"
    
    return card_html
