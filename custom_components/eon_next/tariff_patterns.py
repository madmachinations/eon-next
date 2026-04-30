#!/usr/bin/env python3
"""
Tariff time pattern configurations for different EON tariff types.

The EON API only provides rate values without time metadata, so we need
to maintain hardcoded patterns for known tariffs.
"""

# Tariff pattern definitions
# Each pattern defines time ranges and which rate index applies to each range

TARIFF_PATTERNS = {
    # Next Drive Smart: Off-Peak 00:00-07:00, Peak 07:00-24:00
    # Rate 0 = Off-Peak, Rate 1 = Peak
    "next_drive": {
        "type": "2-rate",
        "off_peak_start": 0,   # 00:00
        "off_peak_end": 7,     # 07:00
        "rate_mapping": {
            "off_peak": 0,
            "peak": 1
        },
        "description": "Next Drive: Off-Peak 00:00-07:00, Peak 07:00-24:00"
    },
    
    # Economy 7: Typically 00:00-07:00 off-peak (varies by supplier)
    "economy_7": {
        "type": "2-rate",
        "off_peak_start": 0,
        "off_peak_end": 7,
        "rate_mapping": {
            "off_peak": 0,
            "peak": 1
        },
        "description": "Economy 7: Off-Peak 00:00-07:00, Peak 07:00-24:00"
    },
}


def get_tariff_pattern(tariff_name: str) -> dict:
    """
    Get the time pattern configuration for a tariff.
    
    Args:
        tariff_name: The display name or tariff code
        
    Returns:
        Pattern configuration dict or None if not found
    """
    tariff_name_lower = tariff_name.lower()
    tariff_name_upper = tariff_name.upper()
    
    # Check for specific tariff matches
    if "next drive" in tariff_name_lower or "NEXT_DRIVE" in tariff_name_upper:
        return TARIFF_PATTERNS["next_drive"]
    elif "economy 7" in tariff_name_lower or "ECONOMY_7" in tariff_name_upper:
        return TARIFF_PATTERNS["economy_7"]
    
    return None


def get_current_rate_index(pattern: dict, hour: int) -> int:
    """
    Get the rate index for the current hour based on tariff pattern.
    
    Args:
        pattern: Tariff pattern configuration
        hour: Current hour (0-23)
        
    Returns:
        Rate index (0 or 1 for 2-rate tariffs)
    """
    if pattern["type"] != "2-rate":
        return 0  # Default to first rate
    
    off_peak_start = pattern["off_peak_start"]
    off_peak_end = pattern["off_peak_end"]
    
    # Check if current hour is in off-peak period
    if off_peak_start <= hour < off_peak_end:
        return pattern["rate_mapping"]["off_peak"]
    else:
        return pattern["rate_mapping"]["peak"]


def get_current_period_name(pattern: dict, hour: int) -> str:
    """
    Get the period name (Off-Peak/Peak) for the current hour.
    
    Args:
        pattern: Tariff pattern configuration
        hour: Current hour (0-23)
        
    Returns:
        Period name string
    """
    if pattern["type"] != "2-rate":
        return "Unknown"
    
    off_peak_start = pattern["off_peak_start"]
    off_peak_end = pattern["off_peak_end"]
    
    if off_peak_start <= hour < off_peak_end:
        return "Off-Peak"
    else:
        return "Peak"


def get_period_hours(pattern: dict) -> tuple:
    """
    Get the off-peak and peak hour ranges as formatted strings.
    
    Returns:
        Tuple of (off_peak_str, peak_str)
    """
    off_peak_start = pattern["off_peak_start"]
    off_peak_end = pattern["off_peak_end"]
    
    off_peak_str = f"{off_peak_start:02d}:00-{off_peak_end:02d}:00"
    
    # Calculate peak hours
    if off_peak_end == 0:
        peak_str = "00:00-23:59"
    else:
        peak_str = f"{off_peak_end:02d}:00-23:59"
    
    return off_peak_str, peak_str
