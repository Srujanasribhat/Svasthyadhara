"""Utility functions for the Healthcare App."""

import streamlit as st
import json
from datetime import datetime, date
from typing import Any, Dict, List
import re

def format_date(d: Any, format_str: str = "%B %d, %Y") -> str:
    """Format date for display."""
    if not d:
        return "N/A"
    if isinstance(d, str):
        try:
            d = datetime.fromisoformat(d.replace('Z', '+00:00'))
        except:
            return d
    return d.strftime(format_str)

def format_datetime(dt: Any, format_str: str = "%B %d, %Y at %I:%M %p") -> str:
    """Format datetime for display."""
    if not dt:
        return "N/A"
    if isinstance(dt, str):
        try:
            dt = datetime.fromisoformat(dt.replace('Z', '+00:00'))
        except:
            return dt
    return dt.strftime(format_str)

def parse_json_field(value: Any) -> Any:
    """Parse JSON field from database."""
    if not value:
        return None
    if isinstance(value, (dict, list)):
        return value
    try:
        return json.loads(value)
    except:
        return value

def calculate_age(birth_date: Any) -> int:
    """Calculate age from birth date."""
    if not birth_date:
        return 0
    if isinstance(birth_date, str):
        birth_date = datetime.strptime(birth_date, "%Y-%m-%d").date()
    today = date.today()
    return today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))

def validate_email(email: str) -> bool:
    """Validate email format."""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_phone(phone: str) -> bool:
    """Validate phone number format."""
    pattern = r'^\+?[1-9]\d{9,14}$'
    return re.match(pattern, phone.replace(" ", "").replace("-", "")) is not None

def get_bmi_category(bmi: float) -> tuple:
    """Get BMI category and color."""
    if bmi < 18.5:
        return "Underweight", "blue"
    elif bmi < 25:
        return "Normal", "green"
    elif bmi < 30:
        return "Overweight", "orange"
    else:
        return "Obese", "red"

def get_bp_category(systolic: int, diastolic: int) -> tuple:
    """Get blood pressure category and color."""
    if systolic < 120 and diastolic < 80:
        return "Normal", "green"
    elif systolic < 130 and diastolic < 80:
        return "Elevated", "yellow"
    elif systolic < 140 or diastolic < 90:
        return "High BP Stage 1", "orange"
    elif systolic >= 140 or diastolic >= 90:
        return "High BP Stage 2", "red"
    else:
        return "Hypertensive Crisis", "darkred"

def display_metric_card(title: str, value: str, subtitle: str = None, color: str = "blue"):
    """Display a metric card."""
    st.markdown(f"""
        <div style="
            background: linear-gradient(135deg, #{color}22 0%, #{color}11 100%);
            border-left: 4px solid {color};
            padding: 1rem;
            border-radius: 8px;
            margin-bottom: 0.5rem;
        ">
            <p style="color: #666; margin: 0; font-size: 0.85rem;">{title}</p>
            <p style="font-size: 1.5rem; font-weight: bold; margin: 0.25rem 0; color: {color};">{value}</p>
            {f'<p style="color: #888; margin: 0; font-size: 0.75rem;">{subtitle}</p>' if subtitle else ''}
        </div>
    """, unsafe_allow_html=True)

def display_alert(message: str, alert_type: str = "info"):
    """Display an alert message."""
    colors = {
        "info": ("#e3f2fd", "#1976d2"),
        "success": ("#e8f5e9", "#388e3c"),
        "warning": ("#fff3e0", "#f57c00"),
        "error": ("#ffebee", "#d32f2f")
    }
    bg, border = colors.get(alert_type, colors["info"])
    
    st.markdown(f"""
        <div style="
            background-color: {bg};
            border-left: 4px solid {border};
            padding: 1rem;
            border-radius: 4px;
            margin: 0.5rem 0;
        ">
            {message}
        </div>
    """, unsafe_allow_html=True)

def create_timeline_item(item_type: str, title: str, date_str: str, details: Dict[str, Any]):
    """Create a timeline item display."""
    icons = {
        "consultation": "🏥",
        "prescription": "💊",
        "lab_report": "🔬",
        "appointment": "📅",
        "document": "📄"
    }
    
    icon = icons.get(item_type, "📌")
    
    return f"""
        <div style="
            display: flex;
            gap: 1rem;
            padding: 1rem;
            border-left: 3px solid #1976d2;
            margin-left: 1rem;
            margin-bottom: 1rem;
        ">
            <div style="font-size: 1.5rem;">{icon}</div>
            <div style="flex: 1;">
                <div style="font-weight: bold; color: #333;">{title}</div>
                <div style="color: #666; font-size: 0.85rem;">{date_str}</div>
                <div style="margin-top: 0.5rem; color: #555;">
                    {' • '.join([f'{k}: {v}' for k, v in details.items() if v])}
                </div>
            </div>
        </div>
    """
