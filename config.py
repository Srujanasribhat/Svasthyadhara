"""Configuration settings for the Healthcare App."""

import os
from datetime import timedelta

# Application Settings
APP_NAME = "Svasthyadhara  - flow of health Unified Healthcare Management System"
APP_VERSION = "1.0.0"

# Database Settings
DATABASE_PATH = "healthcare.db"

# JWT Settings
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-super-secret-key-change-in-production")
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION = timedelta(hours=24)

# Health ID Settings
HEALTH_ID_PREFIX = "HC"
HOSPITAL_ID_PREFIX = "HOS"
PHARMACY_ID_PREFIX = "PHR"

# Role Definitions
ROLES = {
    "patient": "Patient",
    "doctor": "Doctor",
    "hospital_admin": "Hospital Administrator",
    "pharmacist": "Pharmacist",
    "system_admin": "System Administrator"
}

# Mock Data Settings
MOCK_HOSPITALS = [
    {"name": "City General Hospital", "city": "New York", "type": "General"},
    {"name": "Metro Health Center", "city": "Los Angeles", "type": "Multi-Specialty"},
    {"name": "Central Medical Institute", "city": "Chicago", "type": "Teaching Hospital"},
]

MOCK_SPECIALIZATIONS = [
    "General Medicine", "Cardiology", "Neurology", "Orthopedics",
    "Pediatrics", "Dermatology", "Ophthalmology", "ENT",
    "Gynecology", "Psychiatry", "Oncology", "Gastroenterology"
]

# Common Medical Data
BLOOD_GROUPS = ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"]

COMMON_ALLERGIES = [
    "Penicillin", "Sulfa drugs", "Aspirin", "Ibuprofen",
    "Latex", "Peanuts", "Shellfish", "Eggs", "Milk", "None"
]

COMMON_CONDITIONS = [
    "Diabetes Type 1", "Diabetes Type 2", "Hypertension",
    "Asthma", "Heart Disease", "Thyroid Disorder",
    "Arthritis", "Migraine", "None"
]
