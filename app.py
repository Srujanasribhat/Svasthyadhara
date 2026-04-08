"""
Svasthyadhara  - flow of health 
Unified Healthcare Management System
Main Application Entry Point
"""

import streamlit as st
from PIL import Image

from datetime import datetime
import base64

# Import modules
from database import init_database
from auth import login_user, register_user, get_current_user, logout
from config import APP_NAME, BLOOD_GROUPS, ROLES
from data.dummy_data import create_dummy_data

# Page imports
from pages.patient_dashboard import render_patient_dashboard
from pages.hospital_dashboard import render_hospital_dashboard
from pages.pharmacy_dashboard import render_pharmacy_dashboard
from pages.doctor_dashboard import render_doctor_dashboard


# Function to encode the logo image as Base64
def get_base64_image(image_path):
    try:
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    except FileNotFoundError:
        return None

# Encode and prepare logo
image_base64 = get_base64_image("logo.png")

# Page configuration
st.set_page_config(
    page_title=APP_NAME,
    page_icon=image_base64,
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
/* General styling */
body, .stApp {
    background-color: #f8fbff;
    font-family: "Inter", sans-serif;
}

/* Header section */
.header-container {
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    text-align: center;
    padding: 3.5rem 0 2rem 0;
}

.app-logo {
    width: 150px;
    height: auto;
    margin-bottom: 1rem;
    border-radius: 18px;
    box-shadow: 0 4px 18px rgba(0, 0, 0, 0.12);
}

.app-name {
    font-size: 3.4rem;
    font-weight: 900;
    color: #003f7d;
    margin-bottom: 0.4rem;
    font-family: "Poppins", sans-serif;
    letter-spacing: 0.5px;
}

.tagline {
    color: #2678c2;
    font-size: 1.35rem;
    font-weight: 500;
    font-family: "Inter", sans-serif;
}

/* Card styles */
.card {
    background-color: white;
    border-radius: 12px;
    box-shadow: 0 4px 10px rgba(0,0,0,0.05);
    padding: 1.5rem;
    margin-bottom: 1rem;
    transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.card:hover {
    transform: translateY(-4px);
    box-shadow: 0 6px 16px rgba(0,0,0,0.08);
}

/* Metrics container */
.metric-container {
    display: flex;
    justify-content: space-evenly;
    gap: 1rem;
    margin-bottom: 2rem;
}

/* Buttons */
.stButton>button {
    border-radius: 8px;
    background-color: #1976d2 !important;
    color: white !important;
    border: none;
    font-weight: 600;
}

.stButton>button:hover {
    background-color: #1565c0 !important;
}

/* Sidebar */
.sidebar-header {
    font-weight: 700;
    color: #004e89;
    margin-bottom: 1rem;
    text-align: center;
}

/* Footer */
.footer {
    text-align: center;
    color: #999;
    border-top: 1px solid #eaeaea;
    padding: 1.5rem 0;
    margin-top: 3rem;
    font-size: 0.9rem;
}
</style>
""", unsafe_allow_html=True)

# Updated Header Section with Logo (base64‑encoded) and Tagline
if image_base64:
    st.markdown(f"""
    <div class="header-container">
        <img src="data:image/png;base64,{image_base64}" class="app-logo">
        <div class="app-name">Svasthyadhara</div>
        <div class="tagline">Your Unified Healthcare App.</div>
    </div>
    """, unsafe_allow_html=True)
else:
    st.markdown("""
    <div class="header-container">
        <div class="app-name">Svasthyadhara</div>
        <div class="tagline">Your Unified Healthcare App.</div>
        <p style='color:red;'>⚠️ Logo not found (logo.png missing)</p>
    </div>
    """, unsafe_allow_html=True)

def init_app():
    """Initialize the application."""
    # Initialize database
    init_database()
    
    # Create dummy data if needed
    create_dummy_data()
    
    # Initialize session state
    if 'user' not in st.session_state:
        st.session_state.user = None
    if 'page' not in st.session_state:
        st.session_state.page = 'home'


def render_home():
    with st.container():
        st.markdown("### Explore Our Services")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("""
            <div class="card">
                <h4>👤 For Patients</h4>
                <ul>
                    <li>Unified Health ID</li>
                    <li>Complete medical history</li>
                    <li>Medicine reminders</li>
                    <li>Book appointments</li>
                    <li>Emergency QR code</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown("""
            <div class="card">
                <h4>🏥 For Hospitals</h4>
                <ul>
                    <li>Patient management</li>
                    <li>Consultation records</li>
                    <li>Lab report integration</li>
                    <li>Appointment scheduling</li>
                    <li>Doctor dashboard</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown("""
            <div class="card">
                <h4>💊 For Pharmacies</h4>
                <ul>
                    <li>Prescription verification</li>
                    <li>Medicine dispensing</li>
                    <li>Purchase tracking</li>
                    <li>Adherence monitoring</li>
                    <li>Inventory management</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Metrics section
        with st.container():
            metric_col1, metric_col2, metric_col3 = st.columns(3)
            metric_col1.metric("Registered Patients", "1,200+", "12%")
            metric_col2.metric("Hospitals Connected", "25+", "5 new")
            metric_col3.metric("Active Doctors", "340+", "Up 8%")
        
        # Tabs for Authentication
        tab1, tab2 = st.tabs(["🔐 Login", "📝 Register"])
        
        with tab1:
            render_login()
        
        with tab2:
            render_register()


def render_login():
    """Render login form."""
    with st.container():
        st.subheader("Login to Your Account")
        
        with st.form("login_form"):
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            
            col1, col2 = st.columns(2)
            with col1:
                submitted = st.form_submit_button("Login", type="primary")
            with col2:
                if st.form_submit_button("Forgot Password?"):
                    st.info("Password reset feature coming soon!")
            
            if submitted:
                if email and password:
                    result = login_user(email, password)
                    if result['success']:
                        st.session_state.user = result['user']
                        st.session_state.token = result['token']
                        st.success("Login successful!")
                        st.rerun()
                    else:
                        st.error(result['message'])
                else:
                    st.warning("Please enter email and password")
        
        with st.expander("📋 Demo Credentials"):
            st.markdown("""
                **Patient:** alice@email.com / patient123  
                **Doctor:** dr.john.smith@healthconnect.com / doctor123  
                **Hospital Admin:** hospital.admin@cityhospital.com / hospital123  
                **Pharmacist:** pharmacist@cityhospital.com / pharmacy123
            """)
def render_register():
    """Render registration form."""
    with st.container():
        st.subheader("Create New Account")
        
        role = st.selectbox("Register as", ["Patient", "Doctor", "Hospital Admin", "Pharmacist"])
        
        with st.form("register_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                first_name = st.text_input("First Name*")
                email = st.text_input("Email*")
                phone = st.text_input("Phone")
                gender = st.selectbox("Gender", ["Male", "Female", "Other"])
            
            with col2:
                last_name = st.text_input("Last Name*")
                password = st.text_input("Password*", type="password")
                confirm_password = st.text_input("Confirm Password*", type="password")
                dob = st.date_input("Date of Birth")
            
            if role == "Patient":
                blood_group = st.selectbox("Blood Group", BLOOD_GROUPS)
                address = st.text_area("Address")
            
            agree = st.checkbox("I agree to the Terms of Service and Privacy Policy")
            
            submitted = st.form_submit_button("Register", type="primary")
            
            if submitted:
                if not all([first_name, last_name, email, password]):
                    st.error("Please fill all required fields")
                elif password != confirm_password:
                    st.error("Passwords do not match")
                elif not agree:
                    st.error("Please agree to the terms")
                else:
                    role_map = {
                        "Patient": "patient",
                        "Doctor": "doctor",
                        "Hospital Admin": "hospital_admin",
                        "Pharmacist": "pharmacist"
                    }
                    
                    result = register_user(
                        email=email,
                        password=password,
                        role=role_map[role],
                        first_name=first_name,
                        last_name=last_name,
                        phone=phone,
                        date_of_birth=dob.isoformat() if dob else None,
                        gender=gender,
                        blood_group=blood_group if role == "Patient" else None,
                        address=address if role == "Patient" else None
                    )
                    
                    if result['success']:
                        st.success(f"Registration successful! Your Health ID: {result.get('health_id', 'N/A')}")
                        st.info("Please login with your credentials")
                    else:
                        st.error(result['message'])


def render_dashboard():
    """Render appropriate dashboard based on user role."""
    user = get_current_user()
    
    if not user:
        st.session_state.user = None
        st.rerun()
    
    # Sidebar Navigation
    with st.sidebar:
        st.markdown(
            f"<div class='sidebar-header'>👤 {user['first_name']} {user['last_name']}</div>",
            unsafe_allow_html=True
        )
        st.caption(f"Role: {user['role'].replace('_', ' ').title()}")
        
        if user.get('health_id'):
            st.caption(f"Health ID: {user['health_id']}")
        
        st.markdown("---")
        st.markdown("### Navigation")
        if st.button("🏠 Dashboard"):
            st.session_state.page = "dashboard"
        
        if st.button("🚪 Logout"):
            logout()
            st.rerun()
    
    # Render role-specific dashboard
    if user['role'] == 'patient':
        render_patient_dashboard()
    elif user['role'] == 'doctor':
        render_doctor_dashboard()
    elif user['role'] == 'hospital_admin':
        render_hospital_dashboard()
    elif user['role'] == 'pharmacist':
        render_pharmacy_dashboard()
    elif user['role'] == 'system_admin':
        st.title("🔧 System Admin Dashboard")
        st.info("Admin dashboard coming soon!")
    else:
        st.error("Unknown role")


def main():
    """Main application entry point."""
    # Initialize
    init_app()
    
    # Check authentication
    if st.session_state.user:
        render_dashboard()
    else:
        render_home()

    # Footer
    st.markdown("""
    <div class="footer">
        © 2024 Svasthyadhara - Unified Healthcare Management System · Built for a healthier tomorrow.
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()