"""Pharmacy Dashboard."""

import streamlit as st
import json
from datetime import datetime

from auth import get_current_user
from models import (
    get_patient_prescriptions, dispense_prescription,
    search_patient_by_health_id
)
from utils import format_date, parse_json_field
from database import get_db

def render_pharmacy_dashboard():
    """Render pharmacy dashboard."""
    user = get_current_user()
    if not user:
        st.error("Please login to access the dashboard.")
        return
    
    st.sidebar.title("💊 Pharmacy")
    st.sidebar.caption(f"Welcome, {user['first_name']}")
    
    menu_options = [
        "📊 Dashboard",
        "🔍 Scan Prescription",
        "💊 Dispense Medicine",
        "📈 Reports"
    ]
    
    selected = st.sidebar.radio("Navigate", menu_options, label_visibility="collapsed")
    
    if "Dashboard" in selected:
        render_pharmacy_home()
    elif "Scan" in selected:
        render_scan_prescription()
    elif "Dispense" in selected:
        render_dispense_medicine()
    elif "Reports" in selected:
        render_pharmacy_reports()

def render_pharmacy_home():
    """Render pharmacy home."""
    st.title("💊 Pharmacy Dashboard")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Prescriptions Today", "45")
    with col2:
        st.metric("Pending Dispensing", "12")
    with col3:
        st.metric("Completed", "33")
    
    st.markdown("---")
    
    st.subheader("Recent Prescriptions")
    st.info("No pending prescriptions to display")

def render_scan_prescription():
    """Render prescription scanning."""
    st.title("🔍 Scan Prescription QR")
    
    st.markdown("""
        Scan the QR code on patient's prescription to verify and dispense medicines.
    """)
    
    # Mock QR scanner
    qr_data = st.text_input("Enter Prescription ID or scan QR")
    
    if qr_data:
        st.success(f"Prescription found: {qr_data}")
        
        # Mock prescription data
        st.markdown("""
            ### Prescription Details
            **Patient:** John Doe  
            **Health ID:** HC-20240101-00001  
            **Doctor:** Dr. Sarah Johnson  
            **Date:** January 15, 2024  
            
            ### Medicines
            1. Paracetamol 500mg - 10 tablets
            2. Amoxicillin 250mg - 21 capsules
            3. Omeprazole 20mg - 14 tablets
        """)
        
        if st.button("Dispense All"):
            st.success("Medicines dispensed successfully!")

def render_dispense_medicine():
    """Render medicine dispensing."""
    st.title("💊 Dispense Medicine")
    
    health_id = st.text_input("Patient Health ID")
    
    if health_id:
        patient = search_patient_by_health_id(health_id)
        
        if patient:
            st.success(f"Patient: {patient.get('first_name', '')} {patient.get('last_name', '')}")
            
            # Get pending prescriptions
            prescriptions = get_patient_prescriptions(patient['id'], active_only=True)
            
            if prescriptions:
                for presc in prescriptions:
                    if not presc.get('is_dispensed'):
                        with st.expander(f"Prescription: {presc.get('prescription_id', '')[:15]}..."):
                            medicines = parse_json_field(presc.get('medicines', '[]'))
                            
                            st.markdown(f"**Doctor:** {presc.get('doctor_name', 'N/A')}")
                            st.markdown(f"**Date:** {format_date(presc.get('created_at'))}")
                            st.markdown(f"**Valid Till:** {format_date(presc.get('valid_till'))}")
                            
                            st.markdown("**Medicines:**")
                            total_amount = 0
                            for med in medicines:
                                col1, col2, col3 = st.columns([2, 1, 1])
                                col1.write(f"💊 {med.get('name', '')}")
                                col2.write(med.get('dosage', ''))
                                # Mock price
                                price = 50.0
                                col3.write(f"₹{price}")
                                total_amount += price
                            
                            st.markdown(f"**Total: ₹{total_amount}**")
                            
                            if st.button(f"Dispense", key=f"disp_{presc['id']}"):
                                dispense_prescription(
                                    presc['prescription_id'],
                                    pharmacy_id=1,
                                    pharmacist_id=get_current_user()['id'],
                                    medicines_dispensed=medicines,
                                    total_amount=total_amount
                                )
                                st.success("Medicines dispensed!")
                                st.rerun()
            else:
                st.info("No pending prescriptions")
        else:
            st.error("Patient not found")

def render_pharmacy_reports():
    """Render pharmacy reports."""
    st.title("📈 Pharmacy Reports")
    
    st.info("Reports feature coming soon!")
    
    # Mock stats
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("This Week")
        st.metric("Total Prescriptions", "156")
        st.metric("Total Revenue", "₹45,230")
    
    with col2:
        st.subheader("This Month")
        st.metric("Total Prescriptions", "623")
        st.metric("Total Revenue", "₹1,82,450")
