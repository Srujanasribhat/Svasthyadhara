"""Hospital Dashboard - Hospital and Doctor features."""

import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
import json

from auth import get_current_user
from models import (
    search_patient_by_health_id, get_patient_profile, get_patient_timeline,
    create_consultation, create_prescription, create_lab_report,
    get_appointments, update_appointment_status, get_hospital_doctors
)
from utils import format_date, format_datetime, parse_json_field, calculate_age
from database import get_db

def render_hospital_dashboard():
    """Render hospital admin dashboard."""
    user = get_current_user()
    if not user:
        st.error("Please login to access the dashboard.")
        return
    
    st.sidebar.title(f"🏥 Hospital Admin")
    st.sidebar.caption(f"Welcome, {user['first_name']}")
    
    menu_options = [
        "📊 Dashboard",
        "🔍 Patient Search",
        "📅 Appointments",
        "👨‍⚕️ Doctors",
        "📋 Add Consultation",
        "🔬 Lab Reports"
    ]
    
    selected = st.sidebar.radio("Navigate", menu_options, label_visibility="collapsed")
    
    if "Dashboard" in selected:
        render_hospital_home()
    elif "Patient Search" in selected:
        render_patient_search()
    elif "Appointments" in selected:
        render_hospital_appointments()
    elif "Doctors" in selected:
        render_doctors_management()
    elif "Consultation" in selected:
        render_add_consultation()
    elif "Lab Reports" in selected:
        render_lab_reports()

def render_hospital_home():
    """Render hospital home dashboard."""
    st.title("🏥 Hospital Dashboard")
    
    # Quick stats
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Today's Appointments", "24")
    with col2:
        st.metric("Active Doctors", "8")
    with col3:
        st.metric("Patients Today", "45")
    with col4:
        st.metric("Pending Reports", "12")
    
    st.markdown("---")
    
    # Today's appointments
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📅 Today's Schedule")
        today_appointments = get_appointments(
            hospital_id=1,  # Mock hospital ID
            date_from=date.today(),
            date_to=date.today()
        )
        
        if today_appointments:
            for apt in today_appointments[:5]:
                st.markdown(f"""
                    **{apt.get('patient_name', 'Patient')}** - {apt.get('appointment_time', '')}  
                    Dr. {apt.get('doctor_name', '')} | {apt.get('specialization', '')}  
                    Status: {apt.get('status', '').title()}
                """)
                st.markdown("---")
        else:
            st.info("No appointments scheduled for today")
    
    with col2:
        st.subheader("⚠️ Pending Actions")
        st.warning("🔬 5 lab reports pending review")
        st.info("📋 3 consultations to complete")
        st.success("✅ All prescriptions dispensed")

def render_patient_search():
    """Render patient search functionality."""
    st.title("🔍 Patient Search")
    
    search_method = st.radio("Search by", ["Health ID", "Phone", "Email"], horizontal=True)
    
    search_value = st.text_input(f"Enter {search_method}")
    
    if st.button("Search") and search_value:
        if search_method == "Health ID":
            patient = search_patient_by_health_id(search_value)
        else:
            # Mock search for other methods
            patient = None
        
        if patient:
            st.success("Patient found!")
            st.session_state.selected_patient = patient
            
            # Display patient info
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("Patient Information")
                st.markdown(f"**Name:** {patient.get('first_name', '')} {patient.get('last_name', '')}")
                st.markdown(f"**Health ID:** {patient.get('health_id', '')}")
                st.markdown(f"**Age:** {calculate_age(patient.get('date_of_birth', ''))}")
                st.markdown(f"**Gender:** {patient.get('gender', 'N/A')}")
                st.markdown(f"**Blood Group:** {patient.get('blood_group', 'N/A')}")
                st.markdown(f"**Phone:** {patient.get('phone', 'N/A')}")
            
            with col2:
                st.subheader("Medical Info")
                allergies = parse_json_field(patient.get('allergies', '[]'))
                conditions = parse_json_field(patient.get('chronic_conditions', '[]'))
                
                st.markdown("**Allergies:**")
                for allergy in (allergies or []):
                    st.markdown(f"- ⚠️ {allergy}")
                
                st.markdown("**Chronic Conditions:**")
                for condition in (conditions or []):
                    st.markdown(f"- {condition}")
            
            # Show consent status
            if patient.get('consent_given'):
                st.success("✅ Patient has given consent for data access")
                
                # View medical history
                if st.button("View Medical History"):
                    timeline = get_patient_timeline(patient['id'])
                    
                    if timeline:
                        st.subheader("Medical Timeline")
                        for item in timeline[:10]:
                            st.markdown(f"**{item['type'].title()}** - {format_date(item['date'])}")
                            st.json(item['data'])
                    else:
                        st.info("No medical records found")
            else:
                st.warning("⚠️ Patient consent required to access medical history")
        else:
            st.error("Patient not found")

def render_hospital_appointments():
    """Render hospital appointments management."""
    st.title("📅 Appointments Management")
    
    # Date filter
    col1, col2, col3 = st.columns(3)
    with col1:
        start_date = st.date_input("From Date", value=date.today())
    with col2:
        end_date = st.date_input("To Date", value=date.today() + timedelta(days=7))
    with col3:
        status_filter = st.selectbox("Status", ["All", "Scheduled", "Completed", "Cancelled"])
    
    # Get appointments
    status = None if status_filter == "All" else status_filter.lower()
    appointments = get_appointments(
        hospital_id=1,  # Mock
        date_from=start_date,
        date_to=end_date,
        status=status
    )
    
    if appointments:
        # Convert to DataFrame for display
        df = pd.DataFrame(appointments)
        display_cols = ['appointment_date', 'appointment_time', 'patient_name', 
                       'doctor_name', 'appointment_type', 'status']
        df_display = df[display_cols] if all(c in df.columns for c in display_cols) else df
        
        st.dataframe(df_display, use_container_width=True)
        
        # Quick actions
        st.subheader("Quick Actions")
        
        for apt in appointments[:5]:
            if apt.get('status') == 'scheduled':
                col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
                with col1:
                    st.write(f"{apt.get('patient_name', '')} - Dr. {apt.get('doctor_name', '')}")
                with col2:
                    if st.button("✅", key=f"complete_{apt['id']}"):
                        update_appointment_status(apt['appointment_id'], 'completed')
                        st.rerun()
                with col3:
                    if st.button("❌", key=f"cancel_{apt['id']}"):
                        update_appointment_status(apt['appointment_id'], 'cancelled')
                        st.rerun()
                with col4:
                    if st.button("📋", key=f"consult_{apt['id']}"):
                        st.session_state.consultation_appointment = apt
    else:
        st.info("No appointments found for the selected criteria")

def render_doctors_management():
    """Render doctors management."""
    st.title("👨‍⚕️ Doctors Management")
    
    doctors = get_hospital_doctors(1)  # Mock hospital ID
    
    if doctors:
        for doc in doctors:
            with st.expander(f"Dr. {doc.get('first_name', '')} {doc.get('last_name', '')} - {doc.get('specialization', '')}"):
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown(f"**Doctor ID:** {doc.get('doctor_id', '')}")
                    st.markdown(f"**Specialization:** {doc.get('specialization', '')}")
                    st.markdown(f"**Qualification:** {doc.get('qualification', '')}")
                with col2:
                    st.markdown(f"**Experience:** {doc.get('experience_years', '')} years")
                    st.markdown(f"**Fee:** ₹{doc.get('consultation_fee', '')}")
                    st.markdown(f"**Contact:** {doc.get('phone', '')}")
    else:
        st.info("No doctors found")

def render_add_consultation():
    """Render add consultation form."""
    st.title("📋 Add Consultation")
    
    # Patient search
    health_id = st.text_input("Patient Health ID")
    
    patient = None
    if health_id:
        patient = search_patient_by_health_id(health_id)
        if patient:
            st.success(f"Patient: {patient.get('first_name', '')} {patient.get('last_name', '')}")
        else:
            st.error("Patient not found")
    
    if patient:
        with st.form("consultation_form"):
            st.subheader("Consultation Details")
            
            # Vitals
            st.markdown("### Vitals")
            col1, col2, col3, col4, col5 = st.columns(5)
            with col1:
                bp_systolic = st.number_input("BP Systolic", min_value=60, max_value=250, value=120)
            with col2:
                bp_diastolic = st.number_input("BP Diastolic", min_value=40, max_value=150, value=80)
            with col3:
                pulse = st.number_input("Pulse", min_value=40, max_value=200, value=72)
            with col4:
                temp = st.number_input("Temperature", min_value=95.0, max_value=108.0, value=98.6)
            with col5:
                weight = st.number_input("Weight (kg)", min_value=10, max_value=300, value=70)
            
            # Symptoms and diagnosis
            st.markdown("### Symptoms & Diagnosis")
            symptoms = st.text_area("Symptoms")
            diagnosis = st.text_area("Diagnosis")
            notes = st.text_area("Notes")
            
            # Prescription
            st.markdown("### Prescription")
            
            num_medicines = st.number_input("Number of medicines", min_value=1, max_value=10, value=1)
            
            medicines = []
            for i in range(num_medicines):
                st.markdown(f"**Medicine {i+1}**")
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    name = st.text_input(f"Name", key=f"med_name_{i}")
                with col2:
                    dosage = st.text_input(f"Dosage", key=f"med_dosage_{i}")
                with col3:
                    frequency = st.text_input(f"Frequency", key=f"med_freq_{i}")
                with col4:
                    duration = st.text_input(f"Duration", key=f"med_dur_{i}")
                
                if name:
                    medicines.append({
                        "name": name,
                        "dosage": dosage,
                        "frequency": frequency,
                        "duration": duration
                    })
            
            instructions = st.text_area("Prescription Instructions")
            
            # Follow up
            follow_up = st.date_input("Follow-up Date (optional)", value=None)
            
            submitted = st.form_submit_button("Save Consultation")
            
            if submitted:
                vitals = {
                    "bp_systolic": bp_systolic,
                    "bp_diastolic": bp_diastolic,
                    "pulse": pulse,
                    "temperature": temp,
                    "weight": weight
                }
                
                # Create consultation
                result = create_consultation(
                    patient_id=patient['id'],
                    doctor_id=1,  # Mock
                    hospital_id=1,  # Mock
                    symptoms=symptoms,
                    diagnosis=diagnosis,
                    notes=notes,
                    vitals=vitals
                )
                
                if result.get('success'):
                    # Create prescription if medicines added
                    if medicines:
                        create_prescription(
                            consultation_id=result['id'],
                            patient_id=patient['id'],
                            doctor_id=1,
                            medicines=medicines,
                            instructions=instructions
                        )
                    
                    st.success("Consultation saved successfully!")
                    st.balloons()
                else:
                    st.error("Failed to save consultation")

def render_lab_reports():
    """Render lab reports management."""
    st.title("🔬 Lab Reports")
    
    tab1, tab2 = st.tabs(["Add Report", "View Reports"])
    
    with tab1:
        health_id = st.text_input("Patient Health ID", key="lab_health_id")
        
        patient = None
        if health_id:
            patient = search_patient_by_health_id(health_id)
            if patient:
                st.success(f"Patient: {patient.get('first_name', '')} {patient.get('last_name', '')}")
        
        if patient:
            with st.form("lab_report_form"):
                test_name = st.text_input("Test Name")
                test_category = st.selectbox("Category", 
                                            ["Blood Test", "Urine Test", "Imaging", "ECG", "Other"])
                
                st.markdown("### Results")
                
                # Dynamic result fields
                num_parameters = st.number_input("Number of parameters", min_value=1, max_value=20, value=3)
                
                results = {}
                for i in range(num_parameters):
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        param_name = st.text_input(f"Parameter {i+1}", key=f"param_{i}")
                    with col2:
                        param_value = st.text_input(f"Value", key=f"value_{i}")
                    with col3:
                        param_unit = st.text_input(f"Unit", key=f"unit_{i}")
                    
                    if param_name and param_value:
                        results[param_name] = f"{param_value} {param_unit}"
                
                normal_range = st.text_input("Normal Range Reference")
                interpretation = st.text_area("Interpretation")
                
                if st.form_submit_button("Save Report"):
                    create_lab_report(
                        patient_id=patient['id'],
                        test_name=test_name,
                        test_category=test_category,
                        results=results,
                        hospital_id=1,
                        normal_range=normal_range,
                        interpretation=interpretation
                    )
                    st.success("Lab report saved!")
    
    with tab2:
        st.info("Search patient to view their lab reports")
