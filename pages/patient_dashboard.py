"""Patient Dashboard - All patient-facing features."""

import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
import json

from auth import get_current_user
from models import (
    get_patient_profile, update_health_profile, get_patient_timeline,
    get_patient_prescriptions, get_appointments, create_appointment,
    get_medicine_reminders, get_medicine_adherence, add_health_metric,
    get_health_metrics, get_patient_documents, upload_external_document,
    get_patient_lab_reports, get_hospitals, get_hospital_doctors,
    get_notifications, mark_notification_read
)
from components.qr_generator import generate_health_qr
from components.ai_features import check_symptoms, check_drug_interactions, calculate_health_risk, generate_smart_alerts
from components.charts import (
    create_health_metrics_chart, create_adherence_chart,
    create_consultation_timeline, create_health_score_gauge
)
from utils import format_date, format_datetime, parse_json_field, calculate_age, display_metric_card
from config import BLOOD_GROUPS, COMMON_ALLERGIES, COMMON_CONDITIONS

def render_patient_dashboard():
    """Render the complete patient dashboard."""
    user = get_current_user()
    if not user:
        st.error("Please login to access the dashboard.")
        return
    
    # Sidebar navigation
    st.sidebar.title(f"👤 {user['first_name']}")
    st.sidebar.caption(f"Health ID: {user.get('health_id', 'N/A')}")
    
    menu_options = [
        "🏠 Dashboard",
        "📋 Health Profile",
        "📅 Timeline",
        "💊 Prescriptions",
        "📆 Appointments",
        "💉 Health Metrics",
        "⏰ Medicine Reminders",
        "🏥 Book Appointment",
        "📹 Teleconsultation",
        "📄 Documents",
        "🆘 Emergency QR",
        "🤖 AI Health Check",
        "🔔 Notifications",
        "👨‍👩‍👧‍👦 Family Accounts",
        "💳 Health Credit Score",
        "🧾 Consent Management"
    ]
    
    selected = st.sidebar.radio("Navigate", menu_options, label_visibility="collapsed")
    
    # Main content area
    if "Dashboard" in selected:
        render_patient_home(user)
    elif "Health Profile" in selected:
        render_health_profile(user)
    elif "Timeline" in selected:
        render_medical_timeline(user)
    elif "Prescriptions" in selected:
        render_prescriptions(user)
    elif "Appointments" in selected:
        render_appointments(user)
    elif "Health Metrics" in selected:
        render_health_metrics(user)
    elif "Medicine Reminders" in selected:
        render_medicine_reminders(user)
    elif "Book Appointment" in selected:
        render_book_appointment(user)
    elif "Teleconsultation" in selected:
        render_teleconsultation(user)
    elif "Documents" in selected:
        render_documents(user)
    elif "Emergency QR" in selected:
        render_emergency_qr(user)
    elif "AI Health" in selected:
        render_ai_health_check(user)
    elif "Notifications" in selected:
        render_notifications(user)
    elif "Family" in selected:
        render_family_accounts(user)
    elif "Credit" in selected:
        render_credit_score(user)
    elif "Consent" in selected:   # ✅ Handle new Consent screen
        render_consent_management(user)

def render_patient_home(user):
    """Render patient home dashboard."""
    st.title("🏠 Welcome to SVASTHYADHARA")
    st.markdown(f"### Hello, {user['first_name']}!")
    
    profile = get_patient_profile(user['id'])
    
    # Quick stats
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        appointments = get_appointments(user_id=user['id'], status="scheduled")
        st.metric("Upcoming Appointments", len(appointments))
    
    with col2:
        prescriptions = get_patient_prescriptions(user['id'], active_only=True)
        st.metric("Active Prescriptions", len(prescriptions))
    
    with col3:
        adherence = get_medicine_adherence(user['id'])
        st.metric("Medicine Adherence", f"{adherence:.0f}%")
    
    with col4:
        notifications = get_notifications(user['id'], unread_only=True)
        st.metric("Unread Notifications", len(notifications))
    
    st.markdown("---")
    
    # Smart alerts
    st.subheader("🔔 Smart Alerts")
    patient_data = {
        "upcoming_appointments": appointments[:3] if appointments else [],
        "medicine_adherence": adherence,
        "overdue_followups": False
    }
    alerts = generate_smart_alerts(patient_data)
    
    if alerts:
        for alert in alerts:
            icon = "⚠️" if alert['priority'] == 'high' else "ℹ️"
            st.info(f"{icon} **{alert['title']}**: {alert['message']}")
    else:
        st.success("✅ No alerts - You're on track!")
    
    # Recent activity
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📅 Upcoming Appointments")
        if appointments:
            for apt in appointments[:3]:
                st.markdown(f"""
                    **{apt.get('doctor_name', 'Doctor')}** - {apt.get('specialization', '')}  
                    📅 {format_date(apt.get('appointment_date'))} at {apt.get('appointment_time', '')}  
                    🏥 {apt.get('hospital_name', '')}
                """)
                st.markdown("---")
        else:
            st.info("No upcoming appointments")
    
    with col2:
        st.subheader("💊 Active Medications")
        if prescriptions:
            for presc in prescriptions[:3]:
                medicines = parse_json_field(presc.get('medicines', '[]'))
                if medicines:
                    for med in medicines[:2]:
                        st.markdown(f"• **{med.get('name', '')}** - {med.get('dosage', '')}")
                st.caption(f"Prescribed by {presc.get('doctor_name', 'Doctor')}")
                st.markdown("---")
        else:
            st.info("No active prescriptions")
    
    # Health metrics overview
    st.subheader("📊 Health Metrics Overview")
    
    metrics = get_health_metrics(user['id'], metric_type="blood_pressure", days=30)
    if metrics:
        fig = create_health_metrics_chart(metrics, "blood_pressure")
        if fig:
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No health metrics recorded yet. Start tracking your health!")

def render_health_profile(user):
    """Render health profile page."""
    st.title("📋 Health Profile")
    
    profile = get_patient_profile(user['id'])
    
    if not profile:
        st.error("Profile not found")
        return
    
    tab1, tab2, tab3 = st.tabs(["Basic Info", "Medical History", "Insurance"])
    
    with tab1:
        st.subheader("Personal Information")
        
        col1, col2 = st.columns(2)
        with col1:
            st.text_input("First Name", value=profile.get('first_name', ''), disabled=True)
            st.text_input("Email", value=profile.get('email', ''), disabled=True)
            dob = profile.get('date_of_birth', '')
            st.text_input("Date of Birth", value=dob, disabled=True)
            st.text_input("Blood Group", value=profile.get('blood_group', ''), disabled=True)
        
        with col2:
            st.text_input("Last Name", value=profile.get('last_name', ''), disabled=True)
            st.text_input("Phone", value=profile.get('phone', ''), disabled=True)
            st.text_input("Gender", value=profile.get('gender', ''), disabled=True)
            age = calculate_age(dob) if dob else 0
            st.text_input("Age", value=str(age), disabled=True)
        
        st.subheader("Emergency Contact")
        col1, col2 = st.columns(2)
        with col1:
            emergency_contact = st.text_input("Emergency Contact Name", 
                                             value=profile.get('emergency_contact', ''))
        with col2:
            emergency_phone = st.text_input("Emergency Phone", 
                                           value=profile.get('emergency_phone', ''))
        
        if st.button("Update Emergency Contact"):
            # Update logic here
            st.success("Emergency contact updated!")
    
    with tab2:
        st.subheader("Medical History")
        
        # Allergies
        current_allergies = parse_json_field(profile.get('allergies')) or []
        allergies = st.multiselect("Allergies", COMMON_ALLERGIES, 
                                   default=[a for a in current_allergies if a in COMMON_ALLERGIES])
        
        # Chronic conditions
        current_conditions = parse_json_field(profile.get('chronic_conditions')) or []
        conditions = st.multiselect("Chronic Conditions", COMMON_CONDITIONS,
                                   default=[c for c in current_conditions if c in COMMON_CONDITIONS])
        
        # Current medications
        current_meds = parse_json_field(profile.get('current_medications')) or []
        medications = st.text_area("Current Medications (one per line)", 
                                   value="\n".join(current_meds))
        
        # Past surgeries
        past_surgeries = parse_json_field(profile.get('past_surgeries')) or []
        surgeries = st.text_area("Past Surgeries (one per line)", 
                                value="\n".join(past_surgeries))
        
        # Family history
        family_history = st.text_area("Family Medical History", 
                                     value=profile.get('family_history', ''))
        
        if st.button("Update Medical History"):
            update_health_profile(
                user['id'],
                allergies=allergies,
                chronic_conditions=conditions,
                current_medications=medications.split("\n") if medications else [],
                past_surgeries=surgeries.split("\n") if surgeries else [],
                family_history=family_history
            )
            st.success("Medical history updated!")
            st.rerun()
    
    with tab3:
        st.subheader("Insurance Information")
        
        insurance_provider = st.text_input("Insurance Provider", 
                                          value=profile.get('insurance_provider', ''))
        policy_number = st.text_input("Policy Number", 
                                     value=profile.get('insurance_policy_number', ''))
        valid_till = st.date_input("Valid Till", 
                                   value=datetime.strptime(profile['insurance_valid_till'], '%Y-%m-%d').date() 
                                   if profile.get('insurance_valid_till') else date.today())
        
        if st.button("Update Insurance Info"):
            update_health_profile(
                user['id'],
                insurance_provider=insurance_provider,
                insurance_policy_number=policy_number,
                insurance_valid_till=valid_till.isoformat()
            )
            st.success("Insurance information updated!")

def render_medical_timeline(user):
    """Render medical timeline."""
    st.title("📅 Medical Timeline")
    
    timeline = get_patient_timeline(user['id'])
    
    if not timeline:
        st.info("No medical records yet.")
        return
    
    # Filter options
    col1, col2 = st.columns([1, 3])
    with col1:
        filter_type = st.selectbox("Filter by", ["All", "Consultations", "Prescriptions", "Lab Reports"])
    
    # Display timeline
    for item in timeline:
        item_type = item['type']
        data = item['data']
        
        if filter_type != "All":
            type_map = {"Consultations": "consultation", "Prescriptions": "prescription", "Lab Reports": "lab_report"}
            if item_type != type_map.get(filter_type):
                continue
        
        with st.expander(f"{'🏥' if item_type == 'consultation' else '💊' if item_type == 'prescription' else '🔬'} {item_type.replace('_', ' ').title()} - {format_date(item['date'])}", expanded=False):
            if item_type == "consultation":
                st.markdown(f"**Doctor:** {data.get('doctor_name', 'N/A')}")
                st.markdown(f"**Hospital:** {data.get('hospital_name', 'N/A')}")
                st.markdown(f"**Symptoms:** {data.get('symptoms', 'N/A')}")
                st.markdown(f"**Diagnosis:** {data.get('diagnosis', 'N/A')}")
                if data.get('notes'):
                    st.markdown(f"**Notes:** {data.get('notes')}")
                
                vitals = parse_json_field(data.get('vitals'))
                if vitals:
                    st.markdown("**Vitals:**")
                    cols = st.columns(4)
                    cols[0].metric("BP", f"{vitals.get('bp_systolic', '-')}/{vitals.get('bp_diastolic', '-')}")
                    cols[1].metric("Pulse", vitals.get('pulse', '-'))
                    cols[2].metric("Temp", f"{vitals.get('temperature', '-')}°F")
                    cols[3].metric("Weight", f"{vitals.get('weight', '-')} kg")
            
            elif item_type == "prescription":
                st.markdown(f"**Prescribed by:** {data.get('doctor_name', 'N/A')}")
                medicines = parse_json_field(data.get('medicines', '[]'))
                st.markdown("**Medicines:**")
                for med in medicines:
                    st.markdown(f"- {med.get('name', '')} ({med.get('dosage', '')}) - {med.get('frequency', '')}")
                if data.get('instructions'):
                    st.markdown(f"**Instructions:** {data.get('instructions')}")
            
            elif item_type == "lab_report":
                st.markdown(f"**Test:** {data.get('test_name', 'N/A')}")
                st.markdown(f"**Category:** {data.get('test_category', 'N/A')}")
                st.markdown(f"**Hospital:** {data.get('hospital_name', 'N/A')}")
                
                results = parse_json_field(data.get('results'))
                if results:
                    st.markdown("**Results:**")
                    for key, value in results.items():
                        st.markdown(f"- {key}: {value}")

def render_prescriptions(user):
    """Render prescriptions page."""
    st.title("💊 My Prescriptions")
    
    tab1, tab2 = st.tabs(["Active", "All Prescriptions"])
    
    with tab1:
        active = get_patient_prescriptions(user['id'], active_only=True)
        if active:
            for presc in active:
                with st.container():
                    st.markdown(f"### Prescription #{presc.get('prescription_id', '')[:15]}...")
                    st.markdown(f"**Prescribed by:** Dr. {presc.get('doctor_name', 'N/A')} ({presc.get('specialization', '')})")
                    st.markdown(f"**Date:** {format_date(presc.get('created_at'))}")
                    st.markdown(f"**Valid Till:** {format_date(presc.get('valid_till'))}")
                    
                    st.markdown("**Medicines:**")
                    medicines = parse_json_field(presc.get('medicines', '[]'))
                    for med in medicines:
                        col1, col2, col3 = st.columns([2, 1, 1])
                        col1.write(f"💊 {med.get('name', '')}")
                        col2.write(med.get('dosage', ''))
                        col3.write(med.get('frequency', ''))
                    
                    if presc.get('instructions'):
                        st.info(f"📝 {presc.get('instructions')}")
                    
                    st.markdown("---")
        else:
            st.info("No active prescriptions")
    
    with tab2:
        all_presc = get_patient_prescriptions(user['id'])
        if all_presc:
            for presc in all_presc:
                status = "✅ Dispensed" if presc.get('is_dispensed') else "⏳ Pending"
                with st.expander(f"{status} - {format_date(presc.get('created_at'))} - Dr. {presc.get('doctor_name', 'N/A')}"):
                    medicines = parse_json_field(presc.get('medicines', '[]'))
                    for med in medicines:
                        st.write(f"• {med.get('name', '')} - {med.get('dosage', '')} - {med.get('frequency', '')}")
        else:
            st.info("No prescriptions found")

def render_appointments(user):
    """Render appointments page."""
    st.title("📆 My Appointments")
    
    tab1, tab2, tab3 = st.tabs(["Upcoming", "Past", "Cancelled"])
    
    with tab1:
        upcoming = get_appointments(user_id=user['id'], status="scheduled")
        if upcoming:
            for apt in upcoming:
                with st.container():
                    col1, col2, col3 = st.columns([3, 2, 1])
                    with col1:
                        st.markdown(f"### 👨‍⚕️ {apt.get('doctor_name', 'Doctor')}")
                        st.caption(apt.get('specialization', ''))
                    with col2:
                        st.markdown(f"📅 **{format_date(apt.get('appointment_date'))}**")
                        st.markdown(f"⏰ {apt.get('appointment_time', '')}")
                    with col3:
                        if st.button("Cancel", key=f"cancel_{apt['id']}"):
                            from models import update_appointment_status
                            update_appointment_status(apt['appointment_id'], "cancelled")
                            st.rerun()
                    
                    st.markdown(f"🏥 {apt.get('hospital_name', '')}")
                    st.markdown(f"📋 Type: {apt.get('appointment_type', '').title()}")
                    st.markdown("---")
        else:
            st.info("No upcoming appointments. Book one now!")
    
    with tab2:
        past = get_appointments(user_id=user['id'], status="completed")
        if past:
            for apt in past:
                st.markdown(f"✅ **{apt.get('doctor_name', 'Doctor')}** - {format_date(apt.get('appointment_date'))}")
        else:
            st.info("No past appointments")
    
    with tab3:
        cancelled = get_appointments(user_id=user['id'], status="cancelled")
        if cancelled:
            for apt in cancelled:
                st.markdown(f"❌ **{apt.get('doctor_name', 'Doctor')}** - {format_date(apt.get('appointment_date'))}")
        else:
            st.info("No cancelled appointments")

def render_health_metrics(user):
    """Render health metrics tracking page."""
    st.title("💉 Health Metrics")
    
    tab1, tab2 = st.tabs(["Track Metrics", "View History"])
    
    with tab1:
        st.subheader("Log New Reading")
        
        metric_type = st.selectbox("Select Metric", 
                                   ["Blood Pressure", "Blood Sugar", "Weight", "Heart Rate", "Temperature"])
        
        col1, col2 = st.columns(2)
        
        if metric_type == "Blood Pressure":
            with col1:
                systolic = st.number_input("Systolic (mmHg)", min_value=60, max_value=250, value=120)
            with col2:
                diastolic = st.number_input("Diastolic (mmHg)", min_value=40, max_value=150, value=80)
            value = systolic
            secondary = diastolic
            unit = "mmHg"
        elif metric_type == "Blood Sugar":
            with col1:
                value = st.number_input("Blood Sugar (mg/dL)", min_value=30, max_value=600, value=100)
            secondary = None
            unit = "mg/dL"
        elif metric_type == "Weight":
            with col1:
                value = st.number_input("Weight (kg)", min_value=20.0, max_value=300.0, value=70.0, step=0.1)
            secondary = None
            unit = "kg"
        elif metric_type == "Heart Rate":
            with col1:
                value = st.number_input("Heart Rate (bpm)", min_value=30, max_value=220, value=72)
            secondary = None
            unit = "bpm"
        else:  # Temperature
            with col1:
                value = st.number_input("Temperature (°F)", min_value=95.0, max_value=108.0, value=98.6, step=0.1)
            secondary = None
            unit = "°F"
        
        notes = st.text_input("Notes (optional)")
        
        if st.button("Save Reading", type="primary"):
            metric_key = metric_type.lower().replace(" ", "_")
            add_health_metric(user['id'], metric_key, value, secondary, unit, notes)
            st.success("Reading saved successfully!")
            st.rerun()
    
    with tab2:
        st.subheader("Health Metrics History")
        
        view_metric = st.selectbox("Select Metric to View", 
                                   ["blood_pressure", "blood_sugar", "weight", "heart_rate"],
                                   format_func=lambda x: x.replace("_", " ").title())
        
        days = st.slider("Days to show", 7, 90, 30)
        
        metrics = get_health_metrics(user['id'], metric_type=view_metric, days=days)
        
        if metrics:
            fig = create_health_metrics_chart(metrics, view_metric)
            if fig:
                st.plotly_chart(fig, use_container_width=True)
            
            # Show data table
            with st.expander("View Raw Data"):
                df = pd.DataFrame(metrics)
                st.dataframe(df[['measured_at', 'value', 'secondary_value', 'notes']])
        else:
            st.info(f"No {view_metric.replace('_', ' ')} readings in the last {days} days")

def render_medicine_reminders(user):
    """Render medicine reminders page."""
    st.title("⏰ Medicine Reminders")
    
    reminders = get_medicine_reminders(user['id'])
    
    if reminders:
        st.subheader("Today's Medications")
        
        for reminder in reminders:
            time_slots = parse_json_field(reminder.get('time_slots', '[]'))
            
            with st.container():
                col1, col2, col3 = st.columns([3, 2, 1])
                with col1:
                    st.markdown(f"### 💊 {reminder.get('medicine_name', '')}")
                    st.caption(f"Dosage: {reminder.get('dosage', '')} | {reminder.get('frequency', '')}")
                with col2:
                    st.markdown("**Times:**")
                    for slot in time_slots:
                        st.markdown(f"⏰ {slot}")
                with col3:
                    if st.button("✅ Taken", key=f"taken_{reminder['id']}"):
                        from models import track_medicine_taken
                        track_medicine_taken(reminder['id'], user['id'], True)
                        st.success("Marked as taken!")
                
                st.progress(0.7)  # Mock progress
                st.caption(f"Valid: {format_date(reminder.get('start_date'))} - {format_date(reminder.get('end_date'))}")
                st.markdown("---")
        
        # Adherence chart
        st.subheader("📊 Adherence Summary")
        adherence = get_medicine_adherence(user['id'])
        col1, col2, col3 = st.columns(3)
        col1.metric("Overall Adherence", f"{adherence:.0f}%")
        col2.metric("Doses Taken", "28")  # Mock
        col3.metric("Doses Missed", "4")  # Mock
    else:
        st.info("No active medicine reminders. Reminders will appear here when your doctor prescribes medications.")

def render_book_appointment(user):
    """Render appointment booking page."""
    st.title("🏥 Book Appointment")
    
    # Step 1: Select hospital
    st.subheader("Step 1: Select Hospital")
    hospitals = get_hospitals()
    
    if not hospitals:
        st.warning("No hospitals available. Please try again later.")
        return
    
    hospital_options = {h['name']: h['id'] for h in hospitals}
    selected_hospital = st.selectbox("Choose Hospital", list(hospital_options.keys()))
    hospital_id = hospital_options[selected_hospital]
    
    # Step 2: Select specialization and doctor
    st.subheader("Step 2: Select Doctor")
    doctors = get_hospital_doctors(hospital_id)
    
    if not doctors:
        st.warning("No doctors available at this hospital.")
        return
    
    # Get unique specializations
    specializations = list(set(d.get('specialization', 'General') for d in doctors))
    selected_spec = st.selectbox("Select Specialization", specializations)
    
    # Filter doctors by specialization
    filtered_doctors = [d for d in doctors if d.get('specialization') == selected_spec]
    doctor_options = {f"Dr. {d['first_name']} {d['last_name']} (₹{d.get('consultation_fee', 'N/A')})": d['id'] 
                     for d in filtered_doctors}
    
    selected_doctor = st.selectbox("Choose Doctor", list(doctor_options.keys()))
    doctor_id = doctor_options[selected_doctor]
    
    # Step 3: Select date and time
    st.subheader("Step 3: Select Date & Time")
    
    col1, col2 = st.columns(2)
    with col1:
        apt_date = st.date_input("Appointment Date", 
                                min_value=date.today(),
                                max_value=date.today() + timedelta(days=30))
    with col2:
        time_slots = ["09:00", "09:30", "10:00", "10:30", "11:00", "11:30",
                     "14:00", "14:30", "15:00", "15:30", "16:00", "16:30"]
        apt_time = st.selectbox("Time Slot", time_slots)
    
    # Step 4: Reason
    st.subheader("Step 4: Additional Information")
    apt_type = st.radio("Appointment Type", ["Consultation", "Follow-up", "Check-up"], horizontal=True)
    reason = st.text_area("Reason for Visit (optional)")
    
    # Book button
    if st.button("📅 Confirm Booking", type="primary"):
        result = create_appointment(
            patient_id=user['id'],
            doctor_id=doctor_id,
            hospital_id=hospital_id,
            appointment_date=apt_date,
            appointment_time=apt_time,
            appointment_type=apt_type.lower(),
            reason=reason
        )
        
        if result.get('success'):
            st.success(f"✅ Appointment booked successfully! ID: {result.get('appointment_id')}")
            st.balloons()
        else:
            st.error("Failed to book appointment. Please try again.")

def render_teleconsultation(user):
    """Render teleconsultation UI placeholder."""
    st.title("📹 Teleconsultation")
    
    st.info("🎥 Video consultation feature coming soon!")
    
    tab1, tab2 = st.tabs(["New Consultation", "Chat History"])
    
    with tab1:
        st.subheader("Start a Video Consultation")
        
        # Mock UI
        hospitals = get_hospitals()
        selected_hospital = st.selectbox("Select Hospital", [h['name'] for h in hospitals])
        
        doctors = ["Dr. John Smith", "Dr. Sarah Johnson", "Dr. Michael Williams"]
        selected_doctor = st.selectbox("Select Doctor", doctors)
        
        st.markdown("---")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🎥 Start Video Call", type="primary"):
                st.info("Video call feature is a placeholder. In production, this would connect to a video service like WebRTC.")
        with col2:
            if st.button("💬 Start Chat"):
                st.info("Chat feature is a placeholder.")
    
    with tab2:
        st.subheader("Previous Consultations")
        st.info("No previous teleconsultations")

def render_documents(user):
    """Render documents upload page."""
    st.title("📄 My Documents")
    
    tab1, tab2 = st.tabs(["Upload Document", "View Documents"])
    
    with tab1:
        st.subheader("Upload External Medical Document")
        
        doc_type = st.selectbox("Document Type", 
                               ["Medical Bill", "Prescription", "Lab Report", "Insurance", "Other"])
        
        doc_name = st.text_input("Document Name")
        description = st.text_area("Description (optional)")
        source = st.text_input("Source (Hospital/Clinic name)")
        doc_date = st.date_input("Document Date")
        
        uploaded_file = st.file_uploader("Choose file", type=['pdf', 'jpg', 'jpeg', 'png'])
        
        if uploaded_file and doc_name:
            if st.button("Upload Document"):
                upload_external_document(
                    patient_id=user['id'],
                    document_type=doc_type,
                    document_name=doc_name,
                    document_data=uploaded_file.read(),
                    description=description,
                    source=source,
                    document_date=doc_date
                )
                st.success("Document uploaded successfully!")
    
    with tab2:
        st.subheader("My Documents")
        
        documents = get_patient_documents(user['id'])
        
        if documents:
            for doc in documents:
                with st.expander(f"📄 {doc.get('document_name', 'Untitled')} - {doc.get('document_type', '')}"):
                    st.markdown(f"**Date:** {format_date(doc.get('document_date'))}")
                    st.markdown(f"**Source:** {doc.get('source', 'N/A')}")
                    if doc.get('description'):
                        st.markdown(f"**Description:** {doc.get('description')}")
                    st.caption(f"Uploaded: {format_datetime(doc.get('uploaded_at'))}")
        else:
            st.info("No documents uploaded yet")

def render_emergency_qr(user):
    """Render emergency QR code page."""
    st.title("🆘 Emergency Health QR")
    
    profile = get_patient_profile(user['id'])
    
    st.markdown("""
        This QR code contains essential health information for emergency situations.
        Medical professionals can scan it to quickly access your critical health data.
    """)
    
    st.markdown("---")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("QR Code")
        
        allergies = parse_json_field(profile.get('allergies', '[]'))
        
        qr_image = generate_health_qr(
            health_id=user.get('health_id', ''),
            patient_name=f"{user['first_name']} {user['last_name']}",
            blood_group=profile.get('blood_group'),
            allergies=allergies,
            emergency_contact=profile.get('emergency_phone')
        )
        
        st.image(qr_image, width=300)
        st.download_button(
            "📥 Download QR Code",
            qr_image,
            file_name=f"emergency_qr_{user.get('health_id', 'health')}.png",
            mime="image/png"
        )
    
    with col2:
        st.subheader("Information Included")
        st.markdown(f"**Health ID:** {user.get('health_id', 'N/A')}")
        st.markdown(f"**Name:** {user['first_name']} {user['last_name']}")
        st.markdown(f"**Blood Group:** {profile.get('blood_group', 'N/A')}")
        
        st.markdown("**Allergies:**")
        if allergies:
            for allergy in allergies:
                st.markdown(f"- {allergy}")
        else:
            st.markdown("- None recorded")
        
        st.markdown(f"**Emergency Contact:** {profile.get('emergency_phone', 'N/A')}")
    
    st.warning("⚠️ Keep this QR code accessible on your phone or print it for your wallet.")

def render_ai_health_check(user):
    """Render AI health check features."""
    st.title("🤖 AI Health Assistant")
    
    tab1, tab2, tab3 = st.tabs(["Symptom Checker", "Drug Interactions", "Health Risk"])
    
    with tab1:
        st.subheader("🩺 Symptom Checker")
        st.caption("Describe your symptoms and get possible conditions. This is not a diagnosis.")
        
        symptoms = st.text_area("Describe your symptoms", 
                               placeholder="e.g., I have a headache, fever, and body aches for the past 2 days")
        
        if st.button("Check Symptoms") and symptoms:
            with st.spinner("Analyzing symptoms..."):
                results = check_symptoms(symptoms)
                
                if results:
                    st.subheader("Possible Conditions")
                    for result in results:
                        severity_color = {"mild": "green", "moderate": "orange", "severe": "red"}
                        st.markdown(f"""
                            ### {result['condition']}
                            **Confidence:** {result['confidence']}%  
                            **Severity:** :{severity_color.get(result['severity'], 'blue')}[{result['severity'].upper()}]
                            
                            **Recommendation:** {result['recommendation']}
                        """)
                        st.progress(result['confidence'] / 100)
                        st.warning(f"⚠️ {result['disclaimer']}")
                        st.markdown("---")
                else:
                    st.info("No matching conditions found. Please consult a doctor for accurate diagnosis.")
    
    with tab2:
        st.subheader("💊 Drug Interaction Checker")
        
        medicines_input = st.text_area("Enter medicines (one per line)", 
                                       placeholder="Aspirin\nWarfarin\nIbuprofen")
        
        if st.button("Check Interactions") and medicines_input:
            medicines = [m.strip() for m in medicines_input.split('\n') if m.strip()]
            
            if len(medicines) >= 2:
                interactions = check_drug_interactions(medicines)
                
                if interactions:
                    st.warning(f"⚠️ Found {len(interactions)} potential interaction(s)")
                    
                    for interaction in interactions:
                        severity_color = {"high": "🔴", "moderate": "🟡", "low": "🟢"}
                        st.markdown(f"""
                            {severity_color.get(interaction['severity'], '⚪')} **{interaction['drug1']} + {interaction['drug2']}**
                            
                            **Severity:** {interaction['severity'].upper()}  
                            **Effect:** {interaction['effect']}  
                            **Recommendation:** {interaction['recommendation']}
                        """)
                        st.markdown("---")
                else:
                    st.success("✅ No known interactions found between these medications.")
            else:
                st.info("Please enter at least 2 medicines to check for interactions.")
    
    with tab3:
        st.subheader("📊 Health Risk Assessment")
        
        risk_type = st.selectbox("Select Risk Type", ["Cardiovascular", "Diabetes"])
        
        st.markdown("Select your risk factors:")
        
        if risk_type == "Cardiovascular":
            factors_options = ["High BP", "Diabetes", "Smoking", "Obesity", "Sedentary", 
                             "Family History", "High Cholesterol", "Age Over 45"]
        else:
            factors_options = ["Obesity", "Sedentary", "Family History", "High BP", 
                             "Age Over 40", "PCOS"]
        
        selected_factors = st.multiselect("Risk Factors", factors_options)
        
        if st.button("Calculate Risk"):
            result = calculate_health_risk(risk_type.lower(), selected_factors)
            
            st.markdown(f"### {result['risk_type']} Risk Assessment")
            
            # Display gauge
            fig = create_health_score_gauge(100 - result['percentage'])  # Invert for health score
            st.plotly_chart(fig, use_container_width=True)
            
            st.markdown(f"""
                **Risk Level:** :{result['color']}[{result['level']}]  
                **Risk Score:** {result['percentage']}%
                
                **Factors Identified:** {', '.join(result['factors_identified']) if result['factors_identified'] else 'None'}
                
                **Recommendations:**
            """)
            
            for rec in result['recommendation']:
                st.markdown(f"• {rec}")

def render_notifications(user):
    """Render notifications page."""
    st.title("🔔 Notifications")
    
    notifications = get_notifications(user['id'])
    
    unread = [n for n in notifications if not n.get('is_read')]
    read = [n for n in notifications if n.get('is_read')]
    
    tab1, tab2 = st.tabs([f"Unread ({len(unread)})", f"Read ({len(read)})"])
    
    with tab1:
        if unread:
            for notif in unread:
                with st.container():
                    col1, col2 = st.columns([4, 1])
                    with col1:
                        st.markdown(f"**{notif.get('title', 'Notification')}**")
                        st.caption(notif.get('message', ''))
                        st.caption(format_datetime(notif.get('created_at')))
                    with col2:
                        if st.button("✓", key=f"mark_{notif['id']}"):
                            mark_notification_read(notif['id'])
                            st.rerun()
                    st.markdown("---")
        else:
            st.info("No unread notifications")
    
    with tab2:
        if read:
            for notif in read:
                st.markdown(f"**{notif.get('title', 'Notification')}**")
                st.caption(notif.get('message', ''))
                st.caption(format_datetime(notif.get('created_at')))
                st.markdown("---")
        else:
            st.info("No read notifications")

def render_family_accounts(user):
    """Render family accounts linking."""
    st.title("👨‍👩‍👧‍👦 Family Accounts")
    
    st.info("Link family member accounts to manage healthcare for your loved ones.")
    
    # Mock UI
    st.subheader("Linked Family Members")
    
    # Placeholder data
    family_members = []
    
    if family_members:
        for member in family_members:
            st.markdown(f"👤 **{member['name']}** - {member['relation']}")
    else:
        st.info("No family members linked yet")
    
    st.markdown("---")
    
    st.subheader("Add Family Member")
    
    col1, col2 = st.columns(2)
    with col1:
        member_health_id = st.text_input("Family Member's Health ID")
    with col2:
        relation = st.selectbox("Relation", ["Spouse", "Child", "Parent", "Sibling", "Other"])
    
    if st.button("Send Link Request"):
        if member_health_id:
            st.success(f"Link request sent to Health ID: {member_health_id}")
        else:
            st.warning("Please enter a valid Health ID")
def render_credit_score(user):
    """Render patient credit score and assign rewards."""
    st.title("💳 Health Credit Score System")

    st.markdown("""
    Your *Health Credit Score* shows your health engagement and consistency.  
    The score ranges from *50 (min)* to *1000 (max)* and grows as you complete appointments,
    take medicines on time, and stay active in the app.
    """)

    # ------------------------
    # Data foundation
    # ------------------------
    adherence = get_medicine_adherence(user['id']) or 0
    appointments = get_appointments(user_id=user['id'])
    metrics = get_health_metrics(user['id'])
    total_appointments = len(appointments)
    completed_appointments = len([a for a in appointments if a.get("status") == "completed"])
    followup_rate = (completed_appointments / total_appointments) * 100 if total_appointments else 0

    # ------------------------
    # App engagement estimate (session usage or interaction)
    # ------------------------
    app_engagement = min(100, 10 + len(metrics) * 5 + followup_rate * 0.2)

    # ------------------------
    # Calculate Scores
    # ------------------------
    adherence_score = min(100, adherence)
    followup_score = min(100, followup_rate)
    metric_score = min(100, len(metrics) * 10)
    app_score = min(100, app_engagement)

    weighted_score = (
        0.35 * adherence_score +
        0.25 * followup_score +
        0.25 * metric_score +
        0.15 * app_score
    )

    credit_score = int(50 + (weighted_score / 100) * (1000 - 50))
    credit_score = min(max(credit_score, 50), 1000)

    # ------------------------
    # Display Score
    # ------------------------
    st.markdown(f"### Your Current Score: *{credit_score} / 1000*")

    fig = create_health_score_gauge(weighted_score)
    st.plotly_chart(fig, use_container_width=True)

    # ------------------------
    # Benefits
    # ------------------------
    st.subheader("🏦 Benefits Based on Credit Score")

    if credit_score < 200:
        tier = "⚠️ Low Tier"
        discount = 0
        insurance_bonus = "Not Eligible"
        st.warning("You need a minimum score of 200 to enjoy benefits.")
    elif 200 <= credit_score < 500:
        tier = "🩺 Basic Tier"
        discount = 5
        insurance_bonus = "Eligible for basic insurance discounts"
    elif 500 <= credit_score < 800:
        tier = "💎 Premium Tier"
        discount = 10
        insurance_bonus = "Premium insurance coverage discounts available"
    else:
        tier = "🌟 Elite Tier"
        discount = 20
        insurance_bonus = "Maximum insurance discounts and exclusive healthcare perks"

    col1, col2, col3 = st.columns(3)
    col1.metric("Tier", tier)
    col2.metric("Pharmacy Discount", f"{discount}%")
    col3.metric("Insurance Benefit", insurance_bonus)

    st.markdown("---")

    # ------------------------
    # Breakdown Table
    # ------------------------
    st.subheader("📊 Score Breakdown")
    df = pd.DataFrame([
        {"Factor": "Medication Adherence", "Score": round(adherence_score, 1)},
        {"Factor": "Follow-up Completion", "Score": round(followup_score, 1)},
        {"Factor": "Health Metric Logging", "Score": round(metric_score, 1)},
        {"Factor": "App Engagement", "Score": round(app_score, 1)},
    ])
    st.dataframe(df, use_container_width=True)

    # ------------------------
    # Improvement Tips
    # ------------------------
    st.subheader("💡 Tips to Boost Your Credit Score")
    tips = []
    if adherence_score < 80:
        tips.append("💊 Improve your medicine intake consistency.")
    if followup_score < 60:
        tips.append("📅 Try not to miss appointments.")
    if metric_score < 50:
        tips.append("📈 Log more health metrics regularly.")
    if app_score < 50:
        tips.append("⚙️ Explore more features in Svasthyadhara for engagement credits.")

    if not tips:
        st.success("🎉 Excellent! You maintain top health engagement.")
    else:
        for tip in tips:
            st.markdown(f"- {tip}")
def render_consent_management(user):
    """Render the complete patient dashboard."""
    user = get_current_user()
    if not user:
        st.error("Please login to access the dashboard.")
        return
    
    # Sidebar navigation
    st.sidebar.title(f"👤 {user['first_name']}")
    st.sidebar.caption(f"Health ID: {user.get('health_id', 'N/A')}")

    """Render patient consent management system."""
    st.title("🧾 Consent Management")
    st.markdown("""
    Manage who can access your health data and how long they can keep it.  
    You control access for doctors, hospitals, or researchers securely.
    """)
    # Mock backend methods (replace with actual DB/API hooks)
    from models import (
        get_patient_consents, create_consent_record, revoke_consent
    )
    # Tabs
    tab1, tab2, tab3 = st.tabs(["Active Consents", "Grant New Consent", "Consent History"])
    # ----------------------------
    # TAB 1: Active Consents
    # ----------------------------
    with tab1:
        st.subheader("🔒 Active Consents")
        consents = get_patient_consents(user['id'], status="active")
        if consents:
            for consent in consents:
                with st.container():
                    col1, col2, col3 = st.columns([3, 2, 1])
                    with col1:
                        st.markdown(f"**Entity:** {consent.get('entity_name', 'N/A')}")
                        st.caption(f"Type: {consent.get('entity_type', 'Doctor/Hospital')}")
                    with col2:
                        st.markdown(f"**Access:** {consent.get('data_type', 'Health Records')}")
                        st.caption(f"Valid Till: {format_date(consent.get('valid_till'))}")
                    with col3:
                        if st.button("🔓 Revoke", key=f"revoke_{consent['id']}"):
                            revoke_consent(consent['id'])
                            st.success("Consent revoked successfully!")
                            st.rerun()
                    st.progress(1.0)
                    st.caption(f"Granted on {format_date(consent.get('granted_on'))}")
                    st.markdown("---")
        else:
            st.info("No active consents found.")
    # ----------------------------
    # TAB 2: Grant New Consent
    # ----------------------------
    with tab2:
        st.subheader("✉️ Grant New Consent")
        col1, col2 = st.columns(2)
        with col1:
            entity_type = st.selectbox("Entity Type", ["Doctor", "Hospital", "Researcher", "Third-Party App"])
            entity_name = st.text_input("Entity Name")
        with col2:
            data_type = st.multiselect(
                "Data Access Type",
                ["Medical Records", "Prescriptions", "Lab Reports", "Vitals", "Insurance Details"],
                default=["Medical Records"]
            )
        valid_days = st.slider("Consent Duration (days)", 1, 365, 30)
        description = st.text_area("Purpose / Reason for Data Access")
        st.markdown("---")
        if st.button("✅ Grant Consent", type="primary"):
            if entity_name:
                valid_till = date.today() + timedelta(days=valid_days)
                create_consent_record(
                    patient_id=user['id'],
                    entity_name=entity_name,
                    entity_type=entity_type,
                    data_type=data_type,
                    purpose=description,
                    valid_till=valid_till.isoformat()
                )
                st.success(f"Consent granted to {entity_type} '{entity_name}' till {valid_till.strftime('%d %b %Y')}.")
                st.balloons()
                st.rerun()
            else:
                st.warning("Please enter valid entity details before granting consent.")
    # ----------------------------
    # TAB 3: Consent History
    # ----------------------------
    with tab3:
        st.subheader("📜 Full Consent History")
        history = get_patient_consents(user['id'])
        if history:
            df = pd.DataFrame(history)
            df_display = df[["entity_name", "entity_type", "data_type", "granted_on", "valid_till", "status", "purpose"]]
            st.dataframe(df_display, use_container_width=True)
        else:
            st.info("No consent history available.")