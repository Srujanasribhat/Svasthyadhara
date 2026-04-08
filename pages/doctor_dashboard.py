"""Doctor Dashboard - Svasthyadhara Professional UI Edition"""

import streamlit as st
from datetime import date, datetime, timedelta
from auth import get_current_user
from models import (
    get_appointments, search_patient_by_health_id, get_patient_timeline,
    create_consultation, create_prescription
)
from utils import format_date, calculate_age, parse_json_field
from database import get_db

# ------------------------------------------------------------------
# Global Styling for Professional Look
# ------------------------------------------------------------------
st.markdown("""
<style>
html, body, [class*="css"] {
    font-family: "Inter", sans-serif !important;
    color: #0a2540;
}

/* Sidebar */
[data-testid="stSidebar"] {
    background-color: #f8fbff;
    border-right: 1px solid #e0e9f5;
}
.sidebar-title {
    color: #003f7d;
    font-weight: 700;
    font-family: 'Poppins', sans-serif;
}

/* Header */
h1, h2, h3 {
    font-family: 'Poppins', sans-serif;
    color: #003f7d;
    margin-bottom: 0.5rem;
}
h4 {
    color: #0a2540;
    font-weight: 600;
}

/* Metric cards */
div[data-testid="stMetric"] {
    background-color: #ffffff;
    border: 1px solid #e3edf8;
    box-shadow: 0 2px 8px rgba(0,0,0,0.04);
    border-radius: 10px;
    padding: 1rem 1.5rem;
}

/* Buttons */
.stButton > button {
    border-radius: 8px;
    background-color: #1976d2 !important;
    color: white !important;
    border: none;
    font-weight: 600;
}
.stButton > button:hover {
    background-color: #125ca2 !important;
}

/* Tables & Expander Styling */
div[data-testid="stExpander"] {
    background-color: #ffffff !important;
    border: 1px solid #e8eef5;
    border-radius: 8px;
    padding: 0.5rem;
}
.block-container {
    max-width: 1300px;
    padding-top: 1rem;
}
</style>
""", unsafe_allow_html=True)


# ------------------------------------------------------------------
# Dashboard Router
# ------------------------------------------------------------------
def render_doctor_dashboard():
    """Render main doctor dashboard."""
    user = get_current_user()
    if not user:
        st.error("Please login to access the dashboard.")
        return

    st.sidebar.markdown("<div class='sidebar-title'>👨‍⚕️ Dr. {}</div>".format(user['last_name']), unsafe_allow_html=True)
    st.sidebar.caption(f"Role: Doctor")

    menu_options = [
        "🏠 Dashboard",
        "📅 My Appointments",
        "🔍 Patient Lookup",
        "🩺 Consultations",
        "📊 Statistics"
    ]

    selected = st.sidebar.radio("Navigate", menu_options, label_visibility="collapsed")

    if "Dashboard" in selected:
        render_doctor_home(user)
    elif "Appointments" in selected:
        render_doctor_appointments(user)
    elif "Lookup" in selected:
        render_patient_lookup()
    elif "Consultations" in selected:
        render_doctor_consultations(user)
    elif "Statistics" in selected:
        render_doctor_stats(user)


# ------------------------------------------------------------------
# HOME DASHBOARD
# ------------------------------------------------------------------
def render_doctor_home(user):
    st.title(f"Welcome, Dr. {user['first_name']} {user['last_name']} 👨‍⚕️")
    st.caption("Unified consultation management dashboard")

    # Fetch doctor_id
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM doctors WHERE user_id = ?", (user['id'],))
        row = cursor.fetchone()
        doctor_id = row['id'] if row else None

    # Metrics
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Today's Appointments", "8")
    col2.metric("Pending Consultations", "3")
    col3.metric("Patients This Week", "42")
    col4.metric("Follow-ups Due", "5")

    st.divider()
    st.subheader("📅 Today's Schedule")

    if doctor_id:
        appointments = get_appointments(doctor_id=doctor_id, date_from=date.today(), date_to=date.today())
        if appointments:
            for apt in appointments:
                with st.container():
                    c1, c2, c3 = st.columns([3, 2, 1])
                    c1.markdown(f"**{apt.get('patient_name', 'Patient')}** — _{apt.get('appointment_type', '').title()}_")
                    c1.caption(f"Health ID: {apt.get('health_id', 'N/A')}")
                    c2.markdown(f"📅 {format_date(apt.get('appointment_date'))}")
                    c2.caption(f"⏰ {apt.get('appointment_time', '')}")
                    status_icon = "🟢" if apt.get('status') == 'scheduled' else "✅"
                    c3.markdown(f"{status_icon} {apt.get('status', '').title()}")
                st.markdown("---")
        else:
            st.info("No appointments scheduled for today.")
    else:
        st.warning("Doctor profile not found.")


# ------------------------------------------------------------------
# APPOINTMENTS
# ------------------------------------------------------------------
def render_doctor_appointments(user):
    st.title("📅 My Appointments")

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM doctors WHERE user_id = ?", (user['id'],))
        row = cursor.fetchone()
        doctor_id = row['id'] if row else None

    if not doctor_id:
        st.error("Doctor profile not found.")
        return

    col1, col2 = st.columns(2)
    with col1:
        date_from = st.date_input("From", value=date.today())
    with col2:
        date_to = st.date_input("To", value=date.today() + timedelta(days=7))

    appointments = get_appointments(doctor_id=doctor_id, date_from=date_from, date_to=date_to)
    st.divider()

    if not appointments:
        st.info("No appointments found in the selected range.")
        return

    for apt in appointments:
        with st.container():
            c1, c2, c3, c4 = st.columns([2.5, 1.5, 1.5, 1])
            c1.markdown(f"**{apt.get('patient_name', 'Unknown')}**")
            c1.caption(f"Health ID: {apt.get('health_id', '-')}")
            c2.markdown(f"📅 {format_date(apt.get('appointment_date'))}")
            c2.caption(f"⏰ {apt.get('appointment_time', '')}")
            c3.caption(apt.get('appointment_type', '').title())
            c4.markdown(f"🔹 {apt.get('status', '').title()}")
        st.markdown("---")


# ------------------------------------------------------------------
# PATIENT LOOKUP
# ------------------------------------------------------------------
def render_patient_lookup():
    st.title("🔍 Patient Lookup")

    health_id = st.text_input("Enter patient Health ID")
    if not health_id:
        st.info("Enter a Health ID to search.")
        return

    patient = search_patient_by_health_id(health_id)
    if not patient:
        st.error("Patient not found.")
        return

    st.success(f"✅ Patient Found: {patient['first_name']} {patient['last_name']}")
    st.markdown(f"**Age:** {calculate_age(patient.get('date_of_birth', ''))}  |  **Gender:** {patient.get('gender', 'N/A')}")

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Basic Info")
        st.markdown(f"**Health ID:** {patient.get('health_id')}")
        st.markdown(f"**Blood Group:** {patient.get('blood_group', '-')}")
    with col2:
        st.subheader("Medical Summary")
        for a in parse_json_field(patient.get('allergies', '[]')) or []:
            st.markdown(f"- ⚠️ Allergy: {a}")
        for c in parse_json_field(patient.get('chronic_conditions', '[]')) or []:
            st.markdown(f"- 🩺 {c}")

    st.divider()
    if st.checkbox("Show Medical Timeline"):
        timeline = get_patient_timeline(patient["id"], limit=10)
        if not timeline:
            st.info("No medical history.")
        else:
            for item in timeline:
                with st.expander(f"{item['type'].title()} – {format_date(item['date'])}", expanded=False):
                    # Display key fields gracefully
                    data = item["data"]
                    st.markdown(f"**Doctor:** {data.get('doctor_name', 'N/A')}  \n"
                                f"**Hospital:** {data.get('hospital_name', 'N/A')}  \n"
                                f"**Diagnosis:** {data.get('diagnosis', '-')}")
                    if data.get("vitals"):
                        vitals = parse_json_field(data.get("vitals", "{}"))
                        st.markdown("**Vitals:**")
                        st.metric("BP", f"{vitals.get('bp_systolic', '-')}/{vitals.get('bp_diastolic', '-')}")
                        st.metric("Pulse", vitals.get("pulse", "-"))
                        st.metric("Temp", f"{vitals.get('temperature', '-')}")


# ------------------------------------------------------------------
# CONSULTATION FORM
# ------------------------------------------------------------------
def render_doctor_consultations(user):
    st.title("🩺 Consultation Workspace")

    st.caption("Record consultation details, vitals and prescriptions")

    health_id = st.text_input("Enter Patient Health ID")
    if not health_id:
        st.info("Search patient to begin consultation.")
        return

    patient = search_patient_by_health_id(health_id)
    if not patient:
        st.error("Patient not found.")
        return

    st.info(f"Consulting: **{patient['first_name']} {patient['last_name']}** (Health ID: {health_id})")

    with st.form("consultation_form"):
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Vitals")
            bp_sys = st.number_input("BP Systolic", 60, 200, 120)
            bp_dia = st.number_input("BP Diastolic", 40, 150, 80)
            pulse = st.number_input("Pulse", 30, 200, 72)
        with col2:
            st.subheader(" ")
            temp = st.number_input("Temperature (°F)", 90.0, 110.0, 98.6)
            weight = st.number_input("Weight (kg)", 20.0, 300.0, 70.0)
            spo2 = st.number_input("SpO₂ (%)", 70, 100, 98)

        st.subheader("Clinical Details")
        symptoms = st.text_area("Symptoms / Chief Complaints", placeholder="Fever, headache, body ache...")
        diagnosis = st.text_area("Diagnosis")
        notes = st.text_area("Additional Notes")

        st.subheader("Prescription")
        prescription_text = st.text_area(
            "Medicines (Name | Dosage | Frequency | Duration)",
            placeholder="Paracetamol | 500mg | 2x daily | 5 days"
        )
        instructions = st.text_input("Instructions (optional)")
        follow_up = st.date_input("Next Follow-up Date (optional)", value=None)

        submitted = st.form_submit_button("💾 Save Consultation")

        if submitted:
            with get_db() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id FROM doctors WHERE user_id = ?", (user['id'],))
                row = cursor.fetchone()
                doctor_id = row['id'] if row else 1

            vitals = dict(bp_systolic=bp_sys, bp_diastolic=bp_dia, pulse=pulse, temperature=temp, weight=weight, spo2=spo2)
            result = create_consultation(
                patient_id=patient['id'],
                doctor_id=doctor_id,
                hospital_id=1,
                symptoms=symptoms,
                diagnosis=diagnosis,
                notes=notes,
                vitals=vitals,
            )

            if result.get("success") and prescription_text:
                meds = []
                for line in prescription_text.strip().split("\n"):
                    parts = [x.strip() for x in line.split("|")]
                    if len(parts) == 4:
                        meds.append(dict(name=parts[0], dosage=parts[1], frequency=parts[2], duration=parts[3]))
                if meds:
                    create_prescription(
                        consultation_id=result["id"],
                        patient_id=patient["id"],
                        doctor_id=doctor_id,
                        medicines=meds,
                        instructions=instructions,
                    )
            st.success("✅ Consultation recorded successfully!")


# ------------------------------------------------------------------
# STATISTICS PAGE
# ------------------------------------------------------------------
def render_doctor_stats(user):
    st.title("📊 Analytics & Insights")

    col1, col2, col3 = st.columns(3)
    col1.metric("Consultations Today", "8")
    col2.metric("Follow-ups Pending", "4")
    col3.metric("Patients This Month", "152")

    st.divider()
    st.info("Detailed insights dashboard (with filters & charts) coming soon.")
