"""Data models and database operations."""

import json
from datetime import datetime, date
from typing import List, Dict, Any, Optional
from database import get_db
from auth import generate_unique_id

# ============== Patient Operations ==============

def get_patient_profile(user_id: int) -> Optional[Dict[str, Any]]:
    """Get complete patient profile."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT u.*, hp.*
            FROM users u
            LEFT JOIN health_profiles hp ON u.id = hp.user_id
            WHERE u.id = ?
        ''', (user_id,))
        result = cursor.fetchone()
        return dict(result) if result else None

def update_health_profile(user_id: int, **kwargs) -> bool:
    """Update patient health profile."""
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Build update query dynamically
        fields = []
        values = []
        for key, value in kwargs.items():
            if value is not None:
                fields.append(f"{key} = ?")
                values.append(json.dumps(value) if isinstance(value, (list, dict)) else value)
        
        if not fields:
            return False
        
        values.append(user_id)
        query = f"UPDATE health_profiles SET {', '.join(fields)}, updated_at = CURRENT_TIMESTAMP WHERE user_id = ?"
        cursor.execute(query, values)
        conn.commit()
        return True

def get_patient_timeline(patient_id: int, limit: int = 50) -> List[Dict[str, Any]]:
    """Get patient's complete medical timeline."""
    with get_db() as conn:
        cursor = conn.cursor()
        
        timeline = []
        
        # Get consultations
        cursor.execute('''
            SELECT c.*, d.specialization, u.first_name || ' ' || u.last_name as doctor_name,
                   h.name as hospital_name
            FROM consultations c
            JOIN doctors d ON c.doctor_id = d.id
            JOIN users u ON d.user_id = u.id
            JOIN hospitals h ON c.hospital_id = h.id
            WHERE c.patient_id = ?
            ORDER BY c.consultation_date DESC
            LIMIT ?
        ''', (patient_id, limit))
        
        for row in cursor.fetchall():
            timeline.append({
                "type": "consultation",
                "date": row["consultation_date"],
                "data": dict(row)
            })
        
        # Get lab reports
        cursor.execute('''
            SELECT lr.*, h.name as hospital_name
            FROM lab_reports lr
            LEFT JOIN hospitals h ON lr.hospital_id = h.id
            WHERE lr.patient_id = ?
            ORDER BY lr.test_date DESC
            LIMIT ?
        ''', (patient_id, limit))
        
        for row in cursor.fetchall():
            timeline.append({
                "type": "lab_report",
                "date": row["test_date"],
                "data": dict(row)
            })
        
        # Get prescriptions
        cursor.execute('''
            SELECT p.*, u.first_name || ' ' || u.last_name as doctor_name
            FROM prescriptions p
            JOIN doctors d ON p.doctor_id = d.id
            JOIN users u ON d.user_id = u.id
            WHERE p.patient_id = ?
            ORDER BY p.created_at DESC
            LIMIT ?
        ''', (patient_id, limit))
        
        for row in cursor.fetchall():
            timeline.append({
                "type": "prescription",
                "date": row["created_at"],
                "data": dict(row)
            })
        
        # Sort by date
        timeline.sort(key=lambda x: x["date"] if x["date"] else "", reverse=True)
        return timeline[:limit]

# ============== Consultation Operations ==============

def create_consultation(
    patient_id: int,
    doctor_id: int,
    hospital_id: int,
    symptoms: str,
    diagnosis: str,
    notes: str = None,
    vitals: Dict = None,
    consultation_type: str = "in-person",
    appointment_id: int = None
) -> Dict[str, Any]:
    """Create a new consultation record."""
    with get_db() as conn:
        cursor = conn.cursor()
        
        consultation_id = generate_unique_id("CON")
        vitals_json = json.dumps(vitals) if vitals else None
        
        cursor.execute('''
            INSERT INTO consultations (
                consultation_id, patient_id, doctor_id, hospital_id,
                appointment_id, symptoms, diagnosis, notes, vitals,
                consultation_type
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            consultation_id, patient_id, doctor_id, hospital_id,
            appointment_id, symptoms, diagnosis, notes, vitals_json,
            consultation_type
        ))
        
        conn.commit()
        return {"success": True, "consultation_id": consultation_id, "id": cursor.lastrowid}

def get_consultation(consultation_id: str) -> Optional[Dict[str, Any]]:
    """Get consultation details."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT c.*, 
                   d.specialization,
                   du.first_name || ' ' || du.last_name as doctor_name,
                   pu.first_name || ' ' || pu.last_name as patient_name,
                   pu.health_id,
                   h.name as hospital_name
            FROM consultations c
            JOIN doctors d ON c.doctor_id = d.id
            JOIN users du ON d.user_id = du.id
            JOIN users pu ON c.patient_id = pu.id
            JOIN hospitals h ON c.hospital_id = h.id
            WHERE c.consultation_id = ?
        ''', (consultation_id,))
        result = cursor.fetchone()
        return dict(result) if result else None

# ============== Prescription Operations ==============

def create_prescription(
    consultation_id: int,
    patient_id: int,
    doctor_id: int,
    medicines: List[Dict],
    instructions: str = None,
    valid_days: int = 30
) -> Dict[str, Any]:
    """Create a new prescription."""
    with get_db() as conn:
        cursor = conn.cursor()
        
        prescription_id = generate_unique_id("PRX")
        valid_till = (datetime.now() + timedelta(days=valid_days)).date()
        
        cursor.execute('''
            INSERT INTO prescriptions (
                prescription_id, consultation_id, patient_id, doctor_id,
                medicines, instructions, valid_till
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            prescription_id, consultation_id, patient_id, doctor_id,
            json.dumps(medicines), instructions, valid_till
        ))
        
        prescription_db_id = cursor.lastrowid
        conn.commit()
        
        return {
            "success": True,
            "prescription_id": prescription_id,
            "id": prescription_db_id
        }

def get_patient_prescriptions(patient_id: int, active_only: bool = False) -> List[Dict[str, Any]]:
    """Get patient's prescriptions."""
    with get_db() as conn:
        cursor = conn.cursor()
        
        query = '''
            SELECT p.*, u.first_name || ' ' || u.last_name as doctor_name,
                   d.specialization
            FROM prescriptions p
            JOIN doctors d ON p.doctor_id = d.id
            JOIN users u ON d.user_id = u.id
            WHERE p.patient_id = ?
        '''
        
        if active_only:
            query += " AND p.valid_till >= date('now') AND p.is_dispensed = 0"
        
        query += " ORDER BY p.created_at DESC"
        
        cursor.execute(query, (patient_id,))
        return [dict(row) for row in cursor.fetchall()]

# ============== Appointment Operations ==============

def create_appointment(
    patient_id: int,
    doctor_id: int,
    hospital_id: int,
    appointment_date: date,
    appointment_time: str,
    appointment_type: str = "consultation",
    reason: str = None
) -> Dict[str, Any]:
    """Create a new appointment."""
    with get_db() as conn:
        cursor = conn.cursor()
        
        appointment_id = generate_unique_id("APT")
        
        cursor.execute('''
            INSERT INTO appointments (
                appointment_id, patient_id, doctor_id, hospital_id,
                appointment_date, appointment_time, appointment_type, reason
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            appointment_id, patient_id, doctor_id, hospital_id,
            appointment_date, appointment_time, appointment_type, reason
        ))
        
        conn.commit()
        return {"success": True, "appointment_id": appointment_id, "id": cursor.lastrowid}

def get_appointments(
    user_id: int = None,
    doctor_id: int = None,
    hospital_id: int = None,
    status: str = None,
    date_from: date = None,
    date_to: date = None
) -> List[Dict[str, Any]]:
    """Get appointments with filters."""
    with get_db() as conn:
        cursor = conn.cursor()
        
        query = '''
            SELECT a.*, 
                   pu.first_name || ' ' || pu.last_name as patient_name,
                   pu.health_id,
                   du.first_name || ' ' || du.last_name as doctor_name,
                   d.specialization,
                   h.name as hospital_name
            FROM appointments a
            JOIN users pu ON a.patient_id = pu.id
            JOIN doctors d ON a.doctor_id = d.id
            JOIN users du ON d.user_id = du.id
            JOIN hospitals h ON a.hospital_id = h.id
            WHERE 1=1
        '''
        params = []
        
        if user_id:
            query += " AND a.patient_id = ?"
            params.append(user_id)
        if doctor_id:
            query += " AND a.doctor_id = ?"
            params.append(doctor_id)
        if hospital_id:
            query += " AND a.hospital_id = ?"
            params.append(hospital_id)
        if status:
            query += " AND a.status = ?"
            params.append(status)
        if date_from:
            query += " AND a.appointment_date >= ?"
            params.append(date_from)
        if date_to:
            query += " AND a.appointment_date <= ?"
            params.append(date_to)
        
        query += " ORDER BY a.appointment_date, a.appointment_time"
        
        cursor.execute(query, params)
        return [dict(row) for row in cursor.fetchall()]

def update_appointment_status(appointment_id: str, status: str, notes: str = None) -> bool:
    """Update appointment status."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE appointments 
            SET status = ?, notes = ?, updated_at = CURRENT_TIMESTAMP
            WHERE appointment_id = ?
        ''', (status, notes, appointment_id))
        conn.commit()
        return cursor.rowcount > 0

# ============== Health Metrics Operations ==============

def add_health_metric(
    patient_id: int,
    metric_type: str,
    value: float,
    secondary_value: float = None,
    unit: str = None,
    notes: str = None
) -> bool:
    """Add a health metric reading."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO health_metrics (
                patient_id, metric_type, value, secondary_value, unit, notes
            ) VALUES (?, ?, ?, ?, ?, ?)
        ''', (patient_id, metric_type, value, secondary_value, unit, notes))
        conn.commit()
        return True

def get_health_metrics(
    patient_id: int,
    metric_type: str = None,
    days: int = 30
) -> List[Dict[str, Any]]:
    """Get patient's health metrics."""
    with get_db() as conn:
        cursor = conn.cursor()
        
        query = '''
            SELECT * FROM health_metrics
            WHERE patient_id = ?
            AND measured_at >= datetime('now', ?)
        '''
        params = [patient_id, f'-{days} days']
        
        if metric_type:
            query += " AND metric_type = ?"
            params.append(metric_type)
        
        query += " ORDER BY measured_at DESC"
        
        cursor.execute(query, params)
        return [dict(row) for row in cursor.fetchall()]

# ============== Medicine Reminder Operations ==============

def create_medicine_reminder(
    patient_id: int,
    prescription_id: int,
    medicine_name: str,
    dosage: str,
    frequency: str,
    time_slots: List[str],
    start_date: date,
    end_date: date
) -> bool:
    """Create medicine reminder."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO medicine_reminders (
                patient_id, prescription_id, medicine_name, dosage,
                frequency, time_slots, start_date, end_date
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            patient_id, prescription_id, medicine_name, dosage,
            frequency, json.dumps(time_slots), start_date, end_date
        ))
        conn.commit()
        return True

def get_medicine_reminders(patient_id: int, active_only: bool = True) -> List[Dict[str, Any]]:
    """Get patient's medicine reminders."""
    with get_db() as conn:
        cursor = conn.cursor()
        
        query = "SELECT * FROM medicine_reminders WHERE patient_id = ?"
        if active_only:
            query += " AND is_active = 1 AND end_date >= date('now')"
        
        cursor.execute(query, (patient_id,))
        return [dict(row) for row in cursor.fetchall()]

def track_medicine_taken(reminder_id: int, patient_id: int, taken: bool = True) -> bool:
    """Track medicine taken status."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO medicine_tracking (
                reminder_id, patient_id, scheduled_time, taken_time, status
            ) VALUES (?, ?, CURRENT_TIMESTAMP, ?, ?)
        ''', (
            reminder_id, patient_id,
            datetime.now() if taken else None,
            "taken" if taken else "missed"
        ))
        conn.commit()
        return True

def get_medicine_adherence(patient_id: int, days: int = 30) -> float:
    """Calculate medicine adherence percentage."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN status = 'taken' THEN 1 ELSE 0 END) as taken
            FROM medicine_tracking
            WHERE patient_id = ?
            AND scheduled_time >= datetime('now', ?)
        ''', (patient_id, f'-{days} days'))
        
        result = cursor.fetchone()
        if result and result["total"] > 0:
            return (result["taken"] / result["total"]) * 100
        return 100.0

# ============== Hospital Operations ==============

def get_hospitals(city: str = None, hospital_type: str = None) -> List[Dict[str, Any]]:
    """Get list of hospitals."""
    with get_db() as conn:
        cursor = conn.cursor()
        
        query = "SELECT * FROM hospitals WHERE is_active = 1"
        params = []
        
        if city:
            query += " AND city = ?"
            params.append(city)
        if hospital_type:
            query += " AND type = ?"
            params.append(hospital_type)
        
        cursor.execute(query, params)
        return [dict(row) for row in cursor.fetchall()]

def get_hospital_doctors(hospital_id: int, specialization: str = None) -> List[Dict[str, Any]]:
    """Get doctors in a hospital."""
    with get_db() as conn:
        cursor = conn.cursor()
        
        query = '''
            SELECT d.*, u.first_name, u.last_name, u.email, u.phone
            FROM doctors d
            JOIN users u ON d.user_id = u.id
            WHERE d.hospital_id = ? AND d.is_active = 1
        '''
        params = [hospital_id]
        
        if specialization:
            query += " AND d.specialization = ?"
            params.append(specialization)
        
        cursor.execute(query, params)
        return [dict(row) for row in cursor.fetchall()]

def search_patient_by_health_id(health_id: str) -> Optional[Dict[str, Any]]:
    """Search patient by Health ID."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT u.*, hp.allergies, hp.chronic_conditions, hp.current_medications
            FROM users u
            LEFT JOIN health_profiles hp ON u.id = hp.user_id
            WHERE u.health_id = ? AND u.role = 'patient'
        ''', (health_id,))
        result = cursor.fetchone()
        return dict(result) if result else None

# ============== Lab Report Operations ==============

def create_lab_report(
    patient_id: int,
    test_name: str,
    test_category: str,
    results: Dict,
    hospital_id: int = None,
    consultation_id: int = None,
    normal_range: str = None,
    interpretation: str = None
) -> Dict[str, Any]:
    """Create a lab report."""
    with get_db() as conn:
        cursor = conn.cursor()
        
        report_id = generate_unique_id("LAB")
        
        cursor.execute('''
            INSERT INTO lab_reports (
                report_id, patient_id, consultation_id, hospital_id,
                test_name, test_category, test_date, results,
                normal_range, interpretation
            ) VALUES (?, ?, ?, ?, ?, ?, date('now'), ?, ?, ?)
        ''', (
            report_id, patient_id, consultation_id, hospital_id,
            test_name, test_category, json.dumps(results),
            normal_range, interpretation
        ))
        
        conn.commit()
        return {"success": True, "report_id": report_id}

def get_patient_lab_reports(patient_id: int, limit: int = 20) -> List[Dict[str, Any]]:
    """Get patient's lab reports."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT lr.*, h.name as hospital_name
            FROM lab_reports lr
            LEFT JOIN hospitals h ON lr.hospital_id = h.id
            WHERE lr.patient_id = ?
            ORDER BY lr.test_date DESC
            LIMIT ?
        ''', (patient_id, limit))
        return [dict(row) for row in cursor.fetchall()]

# ============== Pharmacy Operations ==============

def dispense_prescription(
    prescription_id: str,
    pharmacy_id: int,
    pharmacist_id: int,
    medicines_dispensed: List[Dict],
    total_amount: float
) -> bool:
    """Mark prescription as dispensed."""
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Update prescription
        cursor.execute('''
            UPDATE prescriptions
            SET is_dispensed = 1, dispensed_at = CURRENT_TIMESTAMP, dispensed_by = ?
            WHERE prescription_id = ?
        ''', (pharmacist_id, prescription_id))
        
        # Get prescription details
        cursor.execute("SELECT patient_id, id FROM prescriptions WHERE prescription_id = ?", 
                      (prescription_id,))
        presc = cursor.fetchone()
        
        if presc:
            # Create transaction
            transaction_id = generate_unique_id("TXN")
            cursor.execute('''
                INSERT INTO pharmacy_transactions (
                    transaction_id, pharmacy_id, patient_id, prescription_id,
                    medicines_dispensed, total_amount
                ) VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                transaction_id, pharmacy_id, presc["patient_id"], presc["id"],
                json.dumps(medicines_dispensed), total_amount
            ))
        
        conn.commit()
        return True

# ============== Document Operations ==============

def upload_external_document(
    patient_id: int,
    document_type: str,
    document_name: str,
    document_data: bytes,
    description: str = None,
    source: str = None,
    document_date: date = None
) -> bool:
    """Upload external document."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO external_documents (
                patient_id, document_type, document_name, document_data,
                description, source, document_date
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            patient_id, document_type, document_name, document_data,
            description, source, document_date
        ))
        conn.commit()
        return True

def get_patient_documents(patient_id: int) -> List[Dict[str, Any]]:
    """Get patient's uploaded documents."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, document_type, document_name, description, source,
                   document_date, uploaded_at
            FROM external_documents
            WHERE patient_id = ?
            ORDER BY uploaded_at DESC
        ''', (patient_id,))
        return [dict(row) for row in cursor.fetchall()]

# ============== Notification Operations ==============

def create_notification(
    user_id: int,
    title: str,
    message: str,
    notification_type: str = "info"
) -> bool:
    """Create a notification."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO notifications (user_id, title, message, notification_type)
            VALUES (?, ?, ?, ?)
        ''', (user_id, title, message, notification_type))
        conn.commit()
        return True

def get_notifications(user_id: int, unread_only: bool = False) -> List[Dict[str, Any]]:
    """Get user notifications."""
    with get_db() as conn:
        cursor = conn.cursor()
        
        query = "SELECT * FROM notifications WHERE user_id = ?"
        if unread_only:
            query += " AND is_read = 0"
        query += " ORDER BY created_at DESC LIMIT 50"
        
        cursor.execute(query, (user_id,))
        return [dict(row) for row in cursor.fetchall()]

def mark_notification_read(notification_id: int) -> bool:
    """Mark notification as read."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE notifications SET is_read = 1 WHERE id = ?", (notification_id,))
        conn.commit()
        return True

# Import timedelta for prescription validity
from datetime import timedelta
# In models.py

_consent_store = []

def get_patient_consents(patient_id, status=None):
    records = [c for c in _consent_store if c["patient_id"] == patient_id]
    if status:
        records = [r for r in records if r.get("status") == status]
    return records

def create_consent_record(patient_id, entity_name, entity_type, data_type, purpose, valid_till):
    new_record = {
        "id": len(_consent_store) + 1,
        "patient_id": patient_id,
        "entity_name": entity_name,
        "entity_type": entity_type,
        "data_type": ", ".join(data_type),
        "purpose": purpose,
        "granted_on": str(date.today()),
        "valid_till": str(valid_till),
        "status": "active"
    }
    _consent_store.append(new_record)
    return new_record

def revoke_consent(consent_id):
    for c in _consent_store:
        if c["id"] == consent_id:
            c["status"] = "revoked"
            return True
    return False
