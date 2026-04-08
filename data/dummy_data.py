"""Dummy data generation for testing."""

import random
import uuid
from datetime import datetime, timedelta
from database import get_db
from auth import hash_password, generate_unique_id, generate_health_id
from config import MOCK_HOSPITALS, MOCK_SPECIALIZATIONS, BLOOD_GROUPS
import json

def create_dummy_data():
    """Create dummy data for testing."""
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Check if data already exists
        cursor.execute("SELECT COUNT(*) FROM users")
        if cursor.fetchone()[0] > 0:
            print("Dummy data already exists!")
            return
        
        print("Creating dummy data...")
        
        # Create hospitals
        hospital_ids = []
        for i, hosp in enumerate(MOCK_HOSPITALS):
            hospital_id = f"HOS-{datetime.now().strftime('%Y%m%d')}-{str(i+1).zfill(5)}"
            cursor.execute('''
                INSERT INTO hospitals (hospital_id, name, type, city, address, phone, email, specializations)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                hospital_id,
                hosp["name"],
                hosp["type"],
                hosp["city"],
                f"{random.randint(1, 999)} Medical Avenue, {hosp['city']}",
                f"+1-555-{random.randint(100, 999)}-{random.randint(1000, 9999)}",
                f"info@{hosp['name'].lower().replace(' ', '')}.com",
                json.dumps(random.sample(MOCK_SPECIALIZATIONS, 5))
            ))
            hospital_ids.append(cursor.lastrowid)
        
        # Create pharmacies
        for i, hosp_id in enumerate(hospital_ids):
            pharmacy_id = f"PHR-{datetime.now().strftime('%Y%m%d')}-{str(i+1).zfill(5)}"
            cursor.execute('''
                INSERT INTO pharmacies (pharmacy_id, name, hospital_id, is_hospital_pharmacy, city)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                pharmacy_id,
                f"{MOCK_HOSPITALS[i]['name']} Pharmacy",
                hosp_id,
                True,
                MOCK_HOSPITALS[i]['city']
            ))
        
        # Create system admin
        cursor.execute('''
            INSERT INTO users (email, password_hash, role, first_name, last_name, phone)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            "admin@healthconnect.com",
            hash_password("admin123"),
            "system_admin",
            "System",
            "Administrator",
            "+1-555-000-0001"
        ))
        admin_id = cursor.lastrowid
        
        # Create doctors
        doctor_names = [
            ("John", "Smith"), ("Sarah", "Johnson"), ("Michael", "Williams"),
            ("Emily", "Brown"), ("David", "Jones"), ("Lisa", "Davis"),
            ("Robert", "Miller"), ("Jennifer", "Wilson"), ("James", "Taylor"),
            ("Maria", "Anderson")
        ]
        
        doctor_ids = []
        for i, (first, last) in enumerate(doctor_names):
            # Create user
            cursor.execute('''
                INSERT INTO users (email, password_hash, role, first_name, last_name, phone, gender)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                f"dr.{first.lower()}.{last.lower()}@healthconnect.com",
                hash_password("doctor123"),
                "doctor",
                f"Dr. {first}",
                last,
                f"+1-555-{random.randint(100, 999)}-{random.randint(1000, 9999)}",
                random.choice(["Male", "Female"])
            ))
            user_id = cursor.lastrowid
            
            # Create doctor profile
            doctor_id = f"DOC-{datetime.now().strftime('%Y%m%d')}-{str(i+1).zfill(5)}"
            hospital_id = random.choice(hospital_ids)
            spec = random.choice(MOCK_SPECIALIZATIONS)
            
            cursor.execute('''
                INSERT INTO doctors (user_id, hospital_id, doctor_id, specialization, 
                                   qualification, experience_years, consultation_fee)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                user_id,
                hospital_id,
                doctor_id,
                spec,
                random.choice(["MBBS, MD", "MBBS, MS", "MBBS, DM", "MBBS, MCh"]),
                random.randint(5, 25),
                random.choice([500, 750, 1000, 1500, 2000])
            ))
            doctor_ids.append(cursor.lastrowid)
        
        # Create hospital admin
        cursor.execute('''
            INSERT INTO users (email, password_hash, role, first_name, last_name, phone)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            "hospital.admin@cityhospital.com",
            hash_password("hospital123"),
            "hospital_admin",
            "Hospital",
            "Admin",
            "+1-555-100-0001"
        ))
        
        # Create pharmacist
        cursor.execute('''
            INSERT INTO users (email, password_hash, role, first_name, last_name, phone)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            "pharmacist@cityhospital.com",
            hash_password("pharmacy123"),
            "pharmacist",
            "Pharmacy",
            "Staff",
            "+1-555-200-0001"
        ))
        
        # Create sample patients
        patient_data = [
            ("Alice", "Thompson", "alice@email.com", "1990-05-15", "Female", "O+"),
            ("Bob", "Martinez", "bob@email.com", "1985-08-22", "Male", "A+"),
            ("Carol", "Lee", "carol@email.com", "1978-12-03", "Female", "B+"),
            ("Daniel", "Garcia", "daniel@email.com", "1992-03-28", "Male", "AB+"),
            ("Emma", "Wilson", "emma@email.com", "1988-11-10", "Female", "O-"),
        ]
        
        patient_ids = []
        for first, last, email, dob, gender, blood in patient_data:
            health_id = f"HC-{uuid.uuid4().hex[:8].upper()}"
            cursor.execute('''
                INSERT INTO users (health_id, email, password_hash, role, first_name, last_name,
                                 date_of_birth, gender, blood_group, phone, address, city, consent_given)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                health_id,
                email,
                hash_password("patient123"),
                "patient",
                first,
                last,
                dob,
                gender,
                blood,
                f"+1-555-{random.randint(100, 999)}-{random.randint(1000, 9999)}",
                f"{random.randint(1, 999)} Patient Street",
                random.choice(["New York", "Los Angeles", "Chicago"]),
                True
            ))
            patient_id = cursor.lastrowid
            patient_ids.append(patient_id)
            
            # Create health profile
            cursor.execute('''
                INSERT INTO health_profiles (user_id, allergies, chronic_conditions, current_medications)
                VALUES (?, ?, ?, ?)
            ''', (
                patient_id,
                json.dumps(random.sample(["Penicillin", "Pollen", "Dust", "None"], 2)),
                json.dumps(random.sample(["Hypertension", "Diabetes Type 2", "None"], 1)),
                json.dumps(["Vitamin D", "Multivitamin"])
            ))
        
        # Create sample consultations and prescriptions
        symptoms_list = [
            "Headache and fatigue",
            "Fever and body aches",
            "Cough and cold",
            "Stomach pain",
            "Back pain",
            "Skin rash",
            "Dizziness"
        ]
        
        diagnoses_list = [
            "Viral infection",
            "Common cold",
            "Migraine",
            "Gastritis",
            "Muscular strain",
            "Allergic reaction",
            "Hypertension"
        ]
        
        medicines_list = [
            {"name": "Paracetamol", "dosage": "500mg", "frequency": "Twice daily", "duration": "5 days"},
            {"name": "Amoxicillin", "dosage": "250mg", "frequency": "Three times daily", "duration": "7 days"},
            {"name": "Omeprazole", "dosage": "20mg", "frequency": "Once daily", "duration": "14 days"},
            {"name": "Cetirizine", "dosage": "10mg", "frequency": "Once daily", "duration": "10 days"},
            {"name": "Ibuprofen", "dosage": "400mg", "frequency": "As needed", "duration": "5 days"},
        ]
        
        for patient_id in patient_ids:
            # Create 3-5 consultations per patient
            for _ in range(random.randint(3, 5)):
                consultation_id = generate_unique_id("CON")
                doctor_db_id = random.choice(doctor_ids)
                hospital_id = random.choice(hospital_ids)
                
                consultation_date = datetime.now() - timedelta(days=random.randint(1, 180))
                
                cursor.execute('''
                    INSERT INTO consultations (consultation_id, patient_id, doctor_id, hospital_id,
                                             consultation_date, symptoms, diagnosis, notes, 
                                             vitals, consultation_type)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    consultation_id,
                    patient_id,
                    doctor_db_id,
                    hospital_id,
                    consultation_date,
                    random.choice(symptoms_list),
                    random.choice(diagnoses_list),
                    "Patient advised rest and medication. Follow-up in 1 week if symptoms persist.",
                    json.dumps({
                        "bp_systolic": random.randint(110, 140),
                        "bp_diastolic": random.randint(70, 90),
                        "pulse": random.randint(70, 90),
                        "temperature": round(random.uniform(98.0, 99.5), 1),
                        "weight": random.randint(50, 90)
                    }),
                    random.choice(["in-person", "teleconsultation"])
                ))
                
                consultation_db_id = cursor.lastrowid
                
                # Create prescription
                prescription_id = generate_unique_id("PRX")
                selected_medicines = random.sample(medicines_list, random.randint(1, 3))
                
                cursor.execute('''
                    INSERT INTO prescriptions (prescription_id, consultation_id, patient_id, doctor_id,
                                             medicines, instructions, valid_till)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    prescription_id,
                    consultation_db_id,
                    patient_id,
                    doctor_db_id,
                    json.dumps(selected_medicines),
                    "Take medicines after food. Complete the full course.",
                    (datetime.now() + timedelta(days=30)).date()
                ))
        
        # Create sample health metrics
        metric_types = [
            ("blood_pressure", "mmHg", (110, 140), (70, 90)),
            ("blood_sugar", "mg/dL", (80, 140), None),
            ("weight", "kg", (50, 90), None),
            ("heart_rate", "bpm", (60, 100), None)
        ]
        
        for patient_id in patient_ids:
            for metric_type, unit, (min_val, max_val), secondary_range in metric_types:
                # Create 10-20 readings per metric
                for i in range(random.randint(10, 20)):
                    measured_at = datetime.now() - timedelta(days=random.randint(0, 90))
                    secondary = None
                    if secondary_range:
                        secondary = random.randint(secondary_range[0], secondary_range[1])
                    
                    cursor.execute('''
                        INSERT INTO health_metrics (patient_id, metric_type, value, secondary_value,
                                                  unit, measured_at)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', (
                        patient_id,
                        metric_type,
                        random.randint(min_val, max_val),
                        secondary,
                        unit,
                        measured_at
                    ))
        
        # Create sample appointments
        for patient_id in patient_ids:
            for i in range(random.randint(2, 5)):
                appointment_date = datetime.now() + timedelta(days=random.randint(1, 30))
                appointment_id = generate_unique_id("APT")
                
                cursor.execute('''
                    INSERT INTO appointments (appointment_id, patient_id, doctor_id, hospital_id,
                                            appointment_date, appointment_time, appointment_type,
                                            reason, status)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    appointment_id,
                    patient_id,
                    random.choice(doctor_ids),
                    random.choice(hospital_ids),
                    appointment_date.date(),
                    f"{random.randint(9, 17)}:{random.choice(['00', '30'])}",
                    random.choice(["consultation", "follow-up", "check-up"]),
                    "Regular checkup",
                    "scheduled"
                ))
        
        conn.commit()
        print("Dummy data created successfully!")
        print("\n=== Test Credentials ===")
        print("Patient: alice@email.com / patient123")
        print("Doctor: dr.john.smith@healthconnect.com / doctor123")
        print("Hospital Admin: hospital.admin@cityhospital.com / hospital123")
        print("Pharmacist: pharmacist@cityhospital.com / pharmacy123")
        print("System Admin: admin@healthconnect.com / admin123")

if __name__ == "__main__":
    from database import init_database
    init_database()
    create_dummy_data()
