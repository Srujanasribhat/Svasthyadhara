"""Database initialization and connection management."""

import sqlite3
import os
from contextlib import contextmanager
from config import DATABASE_PATH

def get_connection():
    """Get database connection."""
    conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

@contextmanager
def get_db():
    """Context manager for database connections."""
    conn = get_connection()
    try:
        yield conn
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

def init_database():
    """Initialize database with all required tables."""
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                health_id TEXT UNIQUE,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL,
                first_name TEXT NOT NULL,
                last_name TEXT NOT NULL,
                phone TEXT,
                date_of_birth DATE,
                gender TEXT,
                blood_group TEXT,
                address TEXT,
                city TEXT,
                state TEXT,
                pincode TEXT,
                emergency_contact TEXT,
                emergency_phone TEXT,
                profile_image BLOB,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_active BOOLEAN DEFAULT 1,
                consent_given BOOLEAN DEFAULT 0,
                linked_family_ids TEXT
            )
        ''')
        
        # Hospitals table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS hospitals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                hospital_id TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                type TEXT,
                address TEXT,
                city TEXT,
                state TEXT,
                pincode TEXT,
                phone TEXT,
                email TEXT,
                website TEXT,
                specializations TEXT,
                facilities TEXT,
                bed_count INTEGER,
                emergency_available BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_active BOOLEAN DEFAULT 1
            )
        ''')
        
        # Doctors table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS doctors (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER REFERENCES users(id),
                hospital_id INTEGER REFERENCES hospitals(id),
                doctor_id TEXT UNIQUE NOT NULL,
                specialization TEXT,
                qualification TEXT,
                experience_years INTEGER,
                license_number TEXT,
                consultation_fee DECIMAL(10,2),
                available_days TEXT,
                available_hours TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_active BOOLEAN DEFAULT 1
            )
        ''')
        
        # Patient health profiles
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS health_profiles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER UNIQUE REFERENCES users(id),
                allergies TEXT,
                chronic_conditions TEXT,
                current_medications TEXT,
                past_surgeries TEXT,
                family_history TEXT,
                lifestyle_info TEXT,
                vaccination_records TEXT,
                insurance_provider TEXT,
                insurance_policy_number TEXT,
                insurance_valid_till DATE,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Consultations table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS consultations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                consultation_id TEXT UNIQUE NOT NULL,
                patient_id INTEGER REFERENCES users(id),
                doctor_id INTEGER REFERENCES doctors(id),
                hospital_id INTEGER REFERENCES hospitals(id),
                appointment_id INTEGER REFERENCES appointments(id),
                consultation_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                symptoms TEXT,
                diagnosis TEXT,
                notes TEXT,
                vitals TEXT,
                follow_up_date DATE,
                follow_up_notes TEXT,
                consultation_type TEXT DEFAULT 'in-person',
                status TEXT DEFAULT 'completed',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Prescriptions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS prescriptions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                prescription_id TEXT UNIQUE NOT NULL,
                consultation_id INTEGER REFERENCES consultations(id),
                patient_id INTEGER REFERENCES users(id),
                doctor_id INTEGER REFERENCES doctors(id),
                medicines TEXT NOT NULL,
                instructions TEXT,
                valid_till DATE,
                qr_code TEXT,
                is_dispensed BOOLEAN DEFAULT 0,
                dispensed_at TIMESTAMP,
                dispensed_by INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Lab reports table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS lab_reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                report_id TEXT UNIQUE NOT NULL,
                patient_id INTEGER REFERENCES users(id),
                consultation_id INTEGER REFERENCES consultations(id),
                hospital_id INTEGER REFERENCES hospitals(id),
                test_name TEXT NOT NULL,
                test_category TEXT,
                test_date DATE,
                results TEXT,
                normal_range TEXT,
                interpretation TEXT,
                report_file BLOB,
                report_file_name TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Appointments table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS appointments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                appointment_id TEXT UNIQUE NOT NULL,
                patient_id INTEGER REFERENCES users(id),
                doctor_id INTEGER REFERENCES doctors(id),
                hospital_id INTEGER REFERENCES hospitals(id),
                appointment_date DATE NOT NULL,
                appointment_time TIME NOT NULL,
                appointment_type TEXT DEFAULT 'consultation',
                reason TEXT,
                status TEXT DEFAULT 'scheduled',
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Medicine reminders table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS medicine_reminders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                patient_id INTEGER REFERENCES users(id),
                prescription_id INTEGER REFERENCES prescriptions(id),
                medicine_name TEXT NOT NULL,
                dosage TEXT,
                frequency TEXT,
                time_slots TEXT,
                start_date DATE,
                end_date DATE,
                is_active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Medicine tracking (adherence)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS medicine_tracking (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                reminder_id INTEGER REFERENCES medicine_reminders(id),
                patient_id INTEGER REFERENCES users(id),
                scheduled_time TIMESTAMP,
                taken_time TIMESTAMP,
                status TEXT DEFAULT 'pending',
                notes TEXT
            )
        ''')
        
        # Health metrics tracking
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS health_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                patient_id INTEGER REFERENCES users(id),
                metric_type TEXT NOT NULL,
                value DECIMAL(10,2),
                secondary_value DECIMAL(10,2),
                unit TEXT,
                measured_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                notes TEXT
            )
        ''')
        
        # Pharmacies table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS pharmacies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pharmacy_id TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                hospital_id INTEGER REFERENCES hospitals(id),
                address TEXT,
                city TEXT,
                phone TEXT,
                email TEXT,
                is_hospital_pharmacy BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_active BOOLEAN DEFAULT 1
            )
        ''')
        
        # Pharmacy transactions
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS pharmacy_transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                transaction_id TEXT UNIQUE NOT NULL,
                pharmacy_id INTEGER REFERENCES pharmacies(id),
                patient_id INTEGER REFERENCES users(id),
                prescription_id INTEGER REFERENCES prescriptions(id),
                medicines_dispensed TEXT,
                total_amount DECIMAL(10,2),
                bill_image BLOB,
                transaction_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # External documents (uploaded by patients)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS external_documents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                patient_id INTEGER REFERENCES users(id),
                document_type TEXT,
                document_name TEXT,
                document_data BLOB,
                description TEXT,
                source TEXT,
                document_date DATE,
                uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Consent logs
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS consent_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                patient_id INTEGER REFERENCES users(id),
                requester_id INTEGER,
                requester_type TEXT,
                purpose TEXT,
                consent_given BOOLEAN,
                consent_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expiry_date TIMESTAMP,
                revoked_at TIMESTAMP
            )
        ''')
        
        # Notifications table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS notifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER REFERENCES users(id),
                title TEXT,
                message TEXT,
                notification_type TEXT,
                is_read BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        print("Database initialized successfully!")

if __name__ == "__main__":
    init_database()
