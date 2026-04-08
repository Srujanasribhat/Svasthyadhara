"""QR Code generation for health records."""

import qrcode
from io import BytesIO
import base64
import json

def generate_health_qr(health_id: str, patient_name: str, blood_group: str = None, 
                       allergies: list = None, emergency_contact: str = None) -> bytes:
    """Generate emergency QR code with basic health info."""
    data = {
        "health_id": health_id,
        "name": patient_name,
        "blood_group": blood_group,
        "allergies": allergies[:3] if allergies else [],  # Limit to 3
        "emergency_contact": emergency_contact,
        "type": "emergency_health_card"
    }
    
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(json.dumps(data))
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    
    buffer = BytesIO()
    img.save(buffer, format='PNG')
    return buffer.getvalue()

def generate_prescription_qr(prescription_id: str, patient_health_id: str, 
                             doctor_name: str, valid_till: str) -> bytes:
    """Generate QR code for prescription verification."""
    data = {
        "prescription_id": prescription_id,
        "patient_health_id": patient_health_id,
        "doctor": doctor_name,
        "valid_till": valid_till,
        "type": "prescription"
    }
    
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=8,
        border=4,
    )
    qr.add_data(json.dumps(data))
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="darkblue", back_color="white")
    
    buffer = BytesIO()
    img.save(buffer, format='PNG')
    return buffer.getvalue()

def decode_qr_data(qr_data: str) -> dict:
    """Decode QR data JSON."""
    try:
        return json.loads(qr_data)
    except:
        return None