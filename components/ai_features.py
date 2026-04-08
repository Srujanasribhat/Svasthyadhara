"""AI/Smart features - Rule-based implementations."""

from typing import Dict, List, Tuple
import re

# Symptom checker rules (simplified rule-based system)
SYMPTOM_RULES = {
    "common_cold": {
        "symptoms": ["runny nose", "sneezing", "sore throat", "cough", "congestion"],
        "min_match": 3,
        "severity": "mild",
        "recommendation": "Rest, stay hydrated, and consider over-the-counter cold medications. See a doctor if symptoms persist beyond 10 days."
    },
    "flu": {
        "symptoms": ["fever", "body aches", "fatigue", "headache", "cough", "chills"],
        "min_match": 4,
        "severity": "moderate",
        "recommendation": "Rest and stay hydrated. Consider antiviral medications if within 48 hours of symptom onset. Seek medical attention if breathing becomes difficult."
    },
    "migraine": {
        "symptoms": ["severe headache", "nausea", "light sensitivity", "throbbing pain", "vision changes"],
        "min_match": 3,
        "severity": "moderate",
        "recommendation": "Rest in a dark, quiet room. Take prescribed migraine medication. Seek emergency care if this is your first severe headache or symptoms are different from usual."
    },
    "gastritis": {
        "symptoms": ["stomach pain", "nausea", "bloating", "indigestion", "loss of appetite"],
        "min_match": 3,
        "severity": "mild",
        "recommendation": "Avoid spicy and acidic foods. Eat smaller meals. Consider antacids. See a doctor if symptoms persist or worsen."
    },
    "anxiety": {
        "symptoms": ["worry", "restlessness", "rapid heartbeat", "sweating", "difficulty concentrating", "sleep problems"],
        "min_match": 4,
        "severity": "moderate",
        "recommendation": "Practice deep breathing and relaxation techniques. Consider speaking with a mental health professional. Seek immediate help if experiencing panic attacks."
    },
    "allergic_reaction": {
        "symptoms": ["itching", "rash", "swelling", "sneezing", "watery eyes", "hives"],
        "min_match": 3,
        "severity": "moderate",
        "recommendation": "Identify and avoid allergen. Take antihistamines. Seek emergency care immediately if experiencing difficulty breathing or throat swelling."
    }
}

# Drug interaction database (simplified)
DRUG_INTERACTIONS = {
    ("aspirin", "warfarin"): {
        "severity": "high",
        "effect": "Increased risk of bleeding",
        "recommendation": "Avoid combination or use with extreme caution under medical supervision"
    },
    ("ibuprofen", "aspirin"): {
        "severity": "moderate",
        "effect": "Reduced cardioprotective effect of aspirin",
        "recommendation": "Take aspirin at least 30 minutes before ibuprofen"
    },
    ("metformin", "alcohol"): {
        "severity": "high",
        "effect": "Increased risk of lactic acidosis and hypoglycemia",
        "recommendation": "Limit alcohol consumption while on metformin"
    },
    ("lisinopril", "potassium"): {
        "severity": "moderate",
        "effect": "Risk of hyperkalemia (high potassium levels)",
        "recommendation": "Monitor potassium levels regularly"
    },
    ("simvastatin", "grapefruit"): {
        "severity": "moderate",
        "effect": "Increased drug concentration and side effects",
        "recommendation": "Avoid grapefruit and grapefruit juice"
    },
    ("amoxicillin", "methotrexate"): {
        "severity": "moderate",
        "effect": "Reduced methotrexate clearance",
        "recommendation": "Monitor for methotrexate toxicity"
    }
}

# Health risk factors
RISK_FACTORS = {
    "cardiovascular": {
        "high_bp": 2,
        "diabetes": 2,
        "smoking": 3,
        "obesity": 2,
        "sedentary": 1,
        "family_history": 2,
        "high_cholesterol": 2,
        "age_over_45": 1
    },
    "diabetes": {
        "obesity": 3,
        "sedentary": 2,
        "family_history": 3,
        "high_bp": 1,
        "age_over_40": 1,
        "pcos": 2
    }
}

def check_symptoms(symptoms_input: str) -> List[Dict]:
    """
    Analyze symptoms and suggest possible conditions.
    This is a simplified rule-based system for demonstration.
    """
    symptoms_lower = symptoms_input.lower()
    results = []
    
    for condition, rules in SYMPTOM_RULES.items():
        matched = sum(1 for symptom in rules["symptoms"] if symptom in symptoms_lower)
        
        if matched >= rules["min_match"]:
            confidence = min(95, (matched / len(rules["symptoms"])) * 100)
            results.append({
                "condition": condition.replace("_", " ").title(),
                "confidence": round(confidence),
                "severity": rules["severity"],
                "matched_symptoms": matched,
                "total_symptoms": len(rules["symptoms"]),
                "recommendation": rules["recommendation"]
            })
    
    # Sort by confidence
    results.sort(key=lambda x: x["confidence"], reverse=True)
    
    # Add disclaimer
    if results:
        for r in results:
            r["disclaimer"] = "This is not a medical diagnosis. Please consult a healthcare professional for proper evaluation."
    
    return results

def check_drug_interactions(medicines: List[str]) -> List[Dict]:
    """
    Check for potential drug interactions.
    Simplified rule-based check.
    """
    interactions = []
    medicines_lower = [m.lower().strip() for m in medicines]
    
    for i, drug1 in enumerate(medicines_lower):
        for drug2 in medicines_lower[i+1:]:
            # Check both orderings
            key1 = (drug1, drug2)
            key2 = (drug2, drug1)
            
            interaction = DRUG_INTERACTIONS.get(key1) or DRUG_INTERACTIONS.get(key2)
            
            if interaction:
                interactions.append({
                    "drug1": drug1.title(),
                    "drug2": drug2.title(),
                    **interaction
                })
    
    return interactions

def calculate_health_risk(risk_type: str, factors: List[str]) -> Dict:
    """
    Calculate health risk score based on factors.
    """
    if risk_type not in RISK_FACTORS:
        return {"error": "Unknown risk type"}
    
    risk_weights = RISK_FACTORS[risk_type]
    total_possible = sum(risk_weights.values())
    actual_score = sum(risk_weights.get(f.lower().replace(" ", "_"), 0) for f in factors)
    
    risk_percentage = (actual_score / total_possible) * 100
    
    if risk_percentage < 20:
        level = "Low"
        color = "green"
    elif risk_percentage < 40:
        level = "Moderate"
        color = "yellow"
    elif risk_percentage < 60:
        level = "Elevated"
        color = "orange"
    else:
        level = "High"
        color = "red"
    
    return {
        "risk_type": risk_type.title(),
        "score": actual_score,
        "max_score": total_possible,
        "percentage": round(risk_percentage, 1),
        "level": level,
        "color": color,
        "factors_identified": factors,
        "recommendation": get_risk_recommendations(risk_type, level)
    }

def get_risk_recommendations(risk_type: str, level: str) -> List[str]:
    """Get recommendations based on risk type and level."""
    recommendations = {
        "cardiovascular": {
            "Low": ["Maintain healthy lifestyle", "Regular exercise", "Balanced diet"],
            "Moderate": ["Consider lifestyle modifications", "Regular BP monitoring", "Reduce salt intake"],
            "Elevated": ["Consult a cardiologist", "Regular health checkups", "Medication review"],
            "High": ["Immediate medical consultation", "Comprehensive cardiac evaluation", "Strict lifestyle changes"]
        },
        "diabetes": {
            "Low": ["Maintain healthy weight", "Regular exercise", "Balanced diet"],
            "Moderate": ["Annual blood sugar testing", "Reduce sugar intake", "Increase physical activity"],
            "Elevated": ["Quarterly blood sugar monitoring", "Consult endocrinologist", "Diet modification"],
            "High": ["Immediate medical consultation", "Regular HbA1c testing", "Comprehensive diabetes screening"]
        }
    }
    
    return recommendations.get(risk_type, {}).get(level, ["Consult a healthcare professional"])

def generate_smart_alerts(patient_data: Dict) -> List[Dict]:
    """
    Generate smart alerts based on patient data.
    """
    alerts = []
    
    # Check for upcoming appointments
    if patient_data.get("upcoming_appointments"):
        for apt in patient_data["upcoming_appointments"][:3]:
            alerts.append({
                "type": "appointment",
                "priority": "medium",
                "title": "Upcoming Appointment",
                "message": f"Appointment with {apt.get('doctor_name', 'Doctor')} on {apt.get('date', 'N/A')}",
                "action": "View appointment details"
            })
    
    # Check medicine adherence
    adherence = patient_data.get("medicine_adherence", 100)
    if adherence < 80:
        alerts.append({
            "type": "medicine",
            "priority": "high",
            "title": "Low Medicine Adherence",
            "message": f"Your medicine adherence is {adherence}%. Regular medication is important for your health.",
            "action": "View medicine schedule"
        })
    
    # Check for overdue follow-ups
    if patient_data.get("overdue_followups"):
        alerts.append({
            "type": "followup",
            "priority": "high",
            "title": "Overdue Follow-up",
            "message": "You have overdue follow-up appointments. Please schedule them soon.",
            "action": "Book follow-up"
        })
    
    # Check health metrics
    if patient_data.get("high_bp_readings", 0) > 2:
        alerts.append({
            "type": "health",
            "priority": "high",
            "title": "Elevated Blood Pressure",
            "message": "Multiple high BP readings detected. Please consult your doctor.",
            "action": "View health metrics"
        })
    
    return alerts
