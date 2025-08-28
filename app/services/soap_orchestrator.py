import os
import openai
from app.db import get_database
from app.models.patient import store_soap_summary, get_note_state



def generate_soap_summary(patient_id: str):
    db = get_database()
    note_state = get_note_state(db, patient_id)
    transcript = note_state["transcript"]

    if not transcript:
        return {"error": "Transcript not found for this visit."}

    prompt = (
        "You are a clinical assistant. Given this doctor-patient consultation transcript, "
        "create a SOAP note (Subjective, Objective, Assessment, Plan) in JSON format."
        "Keep it short and structured.\n\nTranscript:\n" + transcript
    )

    messages = [
        {"role": "system", "content": "You're an AI that writes SOAP summaries for doctors."},
        {"role": "user", "content": prompt}
    ]

    res = openai.ChatCompletion.create(
        model="gpt-4",
        messages=messages,
        temperature=0.4,
        max_tokens=500
    )

    text_output = res.choices[0].message["content"].strip()

    # Optionally parse as dict — or just store raw if GPT returns JSON
    import json
    try:
        soap_dict = json.loads(text_output)
    except json.JSONDecodeError:
        soap_dict = {"raw_text": text_output}

    store_soap_summary(db, patient_id, soap_dict)
    return {"soap_summary": soap_dict}
