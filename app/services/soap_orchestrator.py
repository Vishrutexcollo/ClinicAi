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

    prompt = f"""
        You are a clinical documentation assistant trained to convert doctor-patient consultation transcripts into concise, structured SOAP notes.

        This summary is for **doctor use only** and will be stored in the patient's medical record. It will not be shown to the patient.

        ---

        Your responsibilities:
        - Extract medically relevant information from the transcript.
        - Do not hallucinate or infer anything not explicitly stated.
        - Structure the content as a proper SOAP note in strict JSON format.
        - Keep the language clear, professional, and clinically useful.

        ---

        SECTION-WISE INSTRUCTIONS:

        1. subjective:
        - Include the patient’s reported symptoms, complaints, history of present illness, duration, severity, and any relevant personal or family history.
        - Capture only what the **patient said** (not the doctor).
        - Example: "Patient reports chest pain radiating to the left arm for 2 days."

        2. objective:
        - Include observations made by the doctor during the consultation.
        - Mention physical exam findings, vital signs, lab/imaging results (if shared in transcript), and any clinician remarks.
        - Example: "No chest wall tenderness. BP 130/85. ECG within normal limits."

        3. assessment:
        - Write the doctor’s clinical impression or preliminary diagnosis (if one is suggested).
        - Avoid definitive statements unless the transcript clearly supports it.
        - Example: "Suspected gastroesophageal reflux. Rule out cardiac origin."

        4. plan:
        - Include what the doctor advised: medications, lifestyle changes, diagnostic tests, referrals, or follow-up instructions.
        - Example: "Prescribed omeprazole 20mg. Advised dietary modifications. Recheck in 1 week."

        ---

        DO's:
        - Use medical terms where applicable.
        - Keep sentences brief and direct.
        - Only use information stated in the transcript.
        - Use empty strings for missing sections — do not fabricate.
        - Output strictly valid JSON with no extra comments, markdown, or explanation.

        DON'Ts:
        - Do not include the transcript itself.
        - Do not address the patient.
        - Do not repeat irrelevant or casual conversation.
        - Do not speculate or suggest actions not mentioned by the doctor.

        ---

        Output Format (strictly JSON):

        {{
        "subjective": "<string>",
        "objective": "<string>",
        "assessment": "<string>",
        "plan": "<string>"
        }}

        ---

        Transcript:
        {transcript}
    """

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
