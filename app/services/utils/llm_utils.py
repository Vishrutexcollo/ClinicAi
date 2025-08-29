# app/services/utils/llm_utils.py
import os
from openai import OpenAI
from app.config import OPENAI_API_KEY

_client = OpenAI(api_key=OPENAI_API_KEY or os.getenv("OPENAI_API_KEY", ""))

def generate_soap_from_transcript(structured_transcript: dict) -> str:
    prompt = (
        "Create a concise SOAP (Subjective, Objective, Assessment, Plan) note in JSON. "
        "Use short clinical phrases. If you cannot produce valid JSON, output a minimal JSON "
        'like {"raw_text": "..."}.\n\n'
        f"Transcript: {structured_transcript}"
    )
    resp = _client.chat.completions.create(
        model="gpt-4o-mini",
        temperature=0.3,
        messages=[{"role": "user", "content": prompt}],
    )
    return resp.choices[0].message.content or ""
