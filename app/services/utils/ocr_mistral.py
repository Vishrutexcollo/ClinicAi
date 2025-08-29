# app/services/utils/ocr_mistral.py
import os
from openai import OpenAI
from app.config import OPENAI_API_KEY

_client = OpenAI(api_key=OPENAI_API_KEY or os.getenv("OPENAI_API_KEY", ""))

def extract_prescription_text(image_url: str) -> str:
    """
    Extract ONLY the readable text from a prescription image URL.
    Return a plain text string; on error return empty string.
    """
    if not image_url:
        return ""
    try:
        resp = _client.chat.completions.create(
            model="gpt-4o-mini",
            temperature=0.0,
            messages=[{
                "role": "user",
                "content": [
                    {"type": "text", "text": "Extract only the readable text from this prescription image."},
                    {"type": "image_url", "image_url": {"url": image_url}},
                ],
            }],
        )
        return (resp.choices[0].message.content or "").strip()
    except Exception:
        return ""
