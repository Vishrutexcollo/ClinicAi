import openai
from config import OPENAI_API_KEY

openai.api_key = OPENAI_API_KEY

def generate_soap_from_transcript(structured_transcript: dict) -> str:
    prompt = f"Generate a SOAP summary for: {structured_transcript}"
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}]
    )
    return response['choices'][0]['message']['content']
