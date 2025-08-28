# from fastapi import APIRouter, UploadFile, Form, File
# from fastapi.responses import JSONResponse
# from app.db import get_mongo_client
# from utils.ocr_mistral import extract_prescription_text
# from utils.llm import generate_postvisit_summary
# import os

# router = APIRouter()

# @router.post("/postvisit")
# async def handle_post_visit(
#     patient_id: str = Form(...),
#     visit_id: str = Form(...),
#     prescription: UploadFile = File(...)
# ):
#     # Step 1: Save prescription image locally
#     content = await prescription.read()
#     filename = f"temp_{visit_id}_{prescription.filename}"
#     with open(filename, "wb") as f:
#         f.write(content)

#     # Step 2: Extract prescription text using Mistral or other LLM OCR
#     prescription_data = extract_prescription_text(filename)

#     # Clean up temp file
#     try:
#         os.remove(filename)
#     except Exception:
#         pass

#     # Step 3: Fetch existing previsit + SOAP summaries
#     client = get_mongo_client()
#     db = client["doctor_ai"]  # Use your actual DB name here
#     patients = db["patients"]
#     patient = patients.find_one({"patient_id": patient_id})

#     if not patient:
#         return JSONResponse(status_code=404, content={"error": "Patient not found"})

#     visits = patient.get("visits", [])
#     visit = next((v for v in visits if v.get("visit_id") == visit_id), None)

#     if not visit:
#         return JSONResponse(status_code=404, content={"error": "Visit not found"})

#     previsit = visit.get("previsit_summary")
#     soap = visit.get("soap_summary")

#     # Step 4: Generate postvisit summary using prescription + previsit + SOAP
#     postvisit_summary = generate_postvisit_summary(previsit, soap, prescription_data)

#     # Step 5: Update DB with prescription + postvisit_summary
#     patients.update_one(
#         {"patient_id": patient_id, "visits.visit_id": visit_id},
#         {"$set": {
#             "visits.$.prescription_data": prescription_data,
#             "visits.$.postvisit_summary": postvisit_summary
#         }}
#     )

#     return {
#         "message": "Postvisit data saved",
#         "postvisit_summary": postvisit_summary,
#         "prescription_extracted": prescription_data
#     }