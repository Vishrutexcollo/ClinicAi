# app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import intake, consultation, postvisit

app = FastAPI(
    title="Clinic AI Backend",
    description="API backend for Clinic AI - patient intake, consultation, and post-visit processing.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(intake.router)
app.include_router(consultation.router)
app.include_router(postvisit.router)

@app.get("/")
def read_root():
    return {"message": "Clinic AI backend is running"}
