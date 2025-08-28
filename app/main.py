from fastapi import FastAPI
from app.routers import intake , consultation
app = FastAPI()
app.include_router(intake.router)
app.include_router(consultation.router)
# app.include_router(postvisit.router)
