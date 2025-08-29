from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Import your routers
from app.routers import intake, consultation, postvisit

app = FastAPI(
    title="Clinic AI Backend",
    description="API backend for Clinic AI - patient intake, consultation, and post-visit processing.",
    version="1.0.0"
)

# CORS configuration (adjust origins as needed)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # You can replace this with specific frontend URL(s)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(intake.router)
app.include_router(consultation.router)
app.include_router(postvisit.router)  # Optional: comment out if not implemented yet

@app.get("/")
def read_root():
    return {"message": "Clinic AI backend is running"}
