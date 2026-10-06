import os
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from app.api.routes import router
from app.config import FRONTEND_DIR, UPLOADS_DIR

app = FastAPI(
    title="Smart College Complaint Resolution Agent",
    description="Agentic AI-powered college grievance ingestion, automated routing, priority calculation, incident clustering, and SLA escalation system.",
    version="1.0.0"
)

# CORS middleware for development flexibility
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API endpoints
app.include_router(router)


# Mount static uploads
if UPLOADS_DIR.exists():
    app.mount("/uploads", StaticFiles(directory=str(UPLOADS_DIR)), name="uploads")

# Mount static assets from frontend
if FRONTEND_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")

    @app.get("/", include_in_schema=False)
    async def serve_student_portal():
        return FileResponse(FRONTEND_DIR / "index.html")

    @app.get("/student-login", include_in_schema=False)
    @app.get("/login", include_in_schema=False)
    async def serve_student_login():
        login_file = FRONTEND_DIR / "student_login.html"
        if login_file.exists():
            return FileResponse(login_file)
        return FileResponse(FRONTEND_DIR / "index.html")

    @app.get("/admin", include_in_schema=False)
    async def serve_admin_portal():
        return FileResponse(FRONTEND_DIR / "admin.html")
