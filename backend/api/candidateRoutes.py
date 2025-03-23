import logging
import bcrypt
import sqlite3
import base64
from backend.services.databaseService import DATABASE_PATH
from fastapi import APIRouter, UploadFile, File, HTTPException
from pydantic import BaseModel, EmailStr
from backend.services.candidateService import get_candidate, verify_candidate_password, register_new_candidate
from backend.controllers.candidateController import (
    recognize_candidate_live,
    recognize_candidate_from_base64,
    recognize_candidate,
)

# ✅ Setup Logging
logging.basicConfig(
    filename="backend/logs/candidate_routes.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

router = APIRouter()

DATABASE_PATH = "backend/data/voters.db"

# ✅ Define Pydantic Models for Candidate
class CandidateRegistrationModel(BaseModel):
    universityID: str
    firstname: str
    lastname: str
    email: EmailStr
    password: str
    aboutYourself: str
    image: str  # Base64-encoded image

class CandidateLookupModel(BaseModel):
    universityID: str

class CandidatePasswordVerificationModel(BaseModel):
    universityID: str
    inputPassword: str

class Base64ImageRequest(BaseModel):
    image_base64: str  # Base64-encoded image    

# ✅ Candidate Registration API
@router.post("/register")
async def register_candidate_endpoint(candidate: CandidateRegistrationModel):
    """Registers a new candidate in SQLite."""
    try:
        response = register_new_candidate(candidate.dict())
        return response
    except Exception as e:
        logging.error(f"❌ Error registering candidate: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error registering candidate: {str(e)}")

# ✅ Candidate Face Recognition API (File Upload)
@router.post("/recognize")
async def recognize_candidate_endpoint(file: UploadFile = File(...)):
    """Recognizes a candidate using KNN face matching from a file upload."""
    try:
        return await recognize_candidate(file)
    except Exception as e:
        logging.error(f"❌ Candidate face recognition error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Candidate face recognition error: {str(e)}")

# ✅ Candidate Face Recognition API (Base64 Image)
@router.post("/recognize_base64")
async def recognize_candidate_base64_api(request: Base64ImageRequest):
    """Recognizes a candidate using KNN face matching from a Base64-encoded image."""
    try:
        return recognize_candidate_from_base64(request.image_base64)
    except Exception as e:
        logging.error(f"❌ Error recognizing candidate from base64: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error recognizing candidate: {str(e)}")

# ✅ Real-Time Candidate Face Recognition (Webcam)
@router.get("/real_time_recognition")
async def real_time_candidate_recognition():
    """Runs real-time candidate face recognition using the webcam."""
    try:
        return await recognize_candidate_live()  # Ensure recognize_candidate_live is an async function
    except Exception as e:
        logging.error(f"❌ Error running real-time candidate recognition: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error running real-time candidate recognition: {str(e)}")

# ✅ Live Candidate Face Recognition API (Triggered by Frontend)
@router.get("/live_recognition")
async def run_live_candidate_face_recognition():
    """Triggers real-time candidate face recognition via the API (calls the webcam function)."""
    try:
        await recognize_candidate_live()
        return {"status": "success", "message": "Real-time candidate face recognition started!"}
    except Exception as e:
        logging.error(f"❌ Error triggering live candidate recognition: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error triggering live candidate recognition: {str(e)}")

# ✅ Fetch Candidate Details
@router.post("/get_candidate")
async def get_candidate_endpoint(data: CandidateLookupModel):
    """Fetch candidate details from the database."""
    try:
        candidate = get_candidate(data.universityID)
        if not candidate:
            raise HTTPException(status_code=404, detail="Candidate not found")

        return {"status": "success", "candidate": candidate}
    except Exception as e:
        logging.error(f"❌ Error fetching candidate details: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching candidate: {str(e)}")

# ✅ Verify Candidate Password API
@router.post("/verify-password")
async def verify_candidate_password_api(verify_request: CandidatePasswordVerificationModel):
    """Securely verify a candidate's password using bcrypt."""
    try:
        logging.info(f"🔑 Verifying password for candidate: {verify_request.universityID}")

        # ✅ Perform bcrypt password verification
        verification_result = verify_candidate_password(verify_request.universityID, verify_request.inputPassword)

        if verification_result["status"] == "success":
            logging.info(f"✅ Password verified for candidate: {verify_request.universityID}")
            return verification_result
        else:
            logging.warning(f"⚠️ Invalid password for candidate: {verify_request.universityID}")
            raise HTTPException(status_code=401, detail="Invalid password")

    except Exception as e:
        logging.error(f"❌ Error in verify_candidate_password_api: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error verifying password: {str(e)}")


@router.get("/get_all_candidates")
async def get_all_candidates():
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT universityID, firstname, lastname, aboutYourself, image FROM candidates")
        candidates = cursor.fetchall()
        conn.close()

        if not candidates:
            return {"status": "error", "message": "No candidates found."}

        candidate_list = [
            {
                "universityID": candidate[0],
                "firstname": candidate[1],
                "lastname": candidate[2],
                "aboutYourself": candidate[3],
                "image": base64.b64encode(candidate[4]).decode("utf-8") if candidate[4] else None
            }
            for candidate in candidates
        ]

        return {"status": "success", "candidates": candidate_list}

    except sqlite3.Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")