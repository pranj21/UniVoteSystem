from fastapi import APIRouter, UploadFile, File, HTTPException
from pydantic import BaseModel
from backend.controllers.faceController import (
    recognize_live_face,
    recognize_face_from_base64,
    recognize_user,
    perform_liveness_check,
    register_new_voter,
)
#from backend.services.faceRecognitionService import recognize_face_live
from backend.services.candidateService import register_new_candidate

router = APIRouter()

# ✅ Define Voter Registration Model
class VoterRegistration(BaseModel):
    firstname: str
    lastname: str
    universityID: str
    email: str
    password: str
    image: str  # Base64-encoded image

# ✅ Define Base64 Recognition Request Model
class Base64ImageRequest(BaseModel):
    image_base64: str

    # ✅ Candidate Registration Model
class CandidateRegistration(BaseModel):
    firstname: str
    lastname: str
    universityID: str
    email: str
    password: str
    aboutYourself: str
    image: str  # Base64-encoded image

# ✅ Voter Registration API
@router.post("/register")
async def register_endpoint(voter: VoterRegistration):
    """Registers a new voter with their details and image."""
    try:
        response = register_new_voter(voter.dict()) 
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error registering voter: {str(e)}")

# ✅ Face Recognition API (File Upload)
@router.post("/recognize")
async def recognize_endpoint(file: UploadFile = File(...)):
    """Recognizes a voter using KNN face matching from a file upload."""
    try:
        return await recognize_user(file)  # Ensure recognize_user exists in faceController.py
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Face recognition error: {str(e)}")

# ✅ Face Recognition API (Base64 Image)
@router.post("/recognize_base64")
async def recognize_face_base64_api(request: Base64ImageRequest):
    """Recognizes a voter using KNN face matching from a Base64-encoded image."""
    try:
        return recognize_face_from_base64(request.image_base64)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error recognizing face: {str(e)}")

# ✅ Liveness Check API (Blink Detection)
@router.post("/liveness")
async def liveness_endpoint(file: UploadFile = File(...)):
    """Performs a liveness test to verify if the user is real (blink detection)."""
    try:
        return await perform_liveness_check(file)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Liveness check error: {str(e)}")

# ✅ Real-Time Face Recognition (Webcam)
@router.get("/real_time_recognition")
async def real_time_face_recognition():
    """Runs real-time face recognition using the webcam."""
    try:
        return recognize_face_live()  # Ensure recognize_face_live exists in faceRecognitionService.py
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error running real-time face recognition: {str(e)}")

# ✅ Live Face Recognition API (Triggered by Frontend)
@router.get("/live_recognition")
async def run_live_face_recognition():
    """Triggers real-time face recognition via the API (calls the webcam function)."""
    try:
        recognize_face_live()
        return {"status": "success", "message": "Real-time face recognition started!"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error triggering live recognition: {str(e)}")


# ✅ Candidate Registration API
@router.post("/api/candidate/register")
async def register_candidate(candidate: CandidateRegistration):
    """Registers a new candidate in SQLite."""
    try:
        response = register_new_candidate(candidate.dict())
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error registering candidate: {str(e)}")