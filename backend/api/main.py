import os
import sys
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.cors import CORSMiddleware
from backend.api.voterRoutes import router as voter_router




# 🔹 Ensure backend directory is in the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

# ✅ Import API Routes Correctly
from backend.api.voterRoutes import router as voter_router
from backend.api.faceRoutes import router as face_router
from backend.api.voteRoutes import router as vote_router
from backend.api.candidateRoutes import router as candidate_router

# ✅ Initialize FastAPI app
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 👈 Allows frontend to access API
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 🎯 Initialize FastAPI App
app = FastAPI(
    title="UniVote Face Recognition API",
    description="API for face recognition & online voting",
    version="1.0"
)

# 🌍 Enable CORS (Frontend to Backend Communication)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins (Change this in production)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 🚀 Include Routes (✅ Fix: Added `voter_router`)
app.include_router(face_router, prefix="/api/face", tags=["Face Recognition"])
app.include_router(vote_router, prefix="/api/vote", tags=["Voting"])
app.include_router(voter_router, prefix="/api/voter", tags=["Voter Management"])  # ✅ Fixed missing voter route
app.include_router(candidate_router, prefix="/api/candidate", tags=["Candidate Management"]) #Candidate
app.include_router(voter_router, prefix="/api/voter", tags=["Admin Management"])  # ✅ FIXED Missing Route

# 📌 Root Endpoint
@app.get("/")
def home():
    return {"message": "Welcome to the UniVote API 🚀"}

# 🔥 Run the API Server (✅ Fix: Ensure correct module is run)
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)  # ✅ Fixed Uvicorn path
