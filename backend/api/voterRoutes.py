from fastapi import APIRouter, Query,  HTTPException
from pydantic import BaseModel, EmailStr, Field
from backend.services.voterService import get_voter_details, register_new_voter
from backend.services.authService import verify_password
import logging
import bcrypt
import sqlite3
from typing import Optional
import base64
import os


# ✅ Database Path
DATABASE_PATH = "backend/data/voters.db"

# ✅ Setup Logging
logging.basicConfig(
    filename="backend/logs/voter_logs.log",
    level=logging.DEBUG, 
    format="%(asctime)s - %(levelname)s - %(message)s",
    filemode="a",
)

logging.info("✅ API Router Initialized.")

# ✅ Setup API Router
router = APIRouter()

# ✅ Define Pydantic Models
class VoterRegistrationModel(BaseModel):
    universityID: str 
    firstname: str 
    lastname: str 
    email: EmailStr 
    password: str 
    image: str

class VoterLookupModel(BaseModel):
    universityID: str

class PasswordVerificationModel(BaseModel):
    universityID: str
    inputPassword: str

# ✅ Register Voter API
@router.post("/register")
async def register_voter_endpoint(voter: VoterRegistrationModel):
    """
    Registers a new voter and automatically updates the face recognition dataset.
    """
    try:
        # ✅ Convert Pydantic Model to Dictionary
        voter_data = voter.dict()

        # ✅ Call the voter registration function
        response = register_new_voter(voter_data)

        # ✅ Handle Response
        if response["status"] == "error":
            raise HTTPException(status_code=400, detail=response["message"])

        return response

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error registering voter: {str(e)}")

# ✅ Retrieve Voter API
@router.post("/get_voter")
async def get_voter(data: VoterLookupModel):
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()

        # ✅ Fetch voter details including image
        cursor.execute("SELECT universityID, firstname, lastname, email, image FROM voters WHERE universityID=?", (data.universityID,))
        voter = cursor.fetchone()
        conn.close()

        if not voter:
            raise HTTPException(status_code=404, detail="Voter not found")

        # ✅ Convert image BLOB to Base64 (if exists)
        image_base64 = None
        if voter[4]:  # Image is stored in index 4
            image_base64 = f"data:image/jpeg;base64,{base64.b64encode(voter[4]).decode()}"

        # ✅ Return voter details with properly formatted image
        return {
            "universityID": voter[0],
            "firstname": voter[1],
            "lastname": voter[2],
            "email": voter[3],
            "image": image_base64
        }

    except sqlite3.Error as e:
        logging.error(f"❌ Database error while fetching voter: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error while fetching voter.")

    except Exception as e:
        logging.error(f"❌ Unexpected error: {str(e)}")
        raise HTTPException(status_code=500, detail="Unexpected error while processing voter data.")


def get_voter_password(universityID):
    try:
        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT password FROM voters WHERE universityID=?", (universityID,))
            result = cursor.fetchone()

        if result:
            return result[0]  # ✅ Return stored bcrypt hashed password
        return None
    except Exception as e:
        logging.error(f"❌ Database error in get_voter_password: {str(e)}")
        return None

# ✅ Verify Password API
@router.post("/verify-password")
async def verify_password_endpoint(data: PasswordVerificationModel):
    """
    Securely verify a voter's password using bcrypt.
    """
    try:
        logging.info(f"🔑 Verifying password for: {data.universityID}")

        # ✅ Retrieve stored password hash
        stored_password_hash = get_voter_password(data.universityID)

        if not stored_password_hash:
            logging.warning(f"⚠️ Voter not found for ID: {data.universityID}")
            raise HTTPException(status_code=404, detail="Voter not found.")

        # ✅ Convert passwords to byte format before bcrypt check
        input_password_bytes = data.inputPassword.encode("utf-8")
        stored_password_bytes = stored_password_hash.encode("utf-8")

        # ✅ Perform bcrypt password verification
        if bcrypt.checkpw(input_password_bytes, stored_password_bytes):
            logging.info(f"✅ Password verified for: {data.universityID}")
            return {"status": "success"}
        
        logging.warning(f"⚠️ Invalid password for: {data.universityID}")
        raise HTTPException(status_code=401, detail="Invalid password")

    except Exception as e:
        logging.error(f"❌ Error in verify_password: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error verifying password: {str(e)}")

# ✅ Retrieve All Voters
@router.get("/get_voters")
async def get_voters():
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()

        # ✅ Fetch voter details including image
        cursor.execute("SELECT universityID, firstname, lastname, email, image FROM voters")
        voters = cursor.fetchall()
        conn.close()

        if not voters:
            return {"status": "error", "message": "No voters found."}

        # ✅ Convert to JSON format with Base64 images
        voter_list = [
            {
                "universityID": voter[0],
                "firstname": voter[1],
                "lastname": voter[2],
                "email": voter[3],
                "image": f"data:image/jpeg;base64,{base64.b64encode(voter[4]).decode()}" if voter[4] else None
            }
            for voter in voters
        ]

        return {"status": "success", "voters": voter_list}

    except sqlite3.Error as e:
        logging.error(f"❌ Database error while fetching voters: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error while fetching voters.")

@router.get("/get_voters")
async def get_voters():
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()

        # ✅ Fetch voter details including the image
        cursor.execute("SELECT universityID, firstname, lastname, email, image FROM voters")
        voters = cursor.fetchall()
        conn.close()

        if not voters:
            return {"status": "error", "message": "No voters found."}

        # ✅ Convert images to Base64 and format JSON response
        voter_list = [
            {
                "universityID": voter[0],
                "firstname": voter[1],
                "lastname": voter[2],
                "email": voter[3],
                "image": f"data:image/jpeg;base64,{base64.b64encode(voter[4]).decode()}" if voter[4] else None
            }
            for voter in voters
        ]

        return {"status": "success", "voters": voter_list}

    except sqlite3.Error as e:
        return {"status": "error", "message": f"Database error: {str(e)}"}