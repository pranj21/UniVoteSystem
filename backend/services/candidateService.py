import sqlite3
import logging
import base64
import bcrypt
import os
import subprocess
import numpy as np
import cv2
from backend.services.databaseService import DATABASE_PATH
import sys 
from pydantic import BaseModel  # ✅ Add this line

# 📌 Paths
DATABASE_PATH = "backend/data/voters.db"

class CandidateLookupModel(BaseModel):
    universityID: str

# ✅ Logging Setup
LOG_DIR = "backend/logs"
os.makedirs(LOG_DIR, exist_ok=True)

LOG_FILE = os.path.join(LOG_DIR, "candidate_logs.log")
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
    filemode="a",
)

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)
console_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
logging.getLogger().addHandler(console_handler)

logging.info("✅ Candidate logging initialized successfully.")

# ✅ Ensure Database Exists
def initialize_database():
    os.makedirs(os.path.dirname(DATABASE_PATH), exist_ok=True)
    try:
        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS candidates (
                    universityID TEXT PRIMARY KEY,
                    firstname TEXT,
                    lastname TEXT,
                    email TEXT,
                    password TEXT,
                    aboutYourself TEXT,
                    image BLOB
                )
            """)
            conn.commit()
        logging.info("✅ Candidate database initialized successfully.")
    except sqlite3.Error as e:
        logging.error(f"❌ Database initialization error: {str(e)}")

# ✅ Hash Password using bcrypt
def hash_password(password):
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

# ✅ Check if Candidate Exists
def check_candidate_exists(universityID):
    try:
        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT universityID FROM candidates WHERE universityID=?", (universityID,))
            return cursor.fetchone() is not None
    except sqlite3.Error as e:
        logging.error(f"❌ Database error in check_candidate_exists: {str(e)}")
        return False

def get_candidate(universityID: str):
    """Fetch candidate details from the database including the profile image."""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT universityID, firstname, lastname, email, aboutYourself, image FROM candidates WHERE universityID = ?", (universityID,))
        candidate = cursor.fetchone()
        conn.close()

        if not candidate:
            return None

        # Convert BLOB image to Base64 (if exists)
        image_base64 = None
        if candidate[5]:  # If image data exists
            image_base64 = base64.b64encode(candidate[5]).decode("utf-8")

        return {
            "universityID": candidate[0],
            "firstname": candidate[1],
            "lastname": candidate[2],
            "email": candidate[3],
            "aboutYourself": candidate[4],
            "image": image_base64  # Base64-encoded image
        }
    except Exception as e:
        logging.error(f"❌ Database error: {str(e)}")
        return None

# ✅ Register New Candidate
def register_new_candidate(candidate_data):
    try:
        initialize_database()
        logging.info(f"🟢 Registering candidate: {candidate_data['universityID']}")

        if check_candidate_exists(candidate_data["universityID"]):
            logging.warning(f"⚠️ Candidate already registered: {candidate_data['universityID']}")
            return {"status": "error", "message": "Candidate already registered."}

        hashed_password = hash_password(candidate_data["password"])

        # ✅ Decode Base64 Image
        try:
            base64_data = candidate_data["image"].split(",")[-1]
            image_data = base64.b64decode(base64_data)
            np_arr = np.frombuffer(image_data, np.uint8)
            image = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

            if image is None:
                raise ValueError("Invalid image format")
            logging.info("🖼️ Candidate image successfully decoded.")

        except Exception as e:
            logging.error(f"❌ Error decoding candidate image: {str(e)}")
            return {"status": "error", "message": "Invalid image format."}

        # ✅ Insert into database
        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO candidates (universityID, firstname, lastname, email, password, aboutYourself, image)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (candidate_data["universityID"], candidate_data["firstname"], candidate_data["lastname"], 
                  candidate_data["email"], hashed_password, candidate_data["aboutYourself"], image_data))
            conn.commit()

        logging.info(f"✅ Candidate registered successfully: {candidate_data['universityID']}")

        # ✅ Train Model After Registration
        update_result = update_candidate_dataset_and_train()
        logging.info(f"🔄 Model update result: {update_result}")

        return {"status": "success", "message": "Candidate registered successfully!"}

    except sqlite3.Error as e:
        logging.error(f"❌ Database Error while registering candidate {candidate_data['universityID']}: {str(e)}")
        return {"status": "error", "message": "Database error while registering."}

# ✅ Automatically Update Candidate Dataset & Train KNN Model
def update_candidate_dataset_and_train():
    """Updates only candidate-related .pkl files and retrains the candidate-specific KNN model."""
    try:
        logging.info("🔄 Updating candidate dataset...")

        # ✅ Step 1: Run add_faces.py but ONLY for candidates
        subprocess.run(["python", "backend/scripts/add_faces.py", "--only-candidates"], check=True)

        logging.info("🔄 Retraining KNN model for CANDIDATES ONLY...")

        # ✅ Step 2: Train only the candidate KNN model
        subprocess.run(["python", "backend/scripts/train_knn.py", "--only-candidates"], check=True)

        logging.info("✅ Candidate dataset updated & model retrained successfully!")
        return {"status": "success", "message": "Candidate model updated successfully!"}

    except subprocess.CalledProcessError as e:
        logging.error(f"❌ Error during candidate model update: {str(e)}")
        return {"status": "error", "message": "Candidate registered, but model update failed."}

# ✅ Retrieve Candidate Password (Hashed)
def get_candidate_password(universityID):
    try:
        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT password FROM candidates WHERE universityID=?", (universityID,))
            result = cursor.fetchone()
        return result[0] if result else None
    except Exception as e:
        logging.error(f"❌ Database error in get_candidate_password: {str(e)}")
        return None    

# ✅ Verify Candidate Password
def verify_candidate_password(universityID, input_password):
    try:
        stored_password_hash = get_candidate_password(universityID)
        if not stored_password_hash:
            return {"status": "error", "message": "Candidate not found"}

        if bcrypt.checkpw(input_password.encode("utf-8"), stored_password_hash.encode("utf-8")):
            return {"status": "success", "message": "Password verified"}
        return {"status": "error", "message": "Incorrect password"}

    except sqlite3.Error as e:
        logging.error(f"❌ Database error while verifying password: {str(e)}")
        return {"status": "error", "message": "Database error"}
