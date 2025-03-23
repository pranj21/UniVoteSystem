import sqlite3
import logging
import os
import hashlib
from datetime import datetime
from fastapi.responses import JSONResponse
import cv2
from backend.services.faceRecognitionService import recognize_face  # ✅ FIXED: Import correct function

# ✅ Ensure log directory exists
LOG_DIR = "backend/logs"
os.makedirs(LOG_DIR, exist_ok=True)

# ✅ Define log file path
LOG_FILE = os.path.join(LOG_DIR, "vote_logs.log")

# ✅ Dedicated Logger for Voting Operations
vote_logger = logging.getLogger("vote_logger")
vote_logger.setLevel(logging.INFO)

# ✅ Remove any previous handlers (Prevents duplicate logs)
if vote_logger.hasHandlers():
    vote_logger.handlers.clear()

# ✅ Create File Handler
vote_log_file = logging.FileHandler(LOG_FILE, mode="a", encoding="utf-8")
vote_log_file.setLevel(logging.INFO)

# ✅ Set Log Format
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
vote_log_file.setFormatter(formatter)

# ✅ Add File Handler to Logger
vote_logger.addHandler(vote_log_file)

# ✅ Ensure logs flush immediately
vote_logger.propagate = False  

# ✅ Manual Test Log Entry (Check if logs work)
vote_logger.info("✅ Logging system initialized successfully!")

DATABASE = "backend/data/voters.db"

def initialize_database():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    # ✅ Ensure `voters` table exists
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS voters (
            universityID TEXT PRIMARY KEY,
            firstname TEXT,
            lastname TEXT,
            email TEXT,
            password TEXT,
            hasVoted INTEGER DEFAULT 0,
            image BLOB
        )
    """)

    # ✅ Ensure `votes` table exists
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS votes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            universityID TEXT,
            candidateID TEXT,
            timestamp TEXT
        )
    """)

    conn.commit()
    conn.close()
    print("✅ Database initialized successfully")


# 🔒 **Secure Hash Function for Logs**
def hash_value(value):
    """🔒 Secure SHA-256 hash function for logs."""
    return hashlib.sha256(value.encode()).hexdigest()

# 🔄 **Immediate Log Flush**
def flush_logs():
    """🔄 Ensures logs are written immediately to file."""
    for handler in vote_logger.handlers:
        handler.flush()

# ✅ **Check if Voter Exists**
def voter_exists(universityID):
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("SELECT universityID FROM voters WHERE universityID=?", (universityID,))
    result = cursor.fetchone()
    conn.close()
    return result is not None

# ✅ **Check if Voter has Already Voted**
def check_has_voted(universityID):
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("SELECT hasVoted FROM voters WHERE universityID=?", (universityID,))
    result = cursor.fetchone()
    conn.close()
    return result is not None and result[0] == 1

# ✅ **Update Voting Status**
def update_voting_status(universityID, status=True):
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("UPDATE voters SET hasVoted=? WHERE universityID=?", (1 if status else 0, universityID))
    conn.commit()
    conn.close()

    # ✅ Log Voter Status Update with Hashed ID
    vote_logger.info(f"✅ Voter status updated: UniversityID={hash_value(universityID)}, hasVoted={status}")
    flush_logs()

# ✅ **Record Vote in Database**
def record_vote(universityID, candidateID):
    """🗳 Securely store vote in database (Raw Data) and log Hashed Data."""
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        cursor.execute("INSERT INTO votes (universityID, candidateID, timestamp) VALUES (?, ?, ?)", 
                       (universityID, candidateID, timestamp))
        conn.commit()

        # ✅ Log Secure Hashed Vote Information
        hashed_voter = hash_value(universityID)
        hashed_candidate = hash_value(candidateID)

        vote_logger.info(f"✅ Vote recorded: UniversityID={hashed_voter}, CandidateID={hashed_candidate}")
        flush_logs()

    except sqlite3.Error as e:
        vote_logger.error(f"❌ Error recording vote for {hash_value(universityID)}: {str(e)}")
        flush_logs()
    finally:
        conn.close()

# ✅ **Cast Vote Function**
def cast_vote(vote_data):
    """🗳️ Handles face verification and vote recording."""
    try:
        # 🧐 **1. Ensure Voter Exists**
        if not voter_exists(vote_data["universityID"]):
            return {"status": "error", "message": "Voter does not exist in the database."}

        # 🛑 **2. Prevent Duplicate Votes**
        if check_has_voted(vote_data["universityID"]):
            vote_logger.warning(f"⚠️ Duplicate vote attempt by UniversityID={hash_value(vote_data['universityID'])}")
            flush_logs()
            return {"status": "error", "message" : "User has already voted."}
            
           
        # 🎭 **3. Verify Face Using CNN & KNN**
        image_path = vote_data["image_path"]  # Use saved image path
        input_image = cv2.imread(image_path)

        if input_image is None:
            return {"status": "error", "message": "Failed to read image file."}

        recognition_result = recognize_face(input_image)  # Call face recognition function

        if recognition_result["status"] != "success":
            vote_logger.warning(f"⚠️ Face mismatch for UniversityID={hash_value(vote_data['universityID'])}")
            flush_logs()
            return {"status": "error", "message": recognition_result["message"]}

        recognized_user_id = recognition_result["recognized_user"]["universityID"]

        if recognized_user_id != vote_data["universityID"]:
            return {"status": "error", "message": "Face does not match the registered voter."}

        # 🗳️ **4. Record Vote and Update Status**
        record_vote(vote_data["universityID"], vote_data["candidateID"])
        update_voting_status(vote_data["universityID"], True)

        vote_logger.info(f"✅ Vote successfully cast by UniversityID={hash_value(vote_data['universityID'])}")
        flush_logs()
        return {"status": "success", "message": "Vote successfully cast!"}
          
    except Exception as e:
        vote_logger.error(f"❌ Error casting vote for {hash_value(vote_data['universityID'])}: {str(e)}")
        flush_logs()
        return {"status": "error", "message": "An error occurred while casting vote."}

# ✅ **Retrieve Election Results**
def get_results():
    """📊 Fetch election results securely."""
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("SELECT candidateID, COUNT(*) FROM votes GROUP BY candidateID")
    results = cursor.fetchall()
    conn.close()

    results_dict = {candidate: count for candidate, count in results}
    vote_logger.info("✅ Election results retrieved successfully.")
    flush_logs()
    return {"status": "success", "results": results_dict} 