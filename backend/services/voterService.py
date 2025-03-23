import sqlite3
import logging
import base64
import bcrypt
import pickle
import os
import numpy as np
import cv2
import subprocess


# ✅ Paths
DATABASE_PATH = "backend/data/voters.db"
FACES_DATA_PATH = "backend/data/voter_faces.pkl"
NAMES_DATA_PATH = "backend/data/voter_names.pkl"

# ✅ Logging Setup
LOG_DIR = "backend/logs"
os.makedirs(LOG_DIR, exist_ok=True)

LOG_FILE = os.path.join(LOG_DIR, "voter_logs.log")
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

logging.info("✅ Logging initialized successfully.")

# ✅ Ensure Database Exists
def initialize_database():
    os.makedirs(os.path.dirname(DATABASE_PATH), exist_ok=True)
    with sqlite3.connect(DATABASE_PATH) as conn:
        cursor = conn.cursor()
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
        conn.commit()
    logging.info("✅ Database initialized successfully.")

# ✅ Hash Password using bcrypt
def hash_password(password):
    hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    logging.debug(f"🔐 Password hashed: {hashed[:10]}...")  # Log first few chars for security
    return hashed

# ✅ Check if Voter Exists
def check_voter_exists(universityID):
    try:
        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT universityID FROM voters WHERE universityID=?", (universityID,))
            return cursor.fetchone() is not None
    except sqlite3.Error as e:
        logging.error(f"❌ Database error in check_voter_exists: {str(e)}")
        return False

# ✅ Register New Voter
def register_new_voter(voter_data):
    try:
        initialize_database()
        logging.info(f"🟢 Registering voter: {voter_data['universityID']}")

        # ✅ Check if voter already exists
        if check_voter_exists(voter_data["universityID"]):
            logging.warning(f"⚠️ Voter already registered: {voter_data['universityID']}")
            return {"status": "error", "message": "Voter already registered."}

        # ✅ Hash Password
        hashed_password = hash_password(voter_data["password"])
        logging.debug(f"🔐 Password hashed successfully.")

        # ✅ Decode Base64 Image
        try:
            base64_data = voter_data["image"]
            if "," in base64_data:
                base64_data = base64_data.split(",")[1]  # Remove `data:image/jpeg;base64,`
            
            image_data = base64.b64decode(base64_data)
            if not image_data:
                raise ValueError("Decoded image is empty")
            logging.info(f"🖼️ Image decoded successfully: {len(image_data)} bytes")
        except Exception as e:
            logging.error(f"❌ Error decoding image: {str(e)}")
            return {"status": "error", "message": "Invalid image format."}

        # ✅ Insert voter data into database
        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO voters (universityID, firstname, lastname, email, password, hasVoted, image)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (voter_data["universityID"], voter_data["firstname"], voter_data["lastname"], 
                  voter_data["email"], hashed_password, 0, image_data))
            conn.commit()

            # ✅ Verify if the voter was actually inserted
            cursor.execute("SELECT * FROM voters WHERE universityID=?", (voter_data["universityID"],))
            inserted_voter = cursor.fetchone()
            if inserted_voter is None:
                logging.error("❌ Data not found after insertion! Possible DB error.")
                return {"status": "error", "message": "Failed to register voter."}

        logging.info(f"✅ Voter registered successfully: {voter_data['universityID']}")

         # ✅ **Automatically Update KNN Model**
        update_result = update_face_dataset_and_train()
        logging.info(f"🔄 Model update result: {update_result}")

        return {"status": "success", "message": "Voter registered successfully!"}

    except sqlite3.Error as e:
        logging.error(f"❌ Database Error while registering voter {voter_data['universityID']}: {str(e)}")
        return {"status": "error", "message": "Database error while registering."}

# ✅ Automatically Update Dataset & Train KNN Model
def update_face_dataset_and_train():
    """Updates only voter-related .pkl files and retrains the voter-specific KNN model."""
    try:
        logging.info("🔄 Updating voter dataset...")

        # ✅ Run add_faces.py but ONLY for voters
        subprocess.run(["python", "backend/scripts/add_faces.py", "--only-voters"], check=True)

        logging.info("🔄 Retraining KNN model for VOTERS ONLY...")

        # ✅ Train only the voter KNN model
        subprocess.run(["python", "backend/scripts/train_knn.py", "--only-voters"], check=True)

        logging.info("✅ Voter dataset updated & model retrained successfully!")
        return {"status": "success", "message": "Voter model updated successfully!"}

    except subprocess.CalledProcessError as e:
        logging.error(f"❌ Error during model update: {str(e)}")
        return {"status": "error", "message": "Voter registered, but model update failed."}


# ✅ Retrieve Voter Details
def get_voter_details(universityID):
    with sqlite3.connect(DATABASE_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT firstname, lastname, email, hasVoted FROM voters WHERE universityID=?", (universityID,))
        result = cursor.fetchone()

    return {
        "firstname": result[0], "lastname": result[1], 
        "email": result[2], "hasVoted": result[3]
    } if result else None

# ✅ Check If Voter Has Voted
def check_has_voted(universityID):
    with sqlite3.connect(DATABASE_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT hasVoted FROM voters WHERE universityID=?", (universityID,))
        return cursor.fetchone()[0] == 1 if cursor.fetchone() else False

# ✅ Update Voter's Voting Status in the Database
def update_voting_status(universityID, status=True):
    """
    Marks a voter as 'hasVoted' after they cast their vote.
    """
    try:
        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE voters SET hasVoted=? WHERE universityID=?", 
                (1 if status else 0, universityID)
            )
            conn.commit()
            logging.info(f"✅ Voting status updated for UniversityID={universityID}")
            return {"status": "success", "message": "Voting status updated"}
    except sqlite3.Error as e:
        logging.error(f"❌ Database error while updating voting status: {str(e)}")
        return {"status": "error", "message": "Failed to update voting status"}
