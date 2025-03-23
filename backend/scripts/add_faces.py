import sqlite3
import cv2
import os
import dlib
import numpy as np
import pickle
import argparse
import logging
from tqdm import tqdm
import subprocess
import sys

# ✅ Paths
DATASET_PATH = "backend/dataset/LFW/lfw-deepfunneled"  # LFW Dataset
DATABASE = "backend/data/voters.db"  # SQLite Voter & Candidate DB
SAVE_PATH = "backend/data"  # Path to Save `.pkl` files
LOG_FILE = "backend/logs/face_processing.log"

# ✅ Directories for Extracted Images
VOTERS_DIR = "backend/data/voters/"
CANDIDATES_DIR = "backend/data/candidates/"
LFW_DIR = "backend/data/lfw/"

# ✅ Ensure necessary directories exist
os.makedirs(VOTERS_DIR, exist_ok=True)
os.makedirs(CANDIDATES_DIR, exist_ok=True)
os.makedirs(LFW_DIR, exist_ok=True)
os.makedirs("backend/logs", exist_ok=True)

# ✅ Setup Logging
logging.basicConfig(
    filename=LOG_FILE, 
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
logging.getLogger().addHandler(console_handler)

logging.info("✅ Face Processing Script Started.")

# ✅ Load Dlib's Face Detector
detector = dlib.get_frontal_face_detector()

# ✅ Storage Lists
lfw_faces, lfw_names = [], []
voter_faces, voter_names = [], []
candidate_faces, candidate_names = [], []
skipped_files = []

# ✅ Argument Parser
parser = argparse.ArgumentParser()
parser.add_argument("--only-voters", action="store_true", help="Process only voter database faces.")
parser.add_argument("--only-candidates", action="store_true", help="Process only candidate database faces.")
args = parser.parse_args()

# 🔹 1️⃣ Process LFW Dataset (Unless `--only-voters` or `--only-candidates` is set)
if not args.only_voters and not args.only_candidates:
    logging.info("🔍 Processing images from LFW dataset...")
    for person_name in tqdm(os.listdir(DATASET_PATH)):
        person_folder = os.path.join(DATASET_PATH, person_name)
        if not os.path.isdir(person_folder):
            continue
        for image_name in os.listdir(person_folder):
            image_path = os.path.join(DATASET_PATH, person_name, image_name)
            image = cv2.imread(image_path)
            if image is None:
                skipped_files.append((image_path, "Corrupted image"))
                continue
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            faces = detector(gray)
            if len(faces) == 0:
                skipped_files.append((image_path, "No face detected"))
                continue
            for face in faces:
                x, y, w, h = face.left(), face.top(), face.width(), face.height()
                face_img = gray[y:y+h, x:x+w]
                if face_img.size == 0:
                    skipped_files.append((image_path, "Empty cropped face"))
                    continue
                face_img = cv2.resize(face_img, (50, 50)).flatten()
                lfw_faces.append(face_img)
                lfw_names.append(person_name)

                # ✅ Save extracted image
                save_path = os.path.join(LFW_DIR, f"{person_name}_{image_name}")
                cv2.imwrite(save_path, gray[y:y+h, x:x+w])

# 🔹 2️⃣ Process Database Images (Voters & Candidates)
def process_database_faces(table_name, faces_list, names_list, output_dir):
    """Extracts and processes face images from SQLite database."""
    logging.info(f"🔹 Processing {table_name} images from database...")

    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute(f"SELECT universityID, firstname, lastname, image FROM {table_name} WHERE image IS NOT NULL")
    user_data = cursor.fetchall()
    conn.close()

    for universityID, firstname, lastname, face_image in user_data:
        try:
            image_array = np.frombuffer(face_image, np.uint8)
            image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)
            if image is None:
                skipped_files.append((universityID, "Invalid image format"))
                continue
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            faces = detector(gray)
            if len(faces) == 0:
                skipped_files.append((universityID, "No face detected"))
                continue
            for face in faces:
                x, y, w, h = face.left(), face.top(), face.width(), face.height()
                face_img = gray[y:y+h, x:x+w]
                if face_img.size == 0:
                    skipped_files.append((universityID, "Empty cropped face"))
                    continue
                face_img = cv2.resize(face_img, (50, 50)).flatten()
                faces_list.append(face_img)
                names_list.append(f"{firstname} {lastname} ({universityID})")

                # ✅ Save extracted image
                save_path = os.path.join(output_dir, f"{universityID}.jpg")
                cv2.imwrite(save_path, gray[y:y+h, x:x+w])

        except Exception as e:
            skipped_files.append((universityID, f"Processing error: {str(e)}"))

# ✅ Process Voters
if not args.only_candidates:
    process_database_faces("voters", voter_faces, voter_names, VOTERS_DIR)

# ✅ Process Candidates
if not args.only_voters:
    process_database_faces("candidates", candidate_faces, candidate_names, CANDIDATES_DIR)

# ✅ Save Processed Data
def save_data(data_list, file_name):
    """Saves processed data as a pickle file."""
    if data_list:
        with open(os.path.join(SAVE_PATH, file_name), "wb") as f:
            pickle.dump(data_list, f)

save_data(voter_faces, "voter_faces.pkl")
save_data(voter_names, "voter_names.pkl")
save_data(candidate_faces, "candidate_faces.pkl")
save_data(candidate_names, "candidate_names.pkl")

if not args.only_voters and not args.only_candidates:
    save_data(lfw_faces, "lfw_faces.pkl")
    save_data(lfw_names, "lfw_names.pkl")

# ✅ Summary Report
logging.info("✅ Face data processing complete!")
logging.info(f"✔️ Voter Faces: {len(voter_faces)}")
logging.info(f"✔️ Candidate Faces: {len(candidate_faces)}")
if not args.only_voters and not args.only_candidates:
    logging.info(f"✔️ LFW Faces: {len(lfw_faces)}")
logging.info(f"⚠️ Skipped Images: {len(skipped_files)}")
if skipped_files:
    with open(os.path.join(SAVE_PATH, "skipped_files.log"), "w") as f:
        for item in skipped_files:
            f.write(f"{item}\n")

logging.info("✅ Image processing completed successfully!")
