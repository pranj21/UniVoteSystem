import pickle
import numpy as np
import argparse
import sqlite3
import os
import logging
import cv2
import dlib
from sklearn.neighbors import KNeighborsClassifier
from sklearn.preprocessing import StandardScaler
import subprocess
import sys

# ✅ Load Dlib Models
FACE_REC_MODEL_PATH = "backend/models/dlib_face_recognition_resnet_model_v1.dat"
PREDICTOR_PATH = "backend/models/shape_predictor_68_face_landmarks.dat"
CNN_MODEL_PATH = "backend/models/mmod_human_face_detector.dat"

cnn_detector = dlib.cnn_face_detection_model_v1(CNN_MODEL_PATH)
face_recognizer = dlib.face_recognition_model_v1(FACE_REC_MODEL_PATH)
landmark_predictor = dlib.shape_predictor(PREDICTOR_PATH)

# 📌 Paths
DATABASE_PATH = "backend/data/voters.db"
VOTER_FACES_PATH = "backend/data/voter_faces.pkl"
VOTER_NAMES_PATH = "backend/data/voter_names.pkl"
CANDIDATE_FACES_PATH = "backend/data/candidate_faces.pkl"
CANDIDATE_NAMES_PATH = "backend/data/candidate_names.pkl"
LFW_FACES_PATH = "backend/data/lfw_faces.pkl"
LFW_NAMES_PATH = "backend/data/lfw_names.pkl"

KNN_VOTER_MODEL_PATH = "backend/data/knn_voter.pkl"
KNN_CANDIDATE_MODEL_PATH = "backend/data/knn_candidate.pkl"
KNN_LFW_MODEL_PATH = "backend/data/knn_lfw.pkl"

SCALER_VOTER_PATH = "backend/data/scaler_voter.pkl"
SCALER_CANDIDATE_PATH = "backend/data/scaler_candidate.pkl"
SCALER_LFW_PATH = "backend/data/scaler_lfw.pkl"

LFW_DATASET_PATH = "backend/dataset/LFW/lfw-deepfunneled"

LOG_FILE = "backend/logs/train_knn.log"

# ✅ Ensure Directories Exist
os.makedirs("backend/logs", exist_ok=True)
os.makedirs("backend/data", exist_ok=True)

# ✅ Setup Logging
logging.basicConfig(
    filename=LOG_FILE, level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
logging.getLogger().addHandler(console_handler)

logging.info("✅ KNN Training Script Started.")

# ✅ Argument Parser
parser = argparse.ArgumentParser()
parser.add_argument("--only-voters", action="store_true", help="Train only voter KNN model.")
parser.add_argument("--only-candidates", action="store_true", help="Train only candidate KNN model.")
parser.add_argument("--only-lfw", action="store_true", help="Train only LFW KNN model.")
args = parser.parse_args()

# ✅ Function to preprocess images (Flattened for Voters & LFW)
def preprocess_face(image):
    """Resize, grayscale, normalize, and flatten image."""
    image = cv2.resize(image, (100, 100))  # Resize
    if len(image.shape) == 3:
        image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)  # Convert to grayscale
    image = cv2.equalizeHist(image)  # Histogram Equalization
    image = image.astype("float32") / 255.0  # Normalize pixel values (0-1)
    return image.flatten()  # ✅ Use Flattened 100x100=10000 features

# ✅ Extract faces from `voters.db`
def extract_faces_from_db(table_name, faces_path, names_path, use_embeddings=False):
    """Extracts face images from a given table in the SQLite database and saves as .pkl."""
    logging.info(f"🔹 Extracting {table_name} faces from database...")

    faces = []
    names = []

    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        cursor.execute(f"SELECT universityID, firstname, lastname, image FROM {table_name} WHERE image IS NOT NULL")
        data = cursor.fetchall()
        conn.close()

        for universityID, firstname, lastname, face_image in data:
            image_array = np.frombuffer(face_image, np.uint8)
            image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)
            if image is None:
                logging.warning(f"⚠️ Skipped {table_name} record {universityID}: Invalid image format")
                continue

            if use_embeddings:
                # ✅ Candidate uses 128-D embeddings
                rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
                faces_detected = cnn_detector(rgb_image)
                if len(faces_detected) == 0:
                    logging.warning(f"⚠️ No face detected for {universityID}. Skipping...")
                    continue

                face_rect = faces_detected[0].rect
                shape = landmark_predictor(rgb_image, face_rect)
                face_embedding = np.array(face_recognizer.compute_face_descriptor(rgb_image, shape))
                faces.append(face_embedding)
            else:
                # ✅ Voters & LFW use flattened images
                processed_face = preprocess_face(image)
                faces.append(processed_face)

            names.append(f"{firstname} {lastname} ({universityID})")

        # ✅ Save extracted data
        with open(faces_path, "wb") as f:
            pickle.dump(faces, f)
        with open(names_path, "wb") as f:
            pickle.dump(names, f)

        logging.info(f"✅ Extracted and saved {len(faces)} {table_name} faces.")

    except sqlite3.Error as e:
        logging.error(f"❌ Database error while extracting {table_name}: {str(e)}")

# ✅ Train KNN Model
def train_knn(faces_path, names_path, model_path, scaler_path, dataset_name, use_flattened):
    """Train KNN model on extracted face data."""
    if not os.path.exists(faces_path) or not os.path.exists(names_path):
        logging.warning(f"⚠️ No dataset found for {dataset_name}. Skipping training.")
        return

    with open(faces_path, "rb") as f:
        faces = pickle.load(f)
    with open(names_path, "rb") as f:
        names = pickle.load(f)

    if len(faces) == 0 or len(names) == 0:
        logging.warning(f"⚠️ No data to train the {dataset_name} model. Skipping training.")
        return

    if len(faces) < 5:
        logging.warning(f"⚠️ The {dataset_name} dataset has fewer than 5 samples. KNN may not perform well.")

    faces = np.array(faces, dtype=np.float32)

    # ✅ Standardize Features
    scaler = StandardScaler()
    faces = scaler.fit_transform(faces)
    with open(SCALER_CANDIDATE_PATH, "wb") as f :
        pickle.dump(scaler, f)

    # ✅ Train KNN Model
    n_neighbors = min(3, len(faces))  # Safeguard for small datasets
    knn = KNeighborsClassifier(n_neighbors=n_neighbors, algorithm="auto", weights="distance")
    knn.fit(faces, names)

    # ✅ Save Model & Scaler
    with open(model_path, "wb") as f:
        pickle.dump(knn, f)
    with open(scaler_path, "wb") as f:
        pickle.dump(scaler, f)

    logging.info(f"✅ {dataset_name} KNN model trained and saved.")

# ✅ Run Training Based on Arguments
if args.only_voters:
    extract_faces_from_db("voters", VOTER_FACES_PATH, VOTER_NAMES_PATH, use_embeddings=False)
    train_knn(VOTER_FACES_PATH, VOTER_NAMES_PATH, KNN_VOTER_MODEL_PATH, SCALER_VOTER_PATH, "Voter DB", use_flattened=True)

elif args.only_candidates:
    extract_faces_from_db("candidates", CANDIDATE_FACES_PATH, CANDIDATE_NAMES_PATH, use_embeddings=True)
    train_knn(CANDIDATE_FACES_PATH, CANDIDATE_NAMES_PATH, KNN_CANDIDATE_MODEL_PATH, SCALER_CANDIDATE_PATH, "Candidate DB", use_flattened=False)

elif args.only_lfw:
    extract_lfw_faces()
    train_knn(LFW_FACES_PATH, LFW_NAMES_PATH, KNN_LFW_MODEL_PATH, SCALER_LFW_PATH, "LFW Dataset", use_flattened=True)
