import cv2
import dlib
import numpy as np
import os
import pickle
import sqlite3
import base64
import logging
from scipy.spatial import distance
from skimage.metrics import structural_similarity as ssim
from sklearn.preprocessing import StandardScaler
from sklearn.neighbors import KNeighborsClassifier

# 📌 Paths
DATABASE_PATH = "backend/data/voters.db"
KNN_MODEL_PATH = "backend/data/knn_voter.pkl"
SCALER_PATH = "backend/data/scaler_voter.pkl"
CNN_MODEL_PATH = "backend/models/mmod_human_face_detector.dat"
FACE_REC_MODEL_PATH = "backend/models/dlib_face_recognition_resnet_model_v1.dat"
PREDICTOR_PATH = "backend/models/shape_predictor_68_face_landmarks.dat"
LOG_FILE = "backend/logs/face_recognition.log"

DATABASE_DIR = "backend/data/face_embeddings"

# ✅ Ensure necessary directories exist
os.makedirs("backend/data", exist_ok=True)
os.makedirs("backend/logs", exist_ok=True)

# ✅ Setup Logging
logging.basicConfig(filename=LOG_FILE, level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# ✅ Load Dlib Models
if not os.path.exists(CNN_MODEL_PATH):
    raise FileNotFoundError("⚠️ CNN model missing! Download from http://dlib.net/files/mmod_human_face_detector.dat.bz2")
cnn_detector = dlib.cnn_face_detection_model_v1(CNN_MODEL_PATH)

if not os.path.exists(FACE_REC_MODEL_PATH):
    raise FileNotFoundError("⚠️ Face Recognition Model missing! Download from http://dlib.net/files/dlib_face_recognition_resnet_model_v1.dat.bz2")
face_recognizer = dlib.face_recognition_model_v1(FACE_REC_MODEL_PATH)

if not os.path.exists(PREDICTOR_PATH):
    raise FileNotFoundError("⚠️ Shape Predictor missing! Download from http://dlib.net/files/shape_predictor_68_face_landmarks.dat.bz2")
landmark_predictor = dlib.shape_predictor(PREDICTOR_PATH)

# ✅ Load KNN Model & Scaler
knn, scaler = None, None
if os.path.exists(KNN_MODEL_PATH) and os.path.exists(SCALER_PATH):
    with open(KNN_MODEL_PATH, "rb") as f:
        knn = pickle.load(f)
    with open(SCALER_PATH, "rb") as f:
        scaler = pickle.load(f)
else:
    logging.warning("⚠️ KNN model not found! Please train the model before running face recognition.")

# ✅ Check for Blurry Images Before Recognition
def is_blurry(image, threshold=50):
    """Detects blur in an image using the Laplacian variance method."""
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    variance = cv2.Laplacian(gray, cv2.CV_64F).var()
    return variance < threshold

# ✅ Preprocess Face
def preprocess_face(image):
    """Prepares a face image for recognition."""
    image = cv2.resize(image, (100, 100))
    image = image.astype("float32") / 255.0  # Normalize
    return image.flatten().reshape(1, -1)

def recognize_face_from_file(image_path):
    """🎭 Recognizes face from an image file instead of Base64."""

    # ✅ Load image from file
    image = cv2.imread(image_path)

    if image is None:
        print(f"⚠️ Error loading image: {image_path}")
        return None

    # ✅ Convert image to RGB (Dlib expects RGB)
    rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

    # ✅ Detect face using Dlib
    faces_detected = cnn_detector(rgb_image)

    if len(faces_detected) == 0:
        print("⚠️ No face detected.")
        return None

    face_rect = faces_detected[0].rect
    shape = landmark_predictor(rgb_image, face_rect)
    face_embedding = np.array(face_recognizer.compute_face_descriptor(rgb_image, shape))

    # ✅ Compare with database
    recognized_user = compare_face_embedding(face_embedding)

    return recognized_user 

# ✅ Recognize Face (With CNN Detection & KNN)
def recognize_face(image_array):
    """Recognizes a face using the trained KNN model with Dlib's CNN face detector."""
    if knn is None:
        return {"status": "error", "message": "Face recognition unavailable. Train the model first."}
    
    try:
        if is_blurry(image_array):
            return {"status": "error", "message": "Image is too blurry for recognition. Use a clearer image."}

        rgb_image = cv2.cvtColor(image_array, cv2.COLOR_BGR2RGB)
        faces = cnn_detector(rgb_image)

        if len(faces) == 0:
            return {"status": "error", "message": "No face detected"}

        for face in faces:
            shape = landmark_predictor(rgb_image, face.rect)
            face_embedding = np.array(face_recognizer.compute_face_descriptor(rgb_image, shape))

            processed_face = preprocess_face(face_embedding)
            processed_face = scaler.transform(processed_face)

            # ✅ Predict Using KNN
            distances, indices = knn.kneighbors(processed_face, n_neighbors=1)
            recognized_user = knn.predict(processed_face)[0]
            confidence = 1 - (distances[0][0] / np.max(distances))

            if confidence < 0.6:
                return fallback_face_recognition(image_array)

            return {
                "status": "success",
                "recognized_user": {
                    "universityID": recognized_user.split()[-1][1:-1],
                    "name": " ".join(recognized_user.split()[:-1]),
                    "confidence": round(confidence, 2)
                }
            }

        return {"status": "error", "message": "Face recognition failed"}

    except Exception as e:
        return {"status": "error", "message": f"Face recognition error: {str(e)}"}

# ✅ Fallback Face Recognition (If KNN Fails)
def fallback_face_recognition(image_array):
    """Fallback method using Dlib Face Embeddings for face comparison."""
    try:
        rgb_image = cv2.cvtColor(image_array, cv2.COLOR_BGR2RGB)
        faces = cnn_detector(rgb_image)

        if len(faces) == 0:
            return {"status": "error", "message": "No face detected"}

        for face in faces:
            shape = landmark_predictor(rgb_image, face.rect)
            face_embedding = np.array(face_recognizer.compute_face_descriptor(rgb_image, shape))

            # ✅ Retrieve stored voter embeddings from the database
            conn = sqlite3.connect(DATABASE_PATH)
            cursor = conn.cursor()
            cursor.execute("SELECT universityID, image FROM voters WHERE image IS NOT NULL")
            voter_data = cursor.fetchall()
            conn.close()

            best_match = None
            best_distance = float("inf")

            for universityID, image_blob in voter_data:
                np_arr = np.frombuffer(image_blob, np.uint8)
                stored_image = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
                stored_faces = cnn_detector(stored_image)

                if len(stored_faces) == 0:
                    continue

                stored_shape = landmark_predictor(stored_image, stored_faces[0].rect)
                stored_embedding = np.array(face_recognizer.compute_face_descriptor(stored_image, stored_shape))

                # ✅ Compute Euclidean distance
                dist = np.linalg.norm(face_embedding - stored_embedding)

                if dist < best_distance:
                    best_distance = dist
                    best_match = universityID

            if best_match and best_distance < 0.6:
                return {"status": "success", "recognized_user": {"universityID": best_match, "message": "Fallback recognition successful"}}

        return {"status": "error", "message": "No similar face found"}

    except Exception as e:
        return {"status": "error", "message": f"Error in fallback recognition: {str(e)}"}


def recognize_face_base64(image_base64: str):
    """Recognizes a face from a Base64-encoded image."""
    try:
        # Decode Base64 image
        image_bytes = base64.b64decode(image_base64)
        np_arr = np.frombuffer(image_bytes, np.uint8)
        image = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

        if image is None:
            return {"status": "error", "message": "Invalid base64 image format"}

        # Call the face recognition function
        from backend.services.faceRecognitionService import recognize_face
        return recognize_face(image)

    except Exception as e:
        return {"status": "error", "message": f"Error recognizing face: {str(e)}"}

        # ✅ Load saved face embeddings
