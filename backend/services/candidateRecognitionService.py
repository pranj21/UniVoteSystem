import cv2
import dlib
import numpy as np
import pickle
import logging
import os
import subprocess
from sklearn.preprocessing import StandardScaler
from sklearn.neighbors import KNeighborsClassifier
from backend.services.faceRecognitionService import preprocess_face

# 📌 Paths
DATABASE_PATH = "backend/data/voters.db"
KNN_MODEL_PATH = "backend/data/knn_candidate.pkl"
SCALER_PATH = "backend/data/scaler_candidate.pkl"
CNN_MODEL_PATH = "backend/models/mmod_human_face_detector.dat"
FACE_REC_MODEL_PATH = "backend/models/dlib_face_recognition_resnet_model_v1.dat"
PREDICTOR_PATH = "backend/models/shape_predictor_68_face_landmarks.dat"

# ✅ Setup Logging
logging.basicConfig(
    filename="backend/logs/candidate_recognition.log", 
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
logging.getLogger().addHandler(console_handler)

# ✅ Load Dlib Models
try:
    cnn_detector = dlib.cnn_face_detection_model_v1(CNN_MODEL_PATH) if os.path.exists(CNN_MODEL_PATH) else None
    face_recognizer = dlib.face_recognition_model_v1(FACE_REC_MODEL_PATH) if os.path.exists(FACE_REC_MODEL_PATH) else None
    landmark_predictor = dlib.shape_predictor(PREDICTOR_PATH) if os.path.exists(PREDICTOR_PATH) else None

    if not cnn_detector:
        logging.error("❌ CNN model missing! Download from http://dlib.net/files/mmod_human_face_detector.dat.bz2")
    if not face_recognizer:
        logging.error("❌ Face Recognition Model missing! Download from http://dlib.net/files/dlib_face_recognition_resnet_model_v1.dat.bz2")
    if not landmark_predictor:
        logging.error("❌ Shape Predictor missing! Download from http://dlib.net/files/shape_predictor_68_face_landmarks.dat.bz2")

except Exception as e:
    logging.error(f"❌ Error loading Dlib models: {str(e)}")

# ✅ Load KNN Model & Scaler
knn_candidate, scaler_candidate = None, None
if os.path.exists(KNN_MODEL_PATH) and os.path.exists(SCALER_PATH):
    try:
        with open(KNN_MODEL_PATH, "rb") as f:
            knn_candidate = pickle.load(f)
        with open(SCALER_PATH, "rb") as f:
            scaler_candidate = pickle.load(f)

        logging.info("✅ Candidate KNN model and Scaler loaded successfully!")
    except (pickle.UnpicklingError, EOFError) as e:
        logging.error(f"❌ Error loading KNN model: {str(e)}")
        knn_candidate, scaler_candidate = None, None
else:
    logging.warning("⚠️ Candidate KNN model not found! Train the model before running face recognition.")

# ✅ Check for Blurry Images
def is_blurry(image, threshold=50):
    """Detects blur using Laplacian variance method."""
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    variance = cv2.Laplacian(gray, cv2.CV_64F).var()
    return variance < threshold

# ✅ Recognize Candidate Face
def recognize_candidate_face(image_array):
    """Recognizes a candidate's face using KNN with CNN detection."""
    global knn_candidate, scaler_candidate

    if knn_candidate is None or scaler_candidate is None:
        logging.error("❌ Candidate KNN Model or Scaler not loaded!")
        return {"status": "error", "message": "Face recognition unavailable. Train the model first."}

    if cnn_detector is None or face_recognizer is None or landmark_predictor is None:
        logging.error("❌ One or more Dlib models are missing!")
        return {"status": "error", "message": "Face recognition model files are missing!"}

    try:
        if is_blurry(image_array):
            return {"status": "error", "message": "Image is too blurry for recognition. Use a clearer image."}

        # ✅ Convert Image to RGB (Required for Dlib)
        rgb_image = cv2.cvtColor(image_array, cv2.COLOR_BGR2RGB)

        # ✅ Detect Faces using CNN Detector
        faces = cnn_detector(rgb_image)
        logging.info(f"👀 Detected Faces: {len(faces)}")

        if len(faces) == 0:
            return {"status": "error", "message": "No face detected"}

        for face in faces:
            # Extract landmarks & embeddings
            shape = landmark_predictor(rgb_image, face.rect)
            face_embedding = np.array(face_recognizer.compute_face_descriptor(rgb_image, shape))
            face_embedding = face_embedding / np.linalg.norm(face_embedding)  # ✅ Normalize to unit vector

            # ✅ Normalize & Scale the Face Embedding (No Flattening)
            try:
                processed_face = scaler_candidate.transform(face_embedding.reshape(1, -1))
                logging.info(f"🔍 Scaled Face Embedding (First 5 values): {processed_face[0][:5]}")

            except Exception as e:
                logging.error(f"⚠️ Error during scaling: {str(e)}")
                return {"status": "error", "message": "Error in face scaling. Try retraining the model."}

            # ✅ Predict Using Candidate KNN
            distances, indices = knn_candidate.kneighbors(processed_face, n_neighbors=1)
            logging.info(f"📏 KNN Distance: {distances[0][0]} | Recognized: {knn_candidate.predict(processed_face)[0]}")

            recognized_user = knn_candidate.predict(processed_face)[0]

            # ✅ Compute Confidence
            max_distance = max(distances[0])  # Prevent division by zero
            confidence = max(0.1, 1 - (distances[0][0] / max_distance))

            logging.info(f"🎯 Recognized User: {recognized_user} | Confidence: {round(confidence, 2)}")

            CONFIDENCE_THRESHOLD = 0.1# 🔥 Adjusted threshold to reduce false negatives

            if confidence < CONFIDENCE_THRESHOLD:
                logging.warning("⚠️ Low confidence score! Face may not be recognized correctly.")
                return {"status": "error", "message": "Face recognition confidence too low."}

            # ✅ Extract university ID correctly
            recognized_parts = recognized_user.split()
            if len(recognized_parts) > 1:
                university_id = recognized_parts[-1][1:-1]  # Extract ID (e.g., "(1)" -> "1")
                name = " ".join(recognized_parts[:-1])  # Extract Name
            else:
                university_id = recognized_user
                name = recognized_user

            return {
                "status": "success",
                "recognized_user": {
                    "universityID": university_id,
                    "name": name,
                    "confidence": round(confidence, 2)
                }
            }

        return {"status": "error", "message": "Face recognition failed"}

    except Exception as e:
        logging.error(f"❌ Face recognition error: {str(e)}")
        return {"status": "error", "message": f"Face recognition error: {str(e)}"}
