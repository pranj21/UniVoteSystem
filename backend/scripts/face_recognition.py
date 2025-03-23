import cv2
import dlib
import numpy as np
import pickle
import logging
import os
import traceback
import sqlite3
from scipy.spatial import distance
from skimage.metrics import structural_similarity as ssim

# ✅ Logging Setup
LOG_DIR = "backend/logs"
LOG_FILE = os.path.join(LOG_DIR, "face_recognition.log")

# ✅ Ensure log directory exists
os.makedirs(LOG_DIR, exist_ok=True)

logging.basicConfig(
    filename=LOG_FILE,
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
    filemode='w'  # 'w' overwrites, use 'a' to append
)

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
console_handler.setFormatter(formatter)
logging.getLogger().addHandler(console_handler)

logging.info("✅ Face Recognition Service Initialized.")

# ✅ Paths
MODEL_PATH = "backend/Model/shape_predictor_68_face_landmarks.dat"
DATABASE = "backend/data/voters.db"

# ✅ Load Face Detector & Shape Predictor
detector = dlib.get_frontal_face_detector()
predictor = dlib.shape_predictor(MODEL_PATH)

# ✅ Indices for Eye Landmarks (Liveness Check)
LEFT_EYE = list(range(36, 42))
RIGHT_EYE = list(range(42, 48))

# ✅ Calculate Eye Aspect Ratio (EAR)
def eye_aspect_ratio(eye):
    A = distance.euclidean(eye[1], eye[5])
    B = distance.euclidean(eye[2], eye[4])
    C = distance.euclidean(eye[0], eye[3])
    return (A + B) / (2.0 * C)

# ✅ Check Liveness (Blink Detection)
def is_live_face(landmarks):
    try:
        left_eye = np.array([[landmarks.part(i).x, landmarks.part(i).y] for i in LEFT_EYE])
        right_eye = np.array([[landmarks.part(i).x, landmarks.part(i).y] for i in RIGHT_EYE])
        ear = (eye_aspect_ratio(left_eye) + eye_aspect_ratio(right_eye)) / 2.0
        return ear < 0.2  # Blink detected
    except:
        return False

# ✅ Recognize Face from Database
def recognize_face_from_database(image_array):
    try:
        gray_input = cv2.cvtColor(image_array, cv2.COLOR_BGR2GRAY)
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute("SELECT universityID, firstname, lastname, image FROM voters")
        stored_faces = cursor.fetchall()
        conn.close()

        for universityID, firstname, lastname, stored_image in stored_faces:
            stored_image_array = np.frombuffer(stored_image, np.uint8)
            stored_image_cv = cv2.imdecode(stored_image_array, cv2.IMREAD_COLOR)
            if stored_image_cv is None:
                continue

            gray_stored = cv2.cvtColor(stored_image_cv, cv2.COLOR_BGR2GRAY)
            resized_input = cv2.resize(gray_input, (100, 100))
            resized_stored = cv2.resize(gray_stored, (100, 100))

            ssim_score = ssim(resized_input, resized_stored)
            dist = np.linalg.norm(resized_input.flatten() - resized_stored.flatten())
            if ssim_score > 0.85 or dist < 25:
                return f"{firstname} {lastname} ({universityID})"
        return None
    except:
        return None

# ✅ Real-Time Face Recognition
video = cv2.VideoCapture(0)
while True:
    ret, frame = video.read()
    if not ret:
        break
    
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = detector(gray)

    for face in faces:
        x, y, w, h = face.left(), face.top(), face.width(), face.height()
        cropped_face = frame[y:y+h, x:x+w]

        recognized_person = recognize_face(cropped_face)
        if recognized_person:
            cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
            cv2.putText(frame, recognized_person, (x, y - 15), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
    
    cv2.imshow("Face Recognition", frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

video.release()
cv2.destroyAllWindows()
