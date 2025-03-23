import logging
import cv2
import numpy as np
import base64
import time
import sqlite3
from backend.services.livenessService import is_live_face
from backend.services.databaseService import DATABASE_PATH
from fastapi import UploadFile, HTTPException
from backend.services.candidateService import register_new_candidate
from backend.services.candidateRecognitionService import recognize_candidate_face

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

# ✅ Convert Uploaded File to OpenCV Image
async def process_image(file: UploadFile):
    try:
        image_bytes = await file.read()
        image_np = np.frombuffer(image_bytes, np.uint8)
        image = cv2.imdecode(image_np, cv2.IMREAD_COLOR)

        if image is None:
            logging.error("❌ Error: Uploaded file is invalid.")
            return None

        return image
    except Exception as e:
        logging.error(f"❌ Error processing uploaded image: {str(e)}")
        return None

# ✅ Convert Base64 Image to OpenCV Format
def process_base64_image(image_base64: str):
    try:
        image_bytes = base64.b64decode(image_base64)
        np_arr = np.frombuffer(image_bytes, np.uint8)
        image = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

        if image is None:
            raise ValueError("Invalid base64 image.")
        return image
    except Exception as e:
        logging.error(f"❌ Error decoding base64 image: {str(e)}")
        return None

# ✅ Recognize Candidate Face from Base64 Image
def recognize_candidate_from_base64(image_base64: str):
    image = process_base64_image(image_base64)
    if image is None:
        return {"status": "error", "message": "Invalid base64 image format"}

    recognition_result = recognize_candidate_face(image)

    if recognition_result["status"] == "success":
        log_candidate_recognition(recognition_result["recognized_user"])
    
    return recognition_result

# ✅ Store Candidate Recognition Logs in `voters.db`
def log_candidate_recognition(recognized_user):
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO candidate_recognition_logs (universityID, recognized_name, confidence) VALUES (?, ?, ?)",
            (recognized_user["universityID"], recognized_user["name"], recognized_user["confidence"])
        )
        conn.commit()
        conn.close()
        logging.info(f"✅ Candidate Recognition logged: {recognized_user['name']} ({recognized_user['universityID']})")
    except Exception as e:
        logging.error(f"❌ Error logging candidate recognition: {str(e)}")

# ✅ Recognize Candidate from Uploaded Image
async def recognize_candidate(file: UploadFile):
    """Recognizes a candidate from an uploaded image using KNN."""
    image = await process_image(file)

    if image is None:
        logging.warning("⚠️ Uploaded image is invalid.")
        return {"status": "error", "message": "Invalid image file"}

    recognition_result = recognize_candidate_face(image)

    if recognition_result.get("status") == "success":
        log_candidate_recognition(recognition_result["recognized_user"])
        return recognition_result
    else:
        logging.warning("❌ Candidate face not recognized in the database.")
        return {"status": "error", "message": "Face not recognized!"}

# ✅ Perform Liveness Check for Candidates
async def perform_candidate_liveness_check(file: UploadFile):
    """Performs a liveness test to verify if the candidate is real (blink detection)."""
    image = await process_image(file)

    if image is None:
        return {"status": "error", "message": "Invalid image file"}

    liveness_result = is_live_face(image)

    if liveness_result.get("status") == "success":
        return liveness_result
    else:
        return {"status": "error", "message": "Liveness test failed. Please blink."}

# ✅ Recognize Candidate Face Only if Liveness is Confirmed
async def recognize_candidate_live(file: UploadFile):
    """Ensures the candidate is alive before recognizing the face."""
    if not detect_blink():
        return {"status": "error", "message": "❌ Liveness test failed. Please blink."}

    # ✅ Process Image & Recognize Face
    image = await process_image(file)
    if image is None:
        return {"status": "error", "message": "Invalid image file"}

    recognition_result = recognize_candidate_face(image)

    if recognition_result["status"] == "success":
        log_candidate_recognition(recognition_result["recognized_user"])

    return recognition_result

# ✅ Check Liveness: Detect Blink from Webcam
def detect_blink():
    """Detects if the candidate blinks (liveness test)."""
    cap = cv2.VideoCapture(0)
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
    eye_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_eye.xml")

    blink_detected = False
    start_time = time.time()

    while True:
        ret, frame = cap.read()
        if not ret:
            logging.error("❌ Webcam error: Unable to read frame.")
            break

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, scaleFactor=1.3, minNeighbors=5)

        for (x, y, w, h) in faces:
            roi_gray = gray[y:y+h, x:x+w]
            eyes = eye_cascade.detectMultiScale(roi_gray)

            if len(eyes) == 0:
                blink_detected = True  # No eyes detected → Likely a blink
                break

        cv2.imshow("Liveness Detection - Blink Test", frame)

        if blink_detected or (time.time() - start_time > 5):  # Stop after 5 seconds
            break

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

    if blink_detected:
        logging.info("✅ Liveness Detected: Blink Confirmed.")
        return True
    else:
        logging.warning("❌ Liveness Test Failed: No Blink Detected.")
        return False
