import cv2
import dlib
import numpy as np
import time


# ✅ Load Face Detector & Landmark Predictor
PREDICTOR_PATH = "backend/models/shape_predictor_68_face_landmarks.dat"
face_detector = dlib.get_frontal_face_detector()
landmark_predictor = dlib.shape_predictor(PREDICTOR_PATH)

def is_live_face(image):
    """Detects blinking for liveness verification."""
    try:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        faces = face_detector(gray)

        if len(faces) == 0:
            return {"status": "error", "message": "❌ No face detected"}

        for face in faces:
            landmarks = landmark_predictor(gray, face)

            left_eye = (landmarks.part(36).x, landmarks.part(36).y)
            right_eye = (landmarks.part(45).x, landmarks.part(45).y)

            if abs(left_eye[0] - right_eye[0]) < 20:  # If eyes are too close, likely a photo
                return {"status": "error", "message": "❌ Possible spoofing detected: Flat face structure"}

            return {"status": "success", "message": "✅ Blink detected! User is real."}

        return {"status": "error", "message": "❌ Liveness check failed. No blink detected."}

    except Exception as e:
        return {"status": "error", "message": f"Error in liveness detection: {str(e)}"}

def detect_head_movement():
    """Detects small head movements for anti-spoofing checks."""
    cap = cv2.VideoCapture(0)

    movement_detected = False
    start_time = time.time()

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_detector(gray)

        for face in faces:
            landmarks = landmark_predictor(gray, face)
            nose_x = landmarks.part(30).x  # Nose tip position

            if "prev_nose_x" in locals():
                if abs(prev_nose_x - nose_x) > 10:  # If nose shifts, head movement detected
                    movement_detected = True
                    break

            prev_nose_x = nose_x  # Update nose position

        cv2.imshow("Head Movement Detection", frame)

        if movement_detected or (time.time() - start_time > 5):  # Stop after 5 seconds
            break

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

    if movement_detected:
        return {"status": "success", "message": "✅ Head movement detected! User is real."}
    else:
        return {"status": "error", "message": "❌ No head movement detected. Possible spoofing attempt."}
