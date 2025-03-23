import sqlite3
import logging
import numpy as np
import cv2

# ✅ Database Path
DATABASE_PATH = "backend/data/voters.db"


# ✅ Configure Logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def fetch_all_voters_faces():
    """
    Fetch all voter face images and their university IDs from the database.
    :return: List of (universityID, image_array)
    """
    results = []

    try:
        logging.info("📡 Fetching all voter face images from the database...")

        # ✅ Connect to SQLite Database
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()

        # ✅ Execute Query
        cursor.execute("SELECT universityID, image FROM voters")
        stored_faces = cursor.fetchall()

        if not stored_faces:
            logging.warning("⚠️ No voter face data found in the database.")
            return []

        # ✅ Process Each Record
        for universityID, stored_image in stored_faces:
            if not stored_image:
                logging.warning(f"⚠️ No image found for University ID: {universityID}")
                continue  # Skip empty images

            try:
                # ✅ Convert Binary Data to OpenCV Image
                stored_image_array = np.frombuffer(stored_image, np.uint8)
                stored_image_cv = cv2.imdecode(stored_image_array, cv2.IMREAD_COLOR)

                if stored_image_cv is None:
                    logging.error(f"❌ Failed to decode image for University ID: {universityID}")
                    continue

                # ✅ Optional: Convert to Grayscale for Face Recognition
                stored_image_cv = cv2.cvtColor(stored_image_cv, cv2.COLOR_BGR2GRAY)

                # ✅ Append Processed Data
                results.append((universityID, stored_image_cv))

            except Exception as img_error:
                logging.error(f"❌ Error processing image for University ID {universityID}: {str(img_error)}")

        logging.info(f"✅ Successfully fetched {len(results)} voter faces.")

    except sqlite3.Error as db_error:
        logging.error(f"❌ Database error fetching voters' faces: {str(db_error)}")

    finally:
        # ✅ Ensure Database Connection is Closed
        if conn:
            conn.close()

    return results
