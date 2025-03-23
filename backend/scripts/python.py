import sqlite3
import cv2
import numpy as np

DATABASE = "backend/data/voters.db"

conn = sqlite3.connect(DATABASE)
cursor = conn.cursor()

cursor.execute("SELECT image FROM voters WHERE universityID = '2'")
result = cursor.fetchone()
conn.close()

if result:
    image_array = np.frombuffer(result[0], np.uint8)
    stored_image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)
    cv2.imshow("Stored Face for University-2", stored_image)
    cv2.waitKey(0)
    cv2.destroyAllWindows()
else:
    print("❌ No image found for University-2!")
