import backend.services.faceRecognitionService as face_service
from backend.services.voterService import check_has_voted, update_voting_status
from backend.services.voteService import record_vote, get_results

import base64
from fastapi import UploadFile

def process_image(file: UploadFile):
    """
    Converts uploaded image to Base64 format.
    """
    image_data = file.file.read()
    return base64.b64encode(image_data).decode("utf-8")  # Convert to Base64 string

def verify_and_cast_vote(file: UploadFile, selected_candidate: str, universityID: str):
    """
    Recognizes voter, verifies eligibility, and casts their vote.
    :param file: Image file uploaded from frontend.
    :param selected_candidate: The candidate selected for voting.
    :param universityID: Voter's University ID.
    :return: Vote status or error message.
    """
    # ✅ Convert image to Base64
    image_base64 = process_image(file)

    # ✅ Face recognition
    recognition_result = face_service.recognize_face_base64(image_base64)


    if recognition_result["status"] == "error":
        return {"status": "error", "message": recognition_result["message"]}

    recognized_user = recognition_result.get("recognized_user")
    if not recognized_user or recognized_user != universityID:
        return {"status": "error", "message": "Face does not match the voter."}

    # ✅ Check if voter has already voted
    if check_has_voted(universityID):
        return {"status": "error", "message": "User has already voted."}

    # ✅ Record vote
    record_vote(universityID, selected_candidate)
    update_voting_status(universityID, True)

    return {"status": "success", "message": "Vote successfully cast!"}

def fetch_voting_results():
    """
    Retrieves current election results.
    :return: A dictionary containing vote counts per candidate.
    """
    return get_results()  # ✅ Fetch voting results
