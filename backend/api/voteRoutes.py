from fastapi import APIRouter, UploadFile, File, HTTPException, Form
from fastapi.responses import JSONResponse
from starlette.responses import StreamingResponse
import asyncio
import aiofiles
from backend.services.voteService import cast_vote , get_results # ✅ Import from voteService
import os
import base64
import cv2


router = APIRouter()

# ✅ Ensure log directory exists
LOG_DIR = "backend/logs"
os.makedirs(LOG_DIR, exist_ok=True)

# ✅ Define log file path
LOG_FILE = "backend/logs/vote_logs.log"

# ✅ Define directory for storing uploaded votes
UPLOAD_DIR = "uploaded_votes"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/cast")
async def cast_vote_api(
    file: UploadFile = File(...),  
    selected_candidate: str = Form(...),  
    universityID: str = Form(...)  
):
    try:
        # ✅ Debugging: Check received data
        print(f"✅ Received vote from: {universityID} for candidate: {selected_candidate}")
        print(f"📸 Received File: {file.filename}")

        # ✅ Save Image for Verification
        file_path = os.path.join(UPLOAD_DIR, f"{universityID}.jpg")
        with open(file_path, "wb") as f:
            f.write(await file.read())

        print(f"📸 File saved: {file_path}")

        # ✅ Call `cast_vote()` and Pass Image Path
        vote_data = {
            "universityID": universityID,
            "candidateID": selected_candidate,
            "image_path": file_path  # Pass file path instead of Base64
        }

        response = cast_vote(vote_data)  

       # if response["status"] == "success":
        return response  # ✅ Vote successfully cast

       # raise HTTPException(status_code=400, detail=response["message"])

    except Exception as e:
       # raise HTTPException(status_code=500, detail=f"Server Error: {str(e)}")
       return JSONResponse(content={"status": "error", "message": f"Server Error: {str(e)}"}, status_code=500)


@router.get("/results")
async def get_results_api():
    """
    Retrieve and return the election results.
    """
    try:
        response = get_results()

        if response["status"] == "success":
            return response

        raise HTTPException(status_code=400, detail=response["message"])

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Server Error: {str(e)}")

#Existing Logs
async def read_existing_logs():
    """Reads all existing logs from the log file."""
    if not os.path.exists(LOG_FILE):
        return []

    
    try:
        async with aiofiles.open(LOG_FILE, "r") as file:
            logs = await file.readlines()
        return logs
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading logs: {str(e)}")

async def stream_live_logs():
    """Streams the latest logs as they are written to the log file."""
    async def event_generator():
         try:
            async with aiofiles.open(LOG_FILE, "r") as file:
                await file.seek(0, os.SEEK_END)  # Move to the end of the file
                while True:
                    line = await file.readline()
                    if line:
                        yield f"data: {line.strip()}\n\n"
                    await asyncio.sleep(1)  # Adjust polling interval for real-time logs
         except Exception as e:
            yield f"data: Error reading live logs: {str(e)}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")

@router.get("/logs")
async def get_vote_logs():
    """Fetches both existing logs and streams live logs."""
    existing_logs = await read_existing_logs()
    return {
        "status": "success",
        "logs": existing_logs
    }

@router.get("/logs/live")
async def get_live_logs():
    """Streams the latest logs as they appear in the log file."""
    return await stream_live_logs()
