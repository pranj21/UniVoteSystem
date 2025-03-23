import { useState, useRef } from "react";
import { useNavigate, Link } from "react-router-dom";
import Webcam from "react-webcam";

export default function VoterLogin() {
  const navigate = useNavigate();
  const [loginData, setLoginData] = useState({ universityID: "", password: "" });
  const [isVerifying, setIsVerifying] = useState(false);
  const [recognizedUser, setRecognizedUser] = useState<{ name: string; universityID: string } | null>(null);
  const [faceBox, setFaceBox] = useState<number[] | null>(null);
  const webcamRef = useRef<Webcam | null>(null);

  // ✅ Handle Webcam Access Errors
  const handleWebcamError = (error: any) => {
    console.error("Webcam access denied or error:", error);
    alert("⚠️ Webcam access is required for face recognition.");
  };

  const handleLogin = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();

    if (!loginData.universityID || !loginData.password) {
      alert("Please enter your University ID and Password.");
      return;
    }

    let voter = null;
    try {
      // ✅ Step 1: Fetch Voter Data
      const voterResponse = await fetch("http://127.0.0.1:8000/api/voter/get_voter", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ universityID: loginData.universityID }),
      });

      if (!voterResponse.ok) {
        alert("Invalid University ID");
        return;
      }

      voter = await voterResponse.json();
    } catch (error) {
      console.error("Error fetching voter:", error);
      alert("Server error while fetching voter details.");
      return;
    }

    try {
      // ✅ Step 2: Verify Password
      const passwordResponse = await fetch("http://127.0.0.1:8000/api/voter/verify-password", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ universityID: loginData.universityID, inputPassword: loginData.password }),
      });

      const passwordResult = await passwordResponse.json();
      if (passwordResult.status !== "success") {
        alert("Invalid password");
        return;
      }
    } catch (error) {
      console.error("Password verification error:", error);
      alert("Error verifying password. Please try again.");
      return;
    }

    // ✅ Step 3: Capture Face Image from Webcam
    if (!webcamRef.current) {
      alert("Webcam is not available!");
      return;
    }

    const imageSrc = webcamRef.current.getScreenshot();
    if (!imageSrc) {
      alert("Failed to capture image. Ensure webcam is working.");
      return;
    }

    setIsVerifying(true);

    try {
      // ✅ Convert Base64 Image to File
      const response = await fetch(imageSrc);
      const blob = await response.blob();
      const file = new File([blob], "face_capture.jpg", { type: "image/jpeg" });

      // ✅ Send Face Image to FastAPI for Recognition
      const formData = new FormData();
      formData.append("file", file);

      const faceResponse = await fetch("http://127.0.0.1:8000/api/face/recognize", {
        method: "POST",
        body: formData,
      });

      const recognitionResult = await faceResponse.json();
      setIsVerifying(false);

      // ✅ Handle Face Recognition Response
      if (recognitionResult.status === "success") {
        if (recognitionResult.recognized_user.universityID === loginData.universityID) {
          // store voter details in sessionStorage
          const voterData = {
            universityID: voter.universityID,
            firstname: voter.firstname,
            lastname: voter.lastname,
            email: voter.email,
            image: voter.image, // Ensure backend sends this
          };
          sessionStorage.setItem("voter", JSON.stringify(voter));
          navigate("/voter_profile", { state: { voter } });

          setRecognizedUser({
            name: recognitionResult.recognized_user.name,
            universityID: recognitionResult.recognized_user.universityID
          });

          setFaceBox(recognitionResult.face_location || null);
        } else {
          alert(`Face recognition mismatch! Found: ${recognitionResult.recognized_user.name}`);
        }
      } else {
        alert("Face recognition failed. Please try again.");
        setRecognizedUser(null);
        setFaceBox(null);
      }
    } catch (error) {
      console.error("Face recognition error:", error);
      alert("Error recognizing face. Please try again.");
      setIsVerifying(false);
    }
  };

  return (
    <div className="d-flex flex-column vh-100 vw-100 justify-content-center align-items-center bg-light background">
      <div className="card p-4 shadow w-50 text-center">
        <h2 className="mb-3">Voter Login</h2>
        <button onClick={() => navigate("/")} className="btn btn-secondary w-20 mb-3">Back</button>

        <form onSubmit={handleLogin}>
          <input 
            type="text" 
            className="form-control mb-2" 
            placeholder="University ID" 
            required
            onChange={(e) => setLoginData({ ...loginData, universityID: e.target.value })} 
          />

          <input 
            type="password" 
            className="form-control mb-2" 
            placeholder="Password" 
            required
            onChange={(e) => setLoginData({ ...loginData, password: e.target.value })} 
          />

          {/* ✅ Webcam for Face Capture */}
          <div className="webcam-container position-relative mb-3">
            <Webcam 
              ref={webcamRef} 
              screenshotFormat="image/jpeg" 
              width={320} 
              height={240} 
              onUserMediaError={handleWebcamError} // ✅ Handle Webcam Errors
            />
            
            {/* ✅ Display Recognized Name and University ID */}
            {recognizedUser && faceBox && (
              <div 
                className="position-absolute bg-dark text-white p-1 rounded"
                style={{
                  top: faceBox[1] - 30, left: faceBox[0],
                  width: faceBox[2], height: faceBox[3]
                }}>
                {recognizedUser.name} ({recognizedUser.universityID})
              </div>
            )}
          </div>

          {isVerifying && <p className="text-warning">Verifying face, please wait...</p>}

          <button type="submit" className="btn btn-primary w-100 mt-3">Login</button>
        </form>

        <p className="mt-2">
          New User? <Link to="/voter_register"> Sign Up</Link>
        </p>
      </div>
    </div>
  );
}
