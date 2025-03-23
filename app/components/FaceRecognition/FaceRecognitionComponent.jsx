import React, { useState, useRef } from "react";
import { useNavigate } from "react-router-dom";
import Webcam from "react-webcam";
import { captureFace } from "../../services/api";

const FaceRecognitionComponent = ({ onAuthenticated }) => {
    const webcamRef = useRef(null);
    const [capturedImage, setCapturedImage] = useState(null);
    const [authStatus, setAuthStatus] = useState(null);
    const [error, setError] = useState(null);
    const [isLoading, setIsLoading] = useState(false);
    const navigate = useNavigate();

    const handleCapture = async () => {
        setError(null);
        setAuthStatus(null);

        if (webcamRef.current) {
            const imageSrc = webcamRef.current.getScreenshot();
            if (imageSrc) {
                setCapturedImage(imageSrc);
                setIsLoading(true);

                try {
                    const response = await captureFace(imageSrc);
                    
                    if (response.data.authenticated) {
                        setAuthStatus("✅ Face Verified!");
                        onAuthenticated(true); // Notify parent component about authentication success
                        setTimeout(() => navigate("/dashboard"), 2000); // Redirect after success
                    } else {
                        setAuthStatus("❌ Face Not Recognized!");
                        onAuthenticated(false);
                    }
                } catch (err) {
                    setError("Error verifying face. Please try again.");
                    console.error("Face Authentication Error:", err);
                } finally {
                    setIsLoading(false);
                }
            }
        }
    };

    return (
        <div className="text-center">
            <h2>Multi-Factor Authentication (Face Recognition)</h2>

            {/* Webcam Preview */}
            <Webcam ref={webcamRef} screenshotFormat="image/jpeg" />

            {/* Capture Button */}
            <button className="btn btn-primary mt-3" onClick={handleCapture} disabled={isLoading}>
                {isLoading ? "Verifying..." : "Verify Face"}
            </button>

            {/* Show Captured Image */}
            {capturedImage && (
                <div className="mt-3">
                    <h3>Captured Image:</h3>
                    <img src={capturedImage} alt="Captured" className="img-thumbnail" />
                </div>
            )}

            {/* Show Authentication Status */}
            {authStatus && (
                <div className={`mt-3 ${authStatus.includes("✅") ? "text-success" : "text-danger"}`}>
                    <h3>{authStatus}</h3>
                </div>
            )}

            {/* Show Error Message */}
            {error && (
                <div className="mt-3 text-danger">
                    <h4>{error}</h4>
                </div>
            )}
        </div>
    );
};

export default FaceRecognitionComponent;
