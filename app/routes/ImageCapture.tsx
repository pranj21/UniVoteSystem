import React, { useRef, useState } from "react";
import Webcam from "react-webcam";

interface WebcamCaptureProps {
  onCapture: (imageSrc: string) => void;
}

const WebcamCapture: React.FC<WebcamCaptureProps> = ({ onCapture }) => {
  const webcamRef = useRef<Webcam>(null);
  const [capturedImage, setCapturedImage] = useState<string | null>(null);
  const [isCameraOn, setIsCameraOn] = useState(false); // Camera off by default

  // Function to start the camera
  const startCamera = () => {
    setCapturedImage(null); // Reset captured image
    setIsCameraOn(true);
  };

  // Function to capture image
  const capture = () => {
    if (webcamRef.current) {
      const imageSrc = webcamRef.current.getScreenshot();
      if (imageSrc) {
        setCapturedImage(imageSrc);
        onCapture(imageSrc);
        setIsCameraOn(false); // Hide camera after capture
      }
    }
  };

  return (
    <div className="text-center">
      {/* If an image is captured, show it */}
      {capturedImage ? (
        <>
          <img src={capturedImage} alt="Captured" className="img-thumbnail mb-3" />
          <div>
            <button className="btn btn-success me-2" type="button">
              Proceed
            </button>
            <button className="btn btn-warning" type="button" onClick={startCamera}>
              Retake Photo
            </button>
          </div>
        </>
      ) : (
        <>
          {/* Show start camera button if the camera is off */}
          {!isCameraOn && (
            <button className="btn btn-primary" type="button" onClick={startCamera}>
              Start Camera
            </button>
          )}

          {/* Show the webcam when camera is on */}
          {isCameraOn && (
            <>
              <Webcam
                ref={webcamRef}
                screenshotFormat="image/jpeg"
                videoConstraints={{ facingMode: "user" }}
                className="mb-3"
              />
              <div>
                <button className="btn btn-primary me-2" type="button" onClick={capture}>
                  Capture Image
                </button>
                <button className="btn btn-secondary" type="button" onClick={() => setIsCameraOn(false)}>
                  Cancel
                </button>
              </div>
            </>
          )}
        </>
      )}
    </div>
  );
};

export default WebcamCapture;
