import React, { useRef } from "react";
import Webcam from "react-webcam";

interface WebcamCaptureProps {
  setCapturedImage: (image: string | null) => void;
}

const WebcamCapture: React.FC<WebcamCaptureProps> = ({ setCapturedImage }) => {
  const webcamRef = useRef<Webcam>(null);

  // Function to capture image
  const captureImage = () => {
    if (webcamRef.current) {
      const imageSrc = webcamRef.current.getScreenshot();
      setCapturedImage(imageSrc || null);
    }
  };

  return (
    <div className="text-center">
      <Webcam
        audio={false}
        ref={webcamRef}
        screenshotFormat="image/png"
        className="mb-2"
      />
    </div>
  );
};

export default WebcamCapture;