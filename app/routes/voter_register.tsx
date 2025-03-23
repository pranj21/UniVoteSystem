import { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import WebcamCapture from "./ImageCapture"; // ✅ Ensure correct path

export default function VoterRegister() {
  const navigate = useNavigate();

  const [voterData, setVoterData] = useState({
    firstname: "",
    lastname: "",
    universityID: "",
    email: "",
    password: "",
    confirmPassword: "",
  });

  const [capturedImage, setCapturedImage] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [imageCaptured, setImageCaptured] = useState(false);

  const handleRegister = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();

    if (!voterData.firstname || !voterData.lastname || !voterData.universityID || !voterData.email || !voterData.password || !voterData.confirmPassword) {
      alert("All fields are required!");
      return;
    }

    if (voterData.password !== voterData.confirmPassword) {
      alert("Passwords do not match!");
      return;
    }

    if (!capturedImage) {
      alert("Please capture an image before proceeding.");
      return;
    }

    const newVoter = {
      firstname: voterData.firstname.trim(),
      lastname: voterData.lastname.trim(),
      universityID: voterData.universityID.trim(),
      email: voterData.email.trim(),
      password: voterData.password,
      image: capturedImage, // Base64 image
    };

    setIsSubmitting(true);

    try {
      const response = await fetch("http://127.0.0.1:8000/api/face/register", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(newVoter),
      });

      const result = await response.json();

      if (response.ok) {
        const voterData = {
          universityID: result.universityID,
          firstname: result.firstname,
          lastname: result.lastname,
          email: result.email,
          image: result.image, // Ensure backend sends this
        };
      
        sessionStorage.setItem("voter", JSON.stringify(voterData)); // ✅ Store voter details
      
        alert("Registration Successful!");
        navigate("/voter_profile", { state: { voterData } });
      } else {
        console.error("Registration Error:", result);
        alert(result.detail || "Registration failed. Please try again.");
      }
    } catch (error) {
      console.error("Error during registration:", error);
      alert("An error occurred. Please try again.");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="d-flex flex-column vh-100 vw-100 justify-content-center align-items-center bg-light background">
      <div className="card p-4 shadow w-50 text-center">
        <h2 className="mb-3 text-center">Voter Registration</h2>
        <form onSubmit={handleRegister}>
          <input type="text" className="form-control mb-2" placeholder="First Name" required
            value={voterData.firstname}
            onChange={(e) => setVoterData({ ...voterData, firstname: e.target.value })} />

          <input type="text" className="form-control mb-2" placeholder="Last Name" required
            value={voterData.lastname}
            onChange={(e) => setVoterData({ ...voterData, lastname: e.target.value })} />

          <input type="text" className="form-control mb-2" placeholder="University ID" required
            value={voterData.universityID}
            onChange={(e) => setVoterData({ ...voterData, universityID: e.target.value })} />

          <input type="email" className="form-control mb-2" placeholder="Email" required
            value={voterData.email}
            onChange={(e) => setVoterData({ ...voterData, email: e.target.value })} />

          <input type="password" className="form-control mb-2" placeholder="Password" required
            value={voterData.password}
            onChange={(e) => setVoterData({ ...voterData, password: e.target.value })} />

          <input type="password" className="form-control mb-2" placeholder="Confirm Password" required
            value={voterData.confirmPassword}
            onChange={(e) => setVoterData({ ...voterData, confirmPassword: e.target.value })} />

          {/* ✅ Webcam for capturing face */}
          <WebcamCapture onCapture={(image) => {
            setCapturedImage(image);
            setImageCaptured(true);
          }} />

          {/* ✅ Show a message when image is captured */}
          {imageCaptured && <p className="text-success mt-2">✅ Image Captured Successfully!</p>}

          <button type="submit" className="btn btn-primary w-100 mt-3" disabled={isSubmitting}>
            {isSubmitting ? "Registering..." : "Register"}
          </button>
        </form>

        <p className="mt-2 text-center">
          Already have an account?
          <Link to="/voter"> Sign in</Link>
        </p>
      </div>
    </div>
  );
}
