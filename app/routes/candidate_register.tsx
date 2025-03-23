import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import WebcamCapture from "./ImageCapture"; // Ensure correct path

export default function CandidateRegister() {
  const navigate = useNavigate();
  const [image, setImage] = useState<string | null>(null); // Store captured image
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleRegister = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const form = e.target as HTMLFormElement;

    if (!image) {
      alert("Please capture your image before submitting.");
      return;
    }

    if (form.checkValidity()) {
      const formData = new FormData(form);
      const candidateData = {
        firstname: formData.get("firstname") as string,
        lastname: formData.get("lastname") as string,
        universityID: formData.get("universityID") as string,
        email: formData.get("email") as string,
        password: formData.get("password") as string,
        confirmPassword: formData.get("confirmPassword") as string,
        aboutYourself: formData.get("aboutYourself") as string,
        image, // Store captured image (Base64 format)
      };

      // Check if passwords match
      if (candidateData.password !== candidateData.confirmPassword) {
        alert("Passwords do not match.");
        return;
      }

      setIsSubmitting(true);

      try {
        // ✅ Send data to FastAPI (SQLite Backend)
        const response = await fetch("http://127.0.0.1:8000/api/candidate/register", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify(candidateData),
        });

        const result = await response.json();

        if (response.ok) {
          alert("Registration Successful!");
          navigate("/candidate");
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
    } else {
      form.classList.add("was-validated");
    }
  };

  return (
    <div className="d-flex flex-column vh-100 vw-100 justify-content-center align-items-center bg-light background">
      <div className="card p-4 shadow w-50 text-center">
        <h2 className="mb-3">Register as Candidate</h2>
        <form noValidate onSubmit={handleRegister}>
          <div className="mb-3">
            <input type="text" className="form-control" name="firstname" placeholder="First Name" required />
            <div className="invalid-feedback">Please enter your Firstname.</div>
          </div>
          <div className="mb-3">
            <input type="text" className="form-control" name="lastname" placeholder="Last Name" required />
            <div className="invalid-feedback">Please enter your Last name.</div>
          </div>
          <div className="mb-3">
            <input type="text" className="form-control" name="universityID" placeholder="University ID" required />
            <div className="invalid-feedback">Please enter your University ID.</div>
          </div>
          <div className="mb-3">
            <input type="email" className="form-control" name="email" placeholder="University Email" required />
            <div className="invalid-feedback">Please enter a valid University email.</div>
          </div>
          <div className="mb-3">
            <input type="password" className="form-control" name="password" placeholder="Create Password" required />
            <div className="invalid-feedback">Please create a password.</div>
          </div>
          <div className="mb-3">
            <input type="password" className="form-control" name="confirmPassword" placeholder="Confirm Password" required />
            <div className="invalid-feedback">Please confirm your password.</div>
          </div>
          <div className="mb-3">
            <textarea className="form-control" name="aboutYourself" rows={4} placeholder="Tell us about yourself" required />
            <div className="invalid-feedback">Please tell us about yourself.</div>
          </div>

          {/* Image Capture Section */}
          <div className="mb-3">
            <label>Capture Your Image:</label>
            <WebcamCapture onCapture={(img) => setImage(img)} />
          </div>

          <button className="btn btn-primary w-100" type="submit" disabled={isSubmitting}>
            {isSubmitting ? "Registering..." : "Confirm Registration"}
          </button>
        </form>

        <p className="mt-2 text-center">
          <Link to="/candidate">Already registered? Sign In</Link>
        </p>
      </div>
    </div>
  );
}
