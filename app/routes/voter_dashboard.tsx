import { useState, useEffect, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import { getAllCandidates } from "./utils/db";
import WebcamCapture from "./ImageCapture";

interface Candidate {
  universityID: string;
  firstname: string;
  lastname: string;
  aboutYourself: string;
  image?: string;
}

export default function VoterDashboard() {
  const [candidates, setCandidates] = useState<Candidate[]>([]);
  const [selectedCandidate, setSelectedCandidate] = useState<string>("");
  const [capturedImage, setCapturedImage] = useState<string | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const navigate = useNavigate();

  const fetchCandidates = useCallback(async () => {
    setLoading(true);
    try {
      const candidatesList = await getAllCandidates();
      if (Array.isArray(candidatesList)) {
        setCandidates(candidatesList);
      } else {
        setCandidates([]);
      }
    } catch (error) {
      console.error("❌ Error fetching candidates:", error);
      setCandidates([]);
    }
    setLoading(false);
  }, []);

  useEffect(() => {
    const voter = sessionStorage.getItem("voter");
    if (!voter) {
      navigate("/voter");
      return;
    }

    fetchCandidates();
    const interval = setInterval(fetchCandidates, 10000);
    return () => clearInterval(interval);
  }, [navigate, fetchCandidates]);

  const castVote = async () => {
    if (!selectedCandidate) {
      alert("⚠️ Please select a candidate before voting.");
      return;
    }

    if (!capturedImage) {
      alert("⚠️ Please capture your image first.");
      return;
    }

    const storedVoter = sessionStorage.getItem("voter");
    if (!storedVoter) {
      alert("⚠️ Session expired, please login again.");
      navigate("/voter");
      return;
    }

    const voter = JSON.parse(storedVoter);

    try {
      const response = await fetch(capturedImage);
      const blob = await response.blob();
      const file = new File([blob], `${voter.universityID}.jpg`, { type: "image/jpeg" });

      const formData = new FormData();
      formData.append("file", file);
      formData.append("selected_candidate", selectedCandidate);
      formData.append("universityID", voter.universityID);

      const voteResponse = await fetch("http://127.0.0.1:8000/api/vote/cast", {
        method: "POST",
        body: formData,
      });

      const result = await voteResponse.json();

      if (voteResponse.status === 200 && result.status === "success") {
        alert("✅ Vote cast successfully!");
        navigate("/voter_profile");
      } else if (
        voteResponse.status === 400 &&
        result.message.toLowerCase().includes("already voted")
      ) {
        alert("❌ You have already voted. Multiple votes are not allowed!");
      } else {
        alert(`❌ Error: ${result.message}`);
      }
    } catch (error) {
      console.error("❌ Error casting vote:", error);
      alert("⚠️ Unable to submit vote. Please try again.");
    }
  };

  return (
    <div className="d-flex flex-column vh-100 justify-content-center align-items-center background">
      <h2 className="mb-3 text-center">Vote for Your Candidate</h2>
      <div className="card p-4 shadow w-50">
        {/* Candidate Dropdown */}
        <div className="mb-3">
          <label className="form-label">Select a Candidate:</label>
          <select
            className="form-select"
            value={selectedCandidate}
            onChange={(e) => setSelectedCandidate(e.target.value)}
            disabled={loading || candidates.length === 0}
          >
            <option value="">-- Choose a Candidate --</option>
            {candidates.map((candidate) => (
              <option key={candidate.universityID} value={candidate.universityID}>
                {candidate.firstname} {candidate.lastname}
              </option>
            ))}
          </select>
        </div>

        {/* Candidate Info */}
        <div className="card mt-3 p-3">
          <h5>Candidate Details:</h5>
          {selectedCandidate ? (
            candidates
              .filter((c) => c.universityID === selectedCandidate)
              .map((candidate) => (
                <div key={candidate.universityID}>
                  <p><strong>Name:</strong> {candidate.firstname} {candidate.lastname}</p>
                  <p><strong>About:</strong> {candidate.aboutYourself}</p>
                </div>
              ))
          ) : (
            <p className="text-muted">Select a candidate to view details</p>
          )}
        </div>

        <WebcamCapture onCapture={setCapturedImage} />

        {/* Vote Button */}
        <button className="btn btn-success mt-3 w-100" onClick={castVote} disabled={loading}>
          {loading ? "⏳ Submitting Vote..." : "🗳️ Submit Vote"}
        </button>
      </div>
    </div>
  );
}
