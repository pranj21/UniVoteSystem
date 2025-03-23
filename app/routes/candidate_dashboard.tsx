import { useEffect, useState } from "react";
import { useNavigate } from "react-router";
import { getCandidate } from "./utils/db"; // ✅ Import your API call


interface Candidate {
  universityID: string;
  firstname: string;
  lastname: string;
  aboutYourself: string;
  image?: string;
}

export default function CandidateDashboard() {
  const [candidate, setCandidate] = useState<any>(null);
  const navigate = useNavigate();

  useEffect(() => {
    const fetchCandidateDetails = async () => {
      const storedCandidate = sessionStorage.getItem("candidate");

      if (storedCandidate) {
        const parsed = JSON.parse(storedCandidate);
        try {
          const response = await getCandidate(parsed.universityID);
          if (response.status === "success") {
            setCandidate(response.candidate);
          } else {
            console.error("Candidate not found");
            navigate("/candidate");
          }
        } catch (error) {
          console.error("Error fetching candidate:", error);
          navigate("/candidate");
        }
      } else {
        navigate("/candidate");
      }
    };

    fetchCandidateDetails();
  }, [navigate]);

  return (
    <div className="d-flex flex-column vh-100 justify-content-center align-items-center bg-light background">
      <div className="card p-4 shadow w-50">
        <button onClick={() => navigate("/candidate")} className="btn btn-secondary w-20 mb-3">
          Back
        </button>
        <h2 className="mb-3">Candidate Profile</h2>
        {candidate ? (
          <div>
            <p><strong>Name:</strong> {candidate.firstname} {candidate.lastname}</p>
            <p><strong>University ID:</strong> {candidate.universityID}</p>
            <p><strong>Email:</strong> {candidate.email}</p>
            <p><strong>About:</strong> {candidate.aboutYourself}</p>
            {candidate.image && (
              <img
                src={`data:image/png;base64,${candidate.image}`}
                alt="Profile"
                className="img-thumbnail"
              />
            )}
          </div>
        ) : (
          <p>Loading...</p>
        )}
        <button className="btn btn-success mt-3" onClick={() => navigate("/voter_dashboard")}>
          Cast Vote
        </button>
        <button className="btn btn-success mt-3" onClick={() => navigate("/result")}>
          View Results
        </button>
      </div>
    </div>
  );
}
