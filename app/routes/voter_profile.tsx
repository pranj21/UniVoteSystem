import { useEffect, useState } from "react";
import { useNavigate } from "react-router";

export default function VoterDashboard() {
  const [voter, setVoter] = useState<any>(null);
  const navigate = useNavigate();

  useEffect(() => {
    // Retrieve voter info from session storage
    const storedVoter = sessionStorage.getItem("voter");
    if (storedVoter) {
      const voter = JSON.parse(storedVoter);
      console.log(voter.firstname, voter.lastname,voter.universityID, voter.email, voter.image); // Debugging
      setVoter(voter);
    } else {
      navigate("/voter"); // Redirect if not found
    }
  }, [navigate]);

  return (
    <div className="d-flex flex-column vh-100 justify-content-center align-items-center bg-light background" >
      <div className="card p-4 shadow w-50">
        <h2 className="mb-3">Voter Profile</h2>
        {voter ? (
          <div>
            <p><strong>Name:</strong> {voter.firstname} {voter.lastname}</p>
            <p><strong>University ID:</strong> {voter.universityID}</p>
            <p><strong>Email:</strong> {voter.email}</p>
            {voter.image && (
              <img src={voter.image} alt="Profile" className="img-thumbnail" />
            )}
          </div>
        ) : (
          <p>Loading...</p>
        )}

    <button className="btn btn-success mt-3" onClick={() => navigate("/voter_dashboard")}>
          Cast Vote
        </button>      
        </div>
    </div>
  );
}    