import { useState } from "react";

interface Voter {
  universityID: string;
  firstname: string;
  lastname: string;
  email: string;
  image?: string; // ✅ Optional for handling missing images
}

interface Candidate {
  universityID: string;
  firstname: string;
  lastname: string;
  aboutYourself: string;
  image: string;
}

export default function AdminDashboard() {
  const [voters, setVoters] = useState<Voter[]>([]);
  const [candidates, setCandidates] = useState<Candidate[]>([]);
  const [showVoters, setShowVoters] = useState(false);
  const [showCandidates, setShowCandidates] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  // ✅ Fetch All Voters
  const fetchVoters = async () => {
    setLoading(true);
    setError("");

    try {
      const response = await fetch("http://127.0.0.1:8000/api/voter/get_voters"); // ✅ Fixed API URL
      const data = await response.json();

      if (!response.ok || data.status !== "success") {
        throw new Error(data.message || "Failed to fetch voters.");
      }

      setVoters(data.voters);
      setShowVoters(true);
      setShowCandidates(false);
    } catch (err) {
      setError("❌ Error fetching voters.");
    } finally {
      setLoading(false);
    }
  };

  // ✅ Fetch All Candidates
  const fetchCandidates = async () => {
    setLoading(true);
    setError("");

    try {
      const response = await fetch("http://127.0.0.1:8000/api/candidate/get_all_candidates");
      const data = await response.json();

      if (!response.ok || data.status !== "success") {
        throw new Error(data.message || "Failed to fetch candidates.");
      }

      setCandidates(data.candidates);
      setShowCandidates(true);
      setShowVoters(false);
    } catch (err) {
      setError("❌ Error fetching candidates.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="container mt-4">
      <h2 className="text-center mb-4">Admin Dashboard</h2>

      {/* ✅ Buttons to Fetch Voter & Candidate Data */}
      <div className="d-flex justify-content-between">
        <button className="btn btn-primary" onClick={fetchVoters}>👤 Show Voters</button>
        <button className="btn btn-secondary" onClick={fetchCandidates}>🏆 Show Candidates</button>
      </div>

      {/* ✅ Loading Indicator */}
      {loading && <p className="text-center mt-3">⏳ Loading...</p>}

      {/* ✅ Show Error Message */}
      {error && <p className="text-danger mt-3 text-center">{error}</p>}

      {/* ✅ Voter Details Table */}
      {showVoters && !loading && voters.length > 0 && (
        <div className="mt-4">
          <h4>👤 Voters List</h4>
          <table className="table table-bordered table-striped">
            <thead>
              <tr>
                <th>Photo</th>
                <th>University ID</th>
                <th>Name</th>
                <th>Email</th>
              </tr>
            </thead>
            <tbody>
              {voters.map((voter) => (
                <tr key={voter.universityID}>
                  <td>
                    {voter.image ? (
                      <img 
                        src={voter.image} 
                        alt={voter.firstname} 
                        width="60"
                        onError={(e) => (e.currentTarget.src = "/default-avatar.png")} // ✅ Handle broken images
                      />
                    ) : (
                      <span>No Image</span>
                    )}
                  </td>
                  <td>{voter.universityID}</td>
                  <td>{voter.firstname} {voter.lastname}</td>
                  <td>{voter.email}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* ✅ Candidate Details Table */}
      {showCandidates && !loading && candidates.length > 0 && (
        <div className="mt-4">
          <h4>🏆 Candidates List</h4>
          <table className="table table-bordered table-striped">
            <thead>
              <tr>
                <th>Photo</th>
                <th>Name</th>
                <th>University ID</th>
                <th>About</th>
              </tr>
            </thead>
            <tbody>
              {candidates.map((candidate) => (
                <tr key={candidate.universityID}>
                  <td>
                    <img 
                      src={`data:image/jpeg;base64,${candidate.image}`} 
                      alt={candidate.firstname} 
                      width="60"
                      onError={(e) => (e.currentTarget.src = "/default-avatar.png")} // ✅ Handle broken images
                    />
                  </td>
                  <td>{candidate.firstname} {candidate.lastname}</td>
                  <td>{candidate.universityID}</td>
                  <td>{candidate.aboutYourself}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* ✅ No Data Message */}
      {!loading && (showVoters || showCandidates) && (voters.length === 0 && candidates.length === 0) && (
        <p className="text-center mt-3">No records found.</p>
      )}
    </div>
  );
}
