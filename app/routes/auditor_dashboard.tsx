import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

interface Candidate {
  universityID: string;
  firstname: string;
  lastname: string;
  votes: number;
  image: string;
}

export default function AuditorDashboard() {
  const [candidates, setCandidates] = useState<Candidate[]>([]);
  const [winner, setWinner] = useState<Candidate | null>(null);
  const [approved, setApproved] = useState(false);
  const [logs, setLogs] = useState<string[]>([]);
  const [error, setError] = useState("");
  const navigate = useNavigate();

  useEffect(() => {
    const isAuditor = sessionStorage.getItem("auditor");
    if (!isAuditor) navigate("/auditor-login");
  }, [navigate]);

  const fetchResults = async () => {
    try {
      console.log("🔄 Fetching election results...");
  
      // Step 1: Fetch vote results
      const response = await fetch("http://127.0.0.1:8000/api/vote/results");
      if (!response.ok) throw new Error(`Failed to fetch results: ${response.status}`);
      const data = await response.json();
  
      if (!data || data.status !== "success") {
        throw new Error(data.message || "Error retrieving election results.");
      }
      console.log("✅ Election results received:", data.results);
  
      // Step 2: Fetch candidate details
      const candidateResponse = await fetch("http://127.0.0.1:8000/api/candidate/get_all_candidates");
      if (!candidateResponse.ok) throw new Error(`Failed to fetch candidates: ${candidateResponse.status}`);
      const candidatesData = await candidateResponse.json();
  
      // ✅ Ensure API response is in correct format
      if (!candidatesData || !Array.isArray(candidatesData.candidates)) {
        throw new Error("Invalid candidate data format.");
      }
  
      console.log("✅ Candidate details received:", candidatesData.candidates);
  
      // Step 3: Merge votes with candidates
      const enrichedCandidates: Candidate[] = candidatesData.candidates.map((c: any) => ({
        universityID: c.universityID,
        firstname: c.firstname,
        lastname: c.lastname,
        votes: data.results[c.universityID] || 0, // Default to 0 if no votes
        image: c.image || "", // Ensure empty image is handled
      })).sort((a: Candidate, b: Candidate) => b.votes - a.votes); // Sort by votes
  
      console.log("📊 Processed Candidate List:", enrichedCandidates);
  
      // Step 4: Update State
      setCandidates(enrichedCandidates);
      if (enrichedCandidates.length > 0) {
        setWinner(enrichedCandidates[0]); // Set top-voted candidate as winner
      }
  
    } catch (err) {
      console.error("❌ Error fetching election results:", err);
      setError("❌ Unable to fetch election results. Try again.");
    }
  };

  const fetchLogs = async () => {
    try {
      const response = await fetch("http://127.0.0.1:8000/api/vote/logs");
      const data = await response.json();
      if (response.ok && data.status === "success") {
        setLogs(data.logs.reverse());
      }
    } catch (err) {
      setLogs(["❌ Error fetching logs"]);
    }
  };

  useEffect(() => {
    fetchLogs();
    const interval = setInterval(fetchLogs, 5000);
    return () => clearInterval(interval);
  }, []);

  const handleApprove = () => {
    if (candidates.length === 0) return;
    setWinner(candidates[0]);
    setApproved(true);
  };

  return (
    <div className="container mt-5">
      <h2 className="text-center mb-4">🗳 Auditor Panel</h2>

      <div className="text-center">
        <button className="btn btn-info me-3" onClick={fetchResults}>📊 Show Results</button>
        <button className="btn btn-success" onClick={handleApprove} disabled={candidates.length === 0}>
          ✅ Approve Result
        </button>
      </div>

      {error && <p className="text-danger text-center mt-3">{error}</p>}

      {candidates.length > 0 && (
        <div className="mt-4">
          <h4>📊 Candidate Vote Counts</h4>
          <table className="table table-bordered table-striped">
            <thead>
              <tr>
                <th>Photo</th>
                <th>Name</th>
                <th>University ID</th>
                <th>Votes</th>
              </tr>
            </thead>
            <tbody>
              {candidates.map((c) => (
                <tr key={c.universityID}>
                  <td><img src={`data:image/jpeg;base64,${c.image}`} alt={c.firstname} width="60" /></td>
                  <td>{c.firstname} {c.lastname}</td>
                  <td>{c.universityID}</td>
                  <td>{c.votes}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {approved && winner && (
        <div className="alert alert-success mt-4 text-center">
          <h4>🏆 Approved Winner</h4>
          <img src={`data:image/jpeg;base64,${winner.image}`} alt={winner.firstname} width="120" className="rounded-circle mb-3"/>
          <p><strong>Name:</strong> {winner.firstname} {winner.lastname}</p>
          <p><strong>University ID:</strong> {winner.universityID}</p>
          <p><strong>Total Votes:</strong> {winner.votes}</p>
          <p className="text-success fw-bold">✅ Officially Approved as Winner</p>
        </div>
      )}

      <div className="mt-4">
        <h4>📜 Live Voting Logs</h4>
        <div className="log-container bg-dark text-white p-3 rounded" style={{ maxHeight: "300px", overflowY: "scroll" }}>
          {logs.length > 0 ? logs.map((log, index) => (
            <p key={index} className="mb-1">{log}</p>
          )) : <p>No logs available</p>}
        </div>
      </div>
    </div>
  );
}