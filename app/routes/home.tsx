import { Link, useNavigate } from "react-router";



export default function Home() {
  const navigate = useNavigate();
  return (
    <div className="d-flex flex-column vh-100 vw-100 justify-content-center align-items-center bg-light background">
      
        <div className="card p-4 shadow w-50 text-center">
        <h2>UniVote</h2>
          <h3>Select Login Type</h3>
          <button onClick={() => navigate("/voter")} className="btn btn-primary w-100 my-2">User Login</button>
          <button onClick={() => navigate("/candidate")} className="btn btn-primary w-100 my-2">Candidate Login</button>

          <p className="mt-2 text-center">
            New to UniVote?
          <Link to="/voter_register"> Sign Up</Link>
        </p>
        <p className="mt-2 text-center">
            Want to stand for the election?
          <Link to="/candidate_register"> Register as a Candidate</Link>
        </p>
        </div>
      </div>
  );
}
