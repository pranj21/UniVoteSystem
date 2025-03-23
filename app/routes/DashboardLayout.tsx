import { Outlet, useNavigate } from "react-router";

export default function DashboardLayout() {
  const navigate = useNavigate();

  return (
    <div className="d-flex">
      {/* Sidebar */}
      <div className="bg-dark text-white p-3" style={{ width: "250px", height: "100vh" }}>
        <h3>Dashboard</h3>
        <ul className="list-unstyled">
          <li>
            <button className="btn btn-link text-white" onClick={() => navigate("/")}>
              Home
            </button>
          </li>
          <li>
            <button className="btn btn-link text-white" onClick={() => navigate("/voter")}>
              Voter
            </button>
          </li>
          <li>
            <button className="btn btn-link text-white" onClick={() => navigate("/candidate")}>
              Candidate
            </button>
          </li>
        </ul>
      </div>

      {/* Main Content */}
      <div className="flex-grow-1 p-4">
        <Outlet />
      </div>
    </div>
  );
}
