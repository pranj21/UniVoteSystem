import { useState } from "react";
import { useNavigate } from "react-router";

export default function AdminLogin() {
  const [credentials, setCredentials] = useState({ username: "", password: "" });
  const [error, setError] = useState("");
  const navigate = useNavigate();

  const handleLogin = (e: React.FormEvent) => {
    e.preventDefault();

    const validAdmin = { username: "admin", password: "admin123" };

    if (credentials.username === validAdmin.username && credentials.password === validAdmin.password) {
      sessionStorage.setItem("admin", "true");
      navigate("/admin_dashboard");
    } else {
      setError("Invalid username or password");
    }
  };

  return (
    <div className="d-flex flex-column vh-100 vw-100 justify-content-center align-items-center background text-white">
      <div className="card p-4 shadow-lg w-50 text-center bg-light text-dark">
        <h2 className="mb-3 d-flex align-items-center justify-content-center">
          <h2 className="me-2" /> Admin Login
        </h2>
        {error && <p className="text-danger">{error}</p>}
        <form onSubmit={handleLogin}>
          <input 
            type="text" 
            className="form-control mb-2" 
            placeholder="Username" 
            required
            onChange={(e) => setCredentials({ ...credentials, username: e.target.value })} 
          />

          <input 
            type="password" 
            className="form-control mb-2" 
            placeholder="Password" 
            required
            onChange={(e) => setCredentials({ ...credentials, password: e.target.value })} 
          />

          <button type="submit" className="btn btn-primary w-100 mt-3">
            Login
          </button>
        </form>
      </div>
    </div>
  );
}
