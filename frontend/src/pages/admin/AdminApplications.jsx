// frontend/src/pages/admin/AdminApplications.jsx
import { useEffect, useState,useRef } from "react";
import Navbar from "../../components/shared/Navbar";
import { adminAPI } from "../../services/api";
import { STATUS_COLORS } from "../../utils/constants";
import "../../styles/dashboard.css";
import "../../styles/admin-applications.css";
import { useNavigate } from "react-router-dom";

export default function AdminApplications() {
  const [applications, setApplications] = useState([]);
  const [loading, setLoading]           = useState(true);
  const navigate = useNavigate();
  const wsRef = useRef(null);

  const fetchAll = () => {
    adminAPI.getAllApplications()
      .then(({ data }) => setApplications(data))
      .finally(() => setLoading(false));
  };

  useEffect(() => { fetchAll(); }, []);


  // WebSocket — connect on mount, disconnect on unmount
  useEffect(() => {
    const token = localStorage.getItem("access_token");
    if (!token) return;

    const ws = new WebSocket(`ws://localhost:8000/ws/admin?token=${token}`);
    wsRef.current = ws;

    ws.onopen = () => {
      console.log("[IntelliVerify] Admin WebSocket connected");
    };

    ws.onmessage = (event) => {
    try {
        const data = JSON.parse(event.data);
        if (data.type === "document_processed") {
            fetchAll();
        }
    } catch (err) {
        console.error("[IntelliVerify] WS message parse error:", err);
    }
  };

    ws.onerror = (err) => {
      console.error("[IntelliVerify] WebSocket error:", err);
    };

    ws.onclose = () => {
      console.log("[IntelliVerify] Admin WebSocket closed");
    };

    // Cleanup — close connection when admin navigates away
    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, []); // Run once on mount

  if (loading) return (
    <div className="dashboard-layout">
      <Navbar />
      <main className="dashboard-main">
        <p className="text-muted">Loading applications…</p>
      </main>
    </div>
  );

  return (
    <div className="dashboard-layout">
      <Navbar />
      <main className="dashboard-main">

        <div className="dashboard-header">
          <h2>All Applications <span className="aa-count">{applications.length}</span></h2>
          <p>Review, approve, or flag candidate applications.</p>
        </div>

        {applications.length === 0 && (
          <div className="card">
            <p className="text-muted">No applications submitted yet.</p>
          </div>
        )}

        {applications.length > 0 && (
          <div className="card aa-table-card">
            <table className="aa-table">
              <thead>
                <tr>
                  <th>Name</th>
                  <th>Category</th>
                  <th>Degree</th>
                  <th>College</th>
                  <th>Submitted</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {applications.map((app) => (
                  <tr
                    key={app.id}
                    onClick={() => navigate(`/admin/${app.id}`)}
                    className="cursor-pointer hover:bg-gray-50"
                  >
                    <td><strong>{app.full_name}</strong></td>
                    <td>{app.category}</td>
                    <td>{app.degree} — {app.branch}</td>
                    <td className="aa-college">{app.college}</td>
                    <td>{new Date(app.created_at).toLocaleDateString("en-IN")}</td>
                    <td>
                      <span
                        className="aa-status-pill"
                        style={{ background: STATUS_COLORS[app.status] || "#aaa" }}
                      >
                        {app.status.replace(/_/g, " ")}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

      </main>
    </div>
  );
}