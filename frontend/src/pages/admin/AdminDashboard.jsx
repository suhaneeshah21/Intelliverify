// frontend/src/pages/admin/AdminDashboard.jsx
import { useEffect, useState, useRef } from "react";
import { useNavigate } from "react-router-dom";
import { Chart, ArcElement, Tooltip, Legend, CategoryScale, LinearScale, BarElement, PointElement, LineElement, Filler, DoughnutController, BarController, LineController } from "chart.js";
import useAuth from "../../hooks/useAuth";
import { adminAPI } from "../../services/api";
import { ROUTES } from "../../utils/constants";
import "../../styles/dashboard.css";
import "../../styles/admin-dashboard.css";
import Navbar from "../../components/shared/Navbar";


Chart.register(ArcElement, Tooltip, Legend, CategoryScale, LinearScale, BarElement, PointElement, LineElement, Filler, DoughnutController, BarController, LineController);
const PIE_COLORS = {
  verified:        "#22c55e",
  action_required: "#f59e0b",
  under_review:    "#3b82f6",
  rejected:        "#ef4444",
  processing:      "#8b5cf6",
  submitted:       "#94a3b8",
};

// ── Reusable canvas chart component ─────────────────────────────────────────
function ChartCanvas({ type, data, options, height = 260 }) {
  const canvasRef = useRef(null);
  const chartRef  = useRef(null);

  useEffect(() => {
    if (!canvasRef.current) return;
    // Destroy previous instance before creating a new one
    if (chartRef.current) {
      chartRef.current.destroy();
      chartRef.current = null;
    }
    chartRef.current = new Chart(canvasRef.current, { type, data, options });
    return () => {
      if (chartRef.current) {
        chartRef.current.destroy();
        chartRef.current = null;
      }
    };
  }, [data]);   // re-run whenever data changes

  return <canvas ref={canvasRef} height={height} />;
}

// ────────────────────────────────────────────────────────────────────────────

export default function AdminDashboard() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [stats, setStats] = useState(null);

  useEffect(() => {
    adminAPI.getStats()
      .then(({ data }) => setStats(data))
      .catch(() => {});
  }, []);

  const get = (key) => stats?.by_status?.[key] ?? 0;

  // ── Chart.js data objects (only built when stats is available) ───────────

  const pieChartData = stats ? (() => {
    const entries = Object.entries(stats.by_status).filter(([, v]) => v > 0);
    return {
      labels: entries.map(([k]) => k.replace(/_/g, " ").replace(/\b\w/g, c => c.toUpperCase())),
      datasets: [{
        data:            entries.map(([, v]) => v),
        backgroundColor: entries.map(([k]) => PIE_COLORS[k] || "#94a3b8"),
        borderWidth: 2,
        borderColor: "#fff",
        hoverOffset: 6,
      }],
    };
  })() : null;

  const pieOptions = {
    cutout: "65%",
    plugins: { legend: { position: "bottom", labels: { boxWidth: 12, padding: 14, font: { size: 12 } } } },
    maintainAspectRatio: false,
  };

  const barChartData = stats ? (() => {
    const entries = Object.entries(stats.by_document_type);
    return {
      labels: entries.map(([k]) => k.replace(/_/g, " ").replace(/\b\w/g, c => c.toUpperCase())),
      datasets: [
        { label: "Verified", data: entries.map(([, v]) => v.verified || 0), backgroundColor: "#22c55e" },
        { label: "Mismatch", data: entries.map(([, v]) => v.mismatch || 0), backgroundColor: "#ef4444" },
        { label: "Other",    data: entries.map(([, v]) => v.other    || 0), backgroundColor: "#94a3b8" },
      ],
    };
  })() : null;

  const barOptions = {
    plugins: { legend: { position: "bottom", labels: { boxWidth: 12, padding: 14, font: { size: 12 } } } },
    scales: {
      x: { grid: { display: false }, ticks: { font: { size: 11 } } },
      y: { beginAtZero: true, ticks: { precision: 0, font: { size: 11 } }, grid: { color: "#e2e8f0" } },
    },
    maintainAspectRatio: false,
  };

  const lineChartData = stats ? {
    labels: stats.submissions_over_time.map(r => r.date.slice(5)),
    datasets: [{
      label: "Submissions",
      data:  stats.submissions_over_time.map(r => r.count),
      borderColor:     "#6366f1",
      backgroundColor: "rgba(99,102,241,0.08)",
      borderWidth: 2,
      pointRadius: 3,
      pointHoverRadius: 5,
      fill: true,
      tension: 0.3,
    }],
  } : null;

  const lineOptions = {
    plugins: { legend: { display: false } },
    scales: {
      x: { grid: { display: false }, ticks: { font: { size: 11 } } },
      y: { beginAtZero: true, ticks: { precision: 0, font: { size: 11 } }, grid: { color: "#e2e8f0" } },
    },
    maintainAspectRatio: false,
  };

  // ────────────────────────────────────────────────────────────────────────

  return (
    <div className="dashboard-layout">
      <Navbar />
      <main className="dashboard-main">

        <div className="dashboard-header">
          <h2>Admin Dashboard</h2>
          <p>Welcome back, {user?.full_name || user?.email}. Here's what's happening today.</p>
        </div>

        {/* Stats grid */}
        <div className="stats-grid">
          <div className="stat-card ad-total">
            <span className="stat-number">{stats?.total ?? "…"}</span>
            <span className="stat-label">Total Applications</span>
          </div>
          <div className="stat-card ad-verified">
            <span className="stat-number">{get("verified")}</span>
            <span className="stat-label">Verified</span>
          </div>
          <div className="stat-card ad-action">
            <span className="stat-number">{get("action_required")}</span>
            <span className="stat-label">Action Required</span>
          </div>
          <div className="stat-card ad-progress">
            <span className="stat-number">{get("submitted") + get("processing")}</span>
            <span className="stat-label">In Progress</span>
          </div>
          <div className="stat-card ad-review">
            <span className="stat-number">{get("under_review")}</span>
            <span className="stat-label">Under Review</span>
          </div>
          <div className="stat-card ad-rejected">
            <span className="stat-number">{get("rejected")}</span>
            <span className="stat-label">Rejected</span>
          </div>
        </div>

        {/* ── Charts ──────────────────────────────────────────────────────── */}
        {stats && (
          <>
            <div className="charts-row">

              <div className="card chart-card">
                <h4 className="card-section-title">Applications by Status</h4>
                {pieChartData ? (
                  <div style={{ height: 260 }}>
                    <ChartCanvas type="doughnut" data={pieChartData} options={pieOptions} height={260} />
                  </div>
                ) : (
                  <p className="chart-empty">No data yet.</p>
                )}
              </div>

              <div className="card chart-card">
                <h4 className="card-section-title">Documents by Type &amp; Verdict</h4>
                {barChartData ? (
                  <div style={{ height: 260 }}>
                    <ChartCanvas type="bar" data={barChartData} options={barOptions} height={260} />
                  </div>
                ) : (
                  <p className="chart-empty">No data yet.</p>
                )}
              </div>

            </div>

            <div className="card chart-card chart-card--full">
              <h4 className="card-section-title">Submissions — Last 30 Days</h4>
              {lineChartData && lineChartData.labels.length > 0 ? (
                <div style={{ height: 200 }}>
                  <ChartCanvas type="line" data={lineChartData} options={lineOptions} height={200} />
                </div>
              ) : (
                <p className="chart-empty">No submissions in the last 30 days.</p>
              )}
            </div>
          </>
        )}
        {/* ──────────────────────────────────────────────────────────────── */}

        {/* Quick actions */}
        <div className="card ad-quick">
          <h4 className="card-section-title">Quick Actions</h4>
          <button className="btn btn-primary"
            onClick={() => navigate(ROUTES.ADMIN_APPLICATIONS)}>
            📋 Review All Applications
          </button>
        </div>

      </main>
    </div>
  );
}