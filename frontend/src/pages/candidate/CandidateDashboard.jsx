// frontend/src/pages/candidate/CandidateDashboard.jsx

import { useState, useEffect, useRef } from "react";
import { useNavigate } from "react-router-dom";
import { applicationAPI } from "../../services/api";
import Navbar from "../../components/shared/Navbar";
import useAuth from "../../hooks/useAuth";
import "../../styles/dashboard.css";
const DOC_STATUS_STYLE = {
  verified:           { bg: "bg-green-50",  border: "border-green-200",  badge: "bg-green-100 text-green-800",  icon: "✓" },
  mismatch:           { bg: "bg-red-50",    border: "border-red-200",    badge: "bg-red-100 text-red-800",      icon: "✗" },
  reupload_requested: { bg: "bg-yellow-50", border: "border-yellow-300", badge: "bg-yellow-100 text-yellow-800",icon: "↩" },
  processing:         { bg: "bg-blue-50",   border: "border-blue-200",   badge: "bg-blue-100 text-blue-800",    icon: "⟳" },
  uploaded:           { bg: "bg-gray-50",   border: "border-gray-200",   badge: "bg-gray-100 text-gray-700",    icon: "↑" },
  rejected:           { bg: "bg-red-100",   border: "border-red-300",    badge: "bg-red-200 text-red-900",      icon: "✗" },
};

const APP_STATUS_BANNER = {
  submitted:       { bg: "bg-gray-100",    text: "text-gray-700",   label: "Submitted — Awaiting Processing" },
  processing:      { bg: "bg-blue-100",    text: "text-blue-800",   label: "Processing — Your documents are being verified" },
  verified:        { bg: "bg-green-100",   text: "text-green-800",  label: "Verified — All documents passed" },
  action_required: { bg: "bg-yellow-100",  text: "text-yellow-800", label: "Action Required — Please review your documents below" },
  under_review:    { bg: "bg-indigo-100",  text: "text-indigo-800", label: "Under Admin Review" },
  rejected:        { bg: "bg-red-100",     text: "text-red-800",    label: "Rejected — See reasons below" },
};

function DocumentStatusCard({ doc, applicationId, onReuploadSuccess }) {
  const style = DOC_STATUS_STYLE[doc.status] || DOC_STATUS_STYLE.uploaded;
  const fileInputRef = useRef(null);
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState(null);

  const handleFileChange = async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    setUploading(true);
    setUploadError(null);
    try {
      await applicationAPI.reuploadDocument(applicationId, doc.id, file);
      onReuploadSuccess();
    } catch (err) {
      setUploadError(err.response?.data?.detail || "Upload failed. Try again.");
    } finally {
      setUploading(false);
      // reset input so same file can be chosen again if needed
      if (fileInputRef.current) fileInputRef.current.value = "";
    }
  };

  return (
    
    <div className={`rounded-xl border p-5 ${style.bg} ${style.border}`}>
      
      <div className="flex items-center justify-between mb-2">
        <h3 className="font-semibold text-gray-800 capitalize text-sm">
          {doc.document_type.replace(/_/g, " ")}
        </h3>
        <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${style.badge}`}>
          {style.icon} {doc.status.replace(/_/g, " ")}
        </span>
      </div>

      {doc.confidence_score !== null && doc.confidence_score !== undefined && (
        <p className="text-xs text-gray-500 mb-2">
          Confidence: {Math.round(doc.confidence_score * 100)}%
        </p>
      )}

      {/* reupload reason */}
      {doc.reupload_reason && (
        <div className="mt-2 p-3 bg-white/70 rounded-lg border border-yellow-200 text-xs text-yellow-900">
          <strong>Reason:</strong> {doc.reupload_reason}
        </div>
      )}

      {/* reupload button */}
      {doc.status === "reupload_requested" && (
        <div className="mt-3">
          <input
            type="file"
            ref={fileInputRef}
            className="hidden"
            accept=".pdf,.jpg,.jpeg,.png"
            onChange={handleFileChange}
          />
          <button
            onClick={() => fileInputRef.current?.click()}
            disabled={uploading}
            className="w-full py-2 text-sm bg-yellow-500 hover:bg-yellow-600 text-white font-medium rounded-lg disabled:opacity-50"
          >
            {uploading ? "Uploading…" : "↑ Reupload Document"}
          </button>
          {uploadError && (
            <p className="text-xs text-red-600 mt-1">{uploadError}</p>
          )}
        </div>
      )}
    </div>
  );
}

export default function CandidateDashboard() {
  const { user } = useAuth();
  const navigate = useNavigate();

  const [applications, setApplications] = useState([]);
  const [loading, setLoading] = useState(true);

  const load = async () => {
    try {
      const res = await applicationAPI.getMyApplications();
      setApplications(res.data);
    } catch {
      // handle silently — show empty state
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, []);

  if (loading) return (
    <div className="flex items-center justify-center h-64 text-gray-500">Loading…</div>
  );

  return (
    <div className="dashboard-layout">
      <Navbar />
      <main className="dashboard-main">
        <div className="max-w-3xl mx-auto px-5 py-8">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">My Applications</h1>
              <p className="text-sm text-gray-500 mt-0.5">Welcome, {user?.full_name || user?.email}</p>
            </div>
            <button
              onClick={() => navigate("/candidate/apply")}
              className="px-4 py-2 bg-indigo-600 text-white text-sm font-medium rounded-lg hover:bg-indigo-700"
            >
              + New Application
            </button>
          </div>

          {applications.length === 0 ? (
            <div className="text-center py-20 text-gray-400">
              <p className="text-lg mb-2">No applications yet.</p>
              <button
                onClick={() => navigate("/candidate/apply")}
                className="text-indigo-600 hover:underline text-sm"
              >
                Submit your first application →
              </button>
            </div>
          ) : (
            applications.map((app) => {
              const banner = APP_STATUS_BANNER[app.status] || APP_STATUS_BANNER.submitted;
              return (
                <div key={app.id} className="bg-white rounded-2xl shadow border border-gray-100 mb-6 overflow-hidden">
                  {/* status banner */}
                  <div className={`px-6 py-3 ${banner.bg} ${banner.text} text-sm font-medium`}>
                    {banner.label}
                  </div>

                  <div className="p-6">
                    <div className="flex items-start justify-between mb-4">
                      <div>
                        <h2 className="font-semibold text-gray-900">{app.full_name}</h2>
                        <p className="text-xs text-gray-400 mt-0.5">
                          Application #{app.id} · {app.degree} · {app.branch}
                        </p>
                      </div>
                    </div>

                    {/* document cards */}
                    {app.documents && app.documents.length > 0 ? (
                      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                        {app.documents.map((doc) => (
                          <DocumentStatusCard
                            key={doc.id}
                            doc={doc}
                            applicationId={app.id}
                            onReuploadSuccess={load}
                          />
                        ))}
                      </div>
                    ) : (
                      <p className="text-sm text-gray-400 italic">No documents uploaded yet.</p>
                    )}
                  </div>
                </div>
              );
            })
          )}
        </div>
      </main>
    </div>
  );
}