// frontend/src/pages/admin/AdminApplicationDetail.jsx

import { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { adminAPI } from "../../services/api";

const FIELD_MAP = {
  gate_scorecard: [
    { label: "Candidate Name",  formKey: "full_name",       extractKey: "candidate_name" },
    { label: "Registration No", formKey: null,              extractKey: "roll_number" },
    { label: "GATE Score",      formKey: "gate_score",      extractKey: "gate_score" },
    { label: "GATE Rank",       formKey: "gate_rank",       extractKey: "gate_rank" },
    { label: "Discipline",      formKey: "branch",          extractKey: "gate_paper" },
    { label: "Year",            formKey: "graduation_year", extractKey: "year_of_passing" },
  ],
  marksheet: [
    { label: "Candidate Name",  formKey: "full_name",       extractKey: "candidate_name" },
    { label: "Percentage",      formKey: "percentage",      extractKey: "percentage" },
    { label: "Degree",          formKey: "degree",          extractKey: "degree" },
    { label: "College",         formKey: "college",         extractKey: "university" },
    { label: "Year",            formKey: "graduation_year", extractKey: "year_of_passing" },
  ],
  degree_certificate: [
    { label: "Candidate Name",  formKey: "full_name",       extractKey: "name" },
    { label: "Degree",          formKey: "degree",          extractKey: "degree" },
    { label: "Branch",          formKey: "branch",          extractKey: "branch" },
    { label: "College",         formKey: "college",         extractKey: "university" },
    { label: "Year",            formKey: "graduation_year", extractKey: "year_of_passing" },
  ],
  caste_certificate: [
    { label: "Candidate Name",  formKey: "full_name",       extractKey: "name" },
    { label: "Category",        formKey: "category",        extractKey: "category" },
  ],
  ews_certificate: [
    { label: "Candidate Name",  formKey: "full_name",       extractKey: "name" },
    { label: "Category",        formKey: "category",        extractKey: "category" },
  ],
};

const STATUS_BADGE = {
  verified:           "bg-green-100 text-green-800",
  mismatch:           "bg-red-100 text-red-800",
  reupload_requested: "bg-yellow-100 text-yellow-800",
  processing:         "bg-blue-100 text-blue-800",
  uploaded:           "bg-gray-100 text-gray-700",
  rejected:           "bg-red-200 text-red-900",
};

function ReasonModal({ title, onConfirm, onCancel }) {
  const [reason, setReason] = useState("");

  return (
    <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50">
      <div className="bg-white rounded-xl shadow-2xl p-6 w-full max-w-md">
        <h3 className="text-lg font-semibold text-gray-800 mb-3">{title}</h3>
        <textarea
          className="w-full border border-gray-300 rounded-lg p-3 text-sm resize-none focus:outline-none focus:ring-2 focus:ring-indigo-400"
          rows={4}
          placeholder="Enter reason (required)..."
          value={reason}
          onChange={(e) => setReason(e.target.value)}
        />
        <div className="flex justify-end gap-3 mt-4">
          <button
            onClick={onCancel}
            className="px-4 py-2 text-sm rounded-lg border border-gray-300 text-gray-600 hover:bg-gray-50"
          >
            Cancel
          </button>
          <button
            onClick={() => reason.trim() && onConfirm(reason.trim())}
            disabled={!reason.trim()}
            className="px-4 py-2 text-sm rounded-lg bg-indigo-600 text-white hover:bg-indigo-700 disabled:opacity-40"
          >
            Confirm
          </button>
        </div>
      </div>
    </div>
  );
}

function ConfidenceBar({ score }) {
  const pct = Math.round((score || 0) * 100);
  const color = pct >= 80 ? "bg-green-500" : pct >= 50 ? "bg-yellow-400" : "bg-red-500";
  return (
    <div className="flex items-center gap-3">
      <div className="flex-1 bg-gray-200 rounded-full h-2">
        <div className={`h-2 rounded-full transition-all ${color}`} style={{ width: `${pct}%` }} />
      </div>
      <span className="text-sm font-medium text-gray-700 w-12 text-right">{pct}%</span>
    </div>
  );
}

function DocumentCard({ doc, formData, onApprove, onReject, onClarify }) {
  const fields     = FIELD_MAP[doc.document_type] || [];
  const mismatches = doc.mismatch_details || {};
  const extracted  = doc.extracted_data || {};
  const canAct     = ["mismatch", "uploaded", "reupload_requested"].includes(doc.status);

  return (
    <div className="bg-white rounded-2xl shadow border border-gray-100 overflow-hidden mb-6">
      {/* header */}
      <div className="flex items-center justify-between px-6 py-4 bg-gray-50 border-b border-gray-100">
        <div>
          <h3 className="font-semibold text-gray-800 capitalize">
            {doc.document_type.replace(/_/g, " ")}
          </h3>
          <span className={`mt-1 inline-block text-xs font-medium px-2 py-0.5 rounded-full ${STATUS_BADGE[doc.status] || "bg-gray-100 text-gray-600"}`}>
            {doc.status.replace(/_/g, " ")}
          </span>
        </div>
        <div className="w-48">
          <p className="text-xs text-gray-500 mb-1">Confidence</p>
          <ConfidenceBar score={doc.confidence_score} />
        </div>
      </div>

      {/* comparison table */}
      <div className="p-6">
        {fields.length > 0 ? (
          <table className="w-full text-sm border-collapse">
            <thead>
              <tr className="text-xs text-gray-500 uppercase">
                <th className="text-left pb-2 w-1/4">Field</th>
                <th className="text-left pb-2 w-1/3 text-blue-600">Form Value</th>
                <th className="text-left pb-2 w-1/3 text-purple-600">OCR Extracted</th>
                <th className="text-left pb-2 w-16">Match</th>
              </tr>
            </thead>
            <tbody>
              {fields.map(({ label, formKey, extractKey }) => {
                const formVal    = formKey ? (formData[formKey] ?? "—") : "—";
                const ocrVal     = extracted[extractKey] ?? "—";
                const isMismatch = mismatches[extractKey] !== undefined;
                const isNa       = formKey === null;

                let rowBg     = "bg-white";
                let matchIcon = "—";
                if (!isNa) {
                  if (isMismatch) {
                    rowBg     = "bg-red-50";
                    matchIcon = "✗";
                  } else if (ocrVal !== "—") {
                    rowBg     = "bg-green-50";
                    matchIcon = "✓";
                  }
                }

                return (
                  <tr key={extractKey} className={`border-t border-gray-100 ${rowBg}`}>
                    <td className="py-2 pr-4 font-medium text-gray-700">{label}</td>
                    <td className="py-2 pr-4 text-blue-800">{String(formVal)}</td>
                    <td className={`py-2 pr-4 font-mono ${isMismatch ? "text-red-700 font-semibold" : "text-gray-800"}`}>
                      {String(ocrVal)}
                      {isMismatch && mismatches[extractKey]?.extracted && (
                        <span className="ml-2 text-xs text-red-500">
                          (extracted: {mismatches[extractKey].extracted})
                        </span>
                      )}
                    </td>
                    <td className={`py-2 text-center font-bold ${isMismatch ? "text-red-500" : "text-green-600"}`}>
                      {matchIcon}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        ) : (
          <p className="text-sm text-gray-400 italic">No field map defined for this document type.</p>
        )}

        {doc.reupload_reason && (
          <div className="mt-4 p-3 bg-yellow-50 border border-yellow-200 rounded-lg text-sm text-yellow-800">
            <strong>Reason on file:</strong> {doc.reupload_reason}
          </div>
        )}
      </div>

      {/* action buttons */}
      {canAct && (
        <div className="flex gap-3 px-6 pb-5">
          <button
            onClick={onApprove}
            className="px-4 py-2 text-sm bg-green-600 text-white rounded-lg hover:bg-green-700 font-medium"
          >
            ✓ Approve
          </button>
          <button
            onClick={onClarify}
            className="px-4 py-2 text-sm bg-yellow-500 text-white rounded-lg hover:bg-yellow-600 font-medium"
          >
            ↩ Request Clarification
          </button>
          <button
            onClick={onReject}
            className="px-4 py-2 text-sm bg-red-600 text-white rounded-lg hover:bg-red-700 font-medium"
          >
            ✗ Reject
          </button>
        </div>
      )}
    </div>
  );
}

export default function AdminApplicationDetail() {
  const { id }       = useParams();
  const navigate     = useNavigate();

  const [application, setApplication]   = useState(null);
  const [loading, setLoading]           = useState(true);
  const [error, setError]               = useState(null);
  const [modal, setModal]               = useState(null);
  const [reportLoading, setReportLoading] = useState(false); // ← new

  const load = async () => {
    try {
      setLoading(true);
      const res = await adminAPI.getApplication(id);
      setApplication(res.data);
    } catch (err) {
      setError(`Failed to load application. ${err.response?.data?.detail || ""}`);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, [id]);

  const handleStatus = async (docId, action, reason = "") => {
    await adminAPI.documentAction(docId, action, reason);
    load();
  };

  // ── Download Report ──────────────────────────────────────────────────────
  const handleDownloadReport = async () => {
    setReportLoading(true);
    try {
      const response = await adminAPI.downloadReport(application.id);
      const url  = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement("a");
      link.href     = url;
      link.download = `intelliverify_application_${application.id}.pdf`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
    } catch (err) {
      alert("Failed to generate report. Please try again.");
      console.error(err);
    } finally {
      setReportLoading(false);
    }
  };
  // ────────────────────────────────────────────────────────────────────────

  if (loading) return (
    <div className="flex items-center justify-center h-64 text-gray-500">Loading application…</div>
  );
  if (error) return (
    <div className="p-8 text-red-600">{error}</div>
  );
  if (!application) return null;

  const appStatusColor = {
    verified:        "bg-green-100 text-green-800",
    action_required: "bg-yellow-100 text-yellow-800",
    under_review:    "bg-blue-100 text-blue-800",
    rejected:        "bg-red-100 text-red-800",
    processing:      "bg-gray-100 text-gray-700",
    submitted:       "bg-gray-100 text-gray-700",
  }[application.status] || "bg-gray-100 text-gray-600";

  return (
    <div className="max-w-5xl mx-auto px-6 py-8">
      <button
        onClick={() => navigate(-1)}
        className="text-sm text-indigo-600 hover:underline mb-6 inline-flex items-center gap-1"
      >
        ← Back to Applications
      </button>

      {/* application header */}
      <div className="bg-white rounded-2xl shadow border border-gray-100 p-6 mb-6">
        <div className="flex items-start justify-between">
          <div>
            <h1 className="text-xl font-bold text-gray-900">
              {application.candidate.name}
            </h1>
            <p className="text-sm text-gray-500 mt-1">{application.candidate.email}</p>
            <p className="text-xs text-gray-400 mt-0.5">Application #{application.id}</p>
          </div>

          {/* ── status badge + download button ── */}
          <div className="flex items-center gap-3">
            <span className={`text-sm font-semibold px-3 py-1 rounded-full ${appStatusColor}`}>
              {application.status.replace(/_/g, " ")}
            </span>
            <button
              onClick={handleDownloadReport}
              disabled={reportLoading}
              className="flex items-center gap-2 px-4 py-1.5 text-sm font-medium bg-slate-800 text-white rounded-lg hover:bg-slate-900 disabled:opacity-50 transition-colors"
            >
              {reportLoading ? (
                <>
                  <span className="inline-block w-3.5 h-3.5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                  Generating…
                </>
              ) : (
                <>⬇ Download Report</>
              )}
            </button>
          </div>
          {/* ───────────────────────────────────── */}

        </div>

        <div className="mt-5 grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
          {Object.entries(application.form_data).map(([key, val]) =>
            val ? (
              <div key={key}>
                <p className="text-xs text-gray-400 capitalize">{key.replace(/_/g, " ")}</p>
                <p className="font-medium text-gray-800">{String(val)}</p>
              </div>
            ) : null
          )}
        </div>
      </div>

      {/* document cards */}
      <h2 className="text-lg font-semibold text-gray-800 mb-4">Documents</h2>
      {application.documents.map((doc) => (
        <DocumentCard
          key={doc.id}
          doc={doc}
          formData={application.form_data}
          onApprove={() => handleStatus(doc.id, "approve")}
          onReject={() => setModal({ type: "reject", documentId: doc.id })}
          onClarify={() => setModal({ type: "clarify", documentId: doc.id })}
        />
      ))}

      {/* modals */}
      {modal?.type === "reject" && (
        <ReasonModal
          title="Reject Document — Enter Reason"
          onConfirm={(reason) => { handleStatus(modal.documentId, "reject", reason); setModal(null); }}
          onCancel={() => setModal(null)}
        />
      )}
      {modal?.type === "clarify" && (
        <ReasonModal
          title="Request Clarification — Enter Reason for Candidate"
          onConfirm={(reason) => { handleStatus(modal.documentId, "clarify", reason); setModal(null); }}
          onCancel={() => setModal(null)}
        />
      )}
    </div>
  );
}