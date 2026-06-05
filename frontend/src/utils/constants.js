// frontend/src/utils/constants.js
export const ROLES = {
  CANDIDATE: "candidate",
  ADMIN: "admin",
  SUPERADMIN: "superadmin",
};

export const ROUTES = {
  HOME: "/",
  LOGIN: "/login",
  REGISTER: "/register",
  CANDIDATE_DASHBOARD: "/candidate/dashboard",
  CANDIDATE_APPLY: "/candidate/apply",        // NEW
  ADMIN_DASHBOARD: "/admin/dashboard",
  ADMIN_APPLICATIONS: "/admin/applications",
  ADMIN_APPLICATION_DETAIL: "/admin/:id",  // NEW
};

export const APPLICATION_STATUS = {
  SUBMITTED: "submitted",
  PROCESSING: "processing",
  VERIFIED: "verified",
  ACTION_REQUIRED: "action_required",
  UNDER_REVIEW: "under_review",
  REJECTED: "rejected",
};

export const STATUS_COLORS = {
  submitted: "#f39c12",
  processing: "#3498db",
  verified: "#2ecc71",
  action_required: "#e74c3c",
  under_review: "#9b59b6",
  rejected: "#7f8c8d",
};

export const DOC_STATUS_COLORS = {
  uploaded: "#3498db",
  processing: "#f39c12",
  verified: "#2ecc71",
  mismatch: "#e74c3c",
  reupload_requested: "#e67e22",
};

export const DOCUMENT_TYPES = [
  { key: "gate_scorecard",     label: "GATE Scorecard",                required: true },
  { key: "marksheet",          label: "10th / 12th Marksheet",         required: false },
  { key: "degree_certificate", label: "Degree Certificate",            required: false  },
  { key: "caste_certificate",  label: "Caste Certificate (OBC/SC/ST)", required: false },
  { key: "ews_certificate",    label: "EWS Certificate",               required: false },
];