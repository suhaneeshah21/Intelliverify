// frontend/src/services/api.js

import axios from "axios";

// ── Axios Instance ────────────────────────
// Creates a configured axios instance with base URL from .env
const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
});

// ── Request Interceptor ───────────────────
// Runs before every request
// Automatically attaches JWT token from localStorage to Authorization header
// So you never have to manually add the token in every API call
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem("access_token");
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// ── Response Interceptor ──────────────────
// Runs after every response
// If backend returns 401 (token expired/invalid) → clear storage and redirect to login
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem("access_token");
      localStorage.removeItem("user");
      window.location.href = "/login";
    }
    return Promise.reject(error);
  }
);


// ── Auth API Calls ────────────────────────

export const authAPI = {
  // Register a new user
  // data = { full_name, email, phone_number, password, role }
  register: (data) => api.post("/auth/register", data),

  // Login
  // data = { email, password }
  // returns { access_token, token_type, role, user }
  login: (data) => api.post("/auth/login", data),

  // Get currently logged in user
  // token is attached automatically by the interceptor
  getMe: () => api.get("/auth/me"),
};


export const applicationAPI = {
  // Submit the application form (JSON — no files)
  submit: (data) => api.post("/applications/", data),

  // Upload one document file for an application
  // Uses multipart/form-data — Content-Type override needed
  uploadDocument: (applicationId, documentType, file) => {
    const form = new FormData();
    form.append("document_type", documentType);
    form.append("file", file);
    return api.post(`/applications/${applicationId}/documents`, form, {
      headers: { "Content-Type": "multipart/form-data" },
    });
  },


  reuploadDocument: (applicationId, documentId, file) => {
  const formData = new FormData();
  formData.append("file", file);
  return api.post(
    `/applications/${applicationId}/documents/${documentId}/reupload`,
    formData,
    { headers: { "Content-Type": "multipart/form-data" } }
  );
  },

  // Candidate views all their own applications
  getMyApplications: () => api.get("/applications/my"),

  // Candidate views one specific application
  getMyApplication: (id) => api.get(`/applications/my/${id}`),
};




// ── Admin API ─────────────────────────────
export const adminAPI = {
  // View all applications across all candidates
  getAllApplications: () => api.get("/admin/all"),

  // View one full application
  getApplication: (id) => api.get(`/admin/${id}`),

  documentAction:(id,action,reason="")=>  api.post(`/admin/documents/${id}/action`, { action ,reason}),

  rejectApplication:(id,reason) => api.post(`/admin/${id}/reject`, { reason }),

  getStats:()=>api.get("/admin/stats/summary"),

  downloadReport: (applicationId) => api.get(`/admin/${applicationId}/report`, { responseType: "blob" }),
};



// ── Export instance for future use ────────
// Other API files (applicationAPI, adminAPI) will import this same instance
export default api;