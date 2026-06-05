// frontend/src/App.jsx

import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { AuthProvider } from "./context/AuthContext";
import ProtectedRoute from "./components/auth/ProtectedRoute";

import Login              from "./pages/auth/Login";
import Register           from "./pages/auth/Register";
import CandidateDashboard from "./pages/candidate/CandidateDashboard";
import AdminDashboard     from "./pages/admin/AdminDashboard";
import ApplicationForm      from "./pages/candidate/ApplicationForm";
import AdminApplications    from "./pages/admin/AdminApplications";
import AdminApplicationDetail from "./pages/admin/AdminApplicationDetail";


import { ROUTES, ROLES } from "./utils/constants";

const App = () => {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>

          {/* ── Public Routes ───────────────────── */}
          {/* Anyone can access these — no auth needed */}
          <Route path={ROUTES.LOGIN}    element={<Login />} />
          <Route path={ROUTES.REGISTER} element={<Register />} />

          {/* ── Candidate Routes ────────────────── */}
          {/* Only candidates can access these */}
          <Route
            path={ROUTES.CANDIDATE_DASHBOARD}
            element={
              <ProtectedRoute allowedRoles={[ROLES.CANDIDATE]}>
                <CandidateDashboard />
              </ProtectedRoute>
            }
          />

          <Route path={ROUTES.CANDIDATE_APPLY}
            element={
              <ProtectedRoute allowedRoles={[ROLES.CANDIDATE]}>
                <ApplicationForm />
              </ProtectedRoute>
            }
          />

          {/* ── Admin Routes ────────────────────── */}
          {/* Only admins and superadmins can access these */}
          <Route
            path={ROUTES.ADMIN_DASHBOARD}
            element={
              <ProtectedRoute allowedRoles={[ROLES.ADMIN, ROLES.SUPERADMIN]}>
                <AdminDashboard />
              </ProtectedRoute>
            }
          />

          <Route path={ROUTES.ADMIN_APPLICATIONS}
            element={
              <ProtectedRoute allowedRoles={[ROLES.ADMIN, ROLES.SUPERADMIN]}>
                <AdminApplications />
              </ProtectedRoute>
            }
          />

          <Route
            path="/admin/:id"
            element={
              <ProtectedRoute allowedRoles={[ROLES.ADMIN, ROLES.SUPERADMIN]}>
                <AdminApplicationDetail />
              </ProtectedRoute>
            }
          />

          {/* ── Default Redirect ────────────────── */}
          {/* Anyone hitting / gets sent to login */}
          <Route
            path={ROUTES.HOME}
            element={<Navigate to={ROUTES.LOGIN} replace />}
          />

          {/* ── 404 ─────────────────────────────── */}
          {/* Any unknown URL also goes to login */}
          <Route
            path="*"
            element={<Navigate to={ROUTES.LOGIN} replace />}
          />
          
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  );
};

export default App;