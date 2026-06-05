// frontend/src/components/auth/ProtectedRoute.jsx

import { Navigate } from "react-router-dom";
import useAuth from "../../hooks/useAuth";
import LoadingSpinner from "../shared/LoadingSpinner";
import { ROUTES } from "../../utils/constants";

const ProtectedRoute = ({ children, allowedRoles }) => {
  const { isAuthenticated, isLoading, user } = useAuth();

  // Still checking localStorage / calling /auth/me
  // Don't render anything yet
  if (isLoading) {
    return <LoadingSpinner />;
  }

  // Not logged in → redirect to login
  if (!isAuthenticated) {
    return <Navigate to={ROUTES.LOGIN} replace />;
  }

  // Logged in but wrong role → redirect to their correct dashboard
  if (allowedRoles && !allowedRoles.includes(user.role)) {
    if (user.role === "candidate") {
      return <Navigate to={ROUTES.CANDIDATE_DASHBOARD} replace />;
    }
    return <Navigate to={ROUTES.ADMIN_DASHBOARD} replace />;
  }

  // All checks passed → render the actual page
  return children;
};

export default ProtectedRoute;