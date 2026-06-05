// frontend/src/components/shared/Navbar.jsx

import { Link } from "react-router-dom";
import useAuth from "../../hooks/useAuth";
import { ROUTES } from "../../utils/constants";
import "../../styles/components.css";

const Navbar = () => {
  const { user, logout } = useAuth();

  const handleLogout = () => {
    logout();
    window.location.href = ROUTES.LOGIN;
  };

  return (
    <nav className="navbar">
      <div className="navbar-brand">
        <Link to="/" className="navbar-logo">
          IntelliVerify
        </Link>
      </div>

      <div className="navbar-center">
        {user?.role === "candidate" && (
          <Link to={ROUTES.CANDIDATE_DASHBOARD} className="navbar-link">
            Dashboard
          </Link>
        )}
        {(user?.role === "admin" || user?.role === "superadmin") && (
          <Link to={ROUTES.ADMIN_DASHBOARD} className="navbar-link">
            Dashboard
          </Link>
        )}
      </div>

      <div className="navbar-right">
        {user && (
          <>
            <span className="navbar-username">{user.full_name}</span>
            <span className={`role-badge role-badge--${user.role}`}>
              {user.role}
            </span>
            <button onClick={handleLogout} className="btn btn-secondary btn-sm">
              Logout
            </button>
          </>
        )}
      </div>
    </nav>
  );
};

export default Navbar;