
import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { authAPI } from "../../services/api";
import useAuth from "../../hooks/useAuth";
import { ROUTES, ROLES } from "../../utils/constants";
import { validateLoginForm, validateEmail, validatePassword } from "../../utils/formValidation";
import "../../styles/auth.css";


const Login=()=>{
  const navigate = useNavigate();
  const {login}=useAuth();

  const [formData, setFormData] = useState({
    email: "",
    password: "",
  });

  const [error,setError]=useState("");
  const [fieldErrors, setFieldErrors] = useState({});
  const [isLoading, setIsLoading] = useState(false);

  const validateField = (name, value) => {
    if (name === "email") return validateEmail(value);
    if (name === "password") return validatePassword(value);
    return null;
  };

  // ── Input change handler ──────────────────
  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData({ ...formData, [name]: value });
    setFieldErrors((prev) => ({ ...prev, [name]: undefined }));
    setError(""); // clear error on every keystroke
  };

  const handleBlur = (e) => {
    const { name, value } = e.target;
    setFieldErrors((prev) => ({ ...prev, [name]: validateField(name, value) }));
  };

  const handleSubmit=async(e)=>{
    e.preventDefault();
    setError("");

    const validationErrors = validateLoginForm(formData);
    setFieldErrors(validationErrors);
    if (Object.keys(validationErrors).length > 0) {
      return;
    }

    setIsLoading(true);

    try{
      const response=await authAPI.login({
        email: formData.email.trim(),
        password: formData.password,
      });
      const {access_token,user}=response.data;
      login(access_token,user); // update context and localStorage

      if(user.role==ROLES.CANDIDATE){
        navigate(ROUTES.CANDIDATE_DASHBOARD);
      }
      else{
        navigate(ROUTES.ADMIN_DASHBOARD);
      }
    }
    catch(err){
      const message = err.response?.data?.detail || "Login failed. Please try again.";
      setError(message);
    }
    finally{
      setIsLoading(false);
    }
  }

  return (
    <div className="auth-page">
      <div className="auth-card">

        {/* Logo */}
        <div className="auth-logo">
          <h1>IntelliVerify</h1>
          <p>Document Processing & Verification Platform</p>
        </div>

        {/* Title */}
        <h2 className="auth-title">Welcome back</h2>
        <p className="auth-subtitle">Sign in to your account to continue</p>

        {/* Error */}
        {error && <div className="alert alert-error">{error}</div>}

        {/* Form */}
        <form onSubmit={handleSubmit} noValidate>
          <div className="form-group">
            <label className="form-label" htmlFor="email">
              Email address
            </label>
            <input
              id="email"
              name="email"
              type="email"
              className={`form-input ${fieldErrors.email ? "is-invalid" : ""}`}
              placeholder="you@example.com"
              value={formData.email}
              onChange={handleChange}
              onBlur={handleBlur}
              required
              autoComplete="email"
              aria-invalid={Boolean(fieldErrors.email)}
            />
            {fieldErrors.email && <span className="field-error">{fieldErrors.email}</span>}
          </div>

          <div className="form-group">
            <label className="form-label" htmlFor="password">
              Password
            </label>
            <input
              id="password"
              name="password"
              type="password"
              className={`form-input ${fieldErrors.password ? "is-invalid" : ""}`}
              placeholder="Enter your password"
              value={formData.password}
              onChange={handleChange}
              onBlur={handleBlur}
              required
              autoComplete="current-password"
              minLength={8}
              maxLength={72}
              aria-invalid={Boolean(fieldErrors.password)}
            />
            {fieldErrors.password && <span className="field-error">{fieldErrors.password}</span>}
          </div>

          <button
            type="submit"
            className="btn btn-primary btn-full"
            disabled={isLoading}
          >
            {isLoading ? "Signing in..." : "Sign in"}
          </button>
        </form>

        {/* Footer */}
        <div className="auth-footer">
          Don't have an account?{" "}
          <Link to={ROUTES.REGISTER}>Create one</Link>
        </div>

      </div>
    </div>
  );
}

export default Login;