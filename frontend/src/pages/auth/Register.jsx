// frontend/src/pages/auth/Register.jsx

import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { authAPI } from "../../services/api";
import useAuth from "../../hooks/useAuth";
import { ROUTES, ROLES } from "../../utils/constants";
import {
  validateRegisterForm,
  validateName,
  validateEmail,
  validateOptionalPhone,
  validatePassword,
} from "../../utils/formValidation";
import "../../styles/auth.css";

const Register = () => {
  const navigate  = useNavigate();
  const { login } = useAuth();

  const [formData, setFormData] = useState({
    full_name:    "",
    email:        "",
    phone_number: "",
    password:     "",
    role:         ROLES.CANDIDATE,
  });
  const [error,     setError]     = useState("");
  const [fieldErrors, setFieldErrors] = useState({});
  const [isLoading, setIsLoading] = useState(false);

  const validateField = (name, value) => {
    if (name === "full_name") return validateName(value);
    if (name === "email") return validateEmail(value);
    if (name === "phone_number") return validateOptionalPhone(value);
    if (name === "password") return validatePassword(value);
    if (name === "role") return value ? null : "Select a valid role.";
    return null;
  };

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData({ ...formData, [name]: value });
    setFieldErrors((prev) => ({ ...prev, [name]: undefined }));
    setError("");
  };

  const handleBlur = (e) => {
    const { name, value } = e.target;
    setFieldErrors((prev) => ({ ...prev, [name]: validateField(name, value) }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");

    const validationErrors = validateRegisterForm(formData);
    setFieldErrors(validationErrors);
    if (Object.keys(validationErrors).length > 0) {
      return;
    }

    setIsLoading(true);

    try {
      // Step 1 — Register
      await authAPI.register({
        full_name: formData.full_name.trim(),
        email: formData.email.trim(),
        phone_number: formData.phone_number.trim() || null,
        password: formData.password,
        role: formData.role,
      });

      // Step 2 — Auto login after register
      const loginResponse = await authAPI.login({
        email:    formData.email,
        password: formData.password,
      });

      const { access_token, user } = loginResponse.data;
      login(access_token, user);

      // Step 3 — Redirect based on role
      if (user.role === ROLES.CANDIDATE) {
        navigate(ROUTES.CANDIDATE_DASHBOARD);
      } else {
        navigate(ROUTES.ADMIN_DASHBOARD);
      }
    } catch (err) {
      const message = err.response?.data?.detail || "Registration failed. Please try again.";
      setError(message);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="auth-page">
      <div className="auth-card">

        {/* Logo */}
        <div className="auth-logo">
          <h1>IntelliVerify</h1>
          <p>Document Processing & Verification Platform</p>
        </div>

        <h2 className="auth-title">Create an account</h2>
        <p className="auth-subtitle">Fill in your details to get started</p>

        {error && <div className="alert alert-error">{error}</div>}

        <form onSubmit={handleSubmit} noValidate>
          <div className="form-group">
            <label className="form-label" htmlFor="full_name">
              Full name
            </label>
            <input
              id="full_name"
              name="full_name"
              type="text"
              className={`form-input ${fieldErrors.full_name ? "is-invalid" : ""}`}
              placeholder="John Doe"
              value={formData.full_name}
              onChange={handleChange}
              onBlur={handleBlur}
              required
              minLength={2}
              maxLength={100}
              aria-invalid={Boolean(fieldErrors.full_name)}
            />
            {fieldErrors.full_name && <span className="field-error">{fieldErrors.full_name}</span>}
          </div>

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
              aria-invalid={Boolean(fieldErrors.email)}
            />
            {fieldErrors.email && <span className="field-error">{fieldErrors.email}</span>}
          </div>

          <div className="form-group">
            <label className="form-label" htmlFor="phone_number">
              Phone number <span className="text-muted">(optional)</span>
            </label>
            <input
              id="phone_number"
              name="phone_number"
              type="tel"
              className={`form-input ${fieldErrors.phone_number ? "is-invalid" : ""}`}
              placeholder="10 to 15 digits"
              value={formData.phone_number}
              onChange={handleChange}
              onBlur={handleBlur}
              inputMode="numeric"
              maxLength={15}
              aria-invalid={Boolean(fieldErrors.phone_number)}
            />
            {fieldErrors.phone_number && <span className="field-error">{fieldErrors.phone_number}</span>}
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
              placeholder="Minimum 8 characters"
              value={formData.password}
              onChange={handleChange}
              onBlur={handleBlur}
              required
              minLength={8}
              maxLength={72}
              aria-invalid={Boolean(fieldErrors.password)}
            />
            {fieldErrors.password && <span className="field-error">{fieldErrors.password}</span>}
          </div>

          <div className="form-group">
            <label className="form-label" htmlFor="role">
              I am registering as
            </label>
            <select
              id="role"
              name="role"
              className={`form-select ${fieldErrors.role ? "is-invalid" : ""}`}
              value={formData.role}
              onChange={handleChange}
              onBlur={handleBlur}
              aria-invalid={Boolean(fieldErrors.role)}
            >
              <option value={ROLES.CANDIDATE}>Candidate</option>
              <option value={ROLES.ADMIN}>Admin</option>
            </select>
            {fieldErrors.role && <span className="field-error">{fieldErrors.role}</span>}
          </div>

          <button
            type="submit"
            className="btn btn-primary btn-full"
            disabled={isLoading}
          >
            {isLoading ? "Creating account..." : "Create account"}
          </button>
        </form>

        <div className="auth-footer">
          Already have an account?{" "}
          <Link to={ROUTES.LOGIN}>Sign in</Link>
        </div>

      </div>
    </div>
  );
};

export default Register;