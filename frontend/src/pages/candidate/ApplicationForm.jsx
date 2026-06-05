// frontend/src/pages/candidate/ApplicationForm.jsx
import { useState , useEffect} from "react";
import { useNavigate } from "react-router-dom";
import Navbar from "../../components/shared/Navbar";
import { applicationAPI } from "../../services/api";
import { ROUTES, DOCUMENT_TYPES } from "../../utils/constants";
import {
  validateApplicationPersonal,
  validateApplicationEducation,
  validateDocuments,
  validateName,
  validateDateOfBirth,
  validateRequiredPhone,
  validateCategory,
  validateRequiredText,
  validateGraduationYear,
  validatePercentage,
  validateGateScore,
  validateGateRank,
} from "../../utils/formValidation";
import "../../styles/dashboard.css";
import "../../styles/application-form.css";

const STEPS = ["Personal Details", "Education Details", "Upload Documents"];

// Check on load if candidate already has an application



export default function ApplicationForm() {
  const navigate = useNavigate();
  const [step, setStep]           = useState(0);
  const [errors, setErrors]       = useState({});
  const [submitError, setSubmitError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const [personal, setPersonal] = useState({
    full_name: "", date_of_birth: "", phone: "", category: "General",
  });

  const [education, setEducation] = useState({
    degree: "", branch: "", college: "",
    graduation_year: "", percentage: "",
    gate_score: "", gate_rank: "",
  });

  const [files, setFiles] = useState({});


  useEffect(() => {
  applicationAPI.getMyApplications().then(({ data }) => {
    const activeStatuses = ["submitted", "processing", "under_review", "action_required"];
    const hasActive = data.some(app => activeStatuses.includes(app.status));
    if (hasActive) {
    navigate(ROUTES.CANDIDATE_DASHBOARD, {
      state: { message: "You already have an application in progress. You can submit a new one only after your current application is verified or rejected." }
    });
}


  });
}, []);

  const updatePersonal  = (e) => {
    const { name, value } = e.target;
    setPersonal((p)  => ({ ...p,  [name]: value }));
    setErrors((prev) => ({ ...prev, [name]: undefined }));
    setSubmitError("");
  };

  const updateEducation = (e) => {
    const { name, value } = e.target;
    setEducation((p) => ({ ...p, [name]: value }));
    setErrors((prev) => ({ ...prev, [name]: undefined }));
    setSubmitError("");
  };

  const handleFileChange = (docType, file) => {
    setFiles((f) => ({ ...f, [docType]: file }));
    setErrors((prev) => ({ ...prev, [docType]: undefined }));
    setSubmitError("");
  };

  const validateCurrentStep = () => {
    if (step === 0) return validateApplicationPersonal(personal);
    if (step === 1) return validateApplicationEducation(education);
    if (step === 2) return validateDocuments(files);
    return {};
  };

  const validateField = (name, value) => {
    if (name === "full_name") return validateName(value);
    if (name === "date_of_birth") return validateDateOfBirth(value);
    if (name === "phone") return validateRequiredPhone(value);
    if (name === "category") return validateCategory(value);
    if (name === "degree") return validateRequiredText(value, "Degree / qualification");
    if (name === "branch") return validateRequiredText(value, "Branch / specialization");
    if (name === "college") return validateRequiredText(value, "College / university");
    if (name === "graduation_year") return validateGraduationYear(value);
    if (name === "percentage") return validatePercentage(value);
    if (name === "gate_score") return validateGateScore(value);
    if (name === "gate_rank") return validateGateRank(value);
    return null;
  };

  const handleBlur = (e) => {
    const { name, value } = e.target;
    setErrors((prev) => ({ ...prev, [name]: validateField(name, value) }));
  };

  const handleNext = () => {
    const validationErrors = validateCurrentStep();
    setErrors(validationErrors);
    if (Object.keys(validationErrors).length > 0) { return; }
    setSubmitError("");
    setStep((s) => s + 1);
  };

  const handleSubmit = async () => {
    const validationErrors = validateCurrentStep();
    setErrors(validationErrors);
    if (Object.keys(validationErrors).length > 0) { return; }
    setSubmitError("");
    setSubmitting(true);

    try {
      // 1 — create application row
      const payload = {
        ...personal,
        ...education,
        gate_score: education.gate_score || null,
        gate_rank:  education.gate_rank  || null,
      };
      const { data: app } = await applicationAPI.submit(payload);

      // 2 — upload each selected file
      for (const [docType, file] of Object.entries(files)) {
        if (!file) continue;
        await applicationAPI.uploadDocument(app.id, docType, file);
      }

      navigate(ROUTES.CANDIDATE_DASHBOARD);
    } catch (err) {
      setSubmitError(err.response?.data?.detail || "Submission failed. Please try again.");
    } finally {
      setSubmitting(false);
    }
  };

  const fieldClassName = (name) => `form-input ${errors[name] ? "is-invalid" : ""}`;
  const renderFieldError = (name) => errors[name] ? <span className="field-error">{errors[name]}</span> : null;

  return (
    <div className="dashboard-layout">
      <Navbar />
      <main className="dashboard-main">

        <div className="af-card">
          <h1 className="af-title">DRDO RAC — Application Form</h1>

          {/* Step indicator */}
          <div className="af-steps">
            {STEPS.map((label, i) => (
              <div key={i} className={`af-step ${i === step ? "active" : i < step ? "done" : ""}`}>
                <div className="af-step-dot">{i < step ? "✓" : i + 1}</div>
                <span className="af-step-label">{label}</span>
              </div>
            ))}
          </div>

          {submitError && <div className="alert alert-error">{submitError}</div>}

          {/* ── Step 0: Personal ── */}
          {step === 0 && (
            <div className="af-section">
              <div className="form-group">
                <label className="form-label">Full Name *</label>
                <input className={fieldClassName("full_name")} name="full_name"
                  value={personal.full_name} onChange={updatePersonal} onBlur={handleBlur}
                  minLength={2} maxLength={100} aria-invalid={Boolean(errors.full_name)} />
                {renderFieldError("full_name")}
              </div>
              <div className="form-group">
                <label className="form-label">Date of Birth *</label>
                <input className={fieldClassName("date_of_birth")} type="date" min="1990-01-01" max="2010-12-31" name="date_of_birth"
                  value={personal.date_of_birth} onChange={updatePersonal} onBlur={handleBlur}
                  aria-invalid={Boolean(errors.date_of_birth)} />
                {renderFieldError("date_of_birth")}
              </div>
              <div className="form-group">
                <label className="form-label">Phone Number *</label>
                <input className={fieldClassName("phone")} name="phone"
                  value={personal.phone} onChange={updatePersonal}
                  onBlur={handleBlur} placeholder="10-digit mobile number"
                  inputMode="numeric" maxLength={15} aria-invalid={Boolean(errors.phone)} />
                {renderFieldError("phone")}
              </div>
              <div className="form-group">
                <label className="form-label">Category *</label>
                <select className={`form-input ${errors.category ? "is-invalid" : ""}`} name="category"
                  value={personal.category} onChange={updatePersonal} onBlur={handleBlur}
                  aria-invalid={Boolean(errors.category)}>
                  <option>General</option>
                  <option>OBC</option>
                  <option>SC</option>
                  <option>ST</option>
                  <option>EWS</option>
                </select>
                {renderFieldError("category")}
              </div>
            </div>
          )}

          {/* ── Step 1: Education ── */}
          {step === 1 && (
            <div className="af-section">
              <div className="form-group">
                <label className="form-label">Degree / Qualification *</label>
                <input className={fieldClassName("degree")} name="degree"
                  value={education.degree} onChange={updateEducation}
                  onBlur={handleBlur} placeholder="e.g. B.Tech"
                  maxLength={255} aria-invalid={Boolean(errors.degree)} />
                {renderFieldError("degree")}
              </div>
              <div className="form-group">
                <label className="form-label">Branch / Specialization *</label>
                <input className={fieldClassName("branch")} name="branch"
                  value={education.branch} onChange={updateEducation}
                  onBlur={handleBlur} placeholder="e.g. Electronics and Communication"
                  maxLength={255} aria-invalid={Boolean(errors.branch)} />
                {renderFieldError("branch")}
              </div>
              <div className="form-group">
                <label className="form-label">College / University *</label>
                <input className={fieldClassName("college")} name="college"
                  value={education.college} onChange={updateEducation} onBlur={handleBlur}
                  maxLength={255} aria-invalid={Boolean(errors.college)} />
                {renderFieldError("college")}
              </div>
              <div className="af-row">
                <div className="form-group">
                  <label className="form-label">Graduation Year *</label>
                  <input className={fieldClassName("graduation_year")} name="graduation_year"
                    value={education.graduation_year} onChange={updateEducation}
                    onBlur={handleBlur} placeholder="e.g. 2024"
                    inputMode="numeric" maxLength={4} aria-invalid={Boolean(errors.graduation_year)} />
                  {renderFieldError("graduation_year")}
                </div>
                <div className="form-group">
                  <label className="form-label">Percentage / CGPA *</label>
                  <input className={fieldClassName("percentage")} name="percentage"
                    value={education.percentage} onChange={updateEducation}
                    onBlur={handleBlur} placeholder="e.g. 78.5"
                    inputMode="decimal" maxLength={6} aria-invalid={Boolean(errors.percentage)} />
                  {renderFieldError("percentage")}
                </div>
              </div>
              <div className="af-row">
                <div className="form-group">
                  <label className="form-label">GATE Score</label>
                  <input className={fieldClassName("gate_score")} name="gate_score"
                    value={education.gate_score} onChange={updateEducation}
                    onBlur={handleBlur} placeholder="Optional"
                    inputMode="decimal" maxLength={6} aria-invalid={Boolean(errors.gate_score)} />
                  {renderFieldError("gate_score")}
                </div>
                <div className="form-group">
                  <label className="form-label">GATE Rank</label>
                  <input className={fieldClassName("gate_rank")} name="gate_rank"
                    value={education.gate_rank} onChange={updateEducation}
                    onBlur={handleBlur} placeholder="Optional"
                    inputMode="numeric" maxLength={6} aria-invalid={Boolean(errors.gate_rank)} />
                  {renderFieldError("gate_rank")}
                </div>
              </div>
            </div>
          )}

          {/* ── Step 2: Documents ── */}
          {step === 2 && (
            <div className="af-section">
              <p className="af-doc-note">
                Upload clear scans. Accepted formats: PDF, JPG, PNG. Max 5 MB each.
              </p>
              {DOCUMENT_TYPES.map((doc) => (
                <div key={doc.key} className="af-upload-row">
                  <span className="af-upload-label">
                    {doc.label}
                    {doc.required && <span className="af-required"> *</span>}
                  </span>
                  <input
                    type="file"
                    accept=".pdf,.jpg,.jpeg,.png"
                    onChange={(e) => handleFileChange(doc.key, e.target.files[0])}
                  />
                  {files[doc.key] && (
                    <span className="af-file-chosen">✓ {files[doc.key].name}</span>
                  )}
                  {errors[doc.key] && <span className="field-error">{errors[doc.key]}</span>}
                </div>
              ))}
            </div>
          )}

          {/* Navigation */}
          <div className="af-actions">
            {step > 0 && (
              <button className="btn btn-secondary" onClick={() => setStep((s) => s - 1)}>
                ← Back
              </button>
            )}
            {step < 2 && (
              <button className="btn btn-primary" onClick={handleNext}>
                Next →
              </button>
            )}
            {step === 2 && (
              <button className="btn btn-primary" onClick={handleSubmit} disabled={submitting}>
                {submitting ? "Submitting…" : "Submit Application"}
              </button>
            )}
          </div>
        </div>

      </main>
    </div>
  );
}