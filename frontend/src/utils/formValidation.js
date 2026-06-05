import { DOCUMENT_TYPES, ROLES } from "./constants";

const EMAIL_REGEX = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
const PHONE_REGEX = /^\d{10,15}$/;
const YEAR_REGEX = /^\d{4}$/;
const INTEGER_REGEX = /^\d+$/;
const DECIMAL_REGEX = /^(?:\d+)(?:\.\d{1,2})?$/;

const MAX_GATE_SCORE = 1000;
const MIN_GRADUATION_YEAR = 1950;
// Allow graduation years up to N years in the future (e.g., candidates graduating soon)
const GRADUATION_FUTURE_YEARS = 5;

const trimValue = (value) => (typeof value === "string" ? value.trim() : "");

const addError = (errors, key, message) => {
  if (message) {
    errors[key] = message;
  }
};

export const validateEmail = (email) => {
  const value = trimValue(email);
  if (!value) return "Email address is required.";
  if (!EMAIL_REGEX.test(value)) return "Enter a valid email address.";
  return null;
};

export const validatePassword = (password) => {
  const value = trimValue(password);
  if (!value) return "Password is required.";
  if (value.length < 8) return "Password must be at least 8 characters long.";
  if (value.length > 72) return "Password must not exceed 72 characters.";
  return null;
};

export const validateName = (name, label = "Full name") => {
  const value = trimValue(name);
  if (!value) return `${label} is required.`;
  if (value.length < 2) return `${label} must be at least 2 characters long.`;
  if (value.length > 100) return `${label} must not exceed 100 characters.`;
  return null;
};

export const validateOptionalPhone = (phone, label = "Phone number") => {
  const value = trimValue(phone);
  if (!value) return null;
  if (!PHONE_REGEX.test(value)) {
    return `${label} must contain 10 to 15 digits.`;
  }
  return null;
};

export const validateRequiredPhone = (phone, label = "Phone number") => {
  const value = trimValue(phone);
  if (!value) return `${label} is required.`;
  return validateOptionalPhone(value, label);
};

export const validateDateOfBirth = (dateOfBirth) => {
  const value = trimValue(dateOfBirth);
  if (!value) return "Date of birth is required.";

  const birthDate = new Date(`${value}T00:00:00`);
  if (Number.isNaN(birthDate.getTime())) return "Enter a valid date of birth.";

  const today = new Date();
  today.setHours(0, 0, 0, 0);
  if (birthDate >= today) return "Date of birth must be in the past.";

  return null;
};

export const validateCategory = (category) => {
  const value = trimValue(category);
  if (!value) return "Category is required.";

  const allowed = ["General", "OBC", "SC", "ST", "EWS"];
  if (!allowed.includes(value)) return "Select a valid category.";
  return null;
};

export const validateRequiredText = (value, label) => {
  const trimmed = trimValue(value);
  if (!trimmed) return `${label} is required.`;
  if (trimmed.length > 255) return `${label} must not exceed 255 characters.`;
  return null;
};

export const validateGraduationYear = (year) => {
  const value = trimValue(year);
  if (!value) return "Graduation year is required.";
  if (!YEAR_REGEX.test(value)) return "Enter a valid 4-digit graduation year.";

  const yearNumber = Number(value);
  const currentYear = new Date().getFullYear();
  const maxAllowed = currentYear + GRADUATION_FUTURE_YEARS;
  if (yearNumber < MIN_GRADUATION_YEAR || yearNumber > maxAllowed) {
    return `Graduation year must be between ${MIN_GRADUATION_YEAR} and ${maxAllowed}.`;
  }

  return null;
};

export const validatePercentage = (percentage) => {
  const value = trimValue(percentage);
  if (!value) return "Percentage / CGPA is required.";
  if (!DECIMAL_REGEX.test(value)) return "Enter a valid percentage or CGPA.";

  const numericValue = Number(value);
  if (Number.isNaN(numericValue) || numericValue < 0 || numericValue > 100) {
    return "Percentage / CGPA must be between 0 and 100.";
  }

  return null;
};

export const validateGateScore = (gateScore) => {
  const value = trimValue(gateScore);
  if (!value) return null;
  if (!DECIMAL_REGEX.test(value)) return "GATE score must be a number.";

  const numericValue = Number(value);
  if (Number.isNaN(numericValue) || numericValue < 0 || numericValue > MAX_GATE_SCORE) {
    return `GATE score must be between 0 and ${MAX_GATE_SCORE}.`;
  }

  return null;
};

export const validateGateRank = (gateRank) => {
  const value = trimValue(gateRank);
  if (!value) return null;
  if (!INTEGER_REGEX.test(value)) return "GATE rank must be a whole number.";

  const numericValue = Number(value);
  if (Number.isNaN(numericValue) || numericValue < 1 || numericValue > 999999) {
    return "GATE rank must be between 1 and 999999.";
  }

  return null;
};

export const validateDocuments = (files) => {
  const errors = {};
  const allowedTypes = ["application/pdf", "image/jpeg", "image/png"];
  const maxFileSizeBytes = 5 * 1024 * 1024;

  DOCUMENT_TYPES.forEach((doc) => {
    const file = files[doc.key];

    if (doc.required && !file) {
      errors[doc.key] = `${doc.label} is required.`;
      return;
    }

    if (!file) return;

    if (!allowedTypes.includes(file.type)) {
      errors[doc.key] = "Only PDF, JPG, and PNG files are allowed.";
      return;
    }

    if (file.size > maxFileSizeBytes) {
      errors[doc.key] = "File size must be 5 MB or smaller.";
    }
  });

  return errors;
};

export const validateLoginForm = (formData) => {
  const errors = {};
  addError(errors, "email", validateEmail(formData.email));
  addError(errors, "password", validatePassword(formData.password));
  return errors;
};

export const validateRegisterForm = (formData) => {
  const errors = {};
  addError(errors, "full_name", validateName(formData.full_name));
  addError(errors, "email", validateEmail(formData.email));
  addError(errors, "phone_number", validateOptionalPhone(formData.phone_number));
  addError(errors, "password", validatePassword(formData.password));

  if (![ROLES.CANDIDATE, ROLES.ADMIN].includes(trimValue(formData.role))) {
    addError(errors, "role", "Select a valid role.");
  }

  return errors;
};

export const validateApplicationPersonal = (personal) => {
  const errors = {};
  addError(errors, "full_name", validateName(personal.full_name));
  addError(errors, "date_of_birth", validateDateOfBirth(personal.date_of_birth));
  addError(errors, "phone", validateRequiredPhone(personal.phone));
  addError(errors, "category", validateCategory(personal.category));
  return errors;
};

export const validateApplicationEducation = (education) => {
  const errors = {};
  addError(errors, "degree", validateRequiredText(education.degree, "Degree / qualification"));
  addError(errors, "branch", validateRequiredText(education.branch, "Branch / specialization"));
  addError(errors, "college", validateRequiredText(education.college, "College / university"));
  addError(errors, "graduation_year", validateGraduationYear(education.graduation_year));
  addError(errors, "percentage", validatePercentage(education.percentage));
  addError(errors, "gate_score", validateGateScore(education.gate_score));
  addError(errors, "gate_rank", validateGateRank(education.gate_rank));
  return errors;
};
