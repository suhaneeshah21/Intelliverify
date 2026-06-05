// frontend/src/components/shared/LoadingSpinner.jsx

import "../../styles/components.css";

const LoadingSpinner = ({ message = "Loading..." }) => {
  return (
    <div className="spinner-overlay">
      <div className="spinner-container">
        <div className="spinner" />
        <p className="spinner-message">{message}</p>
      </div>
    </div>
  );
};

export default LoadingSpinner;