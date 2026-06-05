// frontend/src/hooks/useAuth.js

import { useContext } from "react";
import { AuthContext } from "../context/AuthContext";

const useAuth = () => {
  const context = useContext(AuthContext);

  // If this hook is used outside of AuthProvider it will be null
  // This catches the mistake immediately with a clear error message
  if (!context) {
    throw new Error("useAuth must be used inside AuthProvider");
  }

  return context;
};

export default useAuth;