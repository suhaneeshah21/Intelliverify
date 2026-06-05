// frontend/src/context/AuthContext.jsx

import { createContext, useState, useEffect, useCallback } from "react";
import { authAPI } from "../services/api";

// Create the context
export const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [user, setUser]           = useState(null);
  const [token, setToken]         = useState(null);
  const [isLoading, setIsLoading] = useState(true); // true on first load

  // ── Restore session on app load ───────────
  // When the page refreshes, check localStorage for existing token
  // If found, verify it's still valid by calling /auth/me
  useEffect(() => {
    const restoreSession = async () => {
      const storedToken = localStorage.getItem("access_token");
      const storedUser  = localStorage.getItem("user");

      if (storedToken && storedUser) {
        try {
          // Verify token is still valid with backend
          const response = await authAPI.getMe();
          setUser(response.data);
          setToken(storedToken);
        } catch (error) {
          // Token expired or invalid — clear everything
          localStorage.removeItem("access_token");
          localStorage.removeItem("user");
        }
      }

      setIsLoading(false); // done checking — render the app
    };

    restoreSession();
  }, []);


  // ── Login ─────────────────────────────────
  // Called after successful login API response
  // Stores token and user in both state and localStorage
  const login = useCallback((tokenValue, userData) => {
    localStorage.setItem("access_token", tokenValue);
    localStorage.setItem("user", JSON.stringify(userData));
    setToken(tokenValue);
    setUser(userData);
  }, []);


  // ── Logout ────────────────────────────────
  // Clears everything from state and localStorage
  const logout = useCallback(() => {
    localStorage.removeItem("access_token");
    localStorage.removeItem("user");
    setToken(null);
    setUser(null);
  }, []);


  // ── Value exposed to the whole app ────────
  const value = {
    user,                                    // full user object
    token,                                   // JWT string
    isLoading,                               // true while checking session on load
    isAuthenticated: !!token && !!user,      // boolean — is someone logged in?
    login,
    logout,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};