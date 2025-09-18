import { useState, useEffect, useCallback } from "react";
import { getUser, getToken, isAuthenticated, getUserRole, logout as authLogout } from "../services/authService";

const useAuth = () => {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(null);
  const [loading, setLoading] = useState(true);
  const [isLoggedIn, setIsLoggedIn] = useState(false);

  // Check authentication status on mount
  useEffect(() => {
    const checkAuth = () => {
      const userData = getUser();
      const userToken = getToken();
      const authenticated = isAuthenticated();

      setUser(userData);
      setToken(userToken);
      setIsLoggedIn(authenticated);
      setLoading(false);
    };

    checkAuth();
  }, []);

  // Login function - call this after successful OTP verification
  const login = useCallback((userData, accessToken) => {
    setUser(userData);
    setToken(accessToken);
    setIsLoggedIn(true);
    localStorage.setItem("user", JSON.stringify(userData));
    localStorage.setItem("token", accessToken);
  }, []);

  // Logout function
  const logout = useCallback(async () => {
    try {
      await authLogout();w
    } catch (error) {
      console.error("Logout error:", error);
    } finally {
      setUser(null);
      setToken(null);
      setIsLoggedIn(false);
    }
  }, []);

  // Check if user has specific role
  const hasRole = useCallback((role) => {
    return getUserRole() === role;
  }, []);

  // Check if user is client
  const isClient = useCallback(() => {
    return hasRole("client");
  }, [hasRole]);

  // Check if user is relationship manager
  const isRM = useCallback(() => {
    return hasRole("relationship_manager");
  }, [hasRole]);

  // Get user's full name
  const getUserFullName = useCallback(() => {
    if (!user) return "";
    return `${user.first_name || ""} ${user.last_name || ""}`.trim();
  }, [user]);

  return {
    user,
    token,
    loading,
    isLoggedIn,
    login,
    logout,
    hasRole,
    isClient,
    isRM,
    getUserFullName,
    userRole: getUserRole(),
    isAuthenticated: isAuthenticated()
  };
};

export default useAuth;
