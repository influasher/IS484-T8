import React from "react";
import { Navigate, useLocation } from "react-router-dom";
import useAuth from "../hooks/useAuth";
import { CircularProgress, Box } from "@mui/material";

const ProtectedRoute = ({ children, allowedRoles = [] }) => {
  const { isLoggedIn, loading, userRole } = useAuth();
  const location = useLocation();

  // Show loading spinner while checking authentication
  if (loading) {
    return (
      <Box
        display="flex"
        justifyContent="center"
        alignItems="center"
        minHeight="100vh"
      >
        <CircularProgress />
      </Box>
    );
  }

  // Not authenticated - redirect to login with return URL
  if (!isLoggedIn) {
    return <Navigate to="/Login" state={{ from: location }} replace />;
  }

  // Check role-based access if roles are specified
  if (allowedRoles.length > 0 && !allowedRoles.includes(userRole)) {
    // User doesn't have required role - redirect to appropriate dashboard
    if (userRole === "client") {
      return <Navigate to="/Client" replace />;
    } else if (userRole === "relationship_manager") {
      return <Navigate to="/RM" replace />;
    } else {
      return <Navigate to="/DashboardPage" replace />;
    }
  }

  // User is authenticated and has required role
  return children;
};

export default ProtectedRoute;