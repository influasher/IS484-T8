import axios from "axios";

const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || "http://localhost:5001";
const API_URL = `${API_BASE_URL}/api/auth`;

// Create axios instance with default config
const apiClient = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  }
});

// Request interceptor to add JWT token to requests
apiClient.interceptors.request.use(
  (config) => {
    const token = getToken();
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor to handle token expiration
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Token expired or invalid, remove it and redirect to login
      localStorage.removeItem("token");
      localStorage.removeItem("user");
      window.location.href = "/Login";
    }
    return Promise.reject(error);
  }
);

// Step 1: Send OTP to email
export const sendOTP = async (email) => {
  try {
    const response = await apiClient.post("/login", { email });
    return {
      success: true,
      data: response.data.data,
      message: response.data.message
    };
  } catch (error) {
    console.error("Send OTP error:", error);
    return {
      success: false,
      message: error.response?.data?.message || "Failed to send OTP"
    };
  }
};

// Step 2: Verify OTP and complete login
export const verifyOTP = async (otpCode) => {
  try {
    const response = await apiClient.post("/verify-otp", { otp_code: otpCode });

    if (response.data.data?.access_token) {
      // Store token and user data
      localStorage.setItem("token", response.data.data.access_token);
      localStorage.setItem("user", JSON.stringify(response.data.data.user));
      return {
        success: true,
        data: response.data.data,
        message: response.data.message
      };
    }

    return {
      success: false,
      message: "Invalid response format"
    };
  } catch (error) {
    console.error("Verify OTP error:", error);
    return {
      success: false,
      message: error.response?.data?.message || "Failed to verify OTP"
    };
  }
};

// Logout user
export const logout = async () => {
  try {
    await apiClient.post("/logout");
  } catch (error) {
    console.error("Logout error:", error);
  } finally {
    // Always remove local storage even if API call fails
    localStorage.removeItem("token");
    localStorage.removeItem("user");
  }
};

// Get stored token
export const getToken = () => localStorage.getItem("token");

// Get stored user data
export const getUser = () => {
  const userData = localStorage.getItem("user");
  return userData ? JSON.parse(userData) : null;
};

// Check if user is authenticated
export const isAuthenticated = () => {
  const token = getToken();
  const user = getUser();
  return !!(token && user);
};

// Check user role
export const getUserRole = () => {
  const user = getUser();
  return user?.role || null;
};

export { apiClient };
