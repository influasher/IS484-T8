import axios from "axios";

// Dynamically set API base URL based on environment variables
const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || "http://localhost:5001";

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: { "Content-Type": "application/json" },
});

// Get stored token
const getToken = () => localStorage.getItem("token");

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

export const getData = async (endpoint) => {
  try {
    const response = await apiClient.get(`${endpoint}`);
    return response.data;
} catch (error) {
    console.error("API error:", error);
    return null;
  }
};

export const postData = async (endpoint, data) => {
  try {
    const response = await apiClient.post(`${endpoint}`, data);
    return response.data;
  } catch (error) {
    console.error("API error:", error);
    return null;
  }
};

export const putData = async (endpoint, data) => {
  try {
    const response = await apiClient.put(`${endpoint}`, data);
    return response.data;
  } catch (error) {
    console.error("API error:", error);
    return null;
  }
};

export const postDataBlob = async (endpoint, data) => {
  try {
    const response = await apiClient.post(`${endpoint}`, data, { responseType: 'blob' });
    return response.data;
  } catch (error) {
    console.error("API error:", error);
    return null;
  }
};