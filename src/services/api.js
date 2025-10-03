import axios from "axios";

// Dynamically set API base URL based on environment variables
const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || "http://localhost:5001";

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: { "Content-Type": "application/json" },
});

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

export const postDataBlob = async (endpoint, data) => {
  try {
    const response = await apiClient.post(`${endpoint}`, data, { responseType: 'blob' });
    return response.data;
  } catch (error) {
    console.error("API error:", error);
    return null;
  }
};