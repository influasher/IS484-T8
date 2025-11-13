import axios from "axios";

const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || "http://localhost:5001";
const API_URL = `${API_BASE_URL}/api/entities`;

// Create axios instance with default config
const apiClient = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  }
});

// Get token function (same as auth service)
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

// Entity sentiment service functions
const entitySentimentService = {
  /**
   * Refresh sentiment for all entities
   * @param {number} lookbackDays - Number of days to look back for news (default: 30)
   * @returns {Promise} API response
   */
  refreshAllSentiments: async (lookbackDays = 30) => {
    try {
      const response = await apiClient.post('/sentiment/refresh-all', {
        lookback_days: lookbackDays
      });
      return response.data;
    } catch (error) {
      console.error('Error refreshing all sentiments:', error);
      throw error;
    }
  },

  /**
   * Refresh sentiment for a specific entity
   * @param {string} entityName - Name of the entity
   * @param {number} lookbackDays - Number of days to look back for news (default: 30)
   * @returns {Promise} API response
   */
  refreshEntitySentiment: async (entityName, lookbackDays = 30) => {
    try {
      const response = await apiClient.post(`/${encodeURIComponent(entityName)}/sentiment/refresh`, {
        lookback_days: lookbackDays
      });
      return response.data;
    } catch (error) {
      console.error(`Error refreshing sentiment for ${entityName}:`, error);
      throw error;
    }
  },

  /**
   * Preview sentiment calculation for an entity without updating
   * @param {string} entityName - Name of the entity
   * @param {number} lookbackDays - Number of days to look back for news (default: 30)
   * @returns {Promise} API response
   */
  previewEntitySentiment: async (entityName, lookbackDays = 30) => {
    try {
      const response = await apiClient.get(`/${encodeURIComponent(entityName)}/sentiment/preview`, {
        params: {
          lookback_days: lookbackDays
        }
      });
      return response.data;
    } catch (error) {
      console.error(`Error previewing sentiment for ${entityName}:`, error);
      throw error;
    }
  }
};

export default entitySentimentService;