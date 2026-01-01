import axios from 'axios';

// API configuration for single-domain setup
// In production: Same domain (crewkernegazette.co.uk)
// In development: localhost backend
const isDevelopment = process.env.NODE_ENV === 'development';
export const API_BASE = isDevelopment ? 'http://localhost:8001' : window.location.origin;

console.log('API_BASE configured as:', API_BASE);

// Create centralized axios instance  
export const apiClient = axios.create({
  baseURL: `${API_BASE.replace(/\/$/, '')}/api`,
  withCredentials: true,
  headers: {
    'Content-Type': 'application/json'
  },
  timeout: 30000 // 30 second timeout
});

// Request interceptor - defensive handling for /api paths
apiClient.interceptors.request.use(
  (config) => {
    // If URL starts with /api, ensure we use the baseURL
    if (config.url && config.url.startsWith('/api')) {
      // baseURL is already set, just log for debugging
      console.log(`🔀 API Interceptor: ${config.method?.toUpperCase()} ${config.url} -> ${API_BASE}${config.url}`);
    }
    
    // If sending FormData, let the browser set the Content-Type automatically
    // This is important for file uploads and form submissions
    if (config.data instanceof FormData) {
      delete config.headers['Content-Type'];
    }
    
    return config;
  },
  (error) => {
    console.error('❌ API Request interceptor error:', error);
    return Promise.reject(error);
  }
);

// Response interceptor for error handling
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('❌ API Response error:', error);
    
    if (error.response?.status === 401) {
      // Handle authentication errors
      console.warn('🔒 Authentication required - redirecting to login');
      // Don't redirect automatically to avoid loops
    } else if (error.response?.status >= 400 && error.response?.status < 500) {
      // Client errors - show server message if available
      const serverMessage = error.response?.data?.detail || error.response?.data?.error;
      if (serverMessage) {
        console.error('📝 Server error message:', serverMessage);
      }
    }
    
    return Promise.reject(error);
  }
);