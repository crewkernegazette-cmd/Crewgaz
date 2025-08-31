// API configuration for CRA (Create React App)
export const API_BASE = process.env.REACT_APP_API_URL || 'http://localhost:8001';

// For development, default to localhost
// For production, use the environment variable pointing to api.crewkernegazette.co.uk
console.log('API_BASE configured as:', API_BASE);