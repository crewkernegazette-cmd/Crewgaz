import React, { useState, useContext } from 'react';
import { AuthContext } from '../App';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

const Debug = () => {
  const { user } = useContext(AuthContext);
  const [testResults, setTestResults] = useState({});

  const runTests = async () => {
    const results = {};
    
    // Test 1: Backend URL
    results.backendUrl = BACKEND_URL;
    
    // Test 2: User authentication status
    results.userAuthenticated = !!user;
    results.userInfo = user;
    
    // Test 3: Token in localStorage
    results.tokenExists = !!localStorage.getItem('access_token');
    results.token = localStorage.getItem('access_token')?.substring(0, 50) + '...';
    
    // Test 4: Test API call without auth
    try {
      const response = await axios.get(`${BACKEND_URL}/settings/public`);
      results.publicApiWorks = true;
      results.publicApiData = response.data;
    } catch (error) {
      results.publicApiWorks = false;
      results.publicApiError = error.message;
    }
    
    // Test 5: Test API call with auth
    if (user && localStorage.getItem('token')) {
      try {
        const response = await axios.get(`${BACKEND_URL}/dashboard/stats`);
        results.authApiWorks = true;
        results.authApiData = response.data;
      } catch (error) {
        results.authApiWorks = false;
        results.authApiError = error.message;
      }
    }
    
    // Test 6: Test contact form
    try {
      const response = await axios.post(`${BACKEND_URL}/contact`, {
        email: 'test@example.com',
        inquiry: 'Debug test message'
      });
      results.contactWorks = true;
      results.contactData = response.data;
    } catch (error) {
      results.contactWorks = false;
      results.contactError = error.message;
    }
    
    setTestResults(results);
  };

  return (
    <div className="p-6 bg-gray-900 text-white">
      <h1 className="text-2xl font-bold mb-4">🔧 Debug Information</h1>
      
      <button 
        onClick={runTests}
        className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded mb-4"
      >
        Run Diagnostic Tests
      </button>
      
      {Object.keys(testResults).length > 0 && (
        <div className="space-y-4">
          <div className="bg-gray-800 p-4 rounded">
            <h3 className="font-bold text-lg mb-2">Test Results:</h3>
            <pre className="text-sm overflow-auto">
              {JSON.stringify(testResults, null, 2)}
            </pre>
          </div>
          
          <div className="bg-gray-800 p-4 rounded">
            <h3 className="font-bold text-lg mb-2">Quick Status:</h3>
            <div className="space-y-2">
              <div>Backend URL: <span className="text-yellow-400">{testResults.backendUrl}</span></div>
              <div>User Authenticated: {testResults.userAuthenticated ? '✅' : '❌'}</div>
              <div>Token Exists: {testResults.tokenExists ? '✅' : '❌'}</div>
              <div>Public API: {testResults.publicApiWorks ? '✅' : '❌'}</div>
              <div>Auth API: {testResults.authApiWorks ? '✅' : '❌'}</div>
              <div>Contact Form: {testResults.contactWorks ? '✅' : '❌'}</div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Debug;