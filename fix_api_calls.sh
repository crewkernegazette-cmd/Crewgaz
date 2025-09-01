#!/bin/bash

# Fix all /api/ calls in frontend to remove the prefix since baseURL now includes /api

find /app/frontend/src -name "*.js" -type f -exec sed -i "s|apiClient\.get('/api/|apiClient.get('/|g" {} \;
find /app/frontend/src -name "*.js" -type f -exec sed -i "s|apiClient\.post('/api/|apiClient.post('/|g" {} \;
find /app/frontend/src -name "*.js" -type f -exec sed -i "s|apiClient\.put('/api/|apiClient.put('/|g" {} \;
find /app/frontend/src -name "*.js" -type f -exec sed -i "s|apiClient\.delete('/api/|apiClient.delete('/|g" {} \;

echo "Fixed all apiClient calls to remove /api prefix"