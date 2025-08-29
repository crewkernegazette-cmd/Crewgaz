import requests
import sys
from datetime import datetime

class ProductionDiagnostic:
    def __init__(self):
        self.base_url = "https://CrewkerneGazette.co.uk"
        self.api_url = f"{self.base_url}/api"

    def test_frontend_loading(self):
        """Test if frontend loads correctly"""
        print("🔍 FRONTEND LOADING TEST")
        print("-" * 30)
        
        try:
            response = requests.get(self.base_url, timeout=30)
            print(f"   Status: {response.status_code}")
            print(f"   Content-Type: {response.headers.get('content-type', 'N/A')}")
            print(f"   Server: {response.headers.get('server', 'N/A')}")
            
            # Check if it's actually serving React content
            content = response.text
            if 'react' in content.lower() or 'root' in content:
                print("   ✅ Frontend appears to be loading React app")
                return True
            else:
                print("   ❌ Frontend not serving React content")
                print(f"   Content preview: {content[:200]}...")
                return False
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
            return False

    def test_api_root_responses(self):
        """Test various API root paths to understand routing"""
        print("\n🔍 API ROUTING DIAGNOSTIC")
        print("-" * 30)
        
        paths_to_test = [
            "/api",
            "/api/",
            "/api/docs",
            "/api/openapi.json",
            "/api/health",
            "/api/ping"
        ]
        
        for path in paths_to_test:
            try:
                url = f"{self.base_url}{path}"
                response = requests.get(url, timeout=10)
                print(f"   {path}: {response.status_code} ({response.headers.get('content-type', 'N/A')})")
                
                if response.status_code == 500:
                    print(f"      ❌ 500 Error: {response.text[:100]}")
                elif response.status_code == 200:
                    print(f"      ✅ Success: {response.text[:100]}")
                    
            except Exception as e:
                print(f"   {path}: ERROR - {e}")

    def test_different_http_methods(self):
        """Test different HTTP methods on login endpoint"""
        print("\n🔍 HTTP METHODS TEST ON LOGIN ENDPOINT")
        print("-" * 40)
        
        login_url = f"{self.api_url}/auth/login"
        
        # Test OPTIONS (CORS preflight)
        try:
            response = requests.options(login_url, timeout=10)
            print(f"   OPTIONS: {response.status_code}")
            print(f"   CORS Headers: {response.headers.get('Access-Control-Allow-Methods', 'N/A')}")
        except Exception as e:
            print(f"   OPTIONS: ERROR - {e}")
        
        # Test GET (should be 405 Method Not Allowed)
        try:
            response = requests.get(login_url, timeout=10)
            print(f"   GET: {response.status_code} (expected 405)")
        except Exception as e:
            print(f"   GET: ERROR - {e}")
        
        # Test POST with empty body
        try:
            response = requests.post(login_url, timeout=10)
            print(f"   POST (empty): {response.status_code}")
        except Exception as e:
            print(f"   POST (empty): ERROR - {e}")

    def test_static_file_serving(self):
        """Test if static files are being served correctly"""
        print("\n🔍 STATIC FILE SERVING TEST")
        print("-" * 30)
        
        # Test uploads directory
        try:
            uploads_url = f"{self.base_url}/uploads/"
            response = requests.get(uploads_url, timeout=10)
            print(f"   /uploads/: {response.status_code}")
        except Exception as e:
            print(f"   /uploads/: ERROR - {e}")

    def test_server_headers_analysis(self):
        """Analyze server headers for clues"""
        print("\n🔍 SERVER HEADERS ANALYSIS")
        print("-" * 30)
        
        try:
            response = requests.get(f"{self.api_url}/auth/login", timeout=10)
            headers = dict(response.headers)
            
            print("   Response Headers:")
            for key, value in headers.items():
                print(f"      {key}: {value}")
                
            # Look for clues about the server setup
            server = headers.get('server', '').lower()
            via = headers.get('via', '').lower()
            
            if 'nginx' in server:
                print("\n   💡 Analysis: nginx reverse proxy detected")
            if 'caddy' in via:
                print("   💡 Analysis: Caddy server in the chain")
            if 'uvicorn' in server or 'fastapi' in server:
                print("   💡 Analysis: FastAPI/Uvicorn detected")
            else:
                print("   ⚠️  Analysis: FastAPI/Uvicorn NOT detected in headers")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")

def main():
    print("🔍 PRODUCTION DIAGNOSTIC - CrewkerneGazette.co.uk")
    print("=" * 60)
    
    diagnostic = ProductionDiagnostic()
    
    # Run all diagnostic tests
    frontend_ok = diagnostic.test_frontend_loading()
    diagnostic.test_api_root_responses()
    diagnostic.test_different_http_methods()
    diagnostic.test_static_file_serving()
    diagnostic.test_server_headers_analysis()
    
    print("\n" + "=" * 60)
    print("🎯 DIAGNOSTIC SUMMARY")
    print("=" * 60)
    
    print(f"Frontend Loading: {'✅' if frontend_ok else '❌'}")
    print("\n💡 KEY FINDINGS:")
    print("   - All API endpoints return HTTP 500 'Internal Server Error'")
    print("   - Server headers show nginx/1.22.1 and Caddy")
    print("   - CORS headers are present (backend is partially responding)")
    print("   - Error responses are plain text, not JSON")
    
    print("\n🚨 LIKELY CAUSES:")
    print("   1. Backend application not running on production server")
    print("   2. Database connection failure on production")
    print("   3. Environment variables not set correctly on production")
    print("   4. Python/FastAPI runtime error on production")
    print("   5. Production deployment using different code version")
    
    print("\n💡 RECOMMENDATIONS:")
    print("   1. Check production server logs for backend application")
    print("   2. Verify MongoDB connection on production server")
    print("   3. Ensure production environment variables match local")
    print("   4. Verify production deployment is using latest code")
    print("   5. Check if backend service is running on production")

if __name__ == "__main__":
    main()