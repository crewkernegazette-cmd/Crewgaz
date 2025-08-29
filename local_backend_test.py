import requests
import sys
from datetime import datetime
import json

class LocalBackendTester:
    def __init__(self):
        # Test local backend first to verify fixes
        self.base_url = "http://localhost:8001"
        self.api_url = f"{self.base_url}/api"
        self.token = None
        self.tests_run = 0
        self.tests_passed = 0

    def run_test(self, name, method, endpoint, expected_status, data=None, headers=None):
        """Run a single API test"""
        url = f"{self.api_url}/{endpoint}"
        test_headers = {'Content-Type': 'application/json'}
        
        if self.token:
            test_headers['Authorization'] = f'Bearer {self.token}'
        
        if headers:
            test_headers.update(headers)

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=test_headers, timeout=10)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=test_headers, timeout=10)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=test_headers, timeout=10)
            elif method == 'DELETE':
                response = requests.delete(url, headers=test_headers, timeout=10)

            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                try:
                    response_data = response.json()
                    if isinstance(response_data, dict) and len(str(response_data)) < 500:
                        print(f"   Response: {response_data}")
                    elif isinstance(response_data, list):
                        print(f"   Response: List with {len(response_data)} items")
                    return success, response_data
                except:
                    return success, {}
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"   Error: {error_data}")
                except:
                    print(f"   Error: {response.text}")
                return False, {}

        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False, {}

    def test_admin_login(self):
        """Test admin login with admin/admin123"""
        success, response = self.run_test(
            "Admin Login (admin/admin123)",
            "POST",
            "auth/login",
            200,
            data={"username": "admin", "password": "admin123"}
        )
        if success and 'access_token' in response:
            self.token = response['access_token']
            print(f"   ✅ Token obtained: {self.token[:30]}...")
            return True
        return False

    def test_public_settings(self):
        """Test public settings endpoint"""
        success, response = self.run_test(
            "Public Settings",
            "GET",
            "settings/public",
            200
        )
        return success

    def test_articles_endpoint(self):
        """Test articles endpoint"""
        success, response = self.run_test(
            "Articles List",
            "GET",
            "articles",
            200
        )
        return success

    def test_authenticated_settings(self):
        """Test authenticated settings endpoint"""
        if not self.token:
            print("❌ No token available for authenticated test")
            return False
            
        success, response = self.run_test(
            "Admin Settings (authenticated)",
            "GET",
            "settings",
            200
        )
        return success

    def test_password_change(self):
        """Test password change functionality"""
        if not self.token:
            print("❌ No token available for password change test")
            return False
            
        # Test password change
        success, response = self.run_test(
            "Password Change",
            "POST",
            "auth/change-password",
            200,
            data={
                "current_password": "admin123",
                "new_password": "newpassword123"
            }
        )
        
        if success:
            # Change it back
            success2, response2 = self.run_test(
                "Password Change Back",
                "POST",
                "auth/change-password",
                200,
                data={
                    "current_password": "newpassword123",
                    "new_password": "admin123"
                }
            )
            return success2
        
        return success

def main():
    print("🚀 LOCAL BACKEND TESTING - Verifying Deployment Fixes")
    print("🎯 Target: http://localhost:8001")
    print("=" * 60)
    
    tester = LocalBackendTester()
    
    # Test core functionality
    login_success = tester.test_admin_login()
    public_settings_success = tester.test_public_settings()
    articles_success = tester.test_articles_endpoint()
    
    # Test authenticated endpoints if login worked
    auth_settings_success = False
    password_change_success = False
    
    if login_success:
        auth_settings_success = tester.test_authenticated_settings()
        password_change_success = tester.test_password_change()
    
    # Results
    print("\n" + "=" * 60)
    print("📊 LOCAL BACKEND TEST RESULTS")
    print("=" * 60)
    
    print(f"Admin Login: {'✅' if login_success else '❌'}")
    print(f"Public Settings: {'✅' if public_settings_success else '❌'}")
    print(f"Articles Endpoint: {'✅' if articles_success else '❌'}")
    print(f"Authenticated Settings: {'✅' if auth_settings_success else '❌'}")
    print(f"Password Change: {'✅' if password_change_success else '❌'}")
    
    print(f"\nTests Run: {tester.tests_run}")
    print(f"Tests Passed: {tester.tests_passed}")
    print(f"Success Rate: {(tester.tests_passed/tester.tests_run)*100:.1f}%")
    
    if tester.tests_passed == tester.tests_run:
        print("\n🎉 LOCAL BACKEND: All tests passed! Deployment fixes are working locally.")
        print("💡 ISSUE: Production deployment configuration needs to be updated.")
        return 0
    else:
        print(f"\n⚠️  LOCAL BACKEND: {tester.tests_run - tester.tests_passed} tests failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())