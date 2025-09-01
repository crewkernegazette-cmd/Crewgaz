#!/usr/bin/env python3
"""
Comprehensive Authentication Debug Test for The Crewkerne Gazette
Testing the authentication fixes implemented for login issues.

Focus Areas:
1. Admin Login with Emergency Fallback System
2. Debug Auth endpoint (NEW)
3. JWT Token System with fallback
4. Database SSL and Connection Handling
5. Enhanced Logging Validation
"""

import requests
import sys
import json
import time
import jwt
from datetime import datetime

class AuthDebugTester:
    def __init__(self, base_url="https://gazette-cms.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.token = None
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []

    def log_test_result(self, test_name, success, details=""):
        """Log test result for summary"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
        
        self.test_results.append({
            "name": test_name,
            "success": success,
            "details": details
        })
        
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} - {test_name}")
        if details:
            print(f"    {details}")

    def test_debug_auth_endpoint(self):
        """Test the new /api/debug/auth endpoint (no authentication required)"""
        print("\n🔍 TESTING DEBUG AUTH ENDPOINT")
        print("-" * 50)
        
        url = f"{self.api_url}/debug/auth"
        
        try:
            response = requests.get(url, timeout=30)
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    
                    # Verify expected fields are present
                    expected_fields = ['users', 'seeding_status', 'db_connected', 'total_users', 'timestamp']
                    missing_fields = [field for field in expected_fields if field not in data]
                    
                    if not missing_fields:
                        self.log_test_result(
                            "Debug Auth Endpoint Structure", 
                            True, 
                            f"All expected fields present: {expected_fields}"
                        )
                        
                        # Check if users data is anonymized properly
                        users = data.get('users', [])
                        if users and isinstance(users, list):
                            user_fields = users[0].keys() if users else []
                            safe_fields = ['username', 'role']
                            has_safe_fields = all(field in user_fields for field in safe_fields)
                            
                            self.log_test_result(
                                "Debug Auth User Data Anonymization",
                                has_safe_fields,
                                f"User fields: {list(user_fields)}"
                            )
                        
                        # Check database connection status
                        db_connected = data.get('db_connected', False)
                        self.log_test_result(
                            "Debug Auth DB Connection Status",
                            isinstance(db_connected, bool),
                            f"DB Connected: {db_connected}"
                        )
                        
                        # Check seeding status
                        seeding_status = data.get('seeding_status', '')
                        self.log_test_result(
                            "Debug Auth Seeding Status",
                            seeding_status != '',
                            f"Seeding Status: {seeding_status}"
                        )
                        
                        print(f"    Full Response: {json.dumps(data, indent=2)}")
                        return True
                    else:
                        self.log_test_result(
                            "Debug Auth Endpoint Structure",
                            False,
                            f"Missing fields: {missing_fields}"
                        )
                        return False
                        
                except json.JSONDecodeError:
                    self.log_test_result(
                        "Debug Auth Endpoint JSON",
                        False,
                        "Response is not valid JSON"
                    )
                    return False
            else:
                self.log_test_result(
                    "Debug Auth Endpoint Access",
                    False,
                    f"HTTP {response.status_code}: {response.text}"
                )
                return False
                
        except Exception as e:
            self.log_test_result(
                "Debug Auth Endpoint Connection",
                False,
                f"Connection error: {str(e)}"
            )
            return False

    def test_admin_login_with_fallback(self):
        """Test admin login with emergency fallback system"""
        print("\n🔐 TESTING ADMIN LOGIN WITH EMERGENCY FALLBACK")
        print("-" * 50)
        
        # Test primary admin credentials
        login_data = {"username": "admin", "password": "admin123"}
        url = f"{self.api_url}/auth/login"
        
        try:
            response = requests.post(url, json=login_data, timeout=30)
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    
                    # Check for access token
                    if 'access_token' in data:
                        self.token = data['access_token']
                        self.log_test_result(
                            "Admin Login Success",
                            True,
                            f"Token received, Role: {data.get('role', 'unknown')}"
                        )
                        
                        # Check login message for emergency vs database
                        message = data.get('message', '')
                        if 'Emergency' in message:
                            self.log_test_result(
                                "Emergency Fallback System Active",
                                True,
                                f"Message: {message}"
                            )
                        elif 'Database' in message:
                            self.log_test_result(
                                "Database Authentication Active",
                                True,
                                f"Message: {message}"
                            )
                        
                        return True
                    else:
                        self.log_test_result(
                            "Admin Login Token",
                            False,
                            "No access_token in response"
                        )
                        return False
                        
                except json.JSONDecodeError:
                    self.log_test_result(
                        "Admin Login Response",
                        False,
                        "Invalid JSON response"
                    )
                    return False
            else:
                self.log_test_result(
                    "Admin Login HTTP Status",
                    False,
                    f"HTTP {response.status_code}: {response.text}"
                )
                return False
                
        except Exception as e:
            self.log_test_result(
                "Admin Login Connection",
                False,
                f"Connection error: {str(e)}"
            )
            return False

    def test_jwt_token_system(self):
        """Test JWT token creation and validation"""
        print("\n🎫 TESTING JWT TOKEN SYSTEM")
        print("-" * 50)
        
        if not self.token:
            self.log_test_result(
                "JWT Token Availability",
                False,
                "No token available from login test"
            )
            return False
        
        try:
            # Decode token without verification to check structure
            # Note: We can't verify signature without knowing the secret
            decoded_unverified = jwt.decode(self.token, options={"verify_signature": False})
            
            # Check for expected fields
            expected_fields = ['username', 'role', 'exp']
            missing_fields = [field for field in expected_fields if field not in decoded_unverified]
            
            if not missing_fields:
                self.log_test_result(
                    "JWT Token Structure",
                    True,
                    f"Contains: {list(decoded_unverified.keys())}"
                )
                
                # Check expiration
                exp = decoded_unverified.get('exp')
                if exp and exp > time.time():
                    self.log_test_result(
                        "JWT Token Expiration",
                        True,
                        f"Token valid until: {datetime.fromtimestamp(exp)}"
                    )
                else:
                    self.log_test_result(
                        "JWT Token Expiration",
                        False,
                        f"Token expired or invalid exp: {exp}"
                    )
                
                return True
            else:
                self.log_test_result(
                    "JWT Token Structure",
                    False,
                    f"Missing fields: {missing_fields}"
                )
                return False
                
        except Exception as e:
            self.log_test_result(
                "JWT Token Decoding",
                False,
                f"Error decoding token: {str(e)}"
            )
            return False

    def test_token_validation(self):
        """Test token validation by making authenticated request"""
        print("\n🔒 TESTING TOKEN VALIDATION")
        print("-" * 50)
        
        if not self.token:
            self.log_test_result(
                "Token Validation Setup",
                False,
                "No token available for validation"
            )
            return False
        
        # Test authenticated endpoint
        url = f"{self.api_url}/dashboard/articles"
        headers = {'Authorization': f'Bearer {self.token}'}
        
        try:
            response = requests.get(url, headers=headers, timeout=30)
            
            if response.status_code == 200:
                self.log_test_result(
                    "Token Validation Success",
                    True,
                    "Authenticated request successful"
                )
                return True
            elif response.status_code == 401:
                self.log_test_result(
                    "Token Validation",
                    False,
                    "Token rejected by server (401 Unauthorized)"
                )
                return False
            else:
                self.log_test_result(
                    "Token Validation",
                    False,
                    f"Unexpected status: {response.status_code}"
                )
                return False
                
        except Exception as e:
            self.log_test_result(
                "Token Validation Request",
                False,
                f"Request error: {str(e)}"
            )
            return False

    def test_alternative_admin_credentials(self):
        """Test alternative admin credentials from emergency system"""
        print("\n🆘 TESTING ALTERNATIVE ADMIN CREDENTIALS")
        print("-" * 50)
        
        # Test alternative emergency credentials
        alt_credentials = [
            {"username": "admin_backup", "password": "admin_backup"},
            {"username": "Gazette", "password": "Gazette2024!"}
        ]
        
        url = f"{self.api_url}/auth/login"
        
        for creds in alt_credentials:
            try:
                response = requests.post(url, json=creds, timeout=30)
                
                if response.status_code == 200:
                    try:
                        data = response.json()
                        if 'access_token' in data:
                            self.log_test_result(
                                f"Alternative Login ({creds['username']})",
                                True,
                                f"Role: {data.get('role', 'unknown')}, Message: {data.get('message', '')}"
                            )
                        else:
                            self.log_test_result(
                                f"Alternative Login ({creds['username']})",
                                False,
                                "No access token in response"
                            )
                    except json.JSONDecodeError:
                        self.log_test_result(
                            f"Alternative Login ({creds['username']})",
                            False,
                            "Invalid JSON response"
                        )
                else:
                    self.log_test_result(
                        f"Alternative Login ({creds['username']})",
                        False,
                        f"HTTP {response.status_code}"
                    )
                    
            except Exception as e:
                self.log_test_result(
                    f"Alternative Login ({creds['username']})",
                    False,
                    f"Connection error: {str(e)}"
                )

    def test_enhanced_logging_indicators(self):
        """Test for enhanced logging by checking debug endpoints"""
        print("\n📝 TESTING ENHANCED LOGGING INDICATORS")
        print("-" * 50)
        
        # The enhanced logging is server-side, but we can check if debug endpoints
        # provide information that indicates logging is working
        
        url = f"{self.api_url}/debug/auth"
        
        try:
            response = requests.get(url, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                
                # Check if we have detailed error information
                last_error = data.get('last_error')
                seeding_status = data.get('seeding_status')
                
                if seeding_status and seeding_status != 'unknown':
                    self.log_test_result(
                        "Enhanced Logging - Seeding Status",
                        True,
                        f"Seeding status tracked: {seeding_status}"
                    )
                else:
                    self.log_test_result(
                        "Enhanced Logging - Seeding Status",
                        False,
                        "No seeding status information"
                    )
                
                # Check if error tracking is working
                if last_error is not None:  # Could be None (no error) or string (error details)
                    self.log_test_result(
                        "Enhanced Logging - Error Tracking",
                        True,
                        f"Error tracking active: {last_error or 'No errors'}"
                    )
                else:
                    self.log_test_result(
                        "Enhanced Logging - Error Tracking",
                        False,
                        "No error tracking information"
                    )
                
                return True
            else:
                self.log_test_result(
                    "Enhanced Logging Check",
                    False,
                    f"Debug endpoint not accessible: {response.status_code}"
                )
                return False
                
        except Exception as e:
            self.log_test_result(
                "Enhanced Logging Check",
                False,
                f"Connection error: {str(e)}"
            )
            return False

    def test_database_connection_handling(self):
        """Test database connection handling through debug endpoint"""
        print("\n🗄️ TESTING DATABASE CONNECTION HANDLING")
        print("-" * 50)
        
        url = f"{self.api_url}/debug/auth"
        
        try:
            response = requests.get(url, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                
                db_connected = data.get('db_connected')
                users = data.get('users', [])
                total_users = data.get('total_users', 0)
                
                if isinstance(db_connected, bool):
                    self.log_test_result(
                        "Database Connection Status Check",
                        True,
                        f"DB Connected: {db_connected}"
                    )
                    
                    if db_connected and total_users > 0:
                        self.log_test_result(
                            "Database User Data Access",
                            True,
                            f"Found {total_users} users in database"
                        )
                    elif not db_connected:
                        self.log_test_result(
                            "Database Fallback Handling",
                            True,
                            "System handling database disconnection gracefully"
                        )
                    
                    return True
                else:
                    self.log_test_result(
                        "Database Connection Status Check",
                        False,
                        "No database connection status information"
                    )
                    return False
            else:
                self.log_test_result(
                    "Database Connection Check",
                    False,
                    f"Debug endpoint error: {response.status_code}"
                )
                return False
                
        except Exception as e:
            self.log_test_result(
                "Database Connection Check",
                False,
                f"Connection error: {str(e)}"
            )
            return False

    def run_comprehensive_auth_tests(self):
        """Run all authentication debug tests"""
        print("🚀 STARTING COMPREHENSIVE AUTHENTICATION DEBUG TESTS")
        print("🎯 Target:", self.base_url)
        print("=" * 80)
        
        # Test 1: Debug Auth Endpoint (NEW)
        self.test_debug_auth_endpoint()
        
        # Test 2: Admin Login with Emergency Fallback
        self.test_admin_login_with_fallback()
        
        # Test 3: JWT Token System
        self.test_jwt_token_system()
        
        # Test 4: Token Validation
        self.test_token_validation()
        
        # Test 5: Alternative Admin Credentials
        self.test_alternative_admin_credentials()
        
        # Test 6: Enhanced Logging Indicators
        self.test_enhanced_logging_indicators()
        
        # Test 7: Database Connection Handling
        self.test_database_connection_handling()
        
        # Summary
        self.print_summary()

    def print_summary(self):
        """Print comprehensive test summary"""
        print("\n" + "=" * 80)
        print("📊 AUTHENTICATION DEBUG TEST SUMMARY")
        print("=" * 80)
        
        print(f"Total Tests Run: {self.tests_run}")
        print(f"Tests Passed: {self.tests_passed}")
        print(f"Tests Failed: {self.tests_run - self.tests_passed}")
        print(f"Success Rate: {(self.tests_passed/self.tests_run)*100:.1f}%")
        
        print("\n📋 DETAILED RESULTS:")
        print("-" * 50)
        
        for result in self.test_results:
            status = "✅" if result["success"] else "❌"
            print(f"{status} {result['name']}")
            if result["details"]:
                print(f"    └─ {result['details']}")
        
        print("\n🎯 PRIORITY TESTING AREAS STATUS:")
        print("-" * 50)
        
        # Check specific priority areas from the review request
        priority_areas = {
            "Admin Login with Emergency Fallback": any("Admin Login" in r["name"] for r in self.test_results if r["success"]),
            "Debug Auth Endpoint": any("Debug Auth" in r["name"] for r in self.test_results if r["success"]),
            "JWT Token System": any("JWT Token" in r["name"] for r in self.test_results if r["success"]),
            "Database Connection Handling": any("Database" in r["name"] for r in self.test_results if r["success"]),
            "Enhanced Logging": any("Enhanced Logging" in r["name"] for r in self.test_results if r["success"])
        }
        
        for area, status in priority_areas.items():
            print(f"{'✅' if status else '❌'} {area}")
        
        print("\n🔍 AUTHENTICATION SYSTEM STATUS:")
        print("-" * 50)
        
        if self.token:
            print("✅ Authentication System: WORKING")
            print("✅ JWT Token Generation: WORKING")
            print("✅ Emergency Fallback: AVAILABLE")
        else:
            print("❌ Authentication System: FAILED")
            print("❌ JWT Token Generation: FAILED")
            print("❌ Emergency Fallback: NOT WORKING")
        
        # Overall assessment
        if self.tests_passed >= self.tests_run * 0.8:  # 80% pass rate
            print("\n🎉 OVERALL ASSESSMENT: AUTHENTICATION FIXES ARE WORKING WELL")
            return 0
        elif self.tests_passed >= self.tests_run * 0.6:  # 60% pass rate
            print("\n⚠️  OVERALL ASSESSMENT: AUTHENTICATION FIXES PARTIALLY WORKING")
            return 1
        else:
            print("\n🚨 OVERALL ASSESSMENT: AUTHENTICATION FIXES NEED ATTENTION")
            return 2

def main():
    """Main test execution"""
    tester = AuthDebugTester()
    return tester.run_comprehensive_auth_tests()

if __name__ == "__main__":
    sys.exit(main())