import requests
import sys
from datetime import datetime
import json
import io

class CrewkerneGazetteAPITester:
    def __init__(self, base_url="https://CrewkerneGazette.co.uk"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.token = None
        self.tests_run = 0
        self.tests_passed = 0
        self.created_article_id = None

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
                response = requests.get(url, headers=test_headers)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=test_headers)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=test_headers)
            elif method == 'DELETE':
                response = requests.delete(url, headers=test_headers)

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

    # PRODUCTION SPECIFIC TESTS - For CrewkerneGazette.co.uk Issue Investigation
    def test_production_login_endpoint(self):
        """Test the specific production login endpoint with admin/admin123"""
        print("\n🚨 PRODUCTION LOGIN ENDPOINT TEST - CrewkerneGazette.co.uk")
        print("=" * 60)
        
        url = f"{self.api_url}/auth/login"
        login_data = {"username": "admin", "password": "admin123"}
        headers = {'Content-Type': 'application/json'}
        
        self.tests_run += 1
        print(f"   Testing URL: {url}")
        print(f"   Credentials: {login_data}")
        
        try:
            response = requests.post(url, json=login_data, headers=headers, timeout=30)
            
            print(f"   Status Code: {response.status_code}")
            print(f"   Response Headers: {dict(response.headers)}")
            
            # Capture exact error response for 500 errors
            if response.status_code == 500:
                print("🚨 CRITICAL: HTTP 500 Internal Server Error detected!")
                try:
                    error_data = response.json()
                    print(f"   Error JSON: {error_data}")
                except:
                    print(f"   Error Text: {response.text}")
                    print(f"   Raw Response: {response.content}")
                
                # Check response headers for clues
                content_type = response.headers.get('content-type', '')
                server = response.headers.get('server', '')
                print(f"   Content-Type: {content_type}")
                print(f"   Server: {server}")
                
                return False
            
            try:
                response_data = response.json()
                print(f"   Response Body: {response_data}")
            except:
                print(f"   Response Text: {response.text}")
                response_data = {}
            
            if response.status_code == 200:
                self.tests_passed += 1
                print("✅ Production login successful")
                
                if 'access_token' in response_data:
                    self.token = response_data['access_token']
                    print(f"   ✅ Token received: {self.token[:50]}...")
                    return True
                else:
                    print("   ❌ No access_token in successful response")
                    return False
            else:
                print(f"❌ Production login failed with status {response.status_code}")
                return False
                
        except requests.exceptions.ConnectionError as e:
            print(f"❌ Connection Error: {e}")
            print("   → Backend server may be down or unreachable")
            return False
        except requests.exceptions.Timeout as e:
            print(f"❌ Timeout Error: {e}")
            print("   → Backend server not responding within 30 seconds")
            return False
        except Exception as e:
            print(f"❌ Unexpected Error: {e}")
            return False

    def test_production_public_settings(self):
        """Test the production public settings endpoint"""
        print("\n🔍 PRODUCTION PUBLIC SETTINGS TEST")
        print("-" * 40)
        
        url = f"{self.api_url}/settings/public"
        
        self.tests_run += 1
        print(f"   Testing URL: {url}")
        
        try:
            response = requests.get(url, timeout=30)
            
            print(f"   Status Code: {response.status_code}")
            
            if response.status_code == 500:
                print("🚨 CRITICAL: Public settings endpoint returning HTTP 500!")
                try:
                    error_data = response.json()
                    print(f"   Error JSON: {error_data}")
                except:
                    print(f"   Error Text: {response.text}")
                return False
            
            if response.status_code == 200:
                self.tests_passed += 1
                print("✅ Public settings endpoint working")
                try:
                    response_data = response.json()
                    print(f"   Response: {response_data}")
                    return True
                except:
                    print(f"   Response Text: {response.text}")
                    return True
            else:
                print(f"❌ Public settings failed with status {response.status_code}")
                return False
                
        except requests.exceptions.ConnectionError as e:
            print(f"❌ Connection Error: {e}")
            return False
        except requests.exceptions.Timeout as e:
            print(f"❌ Timeout Error: {e}")
            return False
        except Exception as e:
            print(f"❌ Unexpected Error: {e}")
            return False

    def test_production_users_endpoint(self):
        """Test the production users endpoint (requires authentication)"""
        print("\n🔍 PRODUCTION USERS ENDPOINT TEST")
        print("-" * 40)
        
        # Note: This endpoint doesn't exist in the backend, but testing to see what happens
        url = f"{self.api_url}/users"
        headers = {'Content-Type': 'application/json'}
        
        if self.token:
            headers['Authorization'] = f'Bearer {self.token}'
        
        self.tests_run += 1
        print(f"   Testing URL: {url}")
        print(f"   With Auth: {'Yes' if self.token else 'No'}")
        
        try:
            response = requests.get(url, headers=headers, timeout=30)
            
            print(f"   Status Code: {response.status_code}")
            
            if response.status_code == 500:
                print("🚨 CRITICAL: Users endpoint returning HTTP 500!")
                try:
                    error_data = response.json()
                    print(f"   Error JSON: {error_data}")
                except:
                    print(f"   Error Text: {response.text}")
                return False
            
            # 404 is expected since this endpoint doesn't exist in our backend
            if response.status_code in [200, 404]:
                self.tests_passed += 1
                if response.status_code == 404:
                    print("✅ Users endpoint returns 404 (expected - endpoint doesn't exist)")
                else:
                    print("✅ Users endpoint working")
                    try:
                        response_data = response.json()
                        print(f"   Response: {response_data}")
                    except:
                        print(f"   Response Text: {response.text}")
                return True
            else:
                print(f"❌ Users endpoint failed with status {response.status_code}")
                return False
                
        except requests.exceptions.ConnectionError as e:
            print(f"❌ Connection Error: {e}")
            return False
        except requests.exceptions.Timeout as e:
            print(f"❌ Timeout Error: {e}")
            return False
        except Exception as e:
            print(f"❌ Unexpected Error: {e}")
            return False

    def test_production_articles_endpoint(self):
        """Test the production articles endpoint"""
        print("\n🔍 PRODUCTION ARTICLES ENDPOINT TEST")
        print("-" * 40)
        
        url = f"{self.api_url}/articles"
        
        self.tests_run += 1
        print(f"   Testing URL: {url}")
        
        try:
            response = requests.get(url, timeout=30)
            
            print(f"   Status Code: {response.status_code}")
            
            if response.status_code == 500:
                print("🚨 CRITICAL: Articles endpoint returning HTTP 500!")
                try:
                    error_data = response.json()
                    print(f"   Error JSON: {error_data}")
                except:
                    print(f"   Error Text: {response.text}")
                return False
            
            if response.status_code == 200:
                self.tests_passed += 1
                print("✅ Articles endpoint working")
                try:
                    response_data = response.json()
                    print(f"   Response: Found {len(response_data)} articles")
                    return True
                except:
                    print(f"   Response Text: {response.text}")
                    return True
            else:
                print(f"❌ Articles endpoint failed with status {response.status_code}")
                return False
                
        except requests.exceptions.ConnectionError as e:
            print(f"❌ Connection Error: {e}")
            return False
        except requests.exceptions.Timeout as e:
            print(f"❌ Timeout Error: {e}")
            return False
        except Exception as e:
            print(f"❌ Unexpected Error: {e}")
            return False

    def test_production_backend_health(self):
        """Test overall backend health on production domain"""
        print("\n🔍 PRODUCTION BACKEND HEALTH CHECK")
        print("-" * 40)
        
        # Test basic connectivity to the domain
        try:
            response = requests.get(self.base_url, timeout=30)
            print(f"   Domain Status: {response.status_code}")
            print(f"   Domain accessible: ✅")
        except Exception as e:
            print(f"   Domain Error: {e}")
            return False
        
        # Test if API base path responds
        try:
            api_response = requests.get(self.api_url, timeout=30)
            print(f"   API Base Status: {api_response.status_code}")
            if api_response.status_code == 404:
                print("   API Base: ✅ (404 expected for base API path)")
            elif api_response.status_code == 500:
                print("   API Base: ❌ (500 error indicates backend issues)")
                return False
        except Exception as e:
            print(f"   API Base Error: {e}")
            return False
        
        return True

    def test_backup_admin_login(self):
        """Test login with backup admin credentials"""
        print("\n🔍 BACKUP ADMIN LOGIN TEST")
        print("-" * 30)
        
        success, response = self.run_test(
            "Backup Admin Login",
            "POST",
            "auth/login",
            200,
            data={"username": "admin_backup", "password": "admin123"}
        )
        
        if success and 'access_token' in response:
            print("   ✅ Backup admin login successful")
            self.token = response['access_token']
            return True
        else:
            print("   ❌ Backup admin login failed")
            return False

    def test_login(self):
        """Test admin login"""
        success, response = self.run_test(
            "Admin Login",
            "POST",
            "auth/login",
            200,
            data={"username": "admin", "password": "admin123"}
        )
        if success and 'access_token' in response:
            self.token = response['access_token']
            print(f"   Token obtained: {self.token[:20]}...")
            return True
        return False

def main():
    print("🚀 Starting Crewkerne Gazette API Tests - PRODUCTION ISSUE INVESTIGATION")
    print("🎯 Target: https://CrewkerneGazette.co.uk")
    print("=" * 80)
    
    tester = CrewkerneGazetteAPITester()
    
    # PRODUCTION ISSUE INVESTIGATION - TOP PRIORITY
    print("\n🚨 PRODUCTION ISSUE INVESTIGATION - CrewkerneGazette.co.uk")
    print("=" * 60)
    
    # Test 1: Overall backend health
    backend_healthy = tester.test_production_backend_health()
    
    # Test 2: Specific login endpoint with admin/admin123
    login_working = tester.test_production_login_endpoint()
    
    # Test 3: Public settings endpoint (should work without auth)
    public_settings_working = tester.test_production_public_settings()
    
    # Test 4: Articles endpoint
    articles_working = tester.test_production_articles_endpoint()
    
    # Test 5: Users endpoint (mentioned in request)
    users_working = tester.test_production_users_endpoint()
    
    # Test 6: Try backup admin if main admin fails
    backup_login_working = False
    if not login_working:
        print("\n⚠️  Main admin login failed, testing backup admin...")
        backup_login_working = tester.test_backup_admin_login()
    
    # PRODUCTION DIAGNOSIS
    print("\n" + "=" * 80)
    print("🔍 PRODUCTION DIAGNOSIS SUMMARY")
    print("=" * 80)
    
    print(f"Backend Health Check: {'✅' if backend_healthy else '❌'}")
    print(f"Login Endpoint (/api/auth/login): {'✅' if login_working else '❌'}")
    print(f"Public Settings (/api/settings/public): {'✅' if public_settings_working else '❌'}")
    print(f"Articles Endpoint (/api/articles): {'✅' if articles_working else '❌'}")
    print(f"Users Endpoint (/api/users): {'✅' if users_working else '❌'}")
    print(f"Backup Admin Login: {'✅' if backup_login_working else '❌'}")
    
    # Determine the root cause
    if not backend_healthy:
        print("\n🚨 ROOT CAUSE: Backend server is completely down or unreachable")
        print("💡 RECOMMENDATION: Check server deployment and hosting configuration")
    elif not login_working and not public_settings_working and not articles_working:
        print("\n🚨 ROOT CAUSE: All API endpoints returning 500 errors")
        print("💡 RECOMMENDATION: Backend deployment issue - check server logs and database connectivity")
    elif not login_working and (public_settings_working or articles_working):
        print("\n🚨 ROOT CAUSE: Authentication-specific issue")
        print("💡 RECOMMENDATION: Check database user records and JWT configuration")
    elif login_working:
        print("\n✅ GOOD NEWS: Login is actually working on production!")
        print("💡 NOTE: User may have browser/network specific issues")
    
    # Final Results
    print("\n" + "=" * 80)
    print(f"📊 FINAL RESULTS")
    print(f"Tests Run: {tester.tests_run}")
    print(f"Tests Passed: {tester.tests_passed}")
    print(f"Tests Failed: {tester.tests_run - tester.tests_passed}")
    print(f"Success Rate: {(tester.tests_passed/tester.tests_run)*100:.1f}%")
    
    # Critical production status
    print(f"\n🎯 PRODUCTION STATUS SUMMARY:")
    print(f"   Domain Accessible: {'✅' if backend_healthy else '❌'}")
    print(f"   Login Working: {'✅' if (login_working or backup_login_working) else '❌'}")
    print(f"   API Endpoints: {'✅' if (public_settings_working and articles_working) else '❌'}")
    
    if not (login_working or backup_login_working):
        print("\n🚨 CRITICAL: Production login is completely broken!")
        return 1
    elif tester.tests_passed == tester.tests_run:
        print("\n🎉 Production backend is working correctly!")
        return 0
    else:
        print(f"\n⚠️  Production has some issues ({tester.tests_run - tester.tests_passed} failed tests)")
        return 1

if __name__ == "__main__":
    sys.exit(main())