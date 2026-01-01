#!/usr/bin/env python3
"""
Critical Fixes Backend Testing
Testing the newly implemented endpoints:
1. Edit Article Endpoint (PUT /api/articles/{id})
2. Delete Article Endpoint (DELETE /api/articles/{id})
3. Password Change Endpoint (POST /api/auth/change-password)
4. Static Meta Tags HTML (GET /api/articles/{id}/meta-html)
"""

import requests
import sys
import json
from datetime import datetime

class CriticalFixesTester:
    def __init__(self, base_url="https://viewtrends-1.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.admin_token = None
        self.user_token = None
        self.tests_run = 0
        self.tests_passed = 0
        self.test_article_id = None
        self.test_results = []

    def log_test(self, name, success, details=""):
        """Log test results"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            status = "✅ PASS"
        else:
            status = "❌ FAIL"
        
        result = f"{status} - {name}"
        if details:
            result += f" | {details}"
        
        self.test_results.append(result)
        print(result)

    def make_request(self, method, endpoint, data=None, token=None, expected_status=200):
        """Make HTTP request with proper headers"""
        url = f"{self.api_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}
        
        if token:
            headers['Authorization'] = f'Bearer {token}'
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=30)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=30)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers, timeout=30)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers, timeout=30)
            
            success = response.status_code == expected_status
            
            try:
                response_data = response.json()
            except:
                response_data = {"text": response.text}
            
            return success, response.status_code, response_data
            
        except Exception as e:
            return False, 0, {"error": str(e)}

    def test_admin_login(self):
        """Test admin login to get authentication token"""
        print("\n🔐 Testing Admin Authentication")
        print("-" * 40)
        
        success, status, response = self.make_request(
            'POST', 
            'auth/login',
            data={"username": "admin", "password": "admin123"}
        )
        
        if success and 'access_token' in response:
            self.admin_token = response['access_token']
            self.log_test("Admin Login", True, f"Token: {self.admin_token[:20]}...")
            return True
        else:
            self.log_test("Admin Login", False, f"Status: {status}, Response: {response}")
            return False

    def test_create_test_article(self):
        """Create a test article for edit/delete operations"""
        print("\n📝 Creating Test Article")
        print("-" * 30)
        
        article_data = {
            "title": "Test Article for Critical Fixes",
            "subheading": "Testing edit and delete functionality",
            "content": "This is a test article created to verify the new edit and delete endpoints work correctly.",
            "category": "news",
            "publisher_name": "The Crewkerne Gazette",
            "is_breaking": False,
            "is_published": True,
            "tags": ["test", "critical-fixes", "backend"]
        }
        
        success, status, response = self.make_request(
            'POST',
            'articles',
            data=article_data,
            token=self.admin_token,
            expected_status=200
        )
        
        if success and 'id' in response:
            self.test_article_id = response['id']
            self.log_test("Create Test Article", True, f"Article ID: {self.test_article_id}")
            return True
        else:
            self.log_test("Create Test Article", False, f"Status: {status}, Response: {response}")
            return False

    def test_edit_article_endpoint(self):
        """Test PUT /api/articles/{id} endpoint"""
        print("\n✏️ Testing Edit Article Endpoint")
        print("-" * 35)
        
        if not self.test_article_id:
            self.log_test("Edit Article - No Test Article", False, "Test article creation failed")
            return False
        
        # Test 1: Valid edit with admin permissions
        updated_data = {
            "title": "Updated Test Article Title",
            "subheading": "Updated subheading for testing",
            "content": "This article has been updated to test the PUT endpoint functionality.",
            "category": "music",  # Changed category
            "publisher_name": "The Crewkerne Gazette",
            "is_breaking": True,  # Changed to breaking news
            "is_published": True,
            "tags": ["updated", "test", "edit-endpoint"]
        }
        
        success, status, response = self.make_request(
            'PUT',
            f'articles/{self.test_article_id}',
            data=updated_data,
            token=self.admin_token,
            expected_status=200
        )
        
        if success:
            # Verify the update worked
            if (response.get('title') == updated_data['title'] and 
                response.get('category') == updated_data['category'] and
                response.get('is_breaking') == updated_data['is_breaking']):
                self.log_test("Edit Article - Valid Update", True, "All fields updated correctly")
            else:
                self.log_test("Edit Article - Valid Update", False, "Fields not updated correctly")
        else:
            self.log_test("Edit Article - Valid Update", False, f"Status: {status}, Response: {response}")
        
        # Test 2: Edit non-existent article
        success, status, response = self.make_request(
            'PUT',
            'articles/non-existent-id',
            data=updated_data,
            token=self.admin_token,
            expected_status=404
        )
        
        self.log_test("Edit Article - Non-existent ID", success, f"Status: {status}")
        
        # Test 3: Edit without authentication
        success, status, response = self.make_request(
            'PUT',
            f'articles/{self.test_article_id}',
            data=updated_data,
            token=None,
            expected_status=403
        )
        
        self.log_test("Edit Article - No Auth", success, f"Status: {status}")
        
        return True

    def test_delete_article_endpoint(self):
        """Test DELETE /api/articles/{id} endpoint"""
        print("\n🗑️ Testing Delete Article Endpoint")
        print("-" * 35)
        
        # Test 1: Delete non-existent article
        success, status, response = self.make_request(
            'DELETE',
            'articles/non-existent-id',
            token=self.admin_token,
            expected_status=404
        )
        
        self.log_test("Delete Article - Non-existent ID", success, f"Status: {status}")
        
        # Test 2: Delete without authentication
        if self.test_article_id:
            success, status, response = self.make_request(
                'DELETE',
                f'articles/{self.test_article_id}',
                token=None,
                expected_status=403
            )
            
            self.log_test("Delete Article - No Auth", success, f"Status: {status}")
        
        # Test 3: Valid delete with admin permissions
        if self.test_article_id:
            success, status, response = self.make_request(
                'DELETE',
                f'articles/{self.test_article_id}',
                token=self.admin_token,
                expected_status=200
            )
            
            if success and response.get('message') == "Article deleted successfully":
                self.log_test("Delete Article - Valid Delete", True, "Article deleted successfully")
                
                # Verify article is actually deleted
                success, status, response = self.make_request(
                    'GET',
                    f'articles/{self.test_article_id}',
                    expected_status=404
                )
                
                self.log_test("Delete Article - Verify Deletion", success, f"Article no longer exists (404)")
                self.test_article_id = None  # Clear the ID since article is deleted
            else:
                self.log_test("Delete Article - Valid Delete", False, f"Status: {status}, Response: {response}")
        
        return True

    def test_password_change_endpoint(self):
        """Test POST /api/auth/change-password endpoint"""
        print("\n🔑 Testing Password Change Endpoint")
        print("-" * 38)
        
        # Test 1: Valid password change
        password_data = {
            "current_password": "admin123",
            "new_password": "newpassword123"
        }
        
        success, status, response = self.make_request(
            'POST',
            'auth/change-password',
            data=password_data,
            token=self.admin_token,
            expected_status=200
        )
        
        if success and response.get('message') == "Password changed successfully":
            self.log_test("Password Change - Valid Change", True, "Password updated successfully")
            
            # Test 2: Verify new password works by logging in
            success, status, response = self.make_request(
                'POST',
                'auth/login',
                data={"username": "admin", "password": "newpassword123"},
                expected_status=200
            )
            
            if success and 'access_token' in response:
                self.log_test("Password Change - New Password Login", True, "New password works")
                self.admin_token = response['access_token']  # Update token
                
                # Change password back to original
                password_data = {
                    "current_password": "newpassword123",
                    "new_password": "admin123"
                }
                
                success, status, response = self.make_request(
                    'POST',
                    'auth/change-password',
                    data=password_data,
                    token=self.admin_token,
                    expected_status=200
                )
                
                self.log_test("Password Change - Revert Password", success, "Password reverted to original")
            else:
                self.log_test("Password Change - New Password Login", False, f"Status: {status}")
        else:
            self.log_test("Password Change - Valid Change", False, f"Status: {status}, Response: {response}")
        
        # Test 3: Invalid current password
        password_data = {
            "current_password": "wrongpassword",
            "new_password": "newpassword123"
        }
        
        success, status, response = self.make_request(
            'POST',
            'auth/change-password',
            data=password_data,
            token=self.admin_token,
            expected_status=400
        )
        
        self.log_test("Password Change - Wrong Current Password", success, f"Status: {status}")
        
        # Test 4: No authentication
        success, status, response = self.make_request(
            'POST',
            'auth/change-password',
            data={"current_password": "admin123", "new_password": "newpassword123"},
            token=None,
            expected_status=403
        )
        
        self.log_test("Password Change - No Auth", success, f"Status: {status}")
        
        return True

    def test_meta_html_endpoint(self):
        """Test GET /api/articles/{id}/meta-html endpoint"""
        print("\n🏷️ Testing Static Meta Tags HTML Endpoint")
        print("-" * 45)
        
        # First, create a test article for meta testing
        article_data = {
            "title": "Meta Tags Test Article",
            "subheading": "Testing social sharing meta tags",
            "content": "This article is used to test the meta tags HTML generation for social sharing crawlers.",
            "category": "news",
            "publisher_name": "The Crewkerne Gazette",
            "is_breaking": False,
            "is_published": True,
            "tags": ["meta", "social-sharing", "seo"]
        }
        
        success, status, response = self.make_request(
            'POST',
            'articles',
            data=article_data,
            token=self.admin_token,
            expected_status=200
        )
        
        if success and 'id' in response:
            meta_article_id = response['id']
            self.log_test("Create Meta Test Article", True, f"Article ID: {meta_article_id}")
            
            # Test 1: Valid meta HTML generation
            try:
                url = f"{self.api_url}/articles/{meta_article_id}/meta-html"
                response = requests.get(url, timeout=30)
                
                if response.status_code == 200:
                    html_content = response.text
                    
                    # Check for essential meta tags
                    required_tags = [
                        '<title>Meta Tags Test Article | The Crewkerne Gazette</title>',
                        'property="og:title"',
                        'property="og:description"',
                        'property="og:type" content="article"',
                        'name="twitter:card"',
                        'application/ld+json',
                        '"@type": "NewsArticle"'
                    ]
                    
                    missing_tags = []
                    for tag in required_tags:
                        if tag not in html_content:
                            missing_tags.append(tag)
                    
                    if not missing_tags:
                        self.log_test("Meta HTML - Valid Generation", True, "All required meta tags present")
                    else:
                        self.log_test("Meta HTML - Valid Generation", False, f"Missing tags: {missing_tags}")
                else:
                    self.log_test("Meta HTML - Valid Generation", False, f"Status: {response.status_code}")
                    
            except Exception as e:
                self.log_test("Meta HTML - Valid Generation", False, f"Error: {str(e)}")
            
            # Test 2: Non-existent article
            try:
                url = f"{self.api_url}/articles/non-existent-id/meta-html"
                response = requests.get(url, timeout=30)
                
                success = response.status_code == 404
                self.log_test("Meta HTML - Non-existent Article", success, f"Status: {response.status_code}")
                
            except Exception as e:
                self.log_test("Meta HTML - Non-existent Article", False, f"Error: {str(e)}")
            
            # Clean up meta test article
            success, status, response = self.make_request(
                'DELETE',
                f'articles/{meta_article_id}',
                token=self.admin_token,
                expected_status=200
            )
            
            self.log_test("Cleanup Meta Test Article", success, "Test article removed")
        else:
            self.log_test("Create Meta Test Article", False, f"Status: {status}")
        
        return True

    def test_existing_functionality(self):
        """Test that existing functionality still works"""
        print("\n🔄 Testing Existing Functionality")
        print("-" * 35)
        
        # Test articles list
        success, status, response = self.make_request(
            'GET',
            'articles',
            expected_status=200
        )
        
        if success and isinstance(response, list):
            self.log_test("Existing - Articles List", True, f"Found {len(response)} articles")
        else:
            self.log_test("Existing - Articles List", False, f"Status: {status}")
        
        # Test public settings
        success, status, response = self.make_request(
            'GET',
            'settings/public',
            expected_status=200
        )
        
        if success and 'show_breaking_news_banner' in response:
            self.log_test("Existing - Public Settings", True, "Settings accessible")
        else:
            self.log_test("Existing - Public Settings", False, f"Status: {status}")
        
        # Test admin settings
        success, status, response = self.make_request(
            'GET',
            'settings',
            token=self.admin_token,
            expected_status=200
        )
        
        if success:
            self.log_test("Existing - Admin Settings", True, "Admin settings accessible")
        else:
            self.log_test("Existing - Admin Settings", False, f"Status: {status}")
        
        return True

    def run_all_tests(self):
        """Run all critical fixes tests"""
        print("🚀 Starting Critical Fixes Backend Testing")
        print("🎯 Testing New Endpoints: Edit, Delete, Password Change, Meta HTML")
        print("=" * 80)
        
        # Step 1: Authentication
        if not self.test_admin_login():
            print("❌ Cannot proceed without admin authentication")
            return False
        
        # Step 2: Create test article
        self.test_create_test_article()
        
        # Step 3: Test new endpoints
        self.test_edit_article_endpoint()
        self.test_delete_article_endpoint()
        self.test_password_change_endpoint()
        self.test_meta_html_endpoint()
        
        # Step 4: Test existing functionality
        self.test_existing_functionality()
        
        # Results summary
        print("\n" + "=" * 80)
        print("📊 CRITICAL FIXES TEST RESULTS")
        print("=" * 80)
        
        for result in self.test_results:
            print(result)
        
        print(f"\n📈 SUMMARY:")
        print(f"   Tests Run: {self.tests_run}")
        print(f"   Tests Passed: {self.tests_passed}")
        print(f"   Tests Failed: {self.tests_run - self.tests_passed}")
        print(f"   Success Rate: {(self.tests_passed/self.tests_run)*100:.1f}%")
        
        # Critical assessment
        critical_endpoints = [
            "Edit Article - Valid Update",
            "Delete Article - Valid Delete", 
            "Password Change - Valid Change",
            "Meta HTML - Valid Generation"
        ]
        
        critical_passed = sum(1 for result in self.test_results if any(endpoint in result for endpoint in critical_endpoints) and "✅ PASS" in result)
        
        print(f"\n🎯 CRITICAL ENDPOINTS STATUS:")
        print(f"   Critical Tests Passed: {critical_passed}/{len(critical_endpoints)}")
        
        if critical_passed == len(critical_endpoints):
            print("✅ ALL CRITICAL FIXES WORKING CORRECTLY")
            return True
        else:
            print("❌ SOME CRITICAL FIXES HAVE ISSUES")
            return False

def main():
    tester = CriticalFixesTester()
    success = tester.run_all_tests()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())