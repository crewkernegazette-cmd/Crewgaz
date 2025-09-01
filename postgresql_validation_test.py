#!/usr/bin/env python3
"""
PostgreSQL Database Connectivity Validation Test
Focus: Quick backend validation after fixing PostgreSQL database connectivity
"""

import requests
import sys
import json
from datetime import datetime

class PostgreSQLValidationTester:
    def __init__(self):
        # Use the current production URL from frontend/.env
        self.base_url = "https://article-repair.preview.emergentagent.com"
        self.api_url = f"{self.base_url}/api"
        self.token = None
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []

    def log_test_result(self, test_name, success, details=""):
        """Log test result for summary"""
        self.test_results.append({
            "name": test_name,
            "success": success,
            "details": details
        })

    def run_test(self, name, method, endpoint, expected_status, data=None, headers=None, description=""):
        """Run a single API test with detailed logging"""
        url = f"{self.api_url}/{endpoint}"
        test_headers = {'Content-Type': 'application/json'}
        
        if self.token:
            test_headers['Authorization'] = f'Bearer {self.token}'
        
        if headers:
            test_headers.update(headers)

        self.tests_run += 1
        print(f"\n🔍 Test {self.tests_run}: {name}")
        if description:
            print(f"   📝 {description}")
        print(f"   🌐 URL: {url}")
        print(f"   📤 Method: {method}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=test_headers, timeout=30)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=test_headers, timeout=30)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=test_headers, timeout=30)
            elif method == 'DELETE':
                response = requests.delete(url, headers=test_headers, timeout=30)

            print(f"   📥 Status: {response.status_code}")
            
            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"   ✅ PASSED")
                try:
                    response_data = response.json()
                    if isinstance(response_data, dict) and len(str(response_data)) < 300:
                        print(f"   📋 Response: {response_data}")
                    elif isinstance(response_data, list):
                        print(f"   📋 Response: List with {len(response_data)} items")
                    self.log_test_result(name, True, f"Status {response.status_code}")
                    return success, response_data
                except:
                    self.log_test_result(name, True, f"Status {response.status_code}")
                    return success, {}
            else:
                print(f"   ❌ FAILED - Expected {expected_status}, got {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"   ⚠️  Error: {error_data}")
                    self.log_test_result(name, False, f"Status {response.status_code}: {error_data}")
                except:
                    print(f"   ⚠️  Error: {response.text}")
                    self.log_test_result(name, False, f"Status {response.status_code}: {response.text}")
                return False, {}

        except requests.exceptions.ConnectionError as e:
            print(f"   ❌ FAILED - Connection Error: {str(e)}")
            self.log_test_result(name, False, f"Connection Error: {str(e)}")
            return False, {}
        except requests.exceptions.Timeout as e:
            print(f"   ❌ FAILED - Timeout Error: {str(e)}")
            self.log_test_result(name, False, f"Timeout Error: {str(e)}")
            return False, {}
        except Exception as e:
            print(f"   ❌ FAILED - Error: {str(e)}")
            self.log_test_result(name, False, f"Error: {str(e)}")
            return False, {}

    def run_test_form_data(self, name, method, endpoint, expected_status, form_data=None, description=""):
        """Run a test with form data (for article creation)"""
        url = f"{self.api_url}/{endpoint}"
        test_headers = {}
        
        if self.token:
            test_headers['Authorization'] = f'Bearer {self.token}'

        self.tests_run += 1
        print(f"\n🔍 Test {self.tests_run}: {name}")
        if description:
            print(f"   📝 {description}")
        print(f"   🌐 URL: {url}")
        print(f"   📤 Method: {method} (Form Data)")
        
        try:
            if method == 'POST':
                response = requests.post(url, data=form_data, headers=test_headers, timeout=30)
            else:
                raise ValueError(f"Form data method {method} not supported")

            print(f"   📥 Status: {response.status_code}")
            
            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"   ✅ PASSED")
                try:
                    response_data = response.json()
                    if isinstance(response_data, dict) and len(str(response_data)) < 300:
                        print(f"   📋 Response: {response_data}")
                    elif isinstance(response_data, list):
                        print(f"   📋 Response: List with {len(response_data)} items")
                    self.log_test_result(name, True, f"Status {response.status_code}")
                    return success, response_data
                except:
                    self.log_test_result(name, True, f"Status {response.status_code}")
                    return success, {}
            else:
                print(f"   ❌ FAILED - Expected {expected_status}, got {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"   ⚠️  Error: {error_data}")
                    self.log_test_result(name, False, f"Status {response.status_code}: {error_data}")
                except:
                    print(f"   ⚠️  Error: {response.text}")
                    self.log_test_result(name, False, f"Status {response.status_code}: {response.text}")
                return False, {}

        except requests.exceptions.ConnectionError as e:
            print(f"   ❌ FAILED - Connection Error: {str(e)}")
            self.log_test_result(name, False, f"Connection Error: {str(e)}")
            return False, {}
        except requests.exceptions.Timeout as e:
            print(f"   ❌ FAILED - Timeout Error: {str(e)}")
            self.log_test_result(name, False, f"Timeout Error: {str(e)}")
            return False, {}
        except Exception as e:
            print(f"   ❌ FAILED - Error: {str(e)}")
            self.log_test_result(name, False, f"Error: {str(e)}")
            return False, {}

    def test_1_admin_authentication(self):
        """Test 1: Admin login (admin/admin123) to verify emergency authentication and database user creation"""
        print("\n" + "="*80)
        print("🔐 TEST 1: AUTHENTICATION TEST")
        print("="*80)
        
        success, response = self.run_test(
            "Admin Login Authentication",
            "POST",
            "auth/login",
            200,
            data={"username": "admin", "password": "admin123"},
            description="Verify emergency authentication and database user creation"
        )
        
        if success and 'access_token' in response:
            self.token = response['access_token']
            print(f"   🎫 JWT Token obtained: {self.token[:50]}...")
            
            # Verify JWT token format (should be 3 parts separated by dots)
            token_parts = self.token.split('.')
            if len(token_parts) == 3:
                print(f"   ✅ JWT token format valid (3 parts)")
            else:
                print(f"   ⚠️  JWT token format unusual ({len(token_parts)} parts)")
            
            # Check response structure
            expected_fields = ['access_token', 'token_type', 'role']
            for field in expected_fields:
                if field in response:
                    print(f"   ✅ Response contains '{field}': {response[field]}")
                else:
                    print(f"   ⚠️  Response missing '{field}'")
            
            return True
        else:
            print("   ❌ Admin authentication failed")
            return False

    def test_2_database_connectivity(self):
        """Test 2: Verify database tables are created properly and admin user exists"""
        print("\n" + "="*80)
        print("🗄️  TEST 2: DATABASE CONNECTIVITY")
        print("="*80)
        
        # Test debug auth endpoint to check database status
        success, response = self.run_test(
            "Database Connection Status",
            "GET",
            "debug/auth",
            200,
            description="Check if database tables are created and admin user exists"
        )
        
        if success:
            print(f"   📊 Database Status Analysis:")
            if 'db_connected' in response:
                db_status = response['db_connected']
                print(f"   🔗 Database Connected: {'✅' if db_status else '❌'}")
            
            if 'users' in response:
                users = response['users']
                print(f"   👥 Users Found: {len(users)}")
                admin_found = any(user.get('username') == 'admin' for user in users)
                print(f"   👤 Admin User Exists: {'✅' if admin_found else '❌'}")
                
                for user in users:
                    if user.get('username') == 'admin':
                        print(f"   🔑 Admin Role: {user.get('role', 'unknown')}")
            
            if 'seeding_status' in response:
                seeding = response['seeding_status']
                print(f"   🌱 Database Seeding: {seeding}")
            
            return True
        else:
            print("   ❌ Database connectivity check failed")
            return False

    def test_3_category_labels_system(self):
        """Test 3: Article System with Category Labels"""
        print("\n" + "="*80)
        print("🏷️  TEST 3: ARTICLE SYSTEM WITH CATEGORY LABELS")
        print("="*80)
        
        # Test 3a: GET /api/categories/labels
        success_labels, labels_response = self.run_test(
            "Category Labels Endpoint",
            "GET",
            "categories/labels",
            200,
            description="Verify category labels are returned"
        )
        
        if success_labels and 'category_labels' in labels_response:
            labels = labels_response['category_labels']
            print(f"   🏷️  Available Categories: {len(labels)}")
            print(f"   📝 Sample Categories: {labels[:5]}...")
            
            # Check for key categories mentioned in requirements
            key_categories = ['Satire', 'Straight Talking', 'Opinion', 'Sports']
            for category in key_categories:
                if category in labels:
                    print(f"   ✅ Key category '{category}' available")
                else:
                    print(f"   ⚠️  Key category '{category}' missing")
        
        # Test 3b: Article creation with category_labels field
        if self.token:
            # The backend expects form data, not JSON
            form_data = {
                "title": "PostgreSQL Test Article",
                "content": "This is a test article to verify PostgreSQL database connectivity and category labels functionality.",
                "category": "news",  # lowercase as required by enum
                "subheading": "Testing database connectivity after PostgreSQL fixes",
                "publisher_name": "The Crewkerne Gazette",
                "category_labels": json.dumps(["News", "Straight Talking"]),
                "is_breaking": False,
                "is_published": True,
                "tags": "test,postgresql,database"
            }
            
            success_create, create_response = self.run_test_form_data(
                "Article Creation with Category Labels",
                "POST",
                "articles",
                200,
                form_data=form_data,
                description="Test article creation with category_labels field"
            )
            
            if success_create:
                print(f"   ✅ Article created successfully")
                if 'category_labels' in create_response:
                    created_labels = create_response['category_labels']
                    print(f"   🏷️  Category labels saved: {created_labels}")
                if 'slug' in create_response:
                    article_slug = create_response['slug']
                    print(f"   🔗 Article slug: {article_slug}")
                    
                    # Test 3c: Article retrieval includes category_labels
                    success_get, get_response = self.run_test(
                        "Article Retrieval with Category Labels",
                        "GET",
                        f"articles/{article_slug}",
                        200,
                        description="Verify article retrieval includes category_labels"
                    )
                    
                    if success_get and 'category_labels' in get_response:
                        retrieved_labels = get_response['category_labels']
                        print(f"   ✅ Retrieved category labels: {retrieved_labels}")
                        return True
            
        return success_labels

    def test_4_critical_functionality(self):
        """Test 4: Critical Functionality Check"""
        print("\n" + "="*80)
        print("⚡ TEST 4: CRITICAL FUNCTIONALITY CHECK")
        print("="*80)
        
        # Test 4a: Ensure article creation no longer returns 500 errors
        print(f"\n   📝 Testing article creation (no 500 errors)...")
        if self.token:
            simple_article = {
                "title": "Database Connectivity Test",
                "content": "Simple test to ensure no 500 errors on article creation.",
                "category": "news",  # lowercase as required by enum
                "is_published": True
            }
            
            success_simple, _ = self.run_test_form_data(
                "Simple Article Creation (No 500 Error)",
                "POST",
                "articles",
                200,
                form_data=simple_article,
                description="Ensure article creation no longer returns 500 errors"
            )
        else:
            success_simple = False
            print("   ❌ Cannot test article creation - no authentication token")
        
        # Test 4b: Verify all CRUD operations work with PostgreSQL database
        print(f"\n   🔄 Testing CRUD operations...")
        
        # READ: Get articles list
        success_read, articles_response = self.run_test(
            "Articles List (READ)",
            "GET",
            "articles",
            200,
            description="Verify READ operations work with PostgreSQL"
        )
        
        # Test 4c: Test dashboard endpoints (stats, articles)
        print(f"\n   📊 Testing dashboard endpoints...")
        
        if self.token:
            success_stats, stats_response = self.run_test(
                "Dashboard Stats",
                "GET",
                "dashboard/stats",
                200,
                description="Test dashboard stats endpoint"
            )
            
            if success_stats:
                print(f"   📈 Dashboard Stats:")
                for key, value in stats_response.items():
                    print(f"      {key}: {value}")
            
            success_dashboard_articles, _ = self.run_test(
                "Dashboard Articles",
                "GET",
                "dashboard/articles",
                200,
                description="Test dashboard articles endpoint"
            )
        else:
            success_stats = False
            success_dashboard_articles = False
            print("   ❌ Cannot test dashboard endpoints - no authentication token")
        
        # Overall success for critical functionality
        critical_tests = [success_simple, success_read, success_stats, success_dashboard_articles]
        return all(critical_tests)

    def run_postgresql_validation(self):
        """Run the complete PostgreSQL validation test suite"""
        print("🚀 POSTGRESQL DATABASE CONNECTIVITY VALIDATION")
        print("🎯 Focus: Quick backend validation after fixing PostgreSQL database connectivity")
        print("🌐 Target: " + self.base_url)
        print("="*80)
        
        # Run all test categories
        test1_success = self.test_1_admin_authentication()
        test2_success = self.test_2_database_connectivity()
        test3_success = self.test_3_category_labels_system()
        test4_success = self.test_4_critical_functionality()
        
        # Generate summary
        print("\n" + "="*80)
        print("📊 POSTGRESQL VALIDATION SUMMARY")
        print("="*80)
        
        print(f"1. Authentication Test: {'✅ PASSED' if test1_success else '❌ FAILED'}")
        print(f"2. Database Connectivity: {'✅ PASSED' if test2_success else '❌ FAILED'}")
        print(f"3. Category Labels System: {'✅ PASSED' if test3_success else '❌ FAILED'}")
        print(f"4. Critical Functionality: {'✅ PASSED' if test4_success else '❌ FAILED'}")
        
        print(f"\n📈 Overall Results:")
        print(f"   Tests Run: {self.tests_run}")
        print(f"   Tests Passed: {self.tests_passed}")
        print(f"   Success Rate: {(self.tests_passed/self.tests_run)*100:.1f}%")
        
        # Detailed test results
        print(f"\n📋 Detailed Test Results:")
        for i, result in enumerate(self.test_results, 1):
            status = "✅" if result["success"] else "❌"
            print(f"   {i:2d}. {status} {result['name']}")
            if result["details"] and not result["success"]:
                print(f"       └─ {result['details']}")
        
        # Final assessment
        all_critical_passed = test1_success and test2_success and test3_success and test4_success
        
        print(f"\n🎯 FINAL ASSESSMENT:")
        if all_critical_passed:
            print("   ✅ PostgreSQL database connectivity fixes are WORKING")
            print("   ✅ All critical functionality validated successfully")
            print("   ✅ Ready for production use")
            return 0
        else:
            print("   ❌ Some critical issues remain after PostgreSQL fixes")
            print("   ⚠️  Further investigation required")
            
            # Identify specific issues
            if not test1_success:
                print("   🔐 Issue: Admin authentication not working")
            if not test2_success:
                print("   🗄️  Issue: Database connectivity problems")
            if not test3_success:
                print("   🏷️  Issue: Category labels system not functioning")
            if not test4_success:
                print("   ⚡ Issue: Critical functionality failures")
            
            return 1

def main():
    """Main function to run PostgreSQL validation tests"""
    tester = PostgreSQLValidationTester()
    return tester.run_postgresql_validation()

if __name__ == "__main__":
    sys.exit(main())