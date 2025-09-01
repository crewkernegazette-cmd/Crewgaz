#!/usr/bin/env python3
"""
Comprehensive Article Endpoints Testing for The Crewkerne Gazette
Focused on the specific requirements from the review request:

1. Article Listing Endpoint: GET /api/articles
2. Individual Article Endpoint: GET /api/articles/{slug}  
3. Article Creation: POST /api/articles.json
4. Article Not Found: GET /api/articles/non-existent-slug (404)
5. Database Connectivity: PostgreSQL verification
"""

import requests
import json
import sys
from datetime import datetime
import uuid

class ComprehensiveArticleTester:
    def __init__(self, base_url="https://article-repair.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.token = None
        self.tests_run = 0
        self.tests_passed = 0
        self.created_articles = []
        self.test_results = []
        
    def log_test(self, name, success, details="", critical=False):
        """Log test results with criticality marking"""
        self.tests_run += 1
        status = "✅ PASS" if success else "❌ FAIL"
        priority = "🔴 CRITICAL" if critical and not success else ""
        
        result = {
            "name": name,
            "success": success,
            "details": details,
            "critical": critical
        }
        self.test_results.append(result)
        
        if success:
            self.tests_passed += 1
            print(f"{status} {name}")
        else:
            print(f"{status} {priority} {name}")
        
        if details:
            print(f"   {details}")
        return success
    
    def make_request(self, method, endpoint, data=None, expected_status=200, auth_required=True):
        """Make HTTP request with proper error handling"""
        url = f"{self.api_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}
        
        if auth_required and self.token:
            headers['Authorization'] = f'Bearer {self.token}'
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=30)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=30)
            
            success = response.status_code == expected_status
            
            try:
                response_data = response.json()
            except:
                response_data = {"text": response.text}
            
            return success, response.status_code, response_data
            
        except Exception as e:
            return False, 0, {"error": f"Request error: {str(e)}"}
    
    def test_admin_authentication(self):
        """Test admin authentication as specified in review request"""
        print("\n🔐 REQUIREMENT 1: Admin Authentication (admin/admin123)")
        print("-" * 60)
        
        success, status, response = self.make_request(
            'POST', 
            'auth/login',
            data={"username": "admin", "password": "admin123"},
            expected_status=200,
            auth_required=False
        )
        
        if success and 'access_token' in response:
            self.token = response['access_token']
            return self.log_test(
                "Admin Authentication", 
                True, 
                f"Successfully authenticated with admin/admin123, Role: {response.get('role', 'unknown')}",
                critical=True
            )
        else:
            return self.log_test(
                "Admin Authentication", 
                False, 
                f"Failed to authenticate: Status {status}, Response: {response}",
                critical=True
            )
    
    def test_article_listing_endpoint(self):
        """REQUIREMENT 1: Test GET /api/articles - Article listing endpoint"""
        print("\n📰 REQUIREMENT 1: Article Listing Endpoint (GET /api/articles)")
        print("-" * 60)
        
        success, status, response = self.make_request(
            'GET', 
            'articles',
            expected_status=200,
            auth_required=False
        )
        
        if success:
            articles = response if isinstance(response, list) else []
            
            # Verify JSON structure includes all required fields
            required_fields = ['id', 'uuid', 'slug', 'title', 'content', 'category', 'created_at']
            
            if articles and len(articles) > 0:
                article = articles[0]
                missing_fields = [field for field in required_fields if field not in article]
                
                if missing_fields:
                    details = f"Found {len(articles)} articles but missing required fields: {missing_fields}"
                    success = False
                else:
                    # Check for additional fields mentioned in review
                    additional_fields = ['subheading', 'publisher_name', 'author_name', 'tags', 'is_breaking']
                    present_additional = [field for field in additional_fields if field in article]
                    details = f"Found {len(articles)} articles with all required fields. Additional fields present: {present_additional}"
            else:
                details = "Endpoint accessible but no articles found (empty database)"
            
            return self.log_test(
                "Article Listing Endpoint", 
                success, 
                details,
                critical=True
            )
        else:
            return self.log_test(
                "Article Listing Endpoint", 
                False, 
                f"Failed: Status {status}, Error: {response}",
                critical=True
            )
    
    def test_article_creation(self):
        """REQUIREMENT 3: Test POST /api/articles.json - Article creation"""
        print("\n✍️ REQUIREMENT 3: Article Creation (POST /api/articles.json)")
        print("-" * 60)
        
        if not self.token:
            return self.log_test(
                "Article Creation", 
                False, 
                "Cannot test - no authentication token available",
                critical=True
            )
        
        # Create comprehensive test article with all fields
        test_article = {
            "title": f"Comprehensive Test Article {datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "subheading": "Testing article creation with all fields for frontend path verification",
            "content": "<p>This comprehensive test article verifies that the backend can create articles with all required fields.</p><p>The article should be accessible via both the listing endpoint and individual article endpoint using the correct slug format.</p><p>Created at: " + datetime.now().isoformat() + "</p>",
            "category": "news",
            "publisher_name": "The Crewkerne Gazette",
            "tags": ["test", "api", "verification", "frontend-fix"],
            "category_labels": ["News", "Tech"],
            "is_breaking": False,
            "is_published": True,
            "pin": False,
            "priority": 5
        }
        
        success, status, response = self.make_request(
            'POST', 
            'articles.json',
            data=test_article,
            expected_status=200,
            auth_required=True
        )
        
        if success:
            # Verify all fields are present in response
            required_response_fields = ['id', 'uuid', 'slug', 'title', 'content', 'category']
            missing_fields = [field for field in required_response_fields if field not in response]
            
            if missing_fields:
                details = f"Article created but response missing fields: {missing_fields}"
                success = False
            else:
                # Store for further testing
                self.created_articles.append({
                    'id': response.get('id'),
                    'slug': response.get('slug'),
                    'title': response.get('title'),
                    'uuid': response.get('uuid')
                })
                details = f"Article '{response.get('title')}' created successfully. Slug: '{response.get('slug')}', UUID: {response.get('uuid')}"
            
            return self.log_test(
                "Article Creation", 
                success, 
                details,
                critical=True
            )
        else:
            return self.log_test(
                "Article Creation", 
                False, 
                f"Failed: Status {status}, Error: {response}",
                critical=True
            )
    
    def test_individual_article_endpoint(self):
        """REQUIREMENT 2: Test GET /api/articles/{slug} - Individual article endpoint"""
        print("\n📄 REQUIREMENT 2: Individual Article Endpoint (GET /api/articles/{slug})")
        print("-" * 60)
        
        # Use created article if available, otherwise try to get from listing
        test_slug = None
        test_title = None
        
        if self.created_articles:
            test_slug = self.created_articles[0]['slug']
            test_title = self.created_articles[0]['title']
        else:
            # Try to get from article listing
            success, status, response = self.make_request(
                'GET', 
                'articles?limit=1',
                expected_status=200,
                auth_required=False
            )
            
            if success and response and len(response) > 0:
                test_slug = response[0].get('slug')
                test_title = response[0].get('title')
        
        if not test_slug:
            return self.log_test(
                "Individual Article Endpoint", 
                False, 
                "No articles available to test individual article endpoint",
                critical=True
            )
        
        # Test individual article retrieval
        success, status, response = self.make_request(
            'GET', 
            f'articles/{test_slug}',
            expected_status=200,
            auth_required=False
        )
        
        if success:
            # Verify all required fields are present in proper JSON format
            required_fields = ['id', 'uuid', 'slug', 'title', 'content', 'category', 'created_at']
            missing_fields = [field for field in required_fields if field not in response]
            
            if missing_fields:
                details = f"Article retrieved but missing required fields: {missing_fields}"
                success = False
            else:
                # Verify slug matches and data integrity
                if response.get('slug') == test_slug:
                    details = f"Article '{response.get('title')}' successfully retrieved via slug '{test_slug}'. All required fields present in JSON format."
                else:
                    details = f"Data integrity issue: Expected slug '{test_slug}', got '{response.get('slug')}'"
                    success = False
            
            return self.log_test(
                "Individual Article Endpoint", 
                success, 
                details,
                critical=True
            )
        else:
            return self.log_test(
                "Individual Article Endpoint", 
                False, 
                f"Failed to retrieve article with slug '{test_slug}': Status {status}, Error: {response}",
                critical=True
            )
    
    def test_article_not_found(self):
        """REQUIREMENT 4: Test GET /api/articles/non-existent-slug - 404 handling"""
        print("\n🚫 REQUIREMENT 4: Article Not Found (GET /api/articles/non-existent-slug)")
        print("-" * 60)
        
        non_existent_slug = f"non-existent-article-{uuid.uuid4().hex[:8]}"
        
        success, status, response = self.make_request(
            'GET', 
            f'articles/{non_existent_slug}',
            expected_status=404,
            auth_required=False
        )
        
        if success:
            details = f"Correctly returned 404 for non-existent slug '{non_existent_slug}'"
        else:
            details = f"Expected 404 for non-existent slug '{non_existent_slug}', got {status}: {response}"
        
        return self.log_test(
            "Article Not Found (404)", 
            success, 
            details,
            critical=True
        )
    
    def test_database_connectivity(self):
        """REQUIREMENT 5: Verify PostgreSQL database connectivity and data persistence"""
        print("\n🗄️ REQUIREMENT 5: Database Connectivity (PostgreSQL)")
        print("-" * 60)
        
        connectivity_tests = []
        overall_success = True
        
        # Test 1: Check debug endpoint for database status
        success1, status1, response1 = self.make_request(
            'GET', 
            'debug/auth',
            expected_status=200,
            auth_required=False
        )
        
        if success1 and isinstance(response1, dict):
            db_connected = response1.get('db_connected', False)
            total_users = response1.get('total_users', 0)
            connectivity_tests.append(f"✅ Debug endpoint reports DB connected: {db_connected}, Users: {total_users}")
            if not db_connected:
                overall_success = False
        else:
            connectivity_tests.append("❌ Debug auth endpoint not accessible")
            overall_success = False
        
        # Test 2: Verify articles are being stored and retrieved (data persistence)
        if self.created_articles:
            test_article = self.created_articles[0]
            success2, status2, response2 = self.make_request(
                'GET', 
                f'articles/{test_article["slug"]}',
                expected_status=200,
                auth_required=False
            )
            
            if success2:
                # Verify data integrity
                if (response2.get('title') == test_article['title'] and 
                    response2.get('uuid') == test_article['uuid']):
                    connectivity_tests.append("✅ Data persistence verified - created article matches retrieved data")
                else:
                    connectivity_tests.append("❌ Data integrity issue - created article data doesn't match retrieved data")
                    overall_success = False
            else:
                connectivity_tests.append("❌ Cannot retrieve created article - database read issue")
                overall_success = False
        
        # Test 3: Test article listing (database read operations)
        success3, status3, response3 = self.make_request(
            'GET', 
            'articles',
            expected_status=200,
            auth_required=False
        )
        
        if success3:
            articles_count = len(response3) if isinstance(response3, list) else 0
            connectivity_tests.append(f"✅ Article listing accessible - {articles_count} articles in database")
        else:
            connectivity_tests.append("❌ Article listing not accessible - database connection issue")
            overall_success = False
        
        return self.log_test(
            "Database Connectivity", 
            overall_success, 
            " | ".join(connectivity_tests),
            critical=True
        )
    
    def test_frontend_path_compatibility(self):
        """Verify that the backend endpoints work with the corrected frontend paths"""
        print("\n🔗 FRONTEND PATH COMPATIBILITY: Verify corrected paths work")
        print("-" * 60)
        
        if not self.created_articles:
            return self.log_test(
                "Frontend Path Compatibility", 
                False, 
                "No created articles to test path compatibility"
            )
        
        test_article = self.created_articles[0]
        test_slug = test_article['slug']
        
        # Test the corrected path: /api/articles/{slug} (plural, with /api prefix)
        success, status, response = self.make_request(
            'GET', 
            f'articles/{test_slug}',  # This is the corrected path
            expected_status=200,
            auth_required=False
        )
        
        if success:
            details = f"✅ Corrected frontend path '/api/articles/{test_slug}' works correctly. Article data retrieved successfully."
        else:
            details = f"❌ Corrected frontend path '/api/articles/{test_slug}' failed: Status {status}"
        
        return self.log_test(
            "Frontend Path Compatibility", 
            success, 
            details,
            critical=True
        )
    
    def run_comprehensive_tests(self):
        """Run all comprehensive tests as specified in review request"""
        print("🚀 COMPREHENSIVE ARTICLE ENDPOINTS TESTING")
        print("🎯 Verifying backend functionality for frontend article fetch path correction")
        print("=" * 80)
        
        # Authentication (required for some tests)
        auth_success = self.test_admin_authentication()
        
        # Core requirements from review request
        self.test_article_listing_endpoint()
        
        # Article creation (requires auth)
        if auth_success:
            self.test_article_creation()
        
        # Individual article endpoint (uses created article if available)
        self.test_individual_article_endpoint()
        
        # Error handling
        self.test_article_not_found()
        
        # Database connectivity
        self.test_database_connectivity()
        
        # Frontend compatibility
        self.test_frontend_path_compatibility()
        
        # Print comprehensive summary
        self.print_comprehensive_summary()
    
    def print_comprehensive_summary(self):
        """Print comprehensive test summary"""
        print("\n" + "=" * 80)
        print("📊 COMPREHENSIVE TEST SUMMARY")
        print("=" * 80)
        
        success_rate = (self.tests_passed / self.tests_run * 100) if self.tests_run > 0 else 0
        
        print(f"Total Tests Run: {self.tests_run}")
        print(f"Tests Passed: {self.tests_passed}")
        print(f"Tests Failed: {self.tests_run - self.tests_passed}")
        print(f"Success Rate: {success_rate:.1f}%")
        
        # Critical tests analysis
        critical_tests = [r for r in self.test_results if r['critical']]
        critical_passed = len([r for r in critical_tests if r['success']])
        critical_total = len(critical_tests)
        
        print(f"\nCritical Tests: {critical_passed}/{critical_total} passed")
        
        # Failed tests details
        failed_tests = [r for r in self.test_results if not r['success']]
        if failed_tests:
            print(f"\n❌ FAILED TESTS:")
            for test in failed_tests:
                priority = "🔴 CRITICAL" if test['critical'] else "⚠️ "
                print(f"   {priority} {test['name']}: {test['details']}")
        
        # Article creation summary
        if self.created_articles:
            print(f"\n📝 CREATED ARTICLES: {len(self.created_articles)}")
            for article in self.created_articles:
                print(f"   - {article['title']} (slug: {article['slug']})")
        
        # Final verdict
        print(f"\n🎯 ARTICLE ACCESS FIX VERIFICATION:")
        if success_rate >= 85 and critical_passed == critical_total:
            print("✅ BACKEND ARTICLE ENDPOINTS ARE WORKING CORRECTLY")
            print("✅ Frontend article fetch path correction should resolve user 'article not found' errors")
            print("✅ All required JSON fields are present in API responses")
            print("✅ Database connectivity and data persistence verified")
        elif success_rate >= 70:
            print("⚠️  BACKEND ENDPOINTS MOSTLY WORKING")
            print("⚠️  Some minor issues detected but core functionality operational")
            print("⚠️  Frontend path correction should help but monitor for remaining issues")
        else:
            print("❌ BACKEND ENDPOINTS HAVE SIGNIFICANT ISSUES")
            print("❌ Frontend path correction alone will not resolve all user issues")
            print("❌ Backend problems need to be addressed before frontend fixes will be effective")
        
        return success_rate >= 85 and critical_passed == critical_total

def main():
    """Main test execution"""
    tester = ComprehensiveArticleTester()
    success = tester.run_comprehensive_tests()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())