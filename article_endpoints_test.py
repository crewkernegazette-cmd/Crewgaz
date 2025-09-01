#!/usr/bin/env python3
"""
Article Endpoints Testing for The Crewkerne Gazette
Testing backend article endpoints functionality to verify the article access fix.

Focus Areas:
1. Article Listing Endpoint (GET /api/articles)
2. Individual Article Endpoint (GET /api/articles/{slug})
3. Article Creation (POST /api/articles.json)
4. Article Not Found (404 handling)
5. Database Connectivity Verification
"""

import requests
import json
import sys
from datetime import datetime
import uuid

class ArticleEndpointsTester:
    def __init__(self, base_url="https://article-repair.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.token = None
        self.tests_run = 0
        self.tests_passed = 0
        self.created_articles = []  # Track created articles for cleanup
        
    def log_test(self, name, success, details=""):
        """Log test results"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name}")
            if details:
                print(f"   {details}")
        else:
            print(f"❌ {name}")
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
            
        except requests.exceptions.ConnectionError as e:
            return False, 0, {"error": f"Connection error: {str(e)}"}
        except requests.exceptions.Timeout as e:
            return False, 0, {"error": f"Timeout error: {str(e)}"}
        except Exception as e:
            return False, 0, {"error": f"Request error: {str(e)}"}
    
    def test_admin_authentication(self):
        """Test admin authentication with admin/admin123"""
        print("\n🔐 Testing Admin Authentication")
        print("-" * 40)
        
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
                "Admin Login (admin/admin123)", 
                True, 
                f"Token obtained, Role: {response.get('role', 'unknown')}"
            )
        else:
            return self.log_test(
                "Admin Login (admin/admin123)", 
                False, 
                f"Status: {status}, Response: {response}"
            )
    
    def test_article_listing_endpoint(self):
        """Test GET /api/articles - Article listing endpoint"""
        print("\n📰 Testing Article Listing Endpoint")
        print("-" * 40)
        
        # Test basic article listing
        success, status, response = self.make_request(
            'GET', 
            'articles',
            expected_status=200,
            auth_required=False
        )
        
        if success:
            articles = response if isinstance(response, list) else []
            details = f"Found {len(articles)} articles"
            
            # Verify JSON structure
            if articles and len(articles) > 0:
                article = articles[0]
                required_fields = ['id', 'uuid', 'slug', 'title', 'content', 'category']
                missing_fields = [field for field in required_fields if field not in article]
                
                if missing_fields:
                    details += f", Missing fields: {missing_fields}"
                    success = False
                else:
                    details += f", All required fields present"
            
            return self.log_test("Article Listing Endpoint", success, details)
        else:
            return self.log_test(
                "Article Listing Endpoint", 
                False, 
                f"Status: {status}, Error: {response}"
            )
    
    def test_article_listing_with_category_filter(self):
        """Test GET /api/articles?category=news - Category filtering"""
        print("\n🏷️ Testing Article Listing with Category Filter")
        print("-" * 40)
        
        success, status, response = self.make_request(
            'GET', 
            'articles?category=news',
            expected_status=200,
            auth_required=False
        )
        
        if success:
            articles = response if isinstance(response, list) else []
            details = f"Found {len(articles)} news articles"
            
            # Verify all articles have news category
            if articles:
                non_news_articles = [a for a in articles if a.get('category', '').lower() != 'news']
                if non_news_articles:
                    details += f", {len(non_news_articles)} articles not in news category"
                    success = False
                else:
                    details += ", All articles correctly filtered by news category"
            
            return self.log_test("Article Category Filtering", success, details)
        else:
            return self.log_test(
                "Article Category Filtering", 
                False, 
                f"Status: {status}, Error: {response}"
            )
    
    def test_individual_article_endpoint(self):
        """Test GET /api/articles/{slug} - Individual article endpoint"""
        print("\n📄 Testing Individual Article Endpoint")
        print("-" * 40)
        
        # First get list of articles to find a valid slug
        success, status, response = self.make_request(
            'GET', 
            'articles?limit=5',
            expected_status=200,
            auth_required=False
        )
        
        if not success or not response:
            return self.log_test(
                "Individual Article Endpoint", 
                False, 
                "Could not get articles list to test individual article"
            )
        
        articles = response if isinstance(response, list) else []
        if not articles:
            return self.log_test(
                "Individual Article Endpoint", 
                False, 
                "No articles found to test individual article endpoint"
            )
        
        # Test with first article's slug
        test_article = articles[0]
        test_slug = test_article.get('slug')
        
        if not test_slug:
            return self.log_test(
                "Individual Article Endpoint", 
                False, 
                "Article found but no slug available"
            )
        
        success, status, response = self.make_request(
            'GET', 
            f'articles/{test_slug}',
            expected_status=200,
            auth_required=False
        )
        
        if success:
            # Verify all required fields are present
            required_fields = ['id', 'uuid', 'slug', 'title', 'content', 'category', 'created_at']
            missing_fields = [field for field in required_fields if field not in response]
            
            if missing_fields:
                details = f"Article retrieved but missing fields: {missing_fields}"
                success = False
            else:
                details = f"Article '{response.get('title', 'Unknown')}' retrieved with all fields"
            
            return self.log_test("Individual Article Endpoint", success, details)
        else:
            return self.log_test(
                "Individual Article Endpoint", 
                False, 
                f"Status: {status}, Error: {response}"
            )
    
    def test_article_creation(self):
        """Test POST /api/articles.json - Article creation"""
        print("\n✍️ Testing Article Creation")
        print("-" * 40)
        
        if not self.token:
            return self.log_test(
                "Article Creation", 
                False, 
                "No authentication token available"
            )
        
        # Create test article data
        test_article = {
            "title": f"Test Article {datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "subheading": "This is a test article created by the article endpoints tester",
            "content": "<p>This is test content for verifying article creation functionality. The article should be properly stored and retrievable via the API endpoints.</p><p>Created at: " + datetime.now().isoformat() + "</p>",
            "category": "news",
            "publisher_name": "The Crewkerne Gazette",
            "tags": ["test", "api", "verification"],
            "category_labels": ["News", "Tech"],
            "is_breaking": False,
            "is_published": True,
            "pin": False,
            "priority": 0
        }
        
        success, status, response = self.make_request(
            'POST', 
            'articles.json',
            data=test_article,
            expected_status=200,
            auth_required=True
        )
        
        if success:
            # Verify created article has all expected fields
            required_fields = ['id', 'uuid', 'slug', 'title', 'content']
            missing_fields = [field for field in required_fields if field not in response]
            
            if missing_fields:
                details = f"Article created but missing fields: {missing_fields}"
                success = False
            else:
                # Store created article for cleanup and further testing
                self.created_articles.append({
                    'id': response.get('id'),
                    'slug': response.get('slug'),
                    'title': response.get('title')
                })
                details = f"Article '{response.get('title')}' created successfully with slug '{response.get('slug')}'"
            
            return self.log_test("Article Creation", success, details)
        else:
            return self.log_test(
                "Article Creation", 
                False, 
                f"Status: {status}, Error: {response}"
            )
    
    def test_created_article_retrieval(self):
        """Test that created article can be retrieved via individual article endpoint"""
        print("\n🔍 Testing Created Article Retrieval")
        print("-" * 40)
        
        if not self.created_articles:
            return self.log_test(
                "Created Article Retrieval", 
                False, 
                "No articles were created to test retrieval"
            )
        
        created_article = self.created_articles[0]
        test_slug = created_article['slug']
        
        success, status, response = self.make_request(
            'GET', 
            f'articles/{test_slug}',
            expected_status=200,
            auth_required=False
        )
        
        if success:
            # Verify the retrieved article matches what we created
            if response.get('slug') == test_slug and response.get('title') == created_article['title']:
                details = f"Created article successfully retrieved via slug '{test_slug}'"
            else:
                details = f"Article retrieved but data mismatch. Expected slug: {test_slug}, got: {response.get('slug')}"
                success = False
            
            return self.log_test("Created Article Retrieval", success, details)
        else:
            return self.log_test(
                "Created Article Retrieval", 
                False, 
                f"Status: {status}, Error: {response}"
            )
    
    def test_article_not_found(self):
        """Test GET /api/articles/non-existent-slug - 404 handling"""
        print("\n🚫 Testing Article Not Found (404)")
        print("-" * 40)
        
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
            details = f"Expected 404 for non-existent slug, got {status}: {response}"
        
        return self.log_test("Article Not Found (404)", success, details)
    
    def test_database_connectivity(self):
        """Test database connectivity by verifying data persistence"""
        print("\n🗄️ Testing Database Connectivity")
        print("-" * 40)
        
        # Test 1: Check if articles endpoint works (indicates DB connection)
        success1, status1, response1 = self.make_request(
            'GET', 
            'articles?limit=1',
            expected_status=200,
            auth_required=False
        )
        
        db_connected = success1
        details = []
        
        if success1:
            details.append("✅ Articles endpoint accessible")
        else:
            details.append(f"❌ Articles endpoint failed: {status1}")
        
        # Test 2: Check debug auth endpoint for database status
        success2, status2, response2 = self.make_request(
            'GET', 
            'debug/auth',
            expected_status=200,
            auth_required=False
        )
        
        if success2 and isinstance(response2, dict):
            db_status = response2.get('db_connected', False)
            total_users = response2.get('total_users', 0)
            details.append(f"✅ Debug endpoint reports DB connected: {db_status}, Users: {total_users}")
            if not db_status:
                db_connected = False
        else:
            details.append("⚠️ Debug auth endpoint not available")
        
        # Test 3: Try to create and retrieve an article (full DB test)
        if self.token and db_connected:
            test_title = f"DB Test Article {datetime.now().strftime('%H%M%S')}"
            test_data = {
                "title": test_title,
                "content": "<p>Database connectivity test article</p>",
                "category": "news",
                "is_published": True
            }
            
            success3, status3, response3 = self.make_request(
                'POST', 
                'articles.json',
                data=test_data,
                expected_status=200,
                auth_required=True
            )
            
            if success3:
                details.append("✅ Article creation successful (DB write works)")
                
                # Try to retrieve the created article
                created_slug = response3.get('slug')
                if created_slug:
                    success4, status4, response4 = self.make_request(
                        'GET', 
                        f'articles/{created_slug}',
                        expected_status=200,
                        auth_required=False
                    )
                    
                    if success4:
                        details.append("✅ Article retrieval successful (DB read works)")
                    else:
                        details.append("❌ Article retrieval failed (DB read issue)")
                        db_connected = False
            else:
                details.append(f"❌ Article creation failed: {status3} (DB write issue)")
                db_connected = False
        
        return self.log_test(
            "Database Connectivity", 
            db_connected, 
            " | ".join(details)
        )
    
    def test_breaking_news_filtering(self):
        """Test breaking news filtering functionality"""
        print("\n🚨 Testing Breaking News Filtering")
        print("-" * 40)
        
        success, status, response = self.make_request(
            'GET', 
            'articles?is_breaking=true',
            expected_status=200,
            auth_required=False
        )
        
        if success:
            articles = response if isinstance(response, list) else []
            details = f"Found {len(articles)} breaking news articles"
            
            # Verify all articles are marked as breaking
            if articles:
                non_breaking = [a for a in articles if not a.get('is_breaking', False)]
                if non_breaking:
                    details += f", {len(non_breaking)} articles not marked as breaking"
                    success = False
                else:
                    details += ", All articles correctly marked as breaking news"
            
            return self.log_test("Breaking News Filtering", success, details)
        else:
            return self.log_test(
                "Breaking News Filtering", 
                False, 
                f"Status: {status}, Error: {response}"
            )
    
    def run_all_tests(self):
        """Run all article endpoint tests"""
        print("🚀 Starting Article Endpoints Testing for The Crewkerne Gazette")
        print("🎯 Testing backend article endpoints functionality")
        print("=" * 80)
        
        # Test authentication first
        auth_success = self.test_admin_authentication()
        
        # Core article endpoint tests
        self.test_article_listing_endpoint()
        self.test_article_listing_with_category_filter()
        self.test_individual_article_endpoint()
        
        # Article creation tests (requires auth)
        if auth_success:
            self.test_article_creation()
            self.test_created_article_retrieval()
        
        # Error handling tests
        self.test_article_not_found()
        
        # Database connectivity tests
        self.test_database_connectivity()
        
        # Additional functionality tests
        self.test_breaking_news_filtering()
        
        # Print summary
        self.print_summary()
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 80)
        print("📊 ARTICLE ENDPOINTS TEST SUMMARY")
        print("=" * 80)
        
        success_rate = (self.tests_passed / self.tests_run * 100) if self.tests_run > 0 else 0
        
        print(f"Tests Run: {self.tests_run}")
        print(f"Tests Passed: {self.tests_passed}")
        print(f"Tests Failed: {self.tests_run - self.tests_passed}")
        print(f"Success Rate: {success_rate:.1f}%")
        
        if self.created_articles:
            print(f"\nCreated Articles: {len(self.created_articles)}")
            for article in self.created_articles:
                print(f"  - {article['title']} (slug: {article['slug']})")
        
        print(f"\n🎯 ARTICLE ACCESS FIX VERIFICATION:")
        if success_rate >= 80:
            print("✅ Backend article endpoints are working correctly")
            print("✅ Frontend article fetch path correction should resolve user issues")
        else:
            print("❌ Backend article endpoints have issues that need to be resolved")
            print("❌ Frontend path correction alone may not resolve all user issues")
        
        return success_rate >= 80

def main():
    """Main test execution"""
    tester = ArticleEndpointsTester()
    success = tester.run_all_tests()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())