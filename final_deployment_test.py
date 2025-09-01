#!/usr/bin/env python3
"""
Final Comprehensive Test of The Crewkerne Gazette Category Labels System
As requested in the review - testing all 6 critical areas before deployment
"""

import requests
import json
import sys
from datetime import datetime
import uuid

class FinalDeploymentTester:
    def __init__(self):
        # Use production URL from frontend/.env
        self.base_url = "https://gazette-cms.preview.emergentagent.com"
        self.api_url = f"{self.base_url}/api"
        self.token = None
        self.tests_run = 0
        self.tests_passed = 0
        self.created_articles = []
        
        # Expected 20 categories from review requirements
        self.expected_categories = [
            'Satire', 'Straight Talking', 'Opinion', 'Sports', 'Gossip', 
            'Politics', 'Local News', 'News', 'Agony Aunt', 'Special', 
            'Exclusive', 'Breaking', 'Analysis', 'Interview', 'Review',
            'Investigative', 'Community', 'Business', 'Crime', 'Education'
        ]

    def log_result(self, test_name, success, details=""):
        """Log test result with proper formatting"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {test_name}")
        else:
            print(f"❌ {test_name}")
        
        if details:
            print(f"   {details}")
        return success

    def make_api_call(self, method, endpoint, data=None, auth=True, timeout=30):
        """Make API call with proper error handling"""
        url = f"{self.api_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}
        
        if auth and self.token:
            headers['Authorization'] = f'Bearer {self.token}'
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=timeout)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=timeout)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers, timeout=timeout)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers, timeout=timeout)
            
            try:
                response_data = response.json()
            except:
                response_data = {"text": response.text}
            
            return response.status_code, response_data
            
        except Exception as e:
            return 0, {"error": str(e)}

    def test_1_authentication_admin_system(self):
        """Test 1: Authentication & Admin System"""
        print("\n🔐 TEST 1: AUTHENTICATION & ADMIN SYSTEM")
        print("=" * 60)
        
        # Test admin login (admin/admin123)
        status, response = self.make_api_call(
            'POST', 'auth/login',
            data={"username": "admin", "password": "admin123"},
            auth=False
        )
        
        login_success = status == 200 and 'access_token' in response
        if login_success:
            self.token = response['access_token']
            
        self.log_result(
            "Admin Login (admin/admin123)",
            login_success,
            f"Status: {status}, Token received: {'Yes' if login_success else 'No'}"
        )
        
        # Test emergency authentication
        status2, response2 = self.make_api_call(
            'POST', 'auth/login',
            data={"username": "admin_backup", "password": "admin_backup"},
            auth=False
        )
        
        emergency_success = status2 == 200
        self.log_result(
            "Emergency Authentication Working",
            emergency_success,
            f"Backup admin login status: {status2}"
        )
        
        # Test JWT token generation and validation
        if self.token:
            token_parts = self.token.split('.')
            jwt_valid = len(token_parts) == 3
            self.log_result(
                "JWT Token Generation and Validation",
                jwt_valid,
                f"Token structure: {len(token_parts)} parts (expected 3)"
            )
        
        return login_success

    def test_2_category_labels_system(self):
        """Test 2: Category Labels System"""
        print("\n🏷️ TEST 2: CATEGORY LABELS SYSTEM")
        print("=" * 60)
        
        # Test GET /api/categories/labels endpoint
        status, response = self.make_api_call('GET', 'categories/labels', auth=False)
        
        endpoint_working = status == 200 and 'category_labels' in response
        self.log_result(
            "GET /api/categories/labels endpoint returns all 20 categories",
            endpoint_working,
            f"Status: {status}, Categories found: {len(response.get('category_labels', []))}"
        )
        
        if endpoint_working:
            categories = response['category_labels']
            
            # Verify all 20 expected categories are present
            all_present = len(categories) == 20 and all(cat in categories for cat in self.expected_categories)
            self.log_result(
                "All 20 Expected Categories Present",
                all_present,
                f"Expected: 20, Found: {len(categories)}"
            )
            
            # Verify specific categories mentioned in review
            key_categories = ['Satire', 'Straight Talking', 'Opinion', 'Sports', 'Gossip', 'Politics', 'Local News', 'News']
            key_present = all(cat in categories for cat in key_categories)
            self.log_result(
                "Key Categories Include: Satire, Straight Talking, Opinion, Sports, etc.",
                key_present,
                f"Key categories verified: {', '.join(key_categories[:4])}..."
            )
            
            return categories
        
        return []

    def test_3_article_crud_category_labels(self):
        """Test 3: Article CRUD with Category Labels"""
        print("\n📝 TEST 3: ARTICLE CRUD WITH CATEGORY LABELS")
        print("=" * 60)
        
        if not self.token:
            self.log_result("Article CRUD Tests", False, "No authentication token available")
            return False
        
        # Create test article with category labels using form data (as backend expects)
        timestamp = datetime.now().strftime('%H%M%S')
        article_data = {
            "title": f"Test Category Labels Article {timestamp}",
            "content": "This article tests the category labels system with multiple labels for comprehensive validation.",
            "category": "news",
            "subheading": "Testing multiple category labels functionality",
            "publisher_name": "The Crewkerne Gazette",
            "tags": "test,category-labels,deployment",
            "category_labels": json.dumps(["News", "Breaking", "Local News"]),  # Multiple category labels
            "is_breaking": "false",
            "is_published": "true"
        }
        
        # Use form data instead of JSON for article creation
        url = f"{self.api_url}/articles"
        headers = {'Authorization': f'Bearer {self.token}'}
        
        try:
            response = requests.post(url, data=article_data, headers=headers, timeout=30)
            create_success = response.status_code == 200
            
            if create_success:
                article_response = response.json()
                article_slug = article_response.get('slug')
                self.created_articles.append(article_slug)
                
                # Verify category_labels field properly saved
                returned_labels = article_response.get('category_labels', [])
                expected_labels = ["News", "Breaking", "Local News"]
                labels_saved = set(returned_labels) == set(expected_labels)
                
                self.log_result(
                    "Create article with category_labels field properly saved",
                    labels_saved,
                    f"Expected: {expected_labels}, Got: {returned_labels}"
                )
                
                # Test article retrieval includes category_labels
                status, retrieve_response = self.make_api_call('GET', f'articles/{article_slug}', auth=False)
                retrieval_success = status == 200 and 'category_labels' in retrieve_response
                
                self.log_result(
                    "Article retrieval includes category_labels in response",
                    retrieval_success,
                    f"Category labels in response: {retrieve_response.get('category_labels', [])}"
                )
                
                return True
            else:
                try:
                    error_data = response.json()
                except:
                    error_data = response.text
                
                self.log_result(
                    "Create multiple test articles with different category labels",
                    False,
                    f"Status: {response.status_code}, Error: {error_data}"
                )
                return False
                
        except Exception as e:
            self.log_result(
                "Article Creation with Category Labels",
                False,
                f"Exception: {str(e)}"
            )
            return False

    def test_4_news_prioritization_system(self):
        """Test 4: News Prioritization System"""
        print("\n📰 TEST 4: NEWS PRIORITIZATION SYSTEM")
        print("=" * 60)
        
        # Test GET /api/articles?category=news endpoint
        status, response = self.make_api_call('GET', 'articles?category=news', auth=False)
        
        news_endpoint_working = status == 200 and isinstance(response, list)
        self.log_result(
            "GET /api/articles?category=news endpoint",
            news_endpoint_working,
            f"Status: {status}, News articles found: {len(response) if isinstance(response, list) else 0}"
        )
        
        if news_endpoint_working:
            # Verify news articles are returned separately for homepage prioritization
            news_articles = response
            all_news_category = all(article.get('category') == 'news' for article in news_articles)
            self.log_result(
                "News articles returned separately for homepage prioritization",
                all_news_category,
                f"All {len(news_articles)} articles have 'news' category"
            )
        
        # Test general GET /api/articles endpoint returns all articles
        status2, response2 = self.make_api_call('GET', 'articles', auth=False)
        
        general_endpoint_working = status2 == 200 and isinstance(response2, list)
        self.log_result(
            "General GET /api/articles endpoint returns all articles",
            general_endpoint_working,
            f"Status: {status2}, Total articles found: {len(response2) if isinstance(response2, list) else 0}"
        )
        
        # Test article listing endpoints include category_labels
        if general_endpoint_working:
            articles_with_labels = [a for a in response2 if 'category_labels' in a]
            labels_included = len(articles_with_labels) > 0
            self.log_result(
                "Article listing endpoints include category_labels",
                labels_included,
                f"Articles with category_labels: {len(articles_with_labels)}/{len(response2)}"
            )

    def test_5_database_integration(self):
        """Test 5: Database Integration"""
        print("\n🗄️ TEST 5: DATABASE INTEGRATION")
        print("=" * 60)
        
        # Test database connection stability through debug endpoint
        status, response = self.make_api_call('GET', 'debug/auth', auth=False)
        
        debug_working = status == 200
        self.log_result(
            "Database connection check via debug endpoint",
            debug_working,
            f"Status: {status}, DB connected: {response.get('db_connected', 'unknown')}"
        )
        
        if debug_working:
            db_connected = response.get('db_connected', False)
            total_users = response.get('total_users', 0)
            
            # PostgreSQL connection status
            self.log_result(
                "PostgreSQL connection is stable",
                db_connected,
                f"Database connected: {db_connected}, Users in DB: {total_users}"
            )
        
        # Test that all article fields are being saved correctly
        if self.created_articles:
            test_slug = self.created_articles[0]
            status, article_data = self.make_api_call('GET', f'articles/{test_slug}', auth=False)
            
            if status == 200:
                required_fields = ['title', 'content', 'category', 'category_labels', 'tags', 'slug']
                all_fields_present = all(field in article_data for field in required_fields)
                
                self.log_result(
                    "All article fields saved correctly (title, content, category, category_labels, tags, slug)",
                    all_fields_present,
                    f"Required fields present: {[f for f in required_fields if f in article_data]}"
                )
        
        # Test existing articles work with new category_labels field
        status, all_articles = self.make_api_call('GET', 'articles', auth=False)
        if status == 200 and isinstance(all_articles, list) and len(all_articles) > 0:
            articles_with_labels_field = sum(1 for a in all_articles if 'category_labels' in a)
            backward_compatibility = articles_with_labels_field == len(all_articles)
            
            self.log_result(
                "Existing articles work with new category_labels field",
                backward_compatibility,
                f"Articles with category_labels field: {articles_with_labels_field}/{len(all_articles)}"
            )

    def test_6_production_readiness(self):
        """Test 6: Production Readiness"""
        print("\n🚀 TEST 6: PRODUCTION READINESS")
        print("=" * 60)
        
        # Test all endpoints work without authentication errors
        public_endpoints = [
            ('GET', 'categories/labels'),
            ('GET', 'settings/public'),
            ('GET', 'articles'),
            ('GET', 'debug/auth')
        ]
        
        all_public_working = True
        for method, endpoint in public_endpoints:
            status, response = self.make_api_call(method, endpoint, auth=False)
            endpoint_working = status == 200
            
            if not endpoint_working:
                all_public_working = False
            
            self.log_result(
                f"Public endpoint works: {endpoint}",
                endpoint_working,
                f"Status: {status}"
            )
        
        self.log_result(
            "All endpoints work without authentication errors",
            all_public_working,
            "All public endpoints accessible"
        )
        
        # Test error handling for invalid requests
        status, response = self.make_api_call('GET', 'articles/nonexistent-slug', auth=False)
        error_handling = status == 404
        self.log_result(
            "Error handling for invalid requests",
            error_handling,
            f"404 returned for invalid article slug: {status == 404}"
        )
        
        # Test API responses are in correct format for frontend consumption
        status, categories_response = self.make_api_call('GET', 'categories/labels', auth=False)
        correct_format = (status == 200 and 
                         isinstance(categories_response, dict) and 
                         'category_labels' in categories_response and 
                         isinstance(categories_response['category_labels'], list))
        
        self.log_result(
            "API responses in correct format for frontend consumption",
            correct_format,
            f"Categories endpoint returns proper JSON structure: {correct_format}"
        )

    def cleanup_test_data(self):
        """Clean up test articles"""
        print("\n🧹 CLEANUP: Removing Test Articles")
        print("-" * 40)
        
        if not self.token or not self.created_articles:
            print("   No test articles to clean up")
            return
        
        for article_slug in self.created_articles:
            status, response = self.make_api_call('DELETE', f'articles/by-slug/{article_slug}', auth=True)
            
            if status == 200:
                print(f"✅ Deleted test article: {article_slug}")
            else:
                print(f"⚠️ Could not delete: {article_slug} (Status: {status})")

    def run_final_deployment_test(self):
        """Run complete deployment validation test"""
        print("🎯 FINAL COMPREHENSIVE TEST - THE CREWKERNE GAZETTE")
        print("📰 Category Labels System & News Prioritization Validation")
        print("=" * 80)
        print(f"Target: {self.base_url}")
        print(f"API: {self.api_url}")
        print(f"Test Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80)
        
        # Run all 6 test suites as specified in review
        auth_success = self.test_1_authentication_admin_system()
        categories = self.test_2_category_labels_system()
        
        if auth_success:
            self.test_3_article_crud_category_labels()
        
        self.test_4_news_prioritization_system()
        self.test_5_database_integration()
        self.test_6_production_readiness()
        
        # Cleanup test data
        self.cleanup_test_data()
        
        # Final assessment
        print("\n" + "=" * 80)
        print("📊 FINAL DEPLOYMENT VALIDATION RESULTS")
        print("=" * 80)
        print(f"Total Tests Run: {self.tests_run}")
        print(f"Tests Passed: {self.tests_passed}")
        print(f"Tests Failed: {self.tests_run - self.tests_passed}")
        print(f"Success Rate: {(self.tests_passed/self.tests_run)*100:.1f}%")
        
        # Critical deployment criteria
        critical_passed = (
            auth_success and
            len(categories) == 20 and
            self.tests_passed >= (self.tests_run * 0.85)  # 85% pass rate
        )
        
        print(f"\n🎯 DEPLOYMENT READINESS ASSESSMENT:")
        print(f"   ✅ Authentication System: {'PASS' if auth_success else 'FAIL'}")
        print(f"   ✅ Category Labels (20): {'PASS' if len(categories) == 20 else 'FAIL'}")
        print(f"   ✅ Overall Success (85%+): {'PASS' if self.tests_passed >= (self.tests_run * 0.85) else 'FAIL'}")
        
        if critical_passed:
            print("\n🎉 SYSTEM READY FOR DEPLOYMENT!")
            print("✅ Category labels system and news prioritization fully functional")
            return 0
        else:
            print("\n⚠️ DEPLOYMENT BLOCKED - CRITICAL ISSUES FOUND")
            print("❌ System needs fixes before deployment")
            return 1

def main():
    """Execute final deployment test"""
    tester = FinalDeploymentTester()
    return tester.run_final_deployment_test()

if __name__ == "__main__":
    sys.exit(main())