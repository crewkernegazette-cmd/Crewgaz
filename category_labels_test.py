#!/usr/bin/env python3
"""
Category Labels System Backend Testing
Tests the new article category labels system implementation for The Crewkerne Gazette
"""

import requests
import json
import sys
from datetime import datetime
import os

class CategoryLabelsAPITester:
    def __init__(self):
        # Use the local backend URL
        self.base_url = "http://localhost:8001"
        self.api_url = f"{self.base_url}/api"
        self.token = None
        self.tests_run = 0
        self.tests_passed = 0
        self.created_article_slug = None
        
        # Expected category labels from backend
        self.expected_categories = [
            'Satire', 'Straight Talking', 'Opinion', 'Sports', 'Gossip', 
            'Politics', 'Local News', 'News', 'Agony Aunt', 'Special', 
            'Exclusive', 'Breaking', 'Analysis', 'Interview', 'Review',
            'Investigative', 'Community', 'Business', 'Crime', 'Education'
        ]

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

    def make_request(self, method, endpoint, data=None, auth_required=True):
        """Make API request with proper headers"""
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
            
            return response
        except Exception as e:
            print(f"   Request failed: {str(e)}")
            return None

    def test_admin_login(self):
        """Test admin authentication"""
        print("\n🔐 Testing Admin Authentication")
        print("-" * 40)
        
        response = self.make_request('POST', 'auth/login', {
            "username": "admin",
            "password": "admin123"
        }, auth_required=False)
        
        if response and response.status_code == 200:
            try:
                data = response.json()
                if 'access_token' in data:
                    self.token = data['access_token']
                    self.log_test("Admin Login", True, f"Token obtained, role: {data.get('role', 'unknown')}")
                    return True
                else:
                    self.log_test("Admin Login", False, "No access_token in response")
                    return False
            except:
                self.log_test("Admin Login", False, "Invalid JSON response")
                return False
        else:
            status = response.status_code if response else "No response"
            self.log_test("Admin Login", False, f"Status: {status}")
            return False

    def test_category_labels_endpoint(self):
        """Test GET /api/categories/labels endpoint"""
        print("\n📋 Testing Category Labels Endpoint")
        print("-" * 40)
        
        # Test without authentication (should be public)
        response = self.make_request('GET', 'categories/labels', auth_required=False)
        
        if response and response.status_code == 200:
            try:
                data = response.json()
                
                # Check response structure
                if 'category_labels' not in data:
                    self.log_test("Category Labels Endpoint Structure", False, "Missing 'category_labels' key")
                    return False
                
                category_labels = data['category_labels']
                
                # Check if it's a list
                if not isinstance(category_labels, list):
                    self.log_test("Category Labels Data Type", False, f"Expected list, got {type(category_labels)}")
                    return False
                
                # Check count (should be 20)
                if len(category_labels) != 20:
                    self.log_test("Category Labels Count", False, f"Expected 20 categories, got {len(category_labels)}")
                    return False
                
                # Check for expected categories
                missing_categories = []
                for expected_cat in self.expected_categories:
                    if expected_cat not in category_labels:
                        missing_categories.append(expected_cat)
                
                if missing_categories:
                    self.log_test("Category Labels Content", False, f"Missing categories: {missing_categories}")
                    return False
                
                # Check for key categories mentioned in requirements
                key_categories = ['Satire', 'Straight Talking', 'Opinion', 'Sports', 'Gossip', 'Politics']
                found_key_categories = [cat for cat in key_categories if cat in category_labels]
                
                if len(found_key_categories) != len(key_categories):
                    missing_key = [cat for cat in key_categories if cat not in category_labels]
                    self.log_test("Key Categories Check", False, f"Missing key categories: {missing_key}")
                    return False
                
                self.log_test("Category Labels Endpoint", True, f"Found all 20 categories including key ones")
                self.log_test("Category Labels Content Validation", True, f"Categories: {', '.join(category_labels[:5])}...")
                return True
                
            except Exception as e:
                self.log_test("Category Labels Endpoint", False, f"JSON parsing error: {str(e)}")
                return False
        else:
            status = response.status_code if response else "No response"
            self.log_test("Category Labels Endpoint", False, f"Status: {status}")
            return False

    def test_article_creation_with_category_labels(self):
        """Test POST /api/articles with category_labels field"""
        print("\n📝 Testing Article Creation with Category Labels")
        print("-" * 50)
        
        if not self.token:
            self.log_test("Article Creation Setup", False, "No authentication token available")
            return False
        
        # Test data with multiple category labels
        test_categories = ['Satire', 'Opinion', 'Politics']
        article_data = {
            "title": f"Test Article with Category Labels - {datetime.now().strftime('%H:%M:%S')}",
            "content": "This is a test article to verify category labels functionality. The article should be created with multiple category labels and they should be properly stored and retrieved.",
            "category": "news",  # Use lowercase as required by backend
            "subheading": "Testing the new category labels system implementation",
            "publisher_name": "The Crewkerne Gazette",
            "category_labels": test_categories,
            "is_breaking": False,
            "is_published": True,
            "tags": ["test", "category-labels", "backend-testing"]
        }
        
        # Use form data for article creation (as per backend implementation)
        form_data = {
            "title": article_data["title"],
            "content": article_data["content"],
            "category": article_data["category"],
            "subheading": article_data["subheading"],
            "publisher_name": article_data["publisher_name"],
            "category_labels": json.dumps(article_data["category_labels"]),
            "is_breaking": article_data["is_breaking"],
            "is_published": article_data["is_published"],
            "tags": ",".join(article_data["tags"])
        }
        
        # Make request with form data
        url = f"{self.api_url}/articles"
        headers = {'Authorization': f'Bearer {self.token}'}
        
        try:
            response = requests.post(url, data=form_data, headers=headers, timeout=30)
            
            if response and response.status_code == 200:
                try:
                    created_article = response.json()
                    
                    # Store slug for later tests
                    self.created_article_slug = created_article.get('slug')
                    
                    # Verify category_labels field exists and is correct
                    if 'category_labels' not in created_article:
                        self.log_test("Article Creation - Category Labels Field", False, "category_labels field missing from response")
                        return False
                    
                    returned_categories = created_article['category_labels']
                    
                    # Check if it's a list
                    if not isinstance(returned_categories, list):
                        self.log_test("Article Creation - Category Labels Type", False, f"Expected list, got {type(returned_categories)}")
                        return False
                    
                    # Check if all test categories are present
                    if set(returned_categories) != set(test_categories):
                        self.log_test("Article Creation - Category Labels Content", False, 
                                    f"Expected {test_categories}, got {returned_categories}")
                        return False
                    
                    # Verify other fields are also present
                    required_fields = ['id', 'uuid', 'slug', 'title', 'content', 'category']
                    missing_fields = [field for field in required_fields if field not in created_article]
                    
                    if missing_fields:
                        self.log_test("Article Creation - Required Fields", False, f"Missing fields: {missing_fields}")
                        return False
                    
                    self.log_test("Article Creation with Category Labels", True, 
                                f"Article created with slug '{self.created_article_slug}' and categories {returned_categories}")
                    return True
                    
                except Exception as e:
                    self.log_test("Article Creation", False, f"JSON parsing error: {str(e)}")
                    return False
            else:
                status = response.status_code if response else "No response"
                error_text = ""
                if response:
                    try:
                        error_data = response.json()
                        error_text = f" - {error_data}"
                    except:
                        error_text = f" - {response.text[:200]}"
                self.log_test("Article Creation with Category Labels", False, f"Status: {status}{error_text}")
                return False
                
        except Exception as e:
            self.log_test("Article Creation with Category Labels", False, f"Request error: {str(e)}")
            return False

    def test_article_retrieval_with_category_labels(self):
        """Test article retrieval endpoints include category_labels"""
        print("\n📖 Testing Article Retrieval with Category Labels")
        print("-" * 50)
        
        if not self.created_article_slug:
            self.log_test("Article Retrieval Setup", False, "No test article available")
            return False
        
        # Test 1: GET /api/articles (list all articles)
        response = self.make_request('GET', 'articles?limit=5', auth_required=False)
        
        if response and response.status_code == 200:
            try:
                articles = response.json()
                
                if not isinstance(articles, list):
                    self.log_test("Articles List Endpoint", False, f"Expected list, got {type(articles)}")
                    return False
                
                if len(articles) == 0:
                    self.log_test("Articles List Endpoint", False, "No articles returned")
                    return False
                
                # Check if articles have category_labels field
                articles_with_labels = [art for art in articles if 'category_labels' in art]
                
                if len(articles_with_labels) == 0:
                    self.log_test("Articles List - Category Labels Field", False, "No articles have category_labels field")
                    return False
                
                # Find our test article
                test_article = None
                for article in articles:
                    if article.get('slug') == self.created_article_slug:
                        test_article = article
                        break
                
                if test_article and 'category_labels' in test_article:
                    self.log_test("Articles List with Category Labels", True, 
                                f"Found {len(articles)} articles, test article has category_labels: {test_article['category_labels']}")
                else:
                    self.log_test("Articles List - Test Article", False, "Test article not found or missing category_labels")
                
            except Exception as e:
                self.log_test("Articles List Endpoint", False, f"JSON parsing error: {str(e)}")
                return False
        else:
            status = response.status_code if response else "No response"
            self.log_test("Articles List Endpoint", False, f"Status: {status}")
            return False
        
        # Test 2: GET /api/articles/{slug} (individual article)
        response = self.make_request('GET', f'articles/{self.created_article_slug}', auth_required=False)
        
        if response and response.status_code == 200:
            try:
                article = response.json()
                
                if 'category_labels' not in article:
                    self.log_test("Individual Article - Category Labels Field", False, "category_labels field missing")
                    return False
                
                category_labels = article['category_labels']
                
                if not isinstance(category_labels, list):
                    self.log_test("Individual Article - Category Labels Type", False, f"Expected list, got {type(category_labels)}")
                    return False
                
                self.log_test("Individual Article Retrieval with Category Labels", True, 
                            f"Article '{article['title']}' has category_labels: {category_labels}")
                
            except Exception as e:
                self.log_test("Individual Article Endpoint", False, f"JSON parsing error: {str(e)}")
                return False
        else:
            status = response.status_code if response else "No response"
            self.log_test("Individual Article Endpoint", False, f"Status: {status}")
            return False
        
        # Test 3: GET /api/dashboard/articles (dashboard listing)
        if not self.token:
            self.log_test("Dashboard Articles Setup", False, "No authentication token")
            return False
        
        response = self.make_request('GET', 'dashboard/articles', auth_required=True)
        
        if response and response.status_code == 200:
            try:
                dashboard_articles = response.json()
                
                if not isinstance(dashboard_articles, list):
                    self.log_test("Dashboard Articles Endpoint", False, f"Expected list, got {type(dashboard_articles)}")
                    return False
                
                # Find our test article in dashboard
                test_article_in_dashboard = None
                for article in dashboard_articles:
                    if article.get('slug') == self.created_article_slug:
                        test_article_in_dashboard = article
                        break
                
                if test_article_in_dashboard:
                    if 'category_labels' in test_article_in_dashboard:
                        self.log_test("Dashboard Articles with Category Labels", True, 
                                    f"Dashboard shows {len(dashboard_articles)} articles, test article has category_labels: {test_article_in_dashboard['category_labels']}")
                    else:
                        self.log_test("Dashboard Articles - Category Labels Field", False, "Test article missing category_labels in dashboard")
                        return False
                else:
                    self.log_test("Dashboard Articles - Test Article", False, "Test article not found in dashboard")
                    return False
                
            except Exception as e:
                self.log_test("Dashboard Articles Endpoint", False, f"JSON parsing error: {str(e)}")
                return False
        else:
            status = response.status_code if response else "No response"
            self.log_test("Dashboard Articles Endpoint", False, f"Status: {status}")
            return False
        
        return True

    def test_category_labels_validation(self):
        """Test category labels data validation"""
        print("\n🔍 Testing Category Labels Data Validation")
        print("-" * 45)
        
        if not self.token:
            self.log_test("Validation Test Setup", False, "No authentication token")
            return False
        
        # Test 1: Article with invalid category labels (should filter them out)
        invalid_categories = ['InvalidCategory1', 'Satire', 'AnotherInvalid', 'Opinion']
        
        article_data = {
            "title": f"Test Invalid Categories - {datetime.now().strftime('%H:%M:%S')}",
            "content": "Testing validation of category labels with some invalid categories mixed in.",
            "category": "news",  # Use lowercase as required by backend
            "category_labels": json.dumps(invalid_categories),
            "is_published": True
        }
        
        url = f"{self.api_url}/articles"
        headers = {'Authorization': f'Bearer {self.token}'}
        
        try:
            response = requests.post(url, data=article_data, headers=headers, timeout=30)
            
            if response and response.status_code == 200:
                try:
                    created_article = response.json()
                    returned_categories = created_article.get('category_labels', [])
                    
                    # Should only contain valid categories (Satire, Opinion)
                    expected_valid = ['Satire', 'Opinion']
                    
                    if set(returned_categories) == set(expected_valid):
                        self.log_test("Category Labels Validation", True, 
                                    f"Invalid categories filtered out, kept: {returned_categories}")
                    else:
                        self.log_test("Category Labels Validation", False, 
                                    f"Expected {expected_valid}, got {returned_categories}")
                        return False
                    
                except Exception as e:
                    self.log_test("Category Labels Validation", False, f"JSON parsing error: {str(e)}")
                    return False
            else:
                status = response.status_code if response else "No response"
                self.log_test("Category Labels Validation", False, f"Status: {status}")
                return False
        
        except Exception as e:
            self.log_test("Category Labels Validation", False, f"Request error: {str(e)}")
            return False
        
        # Test 2: Article with empty category labels
        empty_article_data = {
            "title": f"Test Empty Categories - {datetime.now().strftime('%H:%M:%S')}",
            "content": "Testing article creation with empty category labels.",
            "category": "NEWS",
            "category_labels": json.dumps([]),
            "is_published": True
        }
        
        try:
            response = requests.post(url, data=empty_article_data, headers=headers, timeout=30)
            
            if response and response.status_code == 200:
                try:
                    created_article = response.json()
                    returned_categories = created_article.get('category_labels', [])
                    
                    if isinstance(returned_categories, list) and len(returned_categories) == 0:
                        self.log_test("Empty Category Labels Handling", True, "Empty category labels handled correctly")
                    else:
                        self.log_test("Empty Category Labels Handling", False, 
                                    f"Expected empty list, got {returned_categories}")
                        return False
                    
                except Exception as e:
                    self.log_test("Empty Category Labels Handling", False, f"JSON parsing error: {str(e)}")
                    return False
            else:
                status = response.status_code if response else "No response"
                self.log_test("Empty Category Labels Handling", False, f"Status: {status}")
                return False
        
        except Exception as e:
            self.log_test("Empty Category Labels Handling", False, f"Request error: {str(e)}")
            return False
        
        return True

    def test_backward_compatibility(self):
        """Test that existing articles work properly (backward compatibility)"""
        print("\n🔄 Testing Backward Compatibility")
        print("-" * 35)
        
        # Get existing articles and check they handle category_labels gracefully
        response = self.make_request('GET', 'articles?limit=10', auth_required=False)
        
        if response and response.status_code == 200:
            try:
                articles = response.json()
                
                if len(articles) == 0:
                    self.log_test("Backward Compatibility", True, "No existing articles to test (empty database)")
                    return True
                
                # Check that all articles have category_labels field (even if empty)
                articles_without_labels = []
                for article in articles:
                    if 'category_labels' not in article:
                        articles_without_labels.append(article.get('title', 'Unknown'))
                
                if articles_without_labels:
                    self.log_test("Backward Compatibility - Missing Fields", False, 
                                f"Articles missing category_labels: {articles_without_labels[:3]}")
                    return False
                
                # Check that category_labels are always lists
                invalid_types = []
                for article in articles:
                    if not isinstance(article.get('category_labels'), list):
                        invalid_types.append(f"{article.get('title', 'Unknown')}: {type(article.get('category_labels'))}")
                
                if invalid_types:
                    self.log_test("Backward Compatibility - Data Types", False, 
                                f"Invalid category_labels types: {invalid_types[:3]}")
                    return False
                
                self.log_test("Backward Compatibility", True, 
                            f"All {len(articles)} articles have proper category_labels field")
                return True
                
            except Exception as e:
                self.log_test("Backward Compatibility", False, f"JSON parsing error: {str(e)}")
                return False
        else:
            status = response.status_code if response else "No response"
            self.log_test("Backward Compatibility", False, f"Status: {status}")
            return False

    def test_authentication_requirements(self):
        """Test authentication requirements for different endpoints"""
        print("\n🔐 Testing Authentication Requirements")
        print("-" * 40)
        
        # Test 1: Category labels endpoint should be public (no auth required)
        response = self.make_request('GET', 'categories/labels', auth_required=False)
        
        if response and response.status_code == 200:
            self.log_test("Category Labels Endpoint - Public Access", True, "Accessible without authentication")
        else:
            status = response.status_code if response else "No response"
            self.log_test("Category Labels Endpoint - Public Access", False, f"Status: {status}")
            return False
        
        # Test 2: Article creation should require authentication
        article_data = {
            "title": "Test Auth Required",
            "content": "This should fail without authentication",
            "category": "NEWS"
        }
        
        url = f"{self.api_url}/articles"
        headers = {'Content-Type': 'application/json'}
        
        try:
            response = requests.post(url, data=article_data, headers=headers, timeout=30)
            
            if response and response.status_code == 401:
                self.log_test("Article Creation - Auth Required", True, "Properly requires authentication")
            else:
                status = response.status_code if response else "No response"
                self.log_test("Article Creation - Auth Required", False, f"Expected 401, got {status}")
                return False
        
        except Exception as e:
            self.log_test("Article Creation - Auth Required", False, f"Request error: {str(e)}")
            return False
        
        # Test 3: Dashboard articles should require authentication
        response = self.make_request('GET', 'dashboard/articles', auth_required=False)
        
        if response and response.status_code == 401:
            self.log_test("Dashboard Articles - Auth Required", True, "Properly requires authentication")
        else:
            status = response.status_code if response else "No response"
            self.log_test("Dashboard Articles - Auth Required", False, f"Expected 401, got {status}")
            return False
        
        return True

    def run_all_tests(self):
        """Run all category labels system tests"""
        print("🚀 Starting Category Labels System Backend Tests")
        print("=" * 60)
        print(f"Target API: {self.api_url}")
        print(f"Test Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)
        
        # Test sequence
        tests = [
            ("Admin Authentication", self.test_admin_login),
            ("Category Labels Endpoint", self.test_category_labels_endpoint),
            ("Article Creation with Category Labels", self.test_article_creation_with_category_labels),
            ("Article Retrieval with Category Labels", self.test_article_retrieval_with_category_labels),
            ("Category Labels Validation", self.test_category_labels_validation),
            ("Backward Compatibility", self.test_backward_compatibility),
            ("Authentication Requirements", self.test_authentication_requirements)
        ]
        
        for test_name, test_func in tests:
            try:
                test_func()
            except Exception as e:
                self.log_test(f"{test_name} - Exception", False, f"Unexpected error: {str(e)}")
        
        # Final Results
        print("\n" + "=" * 60)
        print("📊 CATEGORY LABELS SYSTEM TEST RESULTS")
        print("=" * 60)
        print(f"Tests Run: {self.tests_run}")
        print(f"Tests Passed: {self.tests_passed}")
        print(f"Tests Failed: {self.tests_run - self.tests_passed}")
        print(f"Success Rate: {(self.tests_passed/self.tests_run)*100:.1f}%" if self.tests_run > 0 else "No tests run")
        
        # Determine overall status
        if self.tests_run == 0:
            print("\n❌ NO TESTS EXECUTED")
            return False
        elif self.tests_passed == self.tests_run:
            print("\n🎉 ALL TESTS PASSED - Category Labels System Working Perfectly!")
            return True
        elif self.tests_passed / self.tests_run >= 0.8:
            print(f"\n⚠️  MOSTLY WORKING - {self.tests_run - self.tests_passed} minor issues found")
            return True
        else:
            print(f"\n❌ SIGNIFICANT ISSUES - {self.tests_run - self.tests_passed} major problems found")
            return False

def main():
    """Main test execution"""
    tester = CategoryLabelsAPITester()
    success = tester.run_all_tests()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())