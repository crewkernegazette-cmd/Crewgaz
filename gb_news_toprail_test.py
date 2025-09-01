#!/usr/bin/env python3
"""
GB News-Style Top Rail System and Mobile Debugging Features Test
================================================================

This test suite validates the newly implemented GB News-style top rail system 
and mobile debugging features for The Crewkerne Gazette.

Test Areas:
1. Top Rail Endpoint Testing
2. Mobile Debug Endpoints  
3. Pinning System Integration
4. Database Migration Validation

Authentication: admin/admin123
Backend URL: https://api.crewkernegazette.co.uk
"""

import requests
import json
import sys
from datetime import datetime
from typing import Dict, List, Any, Optional

class GBNewsTopRailTester:
    def __init__(self, base_url: str = "https://api.crewkernegazette.co.uk"):
        self.base_url = base_url
        self.token = None
        self.tests_run = 0
        self.tests_passed = 0
        self.created_articles = []  # Track created test articles for cleanup
        
        print(f"🚀 GB News Top Rail System Tester")
        print(f"🎯 Target: {self.base_url}")
        print("=" * 80)

    def log_test(self, name: str, success: bool, details: str = ""):
        """Log test result"""
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

    def make_request(self, method: str, endpoint: str, data: Optional[Dict] = None, 
                    auth_required: bool = True, timeout: int = 30) -> tuple[bool, Dict, int]:
        """Make HTTP request with proper error handling"""
        url = f"{self.base_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}
        
        if auth_required and self.token:
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
            else:
                return False, {"error": f"Unsupported method: {method}"}, 0
            
            try:
                response_data = response.json()
            except:
                response_data = {"text": response.text}
            
            return response.status_code in [200, 201], response_data, response.status_code
            
        except requests.exceptions.ConnectionError:
            return False, {"error": "Connection failed - backend may be down"}, 0
        except requests.exceptions.Timeout:
            return False, {"error": f"Request timeout after {timeout}s"}, 0
        except Exception as e:
            return False, {"error": str(e)}, 0

    def test_admin_login(self) -> bool:
        """Test admin authentication"""
        print("\n🔐 AUTHENTICATION TESTING")
        print("-" * 40)
        
        success, response, status = self.make_request(
            'POST', 
            'auth/login',
            data={"username": "admin", "password": "admin123"},
            auth_required=False
        )
        
        if success and 'access_token' in response:
            self.token = response['access_token']
            self.log_test(
                "Admin Login (admin/admin123)", 
                True, 
                f"Token received: {self.token[:30]}..."
            )
            return True
        else:
            self.log_test(
                "Admin Login (admin/admin123)", 
                False, 
                f"Status: {status}, Response: {response}"
            )
            return False

    def test_top_rail_endpoint(self) -> bool:
        """Test GET /api/top-rail endpoint structure and ordering"""
        print("\n📰 TOP RAIL ENDPOINT TESTING")
        print("-" * 40)
        
        success, response, status = self.make_request('GET', 'top-rail', auth_required=False)
        
        if not success:
            self.log_test(
                "Top Rail Endpoint Accessibility", 
                False, 
                f"Status: {status}, Error: {response.get('error', 'Unknown error')}"
            )
            return False
        
        # Test 1: Endpoint accessibility
        self.log_test("Top Rail Endpoint Accessibility", True, f"Status: {status}")
        
        # Test 2: Response structure validation
        required_sections = ['lead', 'secondary', 'more']
        structure_valid = all(section in response for section in required_sections)
        
        self.log_test(
            "Top Rail Response Structure", 
            structure_valid,
            f"Has sections: {list(response.keys())}"
        )
        
        if not structure_valid:
            return False
        
        # Test 3: Content validation
        lead_article = response.get('lead')
        secondary_articles = response.get('secondary', [])
        more_articles = response.get('more', [])
        
        # Lead article validation
        lead_valid = lead_article is not None
        if lead_valid and isinstance(lead_article, dict):
            required_fields = ['id', 'title', 'slug', 'category', 'created_at']
            lead_valid = all(field in lead_article for field in required_fields)
        
        self.log_test(
            "Lead Article Structure", 
            lead_valid,
            f"Lead article: {lead_article.get('title', 'None') if lead_article else 'None'}"
        )
        
        # Secondary articles validation
        secondary_valid = isinstance(secondary_articles, list) and len(secondary_articles) <= 3
        self.log_test(
            "Secondary Articles Structure", 
            secondary_valid,
            f"Count: {len(secondary_articles)}/3 max"
        )
        
        # More articles validation  
        more_valid = isinstance(more_articles, list)
        self.log_test(
            "More Articles Structure", 
            more_valid,
            f"Count: {len(more_articles)}"
        )
        
        # Test 4: Article ordering validation (if we have articles)
        all_articles = []
        if lead_article:
            all_articles.append(lead_article)
        all_articles.extend(secondary_articles)
        all_articles.extend(more_articles)
        
        if all_articles:
            ordering_valid = self.validate_article_ordering(all_articles)
            self.log_test(
                "Article Ordering Logic", 
                ordering_valid,
                "Pinned → Priority → Breaking → Newest"
            )
        else:
            self.log_test(
                "Article Ordering Logic", 
                True,
                "No articles to validate ordering"
            )
        
        return structure_valid and lead_valid and secondary_valid and more_valid

    def validate_article_ordering(self, articles: List[Dict]) -> bool:
        """Validate that articles are ordered correctly: pinned_at DESC, priority DESC, is_breaking DESC, created_at DESC"""
        try:
            for i in range(len(articles) - 1):
                current = articles[i]
                next_article = articles[i + 1]
                
                # Check pinning priority
                current_pinned = current.get('pinned_at') is not None
                next_pinned = next_article.get('pinned_at') is not None
                
                if current_pinned and not next_pinned:
                    continue  # Correct: pinned before unpinned
                elif not current_pinned and next_pinned:
                    return False  # Incorrect: unpinned before pinned
                
                # If both pinned or both unpinned, check other criteria
                current_priority = current.get('priority', 0)
                next_priority = next_article.get('priority', 0)
                
                if current_priority > next_priority:
                    continue  # Correct: higher priority first
                elif current_priority < next_priority:
                    return False  # Incorrect: lower priority first
                
                # If same priority, check breaking news
                current_breaking = current.get('is_breaking', False)
                next_breaking = next_article.get('is_breaking', False)
                
                if current_breaking and not next_breaking:
                    continue  # Correct: breaking before non-breaking
                elif not current_breaking and next_breaking:
                    return False  # Incorrect: non-breaking before breaking
                
                # If same breaking status, check creation date
                current_date = current.get('created_at', '')
                next_date = next_article.get('created_at', '')
                
                if current_date >= next_date:
                    continue  # Correct: newer first
                else:
                    return False  # Incorrect: older first
            
            return True
        except Exception as e:
            print(f"   Ordering validation error: {e}")
            return False

    def test_mobile_debug_endpoints(self) -> bool:
        """Test mobile debugging endpoints"""
        print("\n📱 MOBILE DEBUG ENDPOINTS TESTING")
        print("-" * 40)
        
        # Test 1: GET /api/debug/last-errors (no auth required)
        success, response, status = self.make_request(
            'GET', 
            'debug/last-errors', 
            auth_required=False
        )
        
        self.log_test(
            "Debug Last Errors Endpoint (No Auth)", 
            success,
            f"Status: {status}, Errors count: {len(response) if isinstance(response, list) else 'N/A'}"
        )
        
        # Test 2: POST /api/debug/create-test-article (admin auth required)
        if not self.token:
            self.log_test(
                "Debug Create Test Article (Auth Required)", 
                False,
                "No authentication token available"
            )
            return False
        
        # Test 2a: Create regular test article
        test_article_data = {
            "is_breaking": False,
            "pin": False
        }
        
        success, response, status = self.make_request(
            'POST', 
            'debug/create-test-article',
            data=test_article_data,
            auth_required=True
        )
        
        if success and 'article' in response:
            article_id = response['article'].get('id')
            if article_id:
                self.created_articles.append(article_id)
        
        self.log_test(
            "Create Regular Test Article", 
            success,
            f"Status: {status}, Article ID: {response.get('article', {}).get('id', 'N/A') if success else response.get('error', 'Unknown')}"
        )
        
        # Test 2b: Create breaking news test article
        breaking_article_data = {
            "is_breaking": True,
            "pin": False
        }
        
        success, response, status = self.make_request(
            'POST', 
            'debug/create-test-article',
            data=breaking_article_data,
            auth_required=True
        )
        
        if success and 'article' in response:
            article_id = response['article'].get('id')
            if article_id:
                self.created_articles.append(article_id)
        
        self.log_test(
            "Create Breaking News Test Article", 
            success,
            f"Status: {status}, Breaking: {response.get('article', {}).get('is_breaking', 'N/A') if success else response.get('error', 'Unknown')}"
        )
        
        # Test 2c: Create pinned test article
        pinned_article_data = {
            "is_breaking": False,
            "pin": True
        }
        
        success, response, status = self.make_request(
            'POST', 
            'debug/create-test-article',
            data=pinned_article_data,
            auth_required=True
        )
        
        if success and 'article' in response:
            article_id = response['article'].get('id')
            if article_id:
                self.created_articles.append(article_id)
        
        self.log_test(
            "Create Pinned Test Article", 
            success,
            f"Status: {status}, Pinned: {response.get('article', {}).get('pinned_at') is not None if success else response.get('error', 'Unknown')}"
        )
        
        # Test 2d: Create pinned + breaking test article
        pinned_breaking_data = {
            "is_breaking": True,
            "pin": True
        }
        
        success, response, status = self.make_request(
            'POST', 
            'debug/create-test-article',
            data=pinned_breaking_data,
            auth_required=True
        )
        
        if success and 'article' in response:
            article_id = response['article'].get('id')
            if article_id:
                self.created_articles.append(article_id)
        
        self.log_test(
            "Create Pinned + Breaking Test Article", 
            success,
            f"Status: {status}, Pinned+Breaking: {response.get('article', {}).get('is_breaking', False) and response.get('article', {}).get('pinned_at') is not None if success else response.get('error', 'Unknown')}"
        )
        
        return True

    def test_pinning_system_integration(self) -> bool:
        """Test pinning system integration with article creation"""
        print("\n📌 PINNING SYSTEM INTEGRATION TESTING")
        print("-" * 40)
        
        if not self.token:
            self.log_test(
                "Pinning System Integration", 
                False,
                "No authentication token available"
            )
            return False
        
        # Test 1: JSON endpoint /api/articles.json with pin and priority
        json_article_data = {
            "title": f"Test JSON Article with Pinning {datetime.now().strftime('%H:%M:%S')}",
            "content": "This is a test article created via JSON endpoint to test pinning functionality.",
            "category": "news",
            "pin": True,
            "priority": 8,
            "is_breaking": False,
            "tags": ["test", "pinning", "json"],
            "category_labels": ["News", "Special"]
        }
        
        success, response, status = self.make_request(
            'POST', 
            'articles.json',
            data=json_article_data,
            auth_required=True
        )
        
        json_pinned_correctly = False
        if success and 'pinned_at' in response:
            json_pinned_correctly = response['pinned_at'] is not None
            if response.get('id'):
                self.created_articles.append(response['id'])
        
        self.log_test(
            "JSON Endpoint Pin Integration", 
            success and json_pinned_correctly,
            f"Status: {status}, Pinned: {json_pinned_correctly}, Priority: {response.get('priority', 'N/A') if success else response.get('error', 'Unknown')}"
        )
        
        # Test 2: Priority field handling (0-10 range)
        priority_tests = [
            {"priority": 0, "expected": True},
            {"priority": 5, "expected": True},
            {"priority": 10, "expected": True},
        ]
        
        priority_results = []
        for test_case in priority_tests:
            priority_article_data = {
                "title": f"Priority Test Article {test_case['priority']} {datetime.now().strftime('%H:%M:%S')}",
                "content": f"Testing priority level {test_case['priority']}",
                "category": "news",
                "pin": False,
                "priority": test_case['priority'],
                "is_breaking": False
            }
            
            success, response, status = self.make_request(
                'POST', 
                'articles.json',
                data=priority_article_data,
                auth_required=True
            )
            
            priority_correct = False
            if success and 'priority' in response:
                priority_correct = response['priority'] == test_case['priority']
                if response.get('id'):
                    self.created_articles.append(response['id'])
            
            priority_results.append(priority_correct)
        
        all_priorities_valid = all(priority_results)
        self.log_test(
            "Priority Field Handling (0-10)", 
            all_priorities_valid,
            f"Tested priorities: {[test['priority'] for test in priority_tests]}, Results: {priority_results}"
        )
        
        return success and json_pinned_correctly and all_priorities_valid

    def test_database_migration_validation(self) -> bool:
        """Test database migration validation by checking article fields"""
        print("\n🗄️ DATABASE MIGRATION VALIDATION")
        print("-" * 40)
        
        # Test by creating an article and verifying all new fields are present
        if not self.token:
            self.log_test(
                "Database Migration Validation", 
                False,
                "No authentication token available"
            )
            return False
        
        # Create a comprehensive test article with all new fields
        migration_test_data = {
            "title": f"Migration Test Article {datetime.now().strftime('%H:%M:%S')}",
            "content": "This article tests all new database fields from the migration.",
            "category": "news",
            "pin": True,
            "priority": 7,
            "is_breaking": True,
            "tags": ["migration", "test", "database"],
            "category_labels": ["News", "Breaking", "Special"]
        }
        
        success, response, status = self.make_request(
            'POST', 
            'articles.json',
            data=migration_test_data,
            auth_required=True
        )
        
        if not success:
            self.log_test(
                "Article Creation with New Fields", 
                False,
                f"Status: {status}, Error: {response.get('error', 'Unknown')}"
            )
            return False
        
        # Track created article for cleanup
        if response.get('id'):
            self.created_articles.append(response['id'])
        
        # Validate all new fields are present and correct
        required_fields = ['pinned_at', 'priority']
        fields_present = all(field in response for field in required_fields)
        
        pinned_at_valid = response.get('pinned_at') is not None  # Should be set since pin=True
        priority_valid = response.get('priority') == 7
        breaking_valid = response.get('is_breaking') == True
        
        self.log_test(
            "Article Creation with New Fields", 
            True,
            f"Article ID: {response.get('id')}"
        )
        
        self.log_test(
            "Pinned_at Field Migration", 
            pinned_at_valid,
            f"Pinned_at: {response.get('pinned_at', 'Missing')}"
        )
        
        self.log_test(
            "Priority Field Migration", 
            priority_valid,
            f"Priority: {response.get('priority', 'Missing')}/7 expected"
        )
        
        # Test retrieval to ensure fields persist
        article_slug = response.get('slug')
        if article_slug:
            success, retrieved_article, status = self.make_request(
                'GET', 
                f'articles/{article_slug}',
                auth_required=False
            )
            
            if success:
                retrieval_fields_valid = all(field in retrieved_article for field in required_fields)
                self.log_test(
                    "Field Persistence After Retrieval", 
                    retrieval_fields_valid,
                    f"Retrieved fields: {list(retrieved_article.keys())}"
                )
            else:
                self.log_test(
                    "Field Persistence After Retrieval", 
                    False,
                    f"Could not retrieve article: {status}"
                )
        
        return fields_present and pinned_at_valid and priority_valid

    def test_top_rail_with_mixed_articles(self) -> bool:
        """Test top rail with mix of pinned, unpinned, breaking, and regular articles"""
        print("\n🔄 TOP RAIL WITH MIXED ARTICLES TESTING")
        print("-" * 40)
        
        # After creating test articles, test the top rail again to see ordering
        success, response, status = self.make_request('GET', 'top-rail', auth_required=False)
        
        if not success:
            self.log_test(
                "Top Rail with Mixed Articles", 
                False,
                f"Status: {status}, Error: {response.get('error', 'Unknown')}"
            )
            return False
        
        # Analyze the articles in the top rail
        all_articles = []
        lead_article = response.get('lead')
        secondary_articles = response.get('secondary', [])
        more_articles = response.get('more', [])
        
        if lead_article:
            all_articles.append(lead_article)
        all_articles.extend(secondary_articles)
        all_articles.extend(more_articles)
        
        # Count different types of articles
        pinned_count = sum(1 for article in all_articles if article.get('pinned_at'))
        breaking_count = sum(1 for article in all_articles if article.get('is_breaking'))
        regular_count = len(all_articles) - pinned_count
        
        self.log_test(
            "Top Rail Mixed Articles Analysis", 
            True,
            f"Total: {len(all_articles)}, Pinned: {pinned_count}, Breaking: {breaking_count}, Regular: {regular_count}"
        )
        
        # Verify pinned articles appear first
        pinned_first = True
        found_unpinned = False
        for article in all_articles:
            if article.get('pinned_at'):
                if found_unpinned:
                    pinned_first = False
                    break
            else:
                found_unpinned = True
        
        self.log_test(
            "Pinned Articles First Priority", 
            pinned_first,
            "Pinned articles should appear before unpinned articles"
        )
        
        return pinned_first

    def cleanup_test_articles(self):
        """Clean up created test articles"""
        if not self.created_articles or not self.token:
            return
        
        print("\n🧹 CLEANING UP TEST ARTICLES")
        print("-" * 40)
        
        cleaned_count = 0
        for article_id in self.created_articles:
            success, response, status = self.make_request(
                'DELETE', 
                f'articles/{article_id}',
                auth_required=True
            )
            if success:
                cleaned_count += 1
        
        print(f"   Cleaned up {cleaned_count}/{len(self.created_articles)} test articles")

    def run_all_tests(self) -> bool:
        """Run all test suites"""
        print("🧪 STARTING GB NEWS TOP RAIL SYSTEM TESTS")
        print("=" * 80)
        
        # Test 1: Authentication
        if not self.test_admin_login():
            print("\n❌ CRITICAL: Authentication failed - cannot proceed with authenticated tests")
            return False
        
        # Test 2: Top Rail Endpoint
        top_rail_success = self.test_top_rail_endpoint()
        
        # Test 3: Mobile Debug Endpoints
        mobile_debug_success = self.test_mobile_debug_endpoints()
        
        # Test 4: Pinning System Integration
        pinning_success = self.test_pinning_system_integration()
        
        # Test 5: Database Migration Validation
        migration_success = self.test_database_migration_validation()
        
        # Test 6: Top Rail with Mixed Articles (after creating test articles)
        mixed_articles_success = self.test_top_rail_with_mixed_articles()
        
        # Cleanup
        self.cleanup_test_articles()
        
        # Results Summary
        print("\n" + "=" * 80)
        print("📊 GB NEWS TOP RAIL SYSTEM TEST RESULTS")
        print("=" * 80)
        
        print(f"Tests Run: {self.tests_run}")
        print(f"Tests Passed: {self.tests_passed}")
        print(f"Tests Failed: {self.tests_run - self.tests_passed}")
        print(f"Success Rate: {(self.tests_passed/self.tests_run)*100:.1f}%")
        
        print(f"\n🎯 TEST SUITE RESULTS:")
        print(f"   Authentication: {'✅' if self.token else '❌'}")
        print(f"   Top Rail Endpoint: {'✅' if top_rail_success else '❌'}")
        print(f"   Mobile Debug Endpoints: {'✅' if mobile_debug_success else '❌'}")
        print(f"   Pinning System Integration: {'✅' if pinning_success else '❌'}")
        print(f"   Database Migration: {'✅' if migration_success else '❌'}")
        print(f"   Mixed Articles Ordering: {'✅' if mixed_articles_success else '❌'}")
        
        overall_success = all([
            self.token is not None,
            top_rail_success,
            mobile_debug_success,
            pinning_success,
            migration_success,
            mixed_articles_success
        ])
        
        if overall_success:
            print(f"\n🎉 ALL GB NEWS TOP RAIL SYSTEM TESTS PASSED!")
        else:
            print(f"\n⚠️ SOME TESTS FAILED - Review results above")
        
        return overall_success

def main():
    """Main test execution"""
    tester = GBNewsTopRailTester()
    success = tester.run_all_tests()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())