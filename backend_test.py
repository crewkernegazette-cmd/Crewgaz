import requests
import sys
from datetime import datetime
import json

class CrewkerneGazetteAPITester:
    def __init__(self, base_url="https://news-cms.preview.emergentagent.com"):
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

    def test_auth_me(self):
        """Test getting current user info"""
        success, response = self.run_test(
            "Get Current User",
            "GET",
            "auth/me",
            200
        )
        return success

    def test_create_article(self):
        """Test creating a new article"""
        article_data = {
            "title": f"Test Article {datetime.now().strftime('%H%M%S')}",
            "content": "This is a test article content for API testing purposes.",
            "category": "news",
            "featured_image": "https://example.com/test-image.jpg",
            "video_url": "https://example.com/test-video.mp4",
            "is_breaking": True,
            "is_published": True,
            "tags": ["test", "api", "automation"]
        }
        
        success, response = self.run_test(
            "Create Article",
            "POST",
            "articles",
            200,
            data=article_data
        )
        
        if success and 'id' in response:
            self.created_article_id = response['id']
            print(f"   Created article ID: {self.created_article_id}")
            return True
        return False

    def test_get_articles(self):
        """Test getting all articles"""
        success, response = self.run_test(
            "Get All Articles",
            "GET",
            "articles",
            200
        )
        return success

    def test_get_articles_by_category(self):
        """Test getting articles by category"""
        success, response = self.run_test(
            "Get News Articles",
            "GET",
            "articles?category=news",
            200
        )
        return success

    def test_get_breaking_news(self):
        """Test getting breaking news"""
        success, response = self.run_test(
            "Get Breaking News",
            "GET",
            "articles?is_breaking=true",
            200
        )
        return success

    def test_get_single_article(self):
        """Test getting a single article"""
        if not self.created_article_id:
            print("❌ Skipping - No article ID available")
            return False
            
        success, response = self.run_test(
            "Get Single Article",
            "GET",
            f"articles/{self.created_article_id}",
            200
        )
        return success

    def test_update_article(self):
        """Test updating an article"""
        if not self.created_article_id:
            print("❌ Skipping - No article ID available")
            return False
            
        update_data = {
            "title": f"Updated Test Article {datetime.now().strftime('%H%M%S')}",
            "is_breaking": False
        }
        
        success, response = self.run_test(
            "Update Article",
            "PUT",
            f"articles/{self.created_article_id}",
            200,
            data=update_data
        )
        return success

    def test_dashboard_articles(self):
        """Test getting dashboard articles"""
        success, response = self.run_test(
            "Get Dashboard Articles",
            "GET",
            "dashboard/articles",
            200
        )
        return success

    def test_dashboard_stats(self):
        """Test getting dashboard stats"""
        success, response = self.run_test(
            "Get Dashboard Stats",
            "GET",
            "dashboard/stats",
            200
        )
        return success

    def test_delete_article(self):
        """Test deleting an article"""
        if not self.created_article_id:
            print("❌ Skipping - No article ID available")
            return False
            
        success, response = self.run_test(
            "Delete Article",
            "DELETE",
            f"articles/{self.created_article_id}",
            200
        )
        return success

    def test_invalid_login(self):
        """Test login with invalid credentials"""
        success, response = self.run_test(
            "Invalid Login Test",
            "POST",
            "auth/login",
            401,
            data={"username": "invalid", "password": "invalid"}
        )
        return success

def main():
    print("🚀 Starting Crewkerne Gazette API Tests")
    print("=" * 50)
    
    tester = CrewkerneGazetteAPITester()
    
    # Authentication Tests
    print("\n📋 AUTHENTICATION TESTS")
    print("-" * 30)
    
    if not tester.test_login():
        print("❌ Login failed, stopping tests")
        return 1
    
    tester.test_auth_me()
    tester.test_invalid_login()
    
    # Article CRUD Tests
    print("\n📋 ARTICLE CRUD TESTS")
    print("-" * 30)
    
    tester.test_create_article()
    tester.test_get_articles()
    tester.test_get_articles_by_category()
    tester.test_get_breaking_news()
    tester.test_get_single_article()
    tester.test_update_article()
    
    # Dashboard Tests
    print("\n📋 DASHBOARD TESTS")
    print("-" * 30)
    
    tester.test_dashboard_articles()
    tester.test_dashboard_stats()
    
    # Cleanup
    print("\n📋 CLEANUP TESTS")
    print("-" * 30)
    
    tester.test_delete_article()
    
    # Final Results
    print("\n" + "=" * 50)
    print(f"📊 FINAL RESULTS")
    print(f"Tests Run: {tester.tests_run}")
    print(f"Tests Passed: {tester.tests_passed}")
    print(f"Tests Failed: {tester.tests_run - tester.tests_passed}")
    print(f"Success Rate: {(tester.tests_passed/tester.tests_run)*100:.1f}%")
    
    if tester.tests_passed == tester.tests_run:
        print("🎉 All tests passed!")
        return 0
    else:
        print("⚠️  Some tests failed!")
        return 1

if __name__ == "__main__":
    sys.exit(main())