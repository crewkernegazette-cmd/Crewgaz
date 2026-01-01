#!/usr/bin/env python3
"""
Social Sharing Crawler HTML and Debug Endpoints Test
Tests the newly implemented social sharing crawler fixes and debug endpoints
"""

import requests
import sys
from datetime import datetime
import json
import re
from urllib.parse import urljoin

class SocialSharingTester:
    def __init__(self, base_url="https://viewtrends-1.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.token = None
        self.tests_run = 0
        self.tests_passed = 0
        self.test_article_slug = None
        self.test_article_id = None

    def log_test(self, name, success, details=""):
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

    def login_admin(self):
        """Login with admin credentials"""
        print("\n🔐 Authenticating as admin...")
        
        try:
            response = requests.post(
                f"{self.api_url}/auth/login",
                json={"username": "admin", "password": "admin123"},
                headers={'Content-Type': 'application/json'},
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                if 'access_token' in data:
                    self.token = data['access_token']
                    self.log_test("Admin Login", True, f"Token obtained: {self.token[:20]}...")
                    return True
                else:
                    self.log_test("Admin Login", False, "No access_token in response")
                    return False
            else:
                self.log_test("Admin Login", False, f"Status {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Admin Login", False, f"Error: {str(e)}")
            return False

    def create_test_article(self):
        """Create a test article for crawler testing"""
        print("\n📝 Creating test article for crawler testing...")
        
        if not self.token:
            self.log_test("Create Test Article", False, "No authentication token")
            return False
        
        # Create article with comprehensive data for testing
        article_data = {
            "title": "Test Article for Social Sharing Crawler",
            "subheading": "This is a test subheading for social media preview testing",
            "content": "<p>This is a comprehensive test article created to verify social sharing crawler functionality. It includes <strong>HTML content</strong> and proper meta tag generation.</p><p>The article should display correctly on Facebook, Twitter, LinkedIn and other social media platforms.</p>",
            "category": "news",
            "publisher_name": "The Crewkerne Gazette",
            "featured_image": "https://via.placeholder.com/1200x630/0066cc/ffffff?text=Test+Article+Image",
            "image_caption": "Test image for social sharing",
            "tags": ["test", "social-sharing", "crawler"],
            "category_labels": ["News", "Special"],
            "is_breaking": False,
            "is_published": True,
            "pin": False,
            "priority": 5
        }
        
        try:
            response = requests.post(
                f"{self.api_url}/articles.json",
                json=article_data,
                headers={
                    'Content-Type': 'application/json',
                    'Authorization': f'Bearer {self.token}'
                },
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                self.test_article_slug = data.get('slug')
                self.test_article_id = data.get('id')
                self.log_test("Create Test Article", True, f"Article created with slug: {self.test_article_slug}")
                return True
            else:
                self.log_test("Create Test Article", False, f"Status {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Create Test Article", False, f"Error: {str(e)}")
            return False

    def test_crawler_html_endpoint(self):
        """Test the /article/{slug} endpoint with crawler User-Agent"""
        print("\n🕷️ Testing Social Sharing Crawler HTML...")
        
        if not self.test_article_slug:
            self.log_test("Crawler HTML Test", False, "No test article available")
            return False
        
        # Test with Facebook crawler User-Agent
        crawler_user_agents = [
            "facebookexternalhit/1.1 (+http://www.facebook.com/externalhit_uatext.php)",
            "Twitterbot/1.0",
            "LinkedInBot/1.0 (compatible; Mozilla/5.0; Apache-HttpClient +http://www.linkedin.com/)",
            "WhatsApp/2.19.81 A"
        ]
        
        success_count = 0
        
        for user_agent in crawler_user_agents:
            try:
                response = requests.get(
                    f"{self.base_url}/article/{self.test_article_slug}",
                    headers={'User-Agent': user_agent},
                    timeout=30
                )
                
                if response.status_code == 200:
                    html_content = response.text
                    
                    # Check for required meta tags
                    required_tags = [
                        'og:title',
                        'og:description', 
                        'og:image',
                        'og:type',
                        'og:url',
                        'twitter:card',
                        'twitter:title',
                        'twitter:description',
                        'twitter:image'
                    ]
                    
                    missing_tags = []
                    for tag in required_tags:
                        if f'property="{tag}"' not in html_content and f'name="{tag}"' not in html_content:
                            missing_tags.append(tag)
                    
                    # Check for absolute HTTPS URLs in og:image
                    og_image_match = re.search(r'property="og:image"\s+content="([^"]+)"', html_content)
                    image_url_valid = False
                    if og_image_match:
                        image_url = og_image_match.group(1)
                        image_url_valid = image_url.startswith('https://')
                    
                    # Check for proper HTTP headers
                    cache_control = response.headers.get('Cache-Control', '')
                    x_robots_tag = response.headers.get('X-Robots-Tag', '')
                    
                    if not missing_tags and image_url_valid:
                        success_count += 1
                        self.log_test(f"Crawler HTML ({user_agent.split('/')[0]})", True, 
                                    f"All meta tags present, HTTPS image URL, headers: Cache-Control={cache_control}, X-Robots-Tag={x_robots_tag}")
                    else:
                        issues = []
                        if missing_tags:
                            issues.append(f"Missing tags: {missing_tags}")
                        if not image_url_valid:
                            issues.append("Image URL not HTTPS")
                        self.log_test(f"Crawler HTML ({user_agent.split('/')[0]})", False, "; ".join(issues))
                else:
                    self.log_test(f"Crawler HTML ({user_agent.split('/')[0]})", False, f"Status {response.status_code}")
                    
            except Exception as e:
                self.log_test(f"Crawler HTML ({user_agent.split('/')[0]})", False, f"Error: {str(e)}")
        
        return success_count == len(crawler_user_agents)

    def test_crawler_html_nonexistent_article(self):
        """Test crawler HTML for non-existent article (should return 200 with default meta)"""
        print("\n🔍 Testing crawler HTML for non-existent article...")
        
        try:
            response = requests.get(
                f"{self.base_url}/article/non-existent-article-slug-12345",
                headers={'User-Agent': 'facebookexternalhit/1.1'},
                timeout=30
            )
            
            if response.status_code == 200:
                html_content = response.text
                
                # Should contain default meta tags
                has_title = 'Article Not Found' in html_content or 'The Crewkerne Gazette' in html_content
                has_og_tags = 'property="og:title"' in html_content
                
                if has_title and has_og_tags:
                    self.log_test("Non-existent Article Crawler HTML", True, "Returns 200 with default meta tags")
                    return True
                else:
                    self.log_test("Non-existent Article Crawler HTML", False, "Missing default meta tags")
                    return False
            else:
                self.log_test("Non-existent Article Crawler HTML", False, f"Status {response.status_code} (should be 200)")
                return False
                
        except Exception as e:
            self.log_test("Non-existent Article Crawler HTML", False, f"Error: {str(e)}")
            return False

    def test_debug_article_exists_endpoint(self):
        """Test GET /api/debug/article-exists?slug=test-slug"""
        print("\n🔧 Testing debug article-exists endpoint...")
        
        # Test with existing article
        if self.test_article_slug:
            try:
                response = requests.get(
                    f"{self.api_url}/debug/article-exists?slug={self.test_article_slug}",
                    timeout=30
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get('exists') == True and 'article_id' in data and 'title' in data:
                        self.log_test("Debug Article Exists (existing)", True, f"Found article: {data.get('title')}")
                    else:
                        self.log_test("Debug Article Exists (existing)", False, f"Invalid response format: {data}")
                        return False
                else:
                    self.log_test("Debug Article Exists (existing)", False, f"Status {response.status_code}")
                    return False
                    
            except Exception as e:
                self.log_test("Debug Article Exists (existing)", False, f"Error: {str(e)}")
                return False
        
        # Test with non-existent article
        try:
            response = requests.get(
                f"{self.api_url}/debug/article-exists?slug=non-existent-article-12345",
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('exists') == False:
                    self.log_test("Debug Article Exists (non-existent)", True, "Correctly reports non-existent article")
                    return True
                else:
                    self.log_test("Debug Article Exists (non-existent)", False, f"Should report exists=false: {data}")
                    return False
            else:
                self.log_test("Debug Article Exists (non-existent)", False, f"Status {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Debug Article Exists (non-existent)", False, f"Error: {str(e)}")
            return False

    def test_debug_crawler_meta_endpoint(self):
        """Test GET /api/debug/crawler-meta?slug=test-slug"""
        print("\n🔧 Testing debug crawler-meta endpoint...")
        
        if not self.test_article_slug:
            self.log_test("Debug Crawler Meta", False, "No test article available")
            return False
        
        try:
            response = requests.get(
                f"{self.api_url}/debug/crawler-meta?slug={self.test_article_slug}",
                timeout=30
            )
            
            if response.status_code == 200:
                # Should return HTML content with meta tags
                html_content = response.text
                
                # Check if it's HTML and contains meta tags
                is_html = html_content.strip().startswith('<!DOCTYPE html>')
                has_meta_tags = 'property="og:title"' in html_content
                has_preview_info = 'Test Article for Social Sharing Crawler' in html_content
                
                if is_html and has_meta_tags and has_preview_info:
                    self.log_test("Debug Crawler Meta", True, "Returns HTML with proper meta tags and article info")
                    return True
                else:
                    issues = []
                    if not is_html:
                        issues.append("Not HTML format")
                    if not has_meta_tags:
                        issues.append("Missing meta tags")
                    if not has_preview_info:
                        issues.append("Missing article info")
                    self.log_test("Debug Crawler Meta", False, "; ".join(issues))
                    return False
            else:
                self.log_test("Debug Crawler Meta", False, f"Status {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Debug Crawler Meta", False, f"Error: {str(e)}")
            return False

    def test_article_creation_retrieval(self):
        """Test existing article functionality still works"""
        print("\n📚 Testing existing article functionality...")
        
        # Test GET /api/articles
        try:
            response = requests.get(f"{self.api_url}/articles", timeout=30)
            
            if response.status_code == 200:
                articles = response.json()
                if isinstance(articles, list):
                    self.log_test("Get Articles List", True, f"Retrieved {len(articles)} articles")
                else:
                    self.log_test("Get Articles List", False, "Response is not a list")
                    return False
            else:
                self.log_test("Get Articles List", False, f"Status {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Get Articles List", False, f"Error: {str(e)}")
            return False
        
        # Test GET /api/top-rail
        try:
            response = requests.get(f"{self.api_url}/top-rail", timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                if 'lead' in data and 'secondary' in data and 'more' in data:
                    self.log_test("Get Top Rail", True, "Top rail structure is correct")
                else:
                    self.log_test("Get Top Rail", False, f"Invalid top rail structure: {list(data.keys())}")
                    return False
            else:
                self.log_test("Get Top Rail", False, f"Status {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Get Top Rail", False, f"Error: {str(e)}")
            return False
        
        # Test individual article retrieval
        if self.test_article_slug:
            try:
                response = requests.get(f"{self.api_url}/articles/{self.test_article_slug}", timeout=30)
                
                if response.status_code == 200:
                    article = response.json()
                    if article.get('slug') == self.test_article_slug:
                        self.log_test("Get Individual Article", True, f"Retrieved article: {article.get('title')}")
                        return True
                    else:
                        self.log_test("Get Individual Article", False, "Article slug mismatch")
                        return False
                else:
                    self.log_test("Get Individual Article", False, f"Status {response.status_code}")
                    return False
                    
            except Exception as e:
                self.log_test("Get Individual Article", False, f"Error: {str(e)}")
                return False
        
        return True

    def test_updated_at_crash_fix(self):
        """Test that updated_at=None no longer causes crashes"""
        print("\n🛠️ Testing updated_at=None crash fix...")
        
        if not self.test_article_slug:
            self.log_test("Updated_at Crash Fix", False, "No test article available")
            return False
        
        # Test crawler access multiple times to ensure no crashes
        for i in range(3):
            try:
                response = requests.get(
                    f"{self.base_url}/article/{self.test_article_slug}",
                    headers={'User-Agent': 'facebookexternalhit/1.1'},
                    timeout=30
                )
                
                if response.status_code != 200:
                    self.log_test(f"Updated_at Crash Fix (attempt {i+1})", False, f"Status {response.status_code}")
                    return False
                    
            except Exception as e:
                self.log_test(f"Updated_at Crash Fix (attempt {i+1})", False, f"Error: {str(e)}")
                return False
        
        self.log_test("Updated_at Crash Fix", True, "No crashes detected in multiple crawler requests")
        return True

    def cleanup_test_article(self):
        """Clean up the test article"""
        if self.test_article_slug and self.token:
            try:
                response = requests.delete(
                    f"{self.api_url}/articles/by-slug/{self.test_article_slug}",
                    headers={'Authorization': f'Bearer {self.token}'},
                    timeout=30
                )
                
                if response.status_code == 200:
                    print(f"🧹 Cleaned up test article: {self.test_article_slug}")
                else:
                    print(f"⚠️ Could not clean up test article: Status {response.status_code}")
                    
            except Exception as e:
                print(f"⚠️ Error cleaning up test article: {str(e)}")

    def run_all_tests(self):
        """Run all social sharing and debug endpoint tests"""
        print("🚀 Starting Social Sharing Crawler HTML and Debug Endpoints Tests")
        print("=" * 80)
        
        # Step 1: Authentication
        if not self.login_admin():
            print("❌ Cannot proceed without authentication")
            return False
        
        # Step 2: Create test article
        if not self.create_test_article():
            print("❌ Cannot proceed without test article")
            return False
        
        try:
            # Step 3: Test social sharing crawler HTML fixes
            crawler_html_success = self.test_crawler_html_endpoint()
            
            # Step 4: Test non-existent article handling
            nonexistent_success = self.test_crawler_html_nonexistent_article()
            
            # Step 5: Test debug endpoints
            debug_exists_success = self.test_debug_article_exists_endpoint()
            debug_meta_success = self.test_debug_crawler_meta_endpoint()
            
            # Step 6: Test existing functionality
            existing_functionality_success = self.test_article_creation_retrieval()
            
            # Step 7: Test updated_at crash fix
            crash_fix_success = self.test_updated_at_crash_fix()
            
            # Results summary
            print("\n" + "=" * 80)
            print("📊 TEST RESULTS SUMMARY")
            print("=" * 80)
            
            print(f"✅ Social Sharing Crawler HTML: {'PASS' if crawler_html_success else 'FAIL'}")
            print(f"✅ Non-existent Article Handling: {'PASS' if nonexistent_success else 'FAIL'}")
            print(f"✅ Debug Article Exists Endpoint: {'PASS' if debug_exists_success else 'FAIL'}")
            print(f"✅ Debug Crawler Meta Endpoint: {'PASS' if debug_meta_success else 'FAIL'}")
            print(f"✅ Existing Article Functionality: {'PASS' if existing_functionality_success else 'FAIL'}")
            print(f"✅ Updated_at Crash Fix: {'PASS' if crash_fix_success else 'FAIL'}")
            
            print(f"\n📈 Overall Results:")
            print(f"   Tests Run: {self.tests_run}")
            print(f"   Tests Passed: {self.tests_passed}")
            print(f"   Tests Failed: {self.tests_run - self.tests_passed}")
            print(f"   Success Rate: {(self.tests_passed/self.tests_run)*100:.1f}%")
            
            # Determine overall success
            critical_tests_passed = all([
                crawler_html_success,
                debug_exists_success, 
                debug_meta_success,
                existing_functionality_success,
                crash_fix_success
            ])
            
            if critical_tests_passed:
                print("\n🎉 ALL CRITICAL TESTS PASSED - Social sharing fixes are working correctly!")
                return True
            else:
                print("\n❌ SOME CRITICAL TESTS FAILED - Issues need to be addressed")
                return False
                
        finally:
            # Always clean up
            self.cleanup_test_article()

def main():
    """Main test execution"""
    tester = SocialSharingTester()
    success = tester.run_all_tests()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())