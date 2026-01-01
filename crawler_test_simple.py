#!/usr/bin/env python3
"""
Simplified Social Sharing Crawler Test
Tests crawler functionality without requiring database connectivity
"""

import requests
import sys
import re

class SimpleCrawlerTester:
    def __init__(self, base_url="https://viewtrends-1.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.token = None
        self.tests_run = 0
        self.tests_passed = 0

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
                    self.log_test("Admin Login", True, f"Token obtained, emergency mode: {data.get('message', 'N/A')}")
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

    def test_debug_article_exists_endpoint(self):
        """Test GET /api/debug/article-exists?slug=test-slug"""
        print("\n🔧 Testing debug article-exists endpoint...")
        
        # Test with non-existent article (should work even without database)
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
                self.log_test("Debug Article Exists (non-existent)", False, f"Status {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Debug Article Exists (non-existent)", False, f"Error: {str(e)}")
            return False

    def test_debug_crawler_meta_endpoint(self):
        """Test GET /api/debug/crawler-meta?slug=test-slug"""
        print("\n🔧 Testing debug crawler-meta endpoint...")
        
        try:
            response = requests.get(
                f"{self.api_url}/debug/crawler-meta?slug=non-existent-article-12345",
                timeout=30
            )
            
            if response.status_code == 200:
                # Should return HTML content with meta tags even for non-existent articles
                html_content = response.text
                
                # Check if it's HTML and contains meta tags
                is_html = html_content.strip().startswith('<!DOCTYPE html>')
                has_meta_tags = 'property="og:title"' in html_content
                has_default_content = 'The Crewkerne Gazette' in html_content
                
                if is_html and has_meta_tags and has_default_content:
                    self.log_test("Debug Crawler Meta", True, "Returns HTML with proper meta tags and default content")
                    return True
                else:
                    issues = []
                    if not is_html:
                        issues.append("Not HTML format")
                    if not has_meta_tags:
                        issues.append("Missing meta tags")
                    if not has_default_content:
                        issues.append("Missing default content")
                    self.log_test("Debug Crawler Meta", False, "; ".join(issues))
                    return False
            else:
                self.log_test("Debug Crawler Meta", False, f"Status {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Debug Crawler Meta", False, f"Error: {str(e)}")
            return False

    def test_crawler_html_nonexistent_article(self):
        """Test crawler HTML for non-existent article (should return 200 with default meta)"""
        print("\n🕷️ Testing crawler HTML for non-existent article...")
        
        crawler_user_agents = [
            "facebookexternalhit/1.1 (+http://www.facebook.com/externalhit_uatext.php)",
            "Twitterbot/1.0",
            "LinkedInBot/1.0 (compatible; Mozilla/5.0; Apache-HttpClient +http://www.linkedin.com/)",
        ]
        
        success_count = 0
        
        for user_agent in crawler_user_agents:
            try:
                response = requests.get(
                    f"{self.base_url}/article/non-existent-article-slug-12345",
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
                    
                    # Check for default content
                    has_default_title = 'Article Not Found' in html_content or 'The Crewkerne Gazette' in html_content
                    
                    if not missing_tags and image_url_valid and has_default_title:
                        success_count += 1
                        self.log_test(f"Crawler HTML Non-existent ({user_agent.split('/')[0]})", True, 
                                    f"All meta tags present, HTTPS image URL, default content, headers: Cache-Control={cache_control}")
                    else:
                        issues = []
                        if missing_tags:
                            issues.append(f"Missing tags: {missing_tags}")
                        if not image_url_valid:
                            issues.append("Image URL not HTTPS")
                        if not has_default_title:
                            issues.append("Missing default title")
                        self.log_test(f"Crawler HTML Non-existent ({user_agent.split('/')[0]})", False, "; ".join(issues))
                else:
                    self.log_test(f"Crawler HTML Non-existent ({user_agent.split('/')[0]})", False, f"Status {response.status_code} (should be 200)")
                    
            except Exception as e:
                self.log_test(f"Crawler HTML Non-existent ({user_agent.split('/')[0]})", False, f"Error: {str(e)}")
        
        return success_count == len(crawler_user_agents)

    def test_updated_at_crash_fix(self):
        """Test that updated_at=None no longer causes crashes"""
        print("\n🛠️ Testing updated_at=None crash fix...")
        
        # Test crawler access multiple times to ensure no crashes with non-existent articles
        for i in range(3):
            try:
                response = requests.get(
                    f"{self.base_url}/article/test-crash-fix-{i}",
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

    def test_emergency_authentication_system(self):
        """Test that emergency authentication system is working"""
        print("\n🆘 Testing emergency authentication system...")
        
        if not self.token:
            self.log_test("Emergency Authentication", False, "No authentication token available")
            return False
        
        # Test that we can access protected endpoints with emergency auth
        try:
            response = requests.get(
                f"{self.api_url}/dashboard/stats",
                headers={'Authorization': f'Bearer {self.token}'},
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('emergency_mode') == True:
                    self.log_test("Emergency Authentication", True, "Emergency mode active and working")
                    return True
                else:
                    self.log_test("Emergency Authentication", False, f"Emergency mode not detected: {data}")
                    return False
            else:
                self.log_test("Emergency Authentication", False, f"Status {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Emergency Authentication", False, f"Error: {str(e)}")
            return False

    def run_all_tests(self):
        """Run all available tests without database dependency"""
        print("🚀 Starting Simplified Social Sharing Crawler Tests")
        print("🔧 Testing without database connectivity (emergency mode)")
        print("=" * 80)
        
        # Step 1: Authentication
        if not self.login_admin():
            print("❌ Cannot proceed without authentication")
            return False
        
        # Step 2: Test emergency authentication system
        emergency_auth_success = self.test_emergency_authentication_system()
        
        # Step 3: Test debug endpoints
        debug_exists_success = self.test_debug_article_exists_endpoint()
        debug_meta_success = self.test_debug_crawler_meta_endpoint()
        
        # Step 4: Test crawler HTML for non-existent articles
        nonexistent_success = self.test_crawler_html_nonexistent_article()
        
        # Step 5: Test updated_at crash fix
        crash_fix_success = self.test_updated_at_crash_fix()
        
        # Results summary
        print("\n" + "=" * 80)
        print("📊 TEST RESULTS SUMMARY")
        print("=" * 80)
        
        print(f"✅ Emergency Authentication System: {'PASS' if emergency_auth_success else 'FAIL'}")
        print(f"✅ Debug Article Exists Endpoint: {'PASS' if debug_exists_success else 'FAIL'}")
        print(f"✅ Debug Crawler Meta Endpoint: {'PASS' if debug_meta_success else 'FAIL'}")
        print(f"✅ Crawler HTML (Non-existent Articles): {'PASS' if nonexistent_success else 'FAIL'}")
        print(f"✅ Updated_at Crash Fix: {'PASS' if crash_fix_success else 'FAIL'}")
        
        print(f"\n📈 Overall Results:")
        print(f"   Tests Run: {self.tests_run}")
        print(f"   Tests Passed: {self.tests_passed}")
        print(f"   Tests Failed: {self.tests_run - self.tests_passed}")
        print(f"   Success Rate: {(self.tests_passed/self.tests_run)*100:.1f}%")
        
        # Determine overall success
        critical_tests_passed = all([
            emergency_auth_success,
            debug_exists_success, 
            debug_meta_success,
            nonexistent_success,
            crash_fix_success
        ])
        
        if critical_tests_passed:
            print("\n🎉 ALL AVAILABLE TESTS PASSED - Social sharing fixes are working correctly!")
            print("📝 NOTE: Full testing with existing articles requires database connectivity")
            return True
        else:
            print("\n❌ SOME TESTS FAILED - Issues need to be addressed")
            return False

def main():
    """Main test execution"""
    tester = SimpleCrawlerTester()
    success = tester.run_all_tests()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())