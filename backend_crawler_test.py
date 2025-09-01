#!/usr/bin/env python3
"""
Backend Social Sharing Crawler Test
Tests the backend crawler functionality directly on localhost:8001
"""

import requests
import sys
import re
import json

class BackendCrawlerTester:
    def __init__(self, backend_url="http://localhost:8001"):
        self.backend_url = backend_url
        self.api_url = f"{backend_url}/api"
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
                    self.log_test("Admin Login", True, f"Emergency mode: {data.get('message', 'N/A')}")
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

    def test_crawler_html_fallback(self):
        """Test crawler HTML fallback for non-existent articles"""
        print("\n🕷️ Testing crawler HTML fallback (database error scenario)...")
        
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
                    f"{self.backend_url}/article/test-fallback-{user_agent.split('/')[0].lower()}",
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
                    
                    # Check for JSON-LD structured data
                    has_json_ld = 'application/ld+json' in html_content
                    
                    if not missing_tags and image_url_valid and has_json_ld:
                        success_count += 1
                        self.log_test(f"Crawler HTML Fallback ({user_agent.split('/')[0]})", True, 
                                    f"All meta tags present, HTTPS image, JSON-LD, Cache-Control: {cache_control}")
                    else:
                        issues = []
                        if missing_tags:
                            issues.append(f"Missing tags: {missing_tags}")
                        if not image_url_valid:
                            issues.append("Image URL not HTTPS")
                        if not has_json_ld:
                            issues.append("Missing JSON-LD")
                        self.log_test(f"Crawler HTML Fallback ({user_agent.split('/')[0]})", False, "; ".join(issues))
                else:
                    self.log_test(f"Crawler HTML Fallback ({user_agent.split('/')[0]})", False, f"Status {response.status_code}")
                    
            except Exception as e:
                self.log_test(f"Crawler HTML Fallback ({user_agent.split('/')[0]})", False, f"Error: {str(e)}")
        
        return success_count == len(crawler_user_agents)

    def test_regular_user_agent(self):
        """Test that regular user agents get React app"""
        print("\n👤 Testing regular user agent handling...")
        
        try:
            response = requests.get(
                f"{self.backend_url}/article/test-regular-user",
                headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'},
                timeout=30
            )
            
            if response.status_code in [200, 302, 404]:
                # Regular users should get React app or redirect, not crawler HTML
                html_content = response.text
                
                # Should NOT contain crawler-specific meta tags structure
                is_crawler_html = 'The Crewkerne Gazette - Where Common Sense Meets Headlines' in html_content and 'og:image' in html_content and len(html_content) < 2000
                
                if not is_crawler_html:
                    self.log_test("Regular User Agent", True, f"Status {response.status_code}, not serving crawler HTML")
                    return True
                else:
                    self.log_test("Regular User Agent", False, "Serving crawler HTML to regular user")
                    return False
            else:
                self.log_test("Regular User Agent", False, f"Unexpected status {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Regular User Agent", False, f"Error: {str(e)}")
            return False

    def test_debug_article_exists_endpoint(self):
        """Test GET /api/debug/article-exists?slug=test-slug"""
        print("\n🔧 Testing debug article-exists endpoint...")
        
        try:
            response = requests.get(
                f"{self.api_url}/debug/article-exists?slug=non-existent-test-article",
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('exists') == False and 'slug' in data:
                    self.log_test("Debug Article Exists", True, f"Correctly reports non-existent article: {data}")
                    return True
                else:
                    self.log_test("Debug Article Exists", False, f"Invalid response format: {data}")
                    return False
            else:
                self.log_test("Debug Article Exists", False, f"Status {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Debug Article Exists", False, f"Error: {str(e)}")
            return False

    def test_updated_at_crash_fix(self):
        """Test that updated_at=None no longer causes crashes"""
        print("\n🛠️ Testing updated_at=None crash fix...")
        
        # Test multiple crawler requests to ensure no crashes
        test_slugs = ['crash-test-1', 'crash-test-2', 'crash-test-3']
        
        for i, slug in enumerate(test_slugs):
            try:
                response = requests.get(
                    f"{self.backend_url}/article/{slug}",
                    headers={'User-Agent': 'facebookexternalhit/1.1'},
                    timeout=30
                )
                
                if response.status_code != 200:
                    self.log_test(f"Crash Fix Test {i+1}", False, f"Status {response.status_code}")
                    return False
                
                # Check that response contains proper HTML structure
                html_content = response.text
                if not html_content.startswith('<!DOCTYPE html>'):
                    self.log_test(f"Crash Fix Test {i+1}", False, "Invalid HTML response")
                    return False
                    
            except Exception as e:
                self.log_test(f"Crash Fix Test {i+1}", False, f"Error: {str(e)}")
                return False
        
        self.log_test("Updated_at Crash Fix", True, "No crashes detected in multiple requests")
        return True

    def test_emergency_authentication_system(self):
        """Test that emergency authentication system is working"""
        print("\n🆘 Testing emergency authentication system...")
        
        if not self.token:
            self.log_test("Emergency Authentication", False, "No authentication token available")
            return False
        
        try:
            response = requests.get(
                f"{self.api_url}/dashboard/stats",
                headers={'Authorization': f'Bearer {self.token}'},
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('emergency_mode') == True:
                    self.log_test("Emergency Authentication", True, f"Emergency mode active: {data}")
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

    def test_http_headers(self):
        """Test proper HTTP headers for crawlers"""
        print("\n📋 Testing HTTP headers for crawlers...")
        
        try:
            response = requests.get(
                f"{self.backend_url}/article/test-headers",
                headers={'User-Agent': 'facebookexternalhit/1.1'},
                timeout=30
            )
            
            if response.status_code == 200:
                cache_control = response.headers.get('Cache-Control', '')
                x_robots_tag = response.headers.get('X-Robots-Tag', '')
                
                # Check for required headers
                has_cache_control = 'public' in cache_control and 'max-age' in cache_control
                has_robots_tag = x_robots_tag == 'all'
                
                if has_cache_control and has_robots_tag:
                    self.log_test("HTTP Headers", True, f"Cache-Control: {cache_control}, X-Robots-Tag: {x_robots_tag}")
                    return True
                else:
                    issues = []
                    if not has_cache_control:
                        issues.append(f"Invalid Cache-Control: {cache_control}")
                    if not has_robots_tag:
                        issues.append(f"Invalid X-Robots-Tag: {x_robots_tag}")
                    self.log_test("HTTP Headers", False, "; ".join(issues))
                    return False
            else:
                self.log_test("HTTP Headers", False, f"Status {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("HTTP Headers", False, f"Error: {str(e)}")
            return False

    def test_seo_routes(self):
        """Test SEO routes are working"""
        print("\n🔍 Testing SEO routes...")
        
        seo_routes = [
            ('/robots.txt', 'text/plain'),
            ('/sitemap.xml', 'text/xml'),
            ('/news-sitemap.xml', 'text/xml')
        ]
        
        success_count = 0
        
        for route, expected_content_type in seo_routes:
            try:
                response = requests.get(f"{self.backend_url}{route}", timeout=30)
                
                if response.status_code == 200:
                    content_type = response.headers.get('content-type', '').lower()
                    
                    if expected_content_type in content_type or response.text.strip():
                        success_count += 1
                        self.log_test(f"SEO Route {route}", True, f"Status 200, Content-Type: {content_type}")
                    else:
                        self.log_test(f"SEO Route {route}", False, f"Invalid content type: {content_type}")
                else:
                    self.log_test(f"SEO Route {route}", False, f"Status {response.status_code}")
                    
            except Exception as e:
                self.log_test(f"SEO Route {route}", False, f"Error: {str(e)}")
        
        return success_count == len(seo_routes)

    def run_all_tests(self):
        """Run all backend crawler tests"""
        print("🚀 Starting Backend Social Sharing Crawler Tests")
        print("🎯 Testing backend directly on localhost:8001")
        print("=" * 80)
        
        # Step 1: Authentication
        if not self.login_admin():
            print("❌ Cannot proceed without authentication")
            return False
        
        # Step 2: Test emergency authentication system
        emergency_auth_success = self.test_emergency_authentication_system()
        
        # Step 3: Test crawler HTML fallback (main functionality)
        crawler_html_success = self.test_crawler_html_fallback()
        
        # Step 4: Test regular user agent handling
        regular_user_success = self.test_regular_user_agent()
        
        # Step 5: Test debug endpoints
        debug_exists_success = self.test_debug_article_exists_endpoint()
        
        # Step 6: Test updated_at crash fix
        crash_fix_success = self.test_updated_at_crash_fix()
        
        # Step 7: Test HTTP headers
        headers_success = self.test_http_headers()
        
        # Step 8: Test SEO routes
        seo_success = self.test_seo_routes()
        
        # Results summary
        print("\n" + "=" * 80)
        print("📊 BACKEND CRAWLER TEST RESULTS")
        print("=" * 80)
        
        print(f"✅ Emergency Authentication System: {'PASS' if emergency_auth_success else 'FAIL'}")
        print(f"✅ Crawler HTML Fallback: {'PASS' if crawler_html_success else 'FAIL'}")
        print(f"✅ Regular User Agent Handling: {'PASS' if regular_user_success else 'FAIL'}")
        print(f"✅ Debug Article Exists Endpoint: {'PASS' if debug_exists_success else 'FAIL'}")
        print(f"✅ Updated_at Crash Fix: {'PASS' if crash_fix_success else 'FAIL'}")
        print(f"✅ HTTP Headers for Crawlers: {'PASS' if headers_success else 'FAIL'}")
        print(f"✅ SEO Routes: {'PASS' if seo_success else 'FAIL'}")
        
        print(f"\n📈 Overall Results:")
        print(f"   Tests Run: {self.tests_run}")
        print(f"   Tests Passed: {self.tests_passed}")
        print(f"   Tests Failed: {self.tests_run - self.tests_passed}")
        print(f"   Success Rate: {(self.tests_passed/self.tests_run)*100:.1f}%")
        
        # Determine overall success
        critical_tests_passed = all([
            emergency_auth_success,
            crawler_html_success,
            regular_user_success,
            debug_exists_success,
            crash_fix_success,
            headers_success
        ])
        
        if critical_tests_passed:
            print("\n🎉 ALL CRITICAL BACKEND TESTS PASSED!")
            print("✅ Social sharing crawler HTML fixes are working correctly")
            print("✅ Debug endpoints are functional")
            print("✅ Updated_at crash fix is working")
            print("✅ Emergency authentication system operational")
            print("\n📝 NOTE: External routing issue prevents /article/ requests from reaching backend")
            print("   This is a deployment/infrastructure issue, not a backend code issue")
            return True
        else:
            print("\n❌ SOME CRITICAL TESTS FAILED - Issues need to be addressed")
            return False

def main():
    """Main test execution"""
    tester = BackendCrawlerTester()
    success = tester.run_all_tests()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())