#!/usr/bin/env python3
"""
Social Media Sharing and OG Meta Tags Test Suite
Tests the /og/article/{slug} endpoint and social sharing functionality
"""

import requests
import sys
import re
from datetime import datetime
from urllib.parse import urlparse
import json

class OGSocialSharingTester:
    def __init__(self, base_url="https://viewtrends-1.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.og_url = f"{base_url}/og"
        self.tests_run = 0
        self.tests_passed = 0
        self.token = None
        
        # Crawler user agents for testing
        self.crawler_user_agents = {
            'facebook': 'facebookexternalhit/1.1 (+http://www.facebook.com/externalhit_uatext.php)',
            'twitter': 'Twitterbot/1.0',
            'linkedin': 'LinkedInBot/1.0 (compatible; Mozilla/5.0; Apache-HttpClient +http://www.linkedin.com/)',
            'whatsapp': 'WhatsApp/2.19.81 A',
            'google': 'Googlebot/2.1 (+http://www.google.com/bot.html)',
            'regular': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }

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
        """Login as admin to get authentication token"""
        print("\n🔐 Authenticating as admin...")
        
        try:
            response = requests.post(
                f"{self.api_url}/auth/login",
                json={"username": "admin", "password": "admin123"},
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if 'access_token' in data:
                    self.token = data['access_token']
                    print(f"✅ Admin login successful")
                    return True
            
            print(f"❌ Admin login failed: {response.status_code}")
            return False
            
        except Exception as e:
            print(f"❌ Admin login error: {e}")
            return False

    def create_test_article(self, slug="this-is-a-super-testing-article"):
        """Create a test article for OG testing"""
        print(f"\n📝 Creating test article with slug: {slug}")
        
        if not self.token:
            print("❌ No authentication token available")
            return False
        
        article_data = {
            "title": "This Is A Super Testing Article",
            "subheading": "Testing Facebook sharing and Open Graph meta tags functionality",
            "content": "<p>This is a comprehensive test article for validating social media sharing functionality. It includes proper Open Graph meta tags, Twitter cards, and structured data for optimal social media presentation.</p><p>The article should display correctly when shared on Facebook, Twitter, LinkedIn, and other social platforms.</p>",
            "category": "news",
            "publisher_name": "The Crewkerne Gazette",
            "featured_image": "https://res.cloudinary.com/dqren9j0f/image/upload/w_1200,h_630,c_fill,f_jpg,q_auto/v1/test-og-image.jpg",
            "image_caption": "Test image for social sharing validation",
            "tags": ["facebook", "sharing", "test", "og-tags", "social-media"],
            "category_labels": ["News", "Tech"],
            "is_breaking": False,
            "is_published": True
        }
        
        try:
            response = requests.post(
                f"{self.api_url}/articles.json",
                json=article_data,
                headers={
                    'Content-Type': 'application/json',
                    'Authorization': f'Bearer {self.token}'
                },
                timeout=15
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Test article created successfully")
                print(f"   Slug: {data.get('slug', 'unknown')}")
                print(f"   Title: {data.get('title', 'unknown')}")
                return True
            else:
                print(f"❌ Article creation failed: {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"   Error: {error_data}")
                except:
                    print(f"   Error text: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Article creation error: {e}")
            return False

    def test_og_endpoint_with_crawler(self, slug, user_agent_name):
        """Test OG endpoint with specific crawler user agent"""
        user_agent = self.crawler_user_agents[user_agent_name]
        
        try:
            response = requests.get(
                f"{self.og_url}/article/{slug}",
                headers={'User-Agent': user_agent},
                timeout=10
            )
            
            success = response.status_code == 200
            details = f"Status: {response.status_code}, User-Agent: {user_agent_name}"
            
            if success:
                # Parse HTML content for meta tags
                html_content = response.text
                og_tags = self.extract_og_tags(html_content)
                
                # Validate required OG tags
                required_tags = ['og:title', 'og:description', 'og:type', 'og:url', 'og:image']
                missing_tags = [tag for tag in required_tags if tag not in og_tags]
                
                if missing_tags:
                    success = False
                    details += f", Missing OG tags: {missing_tags}"
                else:
                    details += f", All required OG tags present"
                    
                    # Check for image dimensions
                    if 'og:image:width' in og_tags and 'og:image:height' in og_tags:
                        width = og_tags['og:image:width']
                        height = og_tags['og:image:height']
                        details += f", Image dimensions: {width}x{height}"
                    else:
                        details += f", Missing image dimensions"
            
            self.log_test(f"OG endpoint with {user_agent_name} crawler", success, details)
            return success, response.text if success else ""
            
        except Exception as e:
            self.log_test(f"OG endpoint with {user_agent_name} crawler", False, f"Error: {e}")
            return False, ""

    def extract_og_tags(self, html_content):
        """Extract Open Graph meta tags from HTML"""
        og_tags = {}
        
        # Pattern to match meta property tags
        meta_pattern = r'<meta\s+property="([^"]+)"\s+content="([^"]*)"[^>]*>'
        matches = re.findall(meta_pattern, html_content, re.IGNORECASE)
        
        for prop, content in matches:
            if prop.startswith('og:') or prop.startswith('twitter:'):
                og_tags[prop] = content
        
        # Also check for name-based meta tags (Twitter cards)
        name_pattern = r'<meta\s+name="([^"]+)"\s+content="([^"]*)"[^>]*>'
        name_matches = re.findall(name_pattern, html_content, re.IGNORECASE)
        
        for name, content in name_matches:
            if name.startswith('twitter:'):
                og_tags[name] = content
        
        return og_tags

    def test_og_image_accessibility(self, image_url):
        """Test that OG image URL is accessible and returns proper content"""
        try:
            response = requests.head(image_url, timeout=10)
            
            success = response.status_code == 200
            content_type = response.headers.get('content-type', '')
            is_image = content_type.startswith('image/')
            
            if success and is_image:
                details = f"Status: {response.status_code}, Content-Type: {content_type}"
            elif success and not is_image:
                success = False
                details = f"Status: {response.status_code}, Invalid Content-Type: {content_type}"
            else:
                details = f"Status: {response.status_code}"
            
            self.log_test(f"OG image accessibility: {image_url}", success and is_image, details)
            return success and is_image
            
        except Exception as e:
            self.log_test(f"OG image accessibility: {image_url}", False, f"Error: {e}")
            return False

    def test_non_existent_article_handling(self):
        """Test OG endpoint with non-existent article slug"""
        non_existent_slug = "non-existent-article-slug-12345"
        
        try:
            response = requests.get(
                f"{self.og_url}/article/{non_existent_slug}",
                headers={'User-Agent': self.crawler_user_agents['facebook']},
                timeout=10
            )
            
            # Should return 200 OK with fallback meta tags, not 404
            success = response.status_code == 200
            
            if success:
                html_content = response.text
                og_tags = self.extract_og_tags(html_content)
                
                # Should have fallback OG tags
                has_fallback_tags = (
                    'og:title' in og_tags and 
                    'og:description' in og_tags and 
                    'og:image' in og_tags
                )
                
                if has_fallback_tags:
                    details = f"Status: 200 OK, Fallback OG tags present"
                else:
                    success = False
                    details = f"Status: 200 OK, Missing fallback OG tags"
            else:
                details = f"Status: {response.status_code} (should be 200 OK)"
            
            self.log_test("Non-existent article handling", success, details)
            return success
            
        except Exception as e:
            self.log_test("Non-existent article handling", False, f"Error: {e}")
            return False

    def test_crawler_vs_regular_user_detection(self, slug):
        """Test that crawler and regular user agents get different responses"""
        try:
            # Test with crawler user agent
            crawler_response = requests.get(
                f"{self.og_url}/article/{slug}",
                headers={'User-Agent': self.crawler_user_agents['facebook']},
                timeout=10
            )
            
            # Test with regular user agent  
            regular_response = requests.get(
                f"{self.og_url}/article/{slug}",
                headers={'User-Agent': self.crawler_user_agents['regular']},
                timeout=10
            )
            
            crawler_success = crawler_response.status_code == 200
            regular_success = regular_response.status_code in [200, 302]  # Regular users might get redirected
            
            if crawler_success and regular_success:
                # Check if responses are different (they should be)
                crawler_content = crawler_response.text
                regular_content = regular_response.text
                
                different_responses = crawler_content != regular_content
                details = f"Crawler: {crawler_response.status_code}, Regular: {regular_response.status_code}, Different responses: {different_responses}"
            else:
                different_responses = False
                details = f"Crawler: {crawler_response.status_code}, Regular: {regular_response.status_code}"
            
            self.log_test("Crawler vs regular user detection", crawler_success and regular_success, details)
            return crawler_success and regular_success
            
        except Exception as e:
            self.log_test("Crawler vs regular user detection", False, f"Error: {e}")
            return False

    def test_http_headers_for_crawlers(self, slug):
        """Test that proper HTTP headers are returned for crawlers"""
        try:
            response = requests.get(
                f"{self.og_url}/article/{slug}",
                headers={'User-Agent': self.crawler_user_agents['facebook']},
                timeout=10
            )
            
            success = response.status_code == 200
            
            if success:
                headers = response.headers
                
                # Check for expected headers
                cache_control = headers.get('Cache-Control', '')
                x_robots_tag = headers.get('X-Robots-Tag', '')
                content_type = headers.get('Content-Type', '')
                
                has_cache_control = 'public' in cache_control and 'max-age' in cache_control
                has_robots_tag = x_robots_tag == 'all'
                has_html_content_type = 'text/html' in content_type
                
                details = f"Cache-Control: {cache_control}, X-Robots-Tag: {x_robots_tag}, Content-Type: {content_type}"
                
                if has_cache_control and has_robots_tag and has_html_content_type:
                    details = f"All required headers present - {details}"
                else:
                    success = False
                    missing = []
                    if not has_cache_control:
                        missing.append("Cache-Control")
                    if not has_robots_tag:
                        missing.append("X-Robots-Tag")
                    if not has_html_content_type:
                        missing.append("Content-Type")
                    details = f"Missing headers: {missing} - {details}"
            else:
                details = f"Status: {response.status_code}"
            
            self.log_test("HTTP headers for crawlers", success, details)
            return success
            
        except Exception as e:
            self.log_test("HTTP headers for crawlers", False, f"Error: {e}")
            return False

    def validate_og_meta_tags_completeness(self, html_content):
        """Validate that all required OG meta tags are present and properly formatted"""
        og_tags = self.extract_og_tags(html_content)
        
        # Required OG tags
        required_og_tags = [
            'og:title', 'og:description', 'og:type', 'og:url', 'og:image',
            'og:image:width', 'og:image:height'
        ]
        
        # Required Twitter tags
        required_twitter_tags = [
            'twitter:card', 'twitter:title', 'twitter:description', 'twitter:image'
        ]
        
        missing_og = [tag for tag in required_og_tags if tag not in og_tags]
        missing_twitter = [tag for tag in required_twitter_tags if tag not in og_tags]
        
        # Validate image dimensions
        image_dimensions_valid = False
        if 'og:image:width' in og_tags and 'og:image:height' in og_tags:
            try:
                width = int(og_tags['og:image:width'])
                height = int(og_tags['og:image:height'])
                image_dimensions_valid = width == 1200 and height == 630
            except ValueError:
                pass
        
        # Validate image URL is HTTPS
        image_url_https = False
        if 'og:image' in og_tags:
            image_url_https = og_tags['og:image'].startswith('https://')
        
        success = (
            len(missing_og) == 0 and 
            len(missing_twitter) == 0 and 
            image_dimensions_valid and 
            image_url_https
        )
        
        details_parts = []
        if missing_og:
            details_parts.append(f"Missing OG: {missing_og}")
        if missing_twitter:
            details_parts.append(f"Missing Twitter: {missing_twitter}")
        if not image_dimensions_valid:
            details_parts.append(f"Invalid dimensions: {og_tags.get('og:image:width', 'missing')}x{og_tags.get('og:image:height', 'missing')}")
        if not image_url_https:
            details_parts.append(f"Non-HTTPS image: {og_tags.get('og:image', 'missing')}")
        
        if success:
            details = "All required meta tags present and valid"
        else:
            details = "; ".join(details_parts)
        
        self.log_test("OG meta tags completeness", success, details)
        return success, og_tags

    def run_comprehensive_og_tests(self):
        """Run comprehensive OG and social sharing tests"""
        print("🚀 Starting Social Media Sharing and OG Meta Tags Tests")
        print("=" * 70)
        
        # Step 1: Login and create test article
        if not self.login_admin():
            print("❌ Cannot proceed without admin authentication")
            return False
        
        if not self.create_test_article():
            print("❌ Cannot proceed without test article")
            return False
        
        test_slug = "this-is-a-super-testing-article"
        
        print(f"\n🔍 Testing OG endpoint: {self.og_url}/article/{test_slug}")
        print("-" * 50)
        
        # Step 2: Test OG endpoint with different crawler user agents
        print("\n📱 Testing crawler user agent detection:")
        facebook_success, facebook_html = self.test_og_endpoint_with_crawler(test_slug, 'facebook')
        twitter_success, twitter_html = self.test_og_endpoint_with_crawler(test_slug, 'twitter')
        linkedin_success, _ = self.test_og_endpoint_with_crawler(test_slug, 'linkedin')
        whatsapp_success, _ = self.test_og_endpoint_with_crawler(test_slug, 'whatsapp')
        
        # Step 3: Validate meta tags completeness (using Facebook response)
        print("\n🏷️  Validating meta tags completeness:")
        if facebook_success and facebook_html:
            meta_tags_valid, og_tags = self.validate_og_meta_tags_completeness(facebook_html)
            
            # Test image accessibility if we have an image URL
            if 'og:image' in og_tags:
                self.test_og_image_accessibility(og_tags['og:image'])
        
        # Step 4: Test non-existent article handling
        print("\n🚫 Testing non-existent article handling:")
        self.test_non_existent_article_handling()
        
        # Step 5: Test crawler vs regular user detection
        print("\n🤖 Testing crawler vs regular user detection:")
        self.test_crawler_vs_regular_user_detection(test_slug)
        
        # Step 6: Test HTTP headers for crawlers
        print("\n📋 Testing HTTP headers for crawlers:")
        self.test_http_headers_for_crawlers(test_slug)
        
        return True

    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 70)
        print("📊 SOCIAL MEDIA SHARING TEST SUMMARY")
        print("=" * 70)
        
        success_rate = (self.tests_passed / self.tests_run * 100) if self.tests_run > 0 else 0
        
        print(f"Tests Run: {self.tests_run}")
        print(f"Tests Passed: {self.tests_passed}")
        print(f"Tests Failed: {self.tests_run - self.tests_passed}")
        print(f"Success Rate: {success_rate:.1f}%")
        
        if success_rate >= 90:
            print("\n🎉 EXCELLENT: Social media sharing functionality is working correctly!")
        elif success_rate >= 70:
            print("\n✅ GOOD: Most social sharing features are working with minor issues")
        elif success_rate >= 50:
            print("\n⚠️  MODERATE: Social sharing has significant issues that need attention")
        else:
            print("\n🚨 CRITICAL: Social sharing functionality has major problems")
        
        return success_rate >= 70

def main():
    """Main test execution"""
    # Use the backend URL from frontend .env
    backend_url = "https://viewtrends-1.preview.emergentagent.com"
    
    tester = OGSocialSharingTester(backend_url)
    
    try:
        success = tester.run_comprehensive_og_tests()
        overall_success = tester.print_summary()
        
        return 0 if overall_success else 1
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Tests interrupted by user")
        return 1
    except Exception as e:
        print(f"\n❌ Test execution failed: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())