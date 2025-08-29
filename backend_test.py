import requests
import sys
from datetime import datetime
import json
import io

class CrewkerneGazetteAPITester:
    def __init__(self, base_url="https://CrewkerneGazette.co.uk"):
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

    # HIGH PRIORITY TESTS - Dashboard Features
    def test_change_password(self):
        """Test password change functionality"""
        password_data = {
            "current_password": "admin123",
            "new_password": "newpassword123"
        }
        
        success, response = self.run_test(
            "Change Password",
            "POST",
            "auth/change-password",
            200,
            data=password_data
        )
        
        # Change password back to original for other tests
        if success:
            revert_data = {
                "current_password": "newpassword123",
                "new_password": "admin123"
            }
            self.run_test(
                "Revert Password",
                "POST",
                "auth/change-password",
                200,
                data=revert_data
            )
        
        return success

    def test_get_settings(self):
        """Test fetching site settings"""
        success, response = self.run_test(
            "Get Site Settings",
            "GET",
            "settings",
            200
        )
        return success

    def test_maintenance_mode_toggle(self):
        """Test toggling maintenance mode on/off"""
        # Enable maintenance mode
        enable_data = {"maintenance_mode": True}
        success1, response1 = self.run_test(
            "Enable Maintenance Mode",
            "POST",
            "settings/maintenance",
            200,
            data=enable_data
        )
        
        # Disable maintenance mode
        disable_data = {"maintenance_mode": False}
        success2, response2 = self.run_test(
            "Disable Maintenance Mode",
            "POST",
            "settings/maintenance",
            200,
            data=disable_data
        )
        
        return success1 and success2

    # MEDIUM PRIORITY TESTS - Article Management Features
    def test_create_article_with_new_fields(self):
        """Test creating articles with new fields (subheading, publisher_name, is_breaking)"""
        article_data = {
            "title": f"Breaking News Article {datetime.now().strftime('%H%M%S')}",
            "subheading": "This is a test subheading for the article",
            "content": "This is comprehensive test content for the breaking news article with all new fields.",
            "category": "news",
            "publisher_name": "The Crewkerne Gazette",
            "featured_image": "https://example.com/breaking-news.jpg",
            "video_url": "https://example.com/breaking-video.mp4",
            "is_breaking": True,
            "is_published": True,
            "tags": ["breaking", "urgent", "news"]
        }
        
        success, response = self.run_test(
            "Create Article with New Fields",
            "POST",
            "articles",
            200,
            data=article_data
        )
        
        if success and 'id' in response:
            # Verify new fields are properly stored
            if (response.get('subheading') == article_data['subheading'] and
                response.get('publisher_name') == article_data['publisher_name'] and
                response.get('is_breaking') == article_data['is_breaking']):
                print("   ✅ New fields properly stored")
                # Store this article ID for related articles test
                self.created_article_id = response['id']
                return True
            else:
                print("   ❌ New fields not properly stored")
                return False
        return success

    def test_get_articles_breaking_filter(self):
        """Test fetching articles with breaking news filtering"""
        success, response = self.run_test(
            "Get Breaking News Articles",
            "GET",
            "articles?is_breaking=true",
            200
        )
        
        if success and isinstance(response, list):
            # Verify all returned articles are breaking news
            all_breaking = all(article.get('is_breaking', False) for article in response)
            if all_breaking:
                print(f"   ✅ All {len(response)} articles are breaking news")
            else:
                print("   ❌ Some non-breaking articles returned")
                return False
        
        return success

    def test_related_articles_endpoint(self):
        """Test related articles endpoint for trending topics functionality"""
        if not self.created_article_id:
            print("❌ Skipping - No article ID available")
            return False
            
        success, response = self.run_test(
            "Get Related Articles",
            "GET",
            f"articles/{self.created_article_id}/related",
            200
        )
        
        if success and isinstance(response, list):
            print(f"   ✅ Found {len(response)} related articles")
            # Verify articles don't include the original article
            original_in_results = any(article.get('id') == self.created_article_id for article in response)
            if original_in_results:
                print("   ❌ Original article included in related articles")
                return False
            else:
                print("   ✅ Original article properly excluded")
        
        return success

    def test_invalid_password_change(self):
        """Test password change with wrong current password"""
        password_data = {
            "current_password": "wrongpassword",
            "new_password": "newpassword123"
        }
        
        success, response = self.run_test(
            "Invalid Password Change",
            "POST",
            "auth/change-password",
            400,
            data=password_data
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

    # NEW FEATURE TESTS - Breaking News Banner Toggle
    def test_breaking_news_banner_toggle(self):
        """Test toggling breaking news banner on/off"""
        # Enable breaking news banner
        enable_data = {"show_breaking_news_banner": True}
        success1, response1 = self.run_test(
            "Enable Breaking News Banner",
            "POST",
            "settings/breaking-news-banner",
            200,
            data=enable_data
        )
        
        # Disable breaking news banner
        disable_data = {"show_breaking_news_banner": False}
        success2, response2 = self.run_test(
            "Disable Breaking News Banner",
            "POST",
            "settings/breaking-news-banner",
            200,
            data=disable_data
        )
        
        # Re-enable for other tests
        enable_data = {"show_breaking_news_banner": True}
        success3, response3 = self.run_test(
            "Re-enable Breaking News Banner",
            "POST",
            "settings/breaking-news-banner",
            200,
            data=enable_data
        )
        
        return success1 and success2 and success3

    def test_public_settings_endpoint(self):
        """Test public settings endpoint (no auth required)"""
        # Temporarily remove token for this test
        original_token = self.token
        self.token = None
        
        success, response = self.run_test(
            "Get Public Settings (No Auth)",
            "GET",
            "settings/public",
            200
        )
        
        # Restore token
        self.token = original_token
        
        if success and isinstance(response, dict):
            if 'show_breaking_news_banner' in response:
                print(f"   ✅ Breaking news banner setting: {response['show_breaking_news_banner']}")
                return True
            else:
                print("   ❌ Missing show_breaking_news_banner in response")
                return False
        
        return success

    def test_settings_persistence(self):
        """Test that settings changes persist properly"""
        # First, disable breaking news banner
        disable_data = {"show_breaking_news_banner": False}
        success1, response1 = self.run_test(
            "Disable Banner for Persistence Test",
            "POST",
            "settings/breaking-news-banner",
            200,
            data=disable_data
        )
        
        if not success1:
            return False
        
        # Check if the setting persists via public endpoint
        original_token = self.token
        self.token = None
        
        success2, response2 = self.run_test(
            "Check Persistence via Public Settings",
            "GET",
            "settings/public",
            200
        )
        
        self.token = original_token
        
        if success2 and isinstance(response2, dict):
            if response2.get('show_breaking_news_banner') == False:
                print("   ✅ Settings properly persisted in database")
                
                # Re-enable for other tests
                enable_data = {"show_breaking_news_banner": True}
                self.run_test(
                    "Re-enable Banner after Persistence Test",
                    "POST",
                    "settings/breaking-news-banner",
                    200,
                    data=enable_data
                )
                return True
            else:
                print("   ❌ Settings not properly persisted")
                return False
        
        return False

    def test_image_upload_url_format(self):
        """Test image upload returns correct URL format"""
        # Create a simple test image file in memory (minimal PNG)
        import io
        
        # Create minimal PNG file data (1x1 pixel transparent PNG)
        png_data = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xdb\x00\x00\x00\x00IEND\xaeB`\x82'
        img_bytes = io.BytesIO(png_data)
        
        # Prepare multipart form data
        files = {'file': ('test_image.png', img_bytes, 'image/png')}
        headers = {}
        if self.token:
            headers['Authorization'] = f'Bearer {self.token}'
        
        url = f"{self.api_url}/upload-image"
        
        self.tests_run += 1
        print(f"\n🔍 Testing Image Upload URL Format...")
        print(f"   URL: {url}")
        
        try:
            response = requests.post(url, files=files, headers=headers)
            
            success = response.status_code == 200
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                
                try:
                    response_data = response.json()
                    if 'url' in response_data:
                        url_path = response_data['url']
                        print(f"   Response URL: {url_path}")
                        
                        # Check if URL format is correct (should be "/uploads/filename.ext")
                        if url_path.startswith('/uploads/') and url_path.endswith('.png'):
                            print("   ✅ URL format is correct: /uploads/filename.ext")
                            return True
                        else:
                            print(f"   ❌ URL format incorrect. Expected /uploads/filename.ext, got: {url_path}")
                            return False
                    else:
                        print("   ❌ No 'url' field in response")
                        return False
                except Exception as e:
                    print(f"   ❌ Error parsing response: {e}")
                    return False
            else:
                print(f"❌ Failed - Expected 200, got {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"   Error: {error_data}")
                except:
                    print(f"   Error: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False

    def test_unauthorized_breaking_news_banner_access(self):
        """Test that breaking news banner toggle requires admin authentication"""
        # Remove token temporarily
        original_token = self.token
        self.token = None
        
        banner_data = {"show_breaking_news_banner": False}
        success, response = self.run_test(
            "Unauthorized Breaking News Banner Toggle",
            "POST",
            "settings/breaking-news-banner",
            403,  # Should return 403 Forbidden (FastAPI returns 403 for missing auth)
            data=banner_data
        )
        
        # Restore token
        self.token = original_token
        
        return success

    # PRODUCTION SPECIFIC TESTS - For CrewkerneGazette.co.uk Issue Investigation
    def test_production_login_endpoint(self):
        """Test the specific production login endpoint with admin/admin123"""
        print("\n🚨 PRODUCTION LOGIN ENDPOINT TEST - CrewkerneGazette.co.uk")
        print("=" * 60)
        
        url = f"{self.api_url}/auth/login"
        login_data = {"username": "admin", "password": "admin123"}
        headers = {'Content-Type': 'application/json'}
        
        self.tests_run += 1
        print(f"   Testing URL: {url}")
        print(f"   Credentials: {login_data}")
        
        try:
            response = requests.post(url, json=login_data, headers=headers, timeout=30)
            
            print(f"   Status Code: {response.status_code}")
            print(f"   Response Headers: {dict(response.headers)}")
            
            # Capture exact error response for 500 errors
            if response.status_code == 500:
                print("🚨 CRITICAL: HTTP 500 Internal Server Error detected!")
                try:
                    error_data = response.json()
                    print(f"   Error JSON: {error_data}")
                except:
                    print(f"   Error Text: {response.text}")
                    print(f"   Raw Response: {response.content}")
                
                # Check response headers for clues
                content_type = response.headers.get('content-type', '')
                server = response.headers.get('server', '')
                print(f"   Content-Type: {content_type}")
                print(f"   Server: {server}")
                
                return False
            
            try:
                response_data = response.json()
                print(f"   Response Body: {response_data}")
            except:
                print(f"   Response Text: {response.text}")
                response_data = {}
            
            if response.status_code == 200:
                self.tests_passed += 1
                print("✅ Production login successful")
                
                if 'access_token' in response_data:
                    self.token = response_data['access_token']
                    print(f"   ✅ Token received: {self.token[:50]}...")
                    return True
                else:
                    print("   ❌ No access_token in successful response")
                    return False
            else:
                print(f"❌ Production login failed with status {response.status_code}")
                return False
                
        except requests.exceptions.ConnectionError as e:
            print(f"❌ Connection Error: {e}")
            print("   → Backend server may be down or unreachable")
            return False
        except requests.exceptions.Timeout as e:
            print(f"❌ Timeout Error: {e}")
            print("   → Backend server not responding within 30 seconds")
            return False
        except Exception as e:
            print(f"❌ Unexpected Error: {e}")
            return False

    def test_production_public_settings(self):
        """Test the production public settings endpoint"""
        print("\n🔍 PRODUCTION PUBLIC SETTINGS TEST")
        print("-" * 40)
        
        url = f"{self.api_url}/settings/public"
        
        self.tests_run += 1
        print(f"   Testing URL: {url}")
        
        try:
            response = requests.get(url, timeout=30)
            
            print(f"   Status Code: {response.status_code}")
            
            if response.status_code == 500:
                print("🚨 CRITICAL: Public settings endpoint returning HTTP 500!")
                try:
                    error_data = response.json()
                    print(f"   Error JSON: {error_data}")
                except:
                    print(f"   Error Text: {response.text}")
                return False
            
            if response.status_code == 200:
                self.tests_passed += 1
                print("✅ Public settings endpoint working")
                try:
                    response_data = response.json()
                    print(f"   Response: {response_data}")
                    return True
                except:
                    print(f"   Response Text: {response.text}")
                    return True
            else:
                print(f"❌ Public settings failed with status {response.status_code}")
                return False
                
        except requests.exceptions.ConnectionError as e:
            print(f"❌ Connection Error: {e}")
            return False
        except requests.exceptions.Timeout as e:
            print(f"❌ Timeout Error: {e}")
            return False
        except Exception as e:
            print(f"❌ Unexpected Error: {e}")
            return False

    def test_production_users_endpoint(self):
        """Test the production users endpoint (requires authentication)"""
        print("\n🔍 PRODUCTION USERS ENDPOINT TEST")
        print("-" * 40)
        
        # Note: This endpoint doesn't exist in the backend, but testing to see what happens
        url = f"{self.api_url}/users"
        headers = {'Content-Type': 'application/json'}
        
        if self.token:
            headers['Authorization'] = f'Bearer {self.token}'
        
        self.tests_run += 1
        print(f"   Testing URL: {url}")
        print(f"   With Auth: {'Yes' if self.token else 'No'}")
        
        try:
            response = requests.get(url, headers=headers, timeout=30)
            
            print(f"   Status Code: {response.status_code}")
            
            if response.status_code == 500:
                print("🚨 CRITICAL: Users endpoint returning HTTP 500!")
                try:
                    error_data = response.json()
                    print(f"   Error JSON: {error_data}")
                except:
                    print(f"   Error Text: {response.text}")
                return False
            
            # 404 is expected since this endpoint doesn't exist in our backend
            if response.status_code in [200, 404]:
                self.tests_passed += 1
                if response.status_code == 404:
                    print("✅ Users endpoint returns 404 (expected - endpoint doesn't exist)")
                else:
                    print("✅ Users endpoint working")
                    try:
                        response_data = response.json()
                        print(f"   Response: {response_data}")
                    except:
                        print(f"   Response Text: {response.text}")
                return True
            else:
                print(f"❌ Users endpoint failed with status {response.status_code}")
                return False
                
        except requests.exceptions.ConnectionError as e:
            print(f"❌ Connection Error: {e}")
            return False
        except requests.exceptions.Timeout as e:
            print(f"❌ Timeout Error: {e}")
            return False
        except Exception as e:
            print(f"❌ Unexpected Error: {e}")
            return False

    def test_production_articles_endpoint(self):
        """Test the production articles endpoint"""
        print("\n🔍 PRODUCTION ARTICLES ENDPOINT TEST")
        print("-" * 40)
        
        url = f"{self.api_url}/articles"
        
        self.tests_run += 1
        print(f"   Testing URL: {url}")
        
        try:
            response = requests.get(url, timeout=30)
            
            print(f"   Status Code: {response.status_code}")
            
            if response.status_code == 500:
                print("🚨 CRITICAL: Articles endpoint returning HTTP 500!")
                try:
                    error_data = response.json()
                    print(f"   Error JSON: {error_data}")
                except:
                    print(f"   Error Text: {response.text}")
                return False
            
            if response.status_code == 200:
                self.tests_passed += 1
                print("✅ Articles endpoint working")
                try:
                    response_data = response.json()
                    print(f"   Response: Found {len(response_data)} articles")
                    return True
                except:
                    print(f"   Response Text: {response.text}")
                    return True
            else:
                print(f"❌ Articles endpoint failed with status {response.status_code}")
                return False
                
        except requests.exceptions.ConnectionError as e:
            print(f"❌ Connection Error: {e}")
            return False
        except requests.exceptions.Timeout as e:
            print(f"❌ Timeout Error: {e}")
            return False
        except Exception as e:
            print(f"❌ Unexpected Error: {e}")
            return False

    def test_production_backend_health(self):
        """Test overall backend health on production domain"""
        print("\n🔍 PRODUCTION BACKEND HEALTH CHECK")
        print("-" * 40)
        
        # Test basic connectivity to the domain
        try:
            response = requests.get(self.base_url, timeout=30)
            print(f"   Domain Status: {response.status_code}")
            print(f"   Domain accessible: ✅")
        except Exception as e:
            print(f"   Domain Error: {e}")
            return False
        
        # Test if API base path responds
        try:
            api_response = requests.get(self.api_url, timeout=30)
            print(f"   API Base Status: {api_response.status_code}")
            if api_response.status_code == 404:
                print("   API Base: ✅ (404 expected for base API path)")
            elif api_response.status_code == 500:
                print("   API Base: ❌ (500 error indicates backend issues)")
                return False
        except Exception as e:
            print(f"   API Base Error: {e}")
            return False
        
        return True

    def test_backup_admin_login(self):
        """Test login with backup admin credentials"""
        print("\n🔍 BACKUP ADMIN LOGIN TEST")
        print("-" * 30)
        
        success, response = self.run_test(
            "Backup Admin Login",
            "POST",
            "auth/login",
            200,
            data={"username": "admin_backup", "password": "admin123"}
        )
        
        if success and 'access_token' in response:
            print("   ✅ Backup admin login successful")
            self.token = response['access_token']
            return True
        else:
            print("   ❌ Backup admin login failed")
            return False
    def test_admin_user_exists(self):
        """Test if admin user exists in database by attempting login"""
        print("\n🔍 DEBUGGING: Testing if admin user exists...")
        
        success, response = self.run_test(
            "Admin User Existence Check",
            "POST",
            "auth/login",
            200,  # Expecting success if user exists
            data={"username": "admin", "password": "admin123"}
        )
        
        if success:
            print("   ✅ Admin user exists and login successful")
            if 'access_token' in response:
                print(f"   ✅ JWT token generated successfully")
                print(f"   ✅ User data: {response.get('user', {})}")
                return True
            else:
                print("   ❌ No access_token in response")
                return False
        else:
            print("   ❌ Admin login failed - user may not exist or password incorrect")
            return False

    def test_admin_login_detailed(self):
        """Detailed admin login test with comprehensive error checking"""
        print("\n🔍 DETAILED ADMIN LOGIN TEST...")
        
        url = f"{self.api_url}/auth/login"
        login_data = {"username": "admin", "password": "admin123"}
        headers = {'Content-Type': 'application/json'}
        
        self.tests_run += 1
        print(f"   URL: {url}")
        print(f"   Credentials: {login_data}")
        
        try:
            response = requests.post(url, json=login_data, headers=headers)
            
            print(f"   Status Code: {response.status_code}")
            print(f"   Response Headers: {dict(response.headers)}")
            
            try:
                response_data = response.json()
                print(f"   Response Body: {response_data}")
            except:
                print(f"   Response Text: {response.text}")
                response_data = {}
            
            if response.status_code == 200:
                self.tests_passed += 1
                print("✅ Admin login successful")
                
                # Check token validity
                if 'access_token' in response_data:
                    token = response_data['access_token']
                    print(f"   ✅ Token received: {token[:50]}...")
                    
                    # Test token immediately
                    auth_headers = {
                        'Content-Type': 'application/json',
                        'Authorization': f'Bearer {token}'
                    }
                    
                    me_response = requests.get(f"{self.api_url}/auth/me", headers=auth_headers)
                    if me_response.status_code == 200:
                        print("   ✅ Token is valid and working")
                        user_data = me_response.json()
                        print(f"   ✅ User role: {user_data.get('role')}")
                        return True
                    else:
                        print(f"   ❌ Token validation failed: {me_response.status_code}")
                        return False
                else:
                    print("   ❌ No access_token in successful response")
                    return False
            else:
                print(f"❌ Login failed with status {response.status_code}")
                if response.status_code == 401:
                    print("   → This indicates invalid credentials")
                elif response.status_code == 404:
                    print("   → This indicates the endpoint doesn't exist")
                elif response.status_code == 500:
                    print("   → This indicates a server error")
                return False
                
        except requests.exceptions.ConnectionError as e:
            print(f"❌ Connection Error: {e}")
            print("   → Check if the backend server is running")
            return False
        except Exception as e:
            print(f"❌ Unexpected Error: {e}")
            return False

    def test_create_new_admin_user(self):
        """Test creating a new admin user if the default one has issues"""
        print("\n🔍 TESTING: Creating new admin user...")
        
        new_admin_data = {
            "username": "admin_backup",
            "email": "admin_backup@crewkernegazette.com",
            "password": "admin123",
            "role": "admin"
        }
        
        success, response = self.run_test(
            "Create New Admin User",
            "POST",
            "auth/register",
            200,
            data=new_admin_data
        )
        
        if success:
            print("   ✅ New admin user created successfully")
            
            # Test login with new admin user
            login_success, login_response = self.run_test(
                "Login with New Admin User",
                "POST",
                "auth/login",
                200,
                data={"username": "admin_backup", "password": "admin123"}
            )
            
            if login_success and 'access_token' in login_response:
                print("   ✅ New admin user login successful")
                print("   → You can use admin_backup/admin123 as alternative credentials")
                return True
            else:
                print("   ❌ New admin user login failed")
                return False
        else:
            print("   ❌ Failed to create new admin user")
            return False

    def test_jwt_token_validation(self):
        """Test JWT token generation and validation"""
        print("\n🔍 TESTING: JWT Token Validation...")
        
        # First login to get a token
        success, response = self.run_test(
            "Login for JWT Test",
            "POST",
            "auth/login",
            200,
            data={"username": "admin", "password": "admin123"}
        )
        
        if not success or 'access_token' not in response:
            print("   ❌ Cannot test JWT - login failed")
            return False
        
        token = response['access_token']
        print(f"   Token: {token[:50]}...")
        
        # Test token with /auth/me endpoint
        auth_headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {token}'
        }
        
        url = f"{self.api_url}/auth/me"
        
        try:
            me_response = requests.get(url, headers=auth_headers)
            
            if me_response.status_code == 200:
                print("   ✅ JWT token is valid")
                user_data = me_response.json()
                print(f"   ✅ Authenticated as: {user_data.get('username')} ({user_data.get('role')})")
                return True
            else:
                print(f"   ❌ JWT validation failed: {me_response.status_code}")
                try:
                    error_data = me_response.json()
                    print(f"   Error: {error_data}")
                except:
                    print(f"   Error text: {me_response.text}")
                return False
                
        except Exception as e:
            print(f"   ❌ JWT test error: {e}")
            return False

def main():
    print("🚀 Starting Crewkerne Gazette API Tests - ADMIN LOGIN DEBUGGING")
    print("=" * 70)
    
    tester = CrewkerneGazetteAPITester()
    
    # ADMIN LOGIN DEBUGGING TESTS - Priority Focus
    print("\n📋 ADMIN LOGIN DEBUGGING TESTS - PRODUCTION ISSUE")
    print("-" * 60)
    
    # Test 1: Check if admin user exists and can login
    admin_exists = tester.test_admin_user_exists()
    
    # Test 2: Detailed login test with comprehensive error checking
    detailed_login = tester.test_admin_login_detailed()
    
    # Test 3: JWT token validation
    jwt_valid = tester.test_jwt_token_validation()
    
    # Test 4: Try creating alternative admin user if needed
    if not admin_exists or not detailed_login:
        print("\n⚠️  Primary admin login failed, testing alternative...")
        tester.test_create_new_admin_user()
    
    # Authentication Tests
    print("\n📋 STANDARD AUTHENTICATION TESTS")
    print("-" * 40)
    
    if not tester.test_login():
        print("❌ Standard login failed, stopping remaining tests")
        print("\n" + "=" * 70)
        print("🚨 CRITICAL ISSUE: Admin login is not working")
        print("📋 DIAGNOSIS:")
        if not admin_exists:
            print("   • Admin user may not exist in production database")
        if not detailed_login:
            print("   • Login endpoint may have issues")
        if not jwt_valid:
            print("   • JWT token generation/validation may be broken")
        print("\n💡 RECOMMENDED ACTIONS:")
        print("   1. Check if MongoDB is properly connected")
        print("   2. Verify admin user exists in database")
        print("   3. Check JWT_SECRET configuration")
        print("   4. Try using backup admin credentials if created")
        return 1
    
    tester.test_auth_me()
    
    # HIGH PRIORITY TESTS - Core Dashboard Features
    print("\n📋 HIGH PRIORITY - CORE DASHBOARD FEATURES")
    print("-" * 50)
    
    tester.test_change_password()
    tester.test_get_settings()
    tester.test_maintenance_mode_toggle()
    
    # NEW FEATURE TESTS - Breaking News Banner Toggle & Image Upload
    print("\n📋 NEW FEATURES - BREAKING NEWS BANNER & IMAGE UPLOAD")
    print("-" * 60)
    
    tester.test_breaking_news_banner_toggle()
    tester.test_public_settings_endpoint()
    tester.test_settings_persistence()
    tester.test_image_upload_url_format()
    tester.test_unauthorized_breaking_news_banner_access()
    
    # MEDIUM PRIORITY TESTS - Article Management Features
    print("\n📋 MEDIUM PRIORITY - ARTICLE MANAGEMENT FEATURES")
    print("-" * 55)
    
    tester.test_create_article_with_new_fields()
    tester.test_get_articles_breaking_filter()
    tester.test_related_articles_endpoint()
    
    # Additional Authentication & Validation Tests
    print("\n📋 VALIDATION & ERROR HANDLING TESTS")
    print("-" * 40)
    
    tester.test_invalid_password_change()
    tester.test_invalid_login()
    
    # Standard Article CRUD Tests
    print("\n📋 STANDARD ARTICLE CRUD TESTS")
    print("-" * 35)
    
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
    print("\n" + "=" * 70)
    print(f"📊 FINAL RESULTS")
    print(f"Tests Run: {tester.tests_run}")
    print(f"Tests Passed: {tester.tests_passed}")
    print(f"Tests Failed: {tester.tests_run - tester.tests_passed}")
    print(f"Success Rate: {(tester.tests_passed/tester.tests_run)*100:.1f}%")
    
    # Special focus on admin login results
    print(f"\n🔍 ADMIN LOGIN DIAGNOSIS:")
    print(f"   Admin User Exists: {'✅' if admin_exists else '❌'}")
    print(f"   Detailed Login: {'✅' if detailed_login else '❌'}")
    print(f"   JWT Validation: {'✅' if jwt_valid else '❌'}")
    
    if tester.tests_passed == tester.tests_run:
        print("🎉 All tests passed!")
        return 0
    else:
        print("⚠️  Some tests failed!")
        return 1

if __name__ == "__main__":
    sys.exit(main())