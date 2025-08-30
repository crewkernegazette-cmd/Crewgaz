#!/usr/bin/env python3
"""
Comprehensive Backend Testing for Production Deployment
Testing all priority areas mentioned in the review request
"""

import requests
import sys
import json
import base64
import io
from datetime import datetime
from typing import Dict, Any, Optional

class ComprehensiveBackendTester:
    def __init__(self):
        # Use the frontend .env URL for testing
        with open('/app/frontend/.env', 'r') as f:
            env_content = f.read()
            for line in env_content.split('\n'):
                if line.startswith('REACT_APP_BACKEND_URL='):
                    self.base_url = line.split('=', 1)[1].strip()
                    break
        
        self.api_url = f"{self.base_url}/api"
        self.token = None
        self.tests_run = 0
        self.tests_passed = 0
        self.created_article_id = None
        
        print(f"🎯 Testing Backend URL: {self.api_url}")

    def run_test(self, name: str, method: str, endpoint: str, expected_status: int, 
                 data: Optional[Dict] = None, headers: Optional[Dict] = None) -> tuple[bool, Dict]:
        """Run a single API test with detailed logging"""
        url = f"{self.api_url}/{endpoint}"
        test_headers = {'Content-Type': 'application/json'}
        
        if self.token:
            test_headers['Authorization'] = f'Bearer {self.token}'
        
        if headers:
            test_headers.update(headers)

        self.tests_run += 1
        print(f"\n🔍 Test {self.tests_run}: {name}")
        print(f"   URL: {url}")
        print(f"   Method: {method}")
        if data and len(str(data)) < 200:
            print(f"   Data: {data}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=test_headers, timeout=15)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=test_headers, timeout=15)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=test_headers, timeout=15)
            elif method == 'DELETE':
                response = requests.delete(url, headers=test_headers, timeout=15)

            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"   ✅ PASSED - Status: {response.status_code}")
                try:
                    response_data = response.json()
                    if isinstance(response_data, dict) and len(str(response_data)) < 300:
                        print(f"   Response: {response_data}")
                    elif isinstance(response_data, list):
                        print(f"   Response: List with {len(response_data)} items")
                    return success, response_data
                except:
                    return success, {}
            else:
                print(f"   ❌ FAILED - Expected {expected_status}, got {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"   Error: {error_data}")
                except:
                    print(f"   Error Text: {response.text}")
                return False, {}

        except Exception as e:
            print(f"   ❌ FAILED - Exception: {str(e)}")
            return False, {}

    # PRIORITY 1: Emergency Database System & Authentication
    def test_emergency_database_admin_login(self):
        """Test admin login with emergency in-memory database"""
        print("\n" + "="*60)
        print("🚨 PRIORITY 1: EMERGENCY DATABASE SYSTEM & AUTHENTICATION")
        print("="*60)
        
        # Test primary admin credentials
        success, response = self.run_test(
            "Emergency Database - Admin Login (admin/admin123)",
            "POST",
            "auth/login",
            200,
            data={"username": "admin", "password": "admin123"}
        )
        
        if success and 'access_token' in response:
            self.token = response['access_token']
            print(f"   ✅ JWT Token obtained: {self.token[:50]}...")
            print(f"   ✅ User role: {response.get('user', {}).get('role', 'unknown')}")
            return True
        return False

    def test_backup_admin_credentials(self):
        """Test backup admin credentials"""
        # Reset token for clean test
        original_token = self.token
        self.token = None
        
        success, response = self.run_test(
            "Emergency Database - Backup Admin (admin_backup/admin_backup)",
            "POST", 
            "auth/login",
            200,
            data={"username": "admin_backup", "password": "admin_backup"}
        )
        
        # Restore original token
        self.token = original_token
        
        if success and 'access_token' in response:
            print(f"   ✅ Backup admin working - Role: {response.get('user', {}).get('role', 'unknown')}")
            return True
        else:
            # Try alternative backup credentials
            success2, response2 = self.run_test(
                "Emergency Database - Alternative Backup (Gazette/80085)",
                "POST",
                "auth/login", 
                200,
                data={"username": "Gazette", "password": "80085"}
            )
            if success2:
                print(f"   ✅ Alternative backup admin working")
                return True
        return False

    # PRIORITY 2: Base64 Image Handling
    def test_base64_image_upload(self):
        """Test base64 image upload functionality"""
        print("\n" + "="*60)
        print("🖼️  PRIORITY 2: BASE64 IMAGE HANDLING")
        print("="*60)
        
        if not self.token:
            print("❌ No authentication token - skipping image upload tests")
            return False
        
        # Create a small test image in base64 format
        test_image_b64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
        
        # Test 1: Image upload endpoint
        success, response = self.run_test(
            "Base64 Image Upload - POST /api/upload-image",
            "POST",
            "upload-image",
            200,
            data={"image_data": f"data:image/png;base64,{test_image_b64}"}
        )
        
        if success:
            print(f"   ✅ Image upload successful")
            if 'url' in response:
                print(f"   ✅ Image URL returned: {response['url'][:100]}...")
                return True
        
        return False

    def test_article_with_base64_image(self):
        """Test creating article with base64 image"""
        if not self.token:
            print("❌ No authentication token - skipping article image test")
            return False
            
        # Small test image
        test_image_data = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
        
        article_data = {
            "title": "Test Article with Base64 Image",
            "subheading": "Testing image handling in articles",
            "content": "This article tests base64 image functionality in the CMS.",
            "category": "news",
            "publisher_name": "The Crewkerne Gazette",
            "featured_image": test_image_data,
            "image_caption": "Test image caption",
            "is_breaking": False,
            "tags": ["test", "image", "base64"]
        }
        
        success, response = self.run_test(
            "Article Creation with Base64 Image",
            "POST",
            "articles",
            200,
            data=article_data
        )
        
        if success and 'id' in response:
            self.created_article_id = response['id']
            print(f"   ✅ Article created with image - ID: {self.created_article_id}")
            print(f"   ✅ Image stored: {len(response.get('featured_image', '')) > 0}")
            return True
        return False

    # PRIORITY 3: Article Management with New Fields
    def test_comprehensive_article_management(self):
        """Test article management with all new fields"""
        print("\n" + "="*60)
        print("📰 PRIORITY 3: ARTICLE MANAGEMENT WITH NEW FIELDS")
        print("="*60)
        
        if not self.token:
            print("❌ No authentication token - skipping article management tests")
            return False
        
        # Test article creation with all new fields
        comprehensive_article = {
            "title": "Breaking News: Comprehensive Feature Test",
            "subheading": "Testing all new article fields including tags and publisher",
            "content": "This is a comprehensive test of all new article features including subheading, publisher selection, breaking news flag, and tagging system.",
            "category": "news",
            "publisher_name": "The Crewkerne Gazette",
            "is_breaking": True,
            "is_published": True,
            "tags": ["breaking", "test", "comprehensive", "features"],
            "image_caption": "Test image for comprehensive article"
        }
        
        success, response = self.run_test(
            "Comprehensive Article Creation",
            "POST",
            "articles",
            200,
            data=comprehensive_article
        )
        
        if success and 'id' in response:
            article_id = response['id']
            print(f"   ✅ Article created - ID: {article_id}")
            print(f"   ✅ Subheading: {response.get('subheading', 'Missing')}")
            print(f"   ✅ Publisher: {response.get('publisher_name', 'Missing')}")
            print(f"   ✅ Breaking News: {response.get('is_breaking', False)}")
            print(f"   ✅ Tags: {response.get('tags', [])}")
            
            # Test article retrieval
            success2, response2 = self.run_test(
                "Article Retrieval by ID",
                "GET",
                f"articles/{article_id}",
                200
            )
            
            if success2:
                print(f"   ✅ Article retrieved successfully")
                return True
        
        return False

    def test_breaking_news_filtering(self):
        """Test breaking news filtering"""
        success, response = self.run_test(
            "Breaking News Articles Filter",
            "GET",
            "articles?is_breaking=true",
            200
        )
        
        if success:
            breaking_articles = response if isinstance(response, list) else []
            print(f"   ✅ Breaking news filter working - Found {len(breaking_articles)} articles")
            return True
        return False

    def test_related_articles_endpoint(self):
        """Test related articles for trending topics"""
        if not self.created_article_id:
            print("   ⚠️  No article ID available for related articles test")
            return False
            
        success, response = self.run_test(
            "Related Articles for Trending Topics",
            "GET",
            f"articles/{self.created_article_id}/related",
            200
        )
        
        if success:
            related_articles = response if isinstance(response, list) else []
            print(f"   ✅ Related articles endpoint working - Found {len(related_articles)} related")
            return True
        return False

    # PRIORITY 4: Settings Management
    def test_settings_management(self):
        """Test settings management functionality"""
        print("\n" + "="*60)
        print("⚙️  PRIORITY 4: SETTINGS MANAGEMENT")
        print("="*60)
        
        # Test public settings (no auth required)
        success1, response1 = self.run_test(
            "Public Settings Endpoint",
            "GET",
            "settings/public",
            200
        )
        
        if success1:
            print(f"   ✅ Public settings accessible")
            print(f"   ✅ Breaking news banner status: {response1.get('show_breaking_news_banner', 'unknown')}")
        
        if not self.token:
            print("❌ No authentication token - skipping admin settings tests")
            return success1
        
        # Test admin settings (auth required)
        success2, response2 = self.run_test(
            "Admin Settings Endpoint",
            "GET",
            "settings",
            200
        )
        
        # Test breaking news banner toggle
        success3, response3 = self.run_test(
            "Breaking News Banner Toggle - Enable",
            "POST",
            "settings/breaking-news-banner",
            200,
            data={"show_breaking_news_banner": True}
        )
        
        # Test maintenance mode toggle
        success4, response4 = self.run_test(
            "Maintenance Mode Toggle",
            "POST",
            "settings/maintenance",
            200,
            data={"maintenance_mode": False}
        )
        
        return success1 and success2 and success3 and success4

    # PRIORITY 5: Meta Tags & Social Sharing Backend Support
    def test_meta_tags_social_sharing(self):
        """Test meta tags and social sharing backend support"""
        print("\n" + "="*60)
        print("🔗 PRIORITY 5: META TAGS & SOCIAL SHARING BACKEND SUPPORT")
        print("="*60)
        
        if not self.created_article_id:
            print("   ⚠️  No article ID available for meta tags test")
            return False
        
        # Test structured data endpoint for SEO/meta tags
        success, response = self.run_test(
            "Article Structured Data for SEO/Meta Tags",
            "GET",
            f"articles/{self.created_article_id}/structured-data",
            200
        )
        
        if success:
            print(f"   ✅ Structured data endpoint working")
            print(f"   ✅ Schema.org format: {'@context' in response}")
            print(f"   ✅ Article headline: {response.get('headline', 'Missing')}")
            print(f"   ✅ Publisher info: {response.get('publisher', {}).get('name', 'Missing')}")
            print(f"   ✅ Date published: {response.get('datePublished', 'Missing')}")
            return True
        
        return False

    # ADDITIONAL VERIFICATION TESTS
    def test_dashboard_stats(self):
        """Test dashboard statistics endpoint"""
        if not self.token:
            print("❌ No authentication token - skipping dashboard stats test")
            return False
            
        success, response = self.run_test(
            "Dashboard Statistics",
            "GET",
            "dashboard/stats",
            200
        )
        
        if success:
            print(f"   ✅ Dashboard stats working")
            print(f"   ✅ Total articles: {response.get('total_articles', 0)}")
            print(f"   ✅ Breaking news: {response.get('breaking_news', 0)}")
            print(f"   ✅ Emergency mode: {response.get('emergency_mode', False)}")
            return True
        return False

    def test_debug_endpoints(self):
        """Test debug endpoints for verification"""
        success1, response1 = self.run_test(
            "Debug Articles Endpoint",
            "GET",
            "debug/articles",
            200
        )
        
        success2, response2 = self.run_test(
            "Debug Settings Endpoint", 
            "GET",
            "debug/settings",
            200
        )
        
        if success1:
            print(f"   ✅ Debug articles: {response1.get('total_articles', 0)} articles in memory")
        if success2:
            print(f"   ✅ Debug settings: {response2.get('current_settings', {})}")
            
        return success1 and success2

    def run_comprehensive_tests(self):
        """Run all comprehensive tests in priority order"""
        print("🚀 COMPREHENSIVE BACKEND TESTING FOR PRODUCTION DEPLOYMENT")
        print("🎯 Testing all priority areas for local verification")
        print("="*80)
        
        results = {}
        
        # Priority 1: Emergency Database & Authentication
        results['emergency_auth'] = self.test_emergency_database_admin_login()
        results['backup_auth'] = self.test_backup_admin_credentials()
        
        # Priority 2: Base64 Image Handling
        results['image_upload'] = self.test_base64_image_upload()
        results['article_image'] = self.test_article_with_base64_image()
        
        # Priority 3: Article Management
        results['article_management'] = self.test_comprehensive_article_management()
        results['breaking_news_filter'] = self.test_breaking_news_filtering()
        results['related_articles'] = self.test_related_articles_endpoint()
        
        # Priority 4: Settings Management
        results['settings_management'] = self.test_settings_management()
        
        # Priority 5: Meta Tags & Social Sharing
        results['meta_tags_social'] = self.test_meta_tags_social_sharing()
        
        # Additional Verification
        results['dashboard_stats'] = self.test_dashboard_stats()
        results['debug_endpoints'] = self.test_debug_endpoints()
        
        return results

    def print_final_report(self, results):
        """Print comprehensive final report"""
        print("\n" + "="*80)
        print("📊 COMPREHENSIVE BACKEND TEST RESULTS")
        print("="*80)
        
        print("\n🚨 PRIORITY 1: EMERGENCY DATABASE SYSTEM & AUTHENTICATION")
        print(f"   Emergency Admin Login (admin/admin123): {'✅ PASS' if results['emergency_auth'] else '❌ FAIL'}")
        print(f"   Backup Admin Credentials: {'✅ PASS' if results['backup_auth'] else '❌ FAIL'}")
        
        print("\n🖼️  PRIORITY 2: BASE64 IMAGE HANDLING")
        print(f"   Image Upload Endpoint: {'✅ PASS' if results['image_upload'] else '❌ FAIL'}")
        print(f"   Article with Base64 Image: {'✅ PASS' if results['article_image'] else '❌ FAIL'}")
        
        print("\n📰 PRIORITY 3: ARTICLE MANAGEMENT WITH NEW FIELDS")
        print(f"   Comprehensive Article Creation: {'✅ PASS' if results['article_management'] else '❌ FAIL'}")
        print(f"   Breaking News Filtering: {'✅ PASS' if results['breaking_news_filter'] else '❌ FAIL'}")
        print(f"   Related Articles (Trending): {'✅ PASS' if results['related_articles'] else '❌ FAIL'}")
        
        print("\n⚙️  PRIORITY 4: SETTINGS MANAGEMENT")
        print(f"   Settings Management: {'✅ PASS' if results['settings_management'] else '❌ FAIL'}")
        
        print("\n🔗 PRIORITY 5: META TAGS & SOCIAL SHARING")
        print(f"   Meta Tags & Social Sharing: {'✅ PASS' if results['meta_tags_social'] else '❌ FAIL'}")
        
        print("\n🔍 ADDITIONAL VERIFICATION")
        print(f"   Dashboard Statistics: {'✅ PASS' if results['dashboard_stats'] else '❌ FAIL'}")
        print(f"   Debug Endpoints: {'✅ PASS' if results['debug_endpoints'] else '❌ FAIL'}")
        
        # Calculate overall statistics
        total_categories = len(results)
        passed_categories = sum(1 for result in results.values() if result)
        
        print(f"\n📈 OVERALL STATISTICS")
        print(f"   Tests Run: {self.tests_run}")
        print(f"   Tests Passed: {self.tests_passed}")
        print(f"   Tests Failed: {self.tests_run - self.tests_passed}")
        print(f"   Success Rate: {(self.tests_passed/self.tests_run)*100:.1f}%")
        print(f"   Categories Passed: {passed_categories}/{total_categories}")
        
        # Deployment readiness assessment
        critical_areas = ['emergency_auth', 'settings_management', 'article_management']
        critical_passed = all(results[area] for area in critical_areas if area in results)
        
        print(f"\n🚀 PRODUCTION DEPLOYMENT READINESS")
        if critical_passed and self.tests_passed >= (self.tests_run * 0.8):  # 80% pass rate
            print("   ✅ READY FOR PRODUCTION DEPLOYMENT")
            print("   ✅ All critical systems working locally")
            print("   ✅ Emergency database system functional")
            print("   ✅ Authentication system working")
            print("   ✅ Article management operational")
        else:
            print("   ❌ NOT READY FOR PRODUCTION DEPLOYMENT")
            print("   ❌ Critical issues found that need resolution")
            
        return critical_passed and self.tests_passed >= (self.tests_run * 0.8)

def main():
    """Main test execution"""
    tester = ComprehensiveBackendTester()
    
    try:
        results = tester.run_comprehensive_tests()
        deployment_ready = tester.print_final_report(results)
        
        if deployment_ready:
            print("\n🎉 SUCCESS: Backend is ready for production deployment!")
            return 0
        else:
            print("\n⚠️  WARNING: Backend has issues that should be resolved before deployment")
            return 1
            
    except Exception as e:
        print(f"\n💥 CRITICAL ERROR: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())