#!/usr/bin/env python3
"""
Local Article Slug System and SEO Optimization Testing
for The Crewkerne Gazette

Testing against local backend at localhost:8001
"""

import requests
import sys
import json
import xml.etree.ElementTree as ET
from datetime import datetime
from urllib.parse import urlparse
import re

class LocalArticleSlugSEOTester:
    def __init__(self, base_url="http://localhost:8001"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.token = None
        self.tests_run = 0
        self.tests_passed = 0
        self.created_articles = []
        
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
        return success

    def make_request(self, method, endpoint, data=None, headers=None, expect_json=True):
        """Make HTTP request with error handling"""
        if endpoint.startswith('api/'):
            url = f"{self.api_url}/{endpoint[4:]}"  # Remove 'api/' prefix
        else:
            url = f"{self.base_url}/{endpoint}"
        
        request_headers = {'Content-Type': 'application/json'}
        if self.token:
            request_headers['Authorization'] = f'Bearer {self.token}'
        if headers:
            request_headers.update(headers)
            
        try:
            if method == 'GET':
                response = requests.get(url, headers=request_headers, timeout=10)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=request_headers, timeout=10)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=request_headers, timeout=10)
            elif method == 'DELETE':
                response = requests.delete(url, headers=request_headers, timeout=10)
            
            if expect_json:
                try:
                    return response.status_code, response.json()
                except:
                    return response.status_code, response.text
            else:
                return response.status_code, response.text
                
        except Exception as e:
            return 0, str(e)

    def authenticate(self):
        """Authenticate with admin credentials"""
        print("\n🔐 AUTHENTICATION")
        print("-" * 40)
        
        status, response = self.make_request('POST', 'api/auth/login', {
            "username": "admin",
            "password": "admin123"
        })
        
        if status == 200 and isinstance(response, dict) and 'access_token' in response:
            self.token = response['access_token']
            return self.log_test("Admin Authentication", True, f"Token obtained successfully")
        else:
            return self.log_test("Admin Authentication", False, f"Status: {status}, Response: {response}")

    def test_seo_routes(self):
        """Test SEO routes: robots.txt, sitemap.xml, news-sitemap.xml"""
        print("\n🔍 SEO ROUTES VALIDATION")
        print("-" * 40)
        
        # Test robots.txt
        status, content = self.make_request('GET', 'robots.txt', expect_json=False)
        robots_valid = (
            status == 200 and 
            'User-agent: *' in content and
            'Sitemap: https://crewkernegazette.co.uk/sitemap.xml' in content and
            'Disallow: /dashboard' in content
        )
        self.log_test("GET /robots.txt", robots_valid, 
                     f"Status: {status}, Contains required directives: {robots_valid}")
        
        # Test sitemap.xml
        status, content = self.make_request('GET', 'sitemap.xml', expect_json=False)
        sitemap_valid = False
        if status == 200:
            try:
                # Parse XML to validate structure
                root = ET.fromstring(content)
                namespace = {'ns': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
                urls = root.findall('.//ns:url', namespace)
                sitemap_valid = len(urls) > 0 and any('crewkernegazette.co.uk' in url.find('ns:loc', namespace).text for url in urls)
            except Exception as e:
                print(f"   XML Parse Error: {e}")
                sitemap_valid = False
        
        self.log_test("GET /sitemap.xml", sitemap_valid,
                     f"Status: {status}, Valid XML with URLs: {sitemap_valid}")
        
        # Test news-sitemap.xml
        status, content = self.make_request('GET', 'news-sitemap.xml', expect_json=False)
        news_sitemap_valid = False
        if status == 200:
            try:
                # Parse XML to validate Google News format
                root = ET.fromstring(content)
                news_namespace = {'ns': 'http://www.sitemaps.org/schemas/sitemap/0.9', 
                                'news': 'http://www.google.com/schemas/sitemap-news/0.9'}
                news_sitemap_valid = 'xmlns:news="http://www.google.com/schemas/sitemap-news/0.9"' in content
            except Exception as e:
                print(f"   XML Parse Error: {e}")
                news_sitemap_valid = False
        
        self.log_test("GET /news-sitemap.xml", news_sitemap_valid,
                     f"Status: {status}, Valid Google News format: {news_sitemap_valid}")

    def test_article_slug_generation(self):
        """Test article slug generation and uniqueness"""
        print("\n🏷️  ARTICLE SLUG SYSTEM TESTING")
        print("-" * 40)
        
        if not self.token:
            self.log_test("Article Slug Testing", False, "Authentication required")
            return
        
        # Test article creation with automatic slug generation
        test_articles = [
            {
                "title": "Breaking News: Major Development in Crewkerne Today",
                "content": "This is a comprehensive test article for slug generation testing. It contains enough content to meet the minimum requirements for article creation and provides a realistic example of news content.",
                "category": "NEWS",
                "subheading": "Testing slug generation functionality with realistic content",
                "is_breaking": True,
                "tags": ["test", "slug", "breaking", "crewkerne"]
            },
            {
                "title": "Music Review: Local Band Rocks the Stage at Somerset Festival!",
                "content": "Another comprehensive test article to verify slug uniqueness and generation. This article has different content and category to test the system thoroughly and ensure proper slug handling.",
                "category": "MUSIC", 
                "subheading": "Testing slug uniqueness with different content",
                "is_breaking": False,
                "tags": ["music", "review", "local", "festival"]
            }
        ]
        
        created_slugs = []
        
        for i, article_data in enumerate(test_articles):
            # Create article via form data (as per backend implementation)
            form_data = {
                'title': article_data['title'],
                'content': article_data['content'],
                'category': article_data['category'],
                'subheading': article_data['subheading'],
                'is_breaking': str(article_data['is_breaking']).lower(),
                'tags': json.dumps(article_data['tags'])
            }
            
            # Use requests with form data instead of JSON
            url = f"{self.api_url}/articles"
            headers = {'Authorization': f'Bearer {self.token}'}
            
            try:
                response = requests.post(url, data=form_data, headers=headers, timeout=10)
                status = response.status_code
                
                if status == 200:
                    article = response.json()
                    slug = article.get('slug')
                    if slug:
                        created_slugs.append(slug)
                        self.created_articles.append(article['uuid'])
                        
                        # Verify slug format (SEO-friendly)
                        slug_valid = (
                            re.match(r'^[a-z0-9-]+$', slug) and
                            len(slug) <= 100 and
                            not slug.startswith('-') and
                            not slug.endswith('-')
                        )
                        
                        self.log_test(f"Article Creation #{i+1} with Slug", True,
                                    f"Slug: '{slug}', Valid format: {slug_valid}")
                    else:
                        self.log_test(f"Article Creation #{i+1}", False, "No slug generated")
                else:
                    try:
                        error_data = response.json()
                        self.log_test(f"Article Creation #{i+1}", False, f"Status: {status}, Error: {error_data}")
                    except:
                        self.log_test(f"Article Creation #{i+1}", False, f"Status: {status}, Text: {response.text}")
                    
            except Exception as e:
                self.log_test(f"Article Creation #{i+1}", False, f"Error: {e}")
        
        # Test slug uniqueness
        unique_slugs = len(set(created_slugs)) == len(created_slugs)
        self.log_test("Slug Uniqueness", unique_slugs,
                     f"Created {len(created_slugs)} articles with unique slugs: {unique_slugs}")

    def test_slug_based_routes(self):
        """Test article retrieval using slugs"""
        print("\n🔗 SLUG-BASED ROUTE VALIDATION")
        print("-" * 40)
        
        # Get articles to find their slugs
        status, articles = self.make_request('GET', 'api/articles?limit=5')
        
        if status == 200 and isinstance(articles, list) and len(articles) > 0:
            test_article = articles[0]
            slug = test_article.get('slug')
            
            if slug:
                # Test API route with slug
                status, article_data = self.make_request('GET', f'api/articles/{slug}')
                api_route_valid = (status == 200 and 
                                 isinstance(article_data, dict) and 
                                 article_data.get('slug') == slug)
                
                self.log_test(f"GET /api/articles/{slug}", api_route_valid,
                             f"Status: {status}, Article retrieved: {api_route_valid}")
                
                # Test structured data endpoint
                status, structured_data = self.make_request('GET', f'api/articles/{slug}/structured-data')
                structured_valid = (status == 200 and 
                                  isinstance(structured_data, dict) and
                                  structured_data.get('@type') == 'NewsArticle')
                
                self.log_test(f"GET /api/articles/{slug}/structured-data", structured_valid,
                             f"Status: {status}, NewsArticle schema: {structured_valid}")
                
                # Test article page route (for crawlers)
                status, html_content = self.make_request('GET', f'article/{slug}', 
                                                       headers={'User-Agent': 'facebookexternalhit/1.1'}, 
                                                       expect_json=False)
                
                html_valid = (status == 200 and 
                            'og:title' in html_content and
                            'NewsArticle' in html_content and
                            f'crewkernegazette.co.uk/article/{slug}' in html_content)
                
                self.log_test(f"GET /article/{slug} (crawler)", html_valid,
                             f"Status: {status}, Contains meta tags: {html_valid}")
            else:
                self.log_test("Slug Route Testing", False, "No slug found in article")
        else:
            self.log_test("Slug Route Testing", False, f"Could not retrieve articles: {status}")

    def test_meta_tags_structured_data(self):
        """Test meta tags and structured data generation"""
        print("\n📋 META TAGS & STRUCTURED DATA")
        print("-" * 40)
        
        # Get a sample article
        status, articles = self.make_request('GET', 'api/articles?limit=1')
        
        if status == 200 and isinstance(articles, list) and len(articles) > 0:
            article = articles[0]
            slug = article.get('slug')
            
            if slug:
                # Test structured data endpoint
                status, structured_data = self.make_request('GET', f'api/articles/{slug}/structured-data')
                
                if status == 200 and isinstance(structured_data, dict):
                    # Validate NewsArticle schema
                    required_fields = ['@context', '@type', 'headline', 'datePublished', 'author', 'publisher']
                    schema_valid = all(field in structured_data for field in required_fields)
                    
                    # Check specific values
                    context_valid = structured_data.get('@context') == 'https://schema.org'
                    type_valid = structured_data.get('@type') == 'NewsArticle'
                    publisher_valid = (isinstance(structured_data.get('publisher'), dict) and
                                     structured_data['publisher'].get('name') == 'The Crewkerne Gazette')
                    
                    self.log_test("NewsArticle Schema Validation", schema_valid and context_valid and type_valid,
                                 f"Required fields: {schema_valid}, Context: {context_valid}, Type: {type_valid}")
                    
                    self.log_test("Publisher Information", publisher_valid,
                                 f"Publisher name correct: {publisher_valid}")
                else:
                    self.log_test("Structured Data Generation", False, f"Status: {status}")
                
                # Test meta HTML generation for crawlers
                status, html_content = self.make_request('GET', f'article/{slug}',
                                                       headers={'User-Agent': 'facebookexternalhit/1.1'},
                                                       expect_json=False)
                
                if status == 200:
                    # Check for Open Graph tags
                    og_tags = ['og:title', 'og:description', 'og:type', 'og:url', 'og:image']
                    og_valid = all(tag in html_content for tag in og_tags)
                    
                    # Check for Twitter Card tags
                    twitter_tags = ['twitter:card', 'twitter:title', 'twitter:description', 'twitter:image']
                    twitter_valid = all(tag in html_content for tag in twitter_tags)
                    
                    # Check for canonical URL
                    canonical_valid = f'<link rel="canonical" href="https://crewkernegazette.co.uk/article/{slug}">' in html_content
                    
                    self.log_test("Open Graph Meta Tags", og_valid,
                                 f"All OG tags present: {og_valid}")
                    
                    self.log_test("Twitter Card Meta Tags", twitter_valid,
                                 f"All Twitter tags present: {twitter_valid}")
                    
                    self.log_test("Canonical URL", canonical_valid,
                                 f"Canonical URL with slug: {canonical_valid}")
                else:
                    self.log_test("Meta HTML Generation", False, f"Status: {status}")
            else:
                self.log_test("Meta Tags Testing", False, "No slug available for testing")
        else:
            self.log_test("Meta Tags Testing", False, "No articles available for testing")

    def test_error_handling(self):
        """Test error handling for missing articles"""
        print("\n🚫 ERROR HANDLING VALIDATION")
        print("-" * 40)
        
        # Test non-existent slug
        fake_slug = "non-existent-article-slug-12345"
        
        # Test API endpoint
        status, response = self.make_request('GET', f'api/articles/{fake_slug}')
        api_404_valid = status == 404
        self.log_test("API 404 for missing article", api_404_valid,
                     f"Status: {status} (expected 404)")
        
        # Test structured data endpoint
        status, response = self.make_request('GET', f'api/articles/{fake_slug}/structured-data')
        structured_404_valid = status == 404
        self.log_test("Structured data 404 for missing article", structured_404_valid,
                     f"Status: {status} (expected 404)")
        
        # Test article page route
        status, response = self.make_request('GET', f'article/{fake_slug}', expect_json=False)
        page_404_valid = status == 404
        self.log_test("Article page 404 for missing article", page_404_valid,
                     f"Status: {status} (expected 404)")

    def cleanup_test_articles(self):
        """Clean up created test articles"""
        print("\n🧹 CLEANUP")
        print("-" * 40)
        
        if not self.token or not self.created_articles:
            print("   No cleanup needed")
            return
        
        cleaned_count = 0
        for article_uuid in self.created_articles:
            status, response = self.make_request('DELETE', f'api/articles/{article_uuid}')
            if status == 200:
                cleaned_count += 1
        
        print(f"   Cleaned up {cleaned_count}/{len(self.created_articles)} test articles")

    def run_comprehensive_test(self):
        """Run all tests in sequence"""
        print("🚀 CREWKERNE GAZETTE - LOCAL ARTICLE SLUG SYSTEM & SEO TESTING")
        print("=" * 80)
        print(f"Target: {self.base_url}")
        print(f"API: {self.api_url}")
        print("=" * 80)
        
        # Authentication
        auth_success = self.authenticate()
        
        # Core SEO Routes Testing
        self.test_seo_routes()
        
        # Article Slug System Testing
        if auth_success:
            self.test_article_slug_generation()
            self.test_slug_based_routes()
        
        # Meta Tags and Structured Data
        self.test_meta_tags_structured_data()
        
        # Error Handling
        self.test_error_handling()
        
        # Cleanup
        self.cleanup_test_articles()
        
        # Final Results
        print("\n" + "=" * 80)
        print("📊 FINAL RESULTS")
        print("=" * 80)
        print(f"Tests Run: {self.tests_run}")
        print(f"Tests Passed: {self.tests_passed}")
        print(f"Tests Failed: {self.tests_run - self.tests_passed}")
        print(f"Success Rate: {(self.tests_passed/self.tests_run)*100:.1f}%")
        
        # Critical success criteria
        print(f"\n🎯 CRITICAL SUCCESS CRITERIA:")
        if self.tests_passed >= self.tests_run * 0.8:  # 80% pass rate
            print("✅ PASSED - Article slug system and SEO optimization working correctly")
            return 0
        else:
            print("❌ FAILED - Critical issues found in article slug system or SEO optimization")
            return 1

def main():
    """Main test execution"""
    tester = LocalArticleSlugSEOTester("http://localhost:8001")
    return tester.run_comprehensive_test()

if __name__ == "__main__":
    sys.exit(main())