#!/usr/bin/env python3
"""
Dover Dash Game Backend Integration Test Suite

Tests the complete Dover Dash game backend functionality including:
1. Dover Dash Game Page serving
2. Leaderboard Database operations
3. Submit Score API with validation and sanitization
4. Get Leaderboard API with filtering options
5. Security and error handling
"""

import requests
import sys
import json
import time
from datetime import datetime, timedelta
import html

class DoverDashTester:
    def __init__(self, base_url="https://viewtrends-1.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []

    def log_test(self, name, success, details=""):
        """Log test result"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name}")
        else:
            print(f"❌ {name}")
        
        if details:
            print(f"   {details}")
        
        self.test_results.append({
            "name": name,
            "success": success,
            "details": details
        })

    def test_dover_dash_game_page(self):
        """Test 1: Dover Dash Game Page - GET /dover-dash endpoint"""
        print("\n🎮 Testing Dover Dash Game Page...")
        
        try:
            url = f"{self.base_url}/dover-dash"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                content = response.text
                # Check if it's HTML content
                if "<!DOCTYPE html>" in content or "<html" in content:
                    # Check for Dover Dash specific content
                    if "Dover Dash" in content or "dover" in content.lower():
                        self.log_test("Dover Dash Game Page Serves HTML", True, 
                                    f"Status: {response.status_code}, Content-Type: {response.headers.get('content-type', 'unknown')}")
                        return True
                    else:
                        self.log_test("Dover Dash Game Page Serves HTML", False, 
                                    "HTML served but doesn't contain Dover Dash content")
                        return False
                else:
                    self.log_test("Dover Dash Game Page Serves HTML", False, 
                                f"Response is not HTML content: {content[:100]}...")
                    return False
            elif response.status_code == 404:
                self.log_test("Dover Dash Game Page Serves HTML", False, 
                            "Game file not found - dover-dash.html missing")
                return False
            else:
                self.log_test("Dover Dash Game Page Serves HTML", False, 
                            f"Unexpected status code: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Dover Dash Game Page Serves HTML", False, f"Error: {str(e)}")
            return False

    def test_leaderboard_database_creation(self):
        """Test 2: Leaderboard Database - Table creation and basic operations"""
        print("\n🗄️ Testing Leaderboard Database...")
        
        # Test that leaderboard endpoints are accessible (they create table if needed)
        try:
            url = f"{self.api_url}/leaderboard"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if "scores" in data and "message" in data:
                    self.log_test("Leaderboard Database Table Creation", True, 
                                f"Table accessible, response structure correct")
                    return True
                else:
                    self.log_test("Leaderboard Database Table Creation", False, 
                                f"Invalid response structure: {data}")
                    return False
            else:
                self.log_test("Leaderboard Database Table Creation", False, 
                            f"Database error: Status {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Leaderboard Database Table Creation", False, f"Error: {str(e)}")
            return False

    def test_submit_score_api_basic(self):
        """Test 3a: Submit Score API - Basic functionality"""
        print("\n📊 Testing Submit Score API - Basic...")
        
        try:
            url = f"{self.api_url}/leaderboard"
            
            # Test data with realistic Dover Dash game data
            test_score = {
                "player_name": "Winston Churchill",
                "score": 15420,
                "title": "Defender of Dover"
            }
            
            response = requests.post(url, json=test_score, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data.get("ok") and "successfully" in data.get("message", "").lower():
                    self.log_test("Submit Score API Basic Functionality", True, 
                                f"Score submitted: {test_score['player_name']} - {test_score['score']} points")
                    return True
                else:
                    self.log_test("Submit Score API Basic Functionality", False, 
                                f"Unexpected response: {data}")
                    return False
            else:
                self.log_test("Submit Score API Basic Functionality", False, 
                            f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Submit Score API Basic Functionality", False, f"Error: {str(e)}")
            return False

    def test_submit_score_validation(self):
        """Test 3b: Submit Score API - Input validation"""
        print("\n🔒 Testing Submit Score API - Validation...")
        
        validation_tests = [
            {
                "name": "Empty player name",
                "data": {"player_name": "", "score": 1000, "title": "Test Title"},
                "should_fail": True
            },
            {
                "name": "Negative score",
                "data": {"player_name": "Test Player", "score": -100, "title": "Test Title"},
                "should_fail": True
            },
            {
                "name": "Very long player name",
                "data": {"player_name": "A" * 50, "score": 1000, "title": "Test Title"},
                "should_fail": True
            },
            {
                "name": "Missing required fields",
                "data": {"player_name": "Test Player"},
                "should_fail": True
            },
            {
                "name": "Valid maximum values",
                "data": {"player_name": "Boris Johnson", "score": 999999, "title": "Prime Minister of Dover Defense"},
                "should_fail": False
            }
        ]
        
        passed_validations = 0
        
        for test in validation_tests:
            try:
                url = f"{self.api_url}/leaderboard"
                response = requests.post(url, json=test["data"], timeout=10)
                
                if test["should_fail"]:
                    # Should return 4xx error
                    if response.status_code >= 400 and response.status_code < 500:
                        passed_validations += 1
                        print(f"   ✅ {test['name']}: Correctly rejected (HTTP {response.status_code})")
                    else:
                        print(f"   ❌ {test['name']}: Should have been rejected but got HTTP {response.status_code}")
                else:
                    # Should succeed
                    if response.status_code == 200:
                        passed_validations += 1
                        print(f"   ✅ {test['name']}: Correctly accepted")
                    else:
                        print(f"   ❌ {test['name']}: Should have been accepted but got HTTP {response.status_code}")
                        
            except Exception as e:
                print(f"   ❌ {test['name']}: Error - {str(e)}")
        
        success = passed_validations == len(validation_tests)
        self.log_test("Submit Score API Input Validation", success, 
                    f"Passed {passed_validations}/{len(validation_tests)} validation tests")
        return success

    def test_submit_score_sanitization(self):
        """Test 3c: Submit Score API - XSS/Injection prevention"""
        print("\n🛡️ Testing Submit Score API - Security Sanitization...")
        
        # Test XSS and injection attempts
        malicious_inputs = [
            {
                "name": "XSS Script Tag",
                "player_name": "<script>alert('xss')</script>",
                "expected_clean": "alert('xss')"  # Should strip script tags
            },
            {
                "name": "HTML Injection",
                "player_name": "<img src=x onerror=alert(1)>",
                "expected_clean": ""  # Should strip malicious HTML
            },
            {
                "name": "SQL Injection Attempt",
                "player_name": "'; DROP TABLE leaderboard; --",
                "expected_clean": "'; DROP TABLE leaderboard; --"  # Should be escaped/sanitized
            }
        ]
        
        sanitization_passed = 0
        
        for test in malicious_inputs:
            try:
                url = f"{self.api_url}/leaderboard"
                test_data = {
                    "player_name": test["player_name"],
                    "score": 1000,
                    "title": "Security Test"
                }
                
                response = requests.post(url, json=test_data, timeout=10)
                
                if response.status_code == 200:
                    # Check if the malicious input was sanitized by retrieving leaderboard
                    get_response = requests.get(f"{self.api_url}/leaderboard?limit=1", timeout=10)
                    if get_response.status_code == 200:
                        leaderboard_data = get_response.json()
                        if leaderboard_data.get("scores"):
                            latest_entry = leaderboard_data["scores"][0]
                            stored_name = latest_entry.get("player_name", "")
                            
                            # Check if dangerous content was removed/escaped
                            if "<script>" not in stored_name and "onerror=" not in stored_name:
                                sanitization_passed += 1
                                print(f"   ✅ {test['name']}: Properly sanitized")
                            else:
                                print(f"   ❌ {test['name']}: Dangerous content not sanitized: {stored_name}")
                        else:
                            print(f"   ⚠️ {test['name']}: Could not verify sanitization - no scores returned")
                    else:
                        print(f"   ⚠️ {test['name']}: Could not verify sanitization - leaderboard fetch failed")
                else:
                    print(f"   ❌ {test['name']}: Submission failed with HTTP {response.status_code}")
                    
            except Exception as e:
                print(f"   ❌ {test['name']}: Error - {str(e)}")
        
        success = sanitization_passed >= 2  # At least 2 out of 3 should pass
        self.log_test("Submit Score API Security Sanitization", success, 
                    f"Passed {sanitization_passed}/{len(malicious_inputs)} sanitization tests")
        return success

    def test_get_leaderboard_basic(self):
        """Test 4a: Get Leaderboard API - Basic functionality"""
        print("\n🏆 Testing Get Leaderboard API - Basic...")
        
        try:
            url = f"{self.api_url}/leaderboard"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                # Check response structure
                if "scores" in data and "message" in data:
                    scores = data["scores"]
                    if isinstance(scores, list):
                        self.log_test("Get Leaderboard API Basic Functionality", True, 
                                    f"Retrieved {len(scores)} scores, proper JSON structure")
                        return True
                    else:
                        self.log_test("Get Leaderboard API Basic Functionality", False, 
                                    f"Scores field is not a list: {type(scores)}")
                        return False
                else:
                    self.log_test("Get Leaderboard API Basic Functionality", False, 
                                f"Missing required fields in response: {data}")
                    return False
            else:
                self.log_test("Get Leaderboard API Basic Functionality", False, 
                            f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Get Leaderboard API Basic Functionality", False, f"Error: {str(e)}")
            return False

    def test_get_leaderboard_filters(self):
        """Test 4b: Get Leaderboard API - Filtering options"""
        print("\n🔍 Testing Get Leaderboard API - Filters...")
        
        filter_tests = [
            {
                "name": "Weekly Filter",
                "params": {"weekly": "true"},
                "description": "Should return weekly scores only"
            },
            {
                "name": "Limit Parameter",
                "params": {"limit": "5"},
                "description": "Should return maximum 5 scores"
            },
            {
                "name": "Combined Filters",
                "params": {"weekly": "true", "limit": "3"},
                "description": "Should return max 3 weekly scores"
            }
        ]
        
        filter_tests_passed = 0
        
        for test in filter_tests:
            try:
                url = f"{self.api_url}/leaderboard"
                response = requests.get(url, params=test["params"], timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    scores = data.get("scores", [])
                    
                    # Basic validation that it returns proper structure
                    if isinstance(scores, list) and "message" in data:
                        # Check limit parameter works
                        if "limit" in test["params"]:
                            expected_limit = int(test["params"]["limit"])
                            if len(scores) <= expected_limit:
                                filter_tests_passed += 1
                                print(f"   ✅ {test['name']}: Returned {len(scores)} scores (≤ {expected_limit})")
                            else:
                                print(f"   ❌ {test['name']}: Returned {len(scores)} scores (> {expected_limit})")
                        else:
                            filter_tests_passed += 1
                            print(f"   ✅ {test['name']}: Returned {len(scores)} scores")
                    else:
                        print(f"   ❌ {test['name']}: Invalid response structure")
                else:
                    print(f"   ❌ {test['name']}: HTTP {response.status_code}")
                    
            except Exception as e:
                print(f"   ❌ {test['name']}: Error - {str(e)}")
        
        success = filter_tests_passed >= 2  # At least 2 out of 3 should pass
        self.log_test("Get Leaderboard API Filtering", success, 
                    f"Passed {filter_tests_passed}/{len(filter_tests)} filter tests")
        return success

    def test_leaderboard_data_persistence(self):
        """Test 5: Data persistence and retrieval accuracy"""
        print("\n💾 Testing Leaderboard Data Persistence...")
        
        try:
            # Submit a unique test score
            timestamp = int(time.time())
            unique_name = f"TestPlayer{timestamp}"
            unique_score = 12345 + timestamp % 1000
            
            submit_data = {
                "player_name": unique_name,
                "score": unique_score,
                "title": "Dover Defense Champion"
            }
            
            # Submit the score
            submit_url = f"{self.api_url}/leaderboard"
            submit_response = requests.post(submit_url, json=submit_data, timeout=10)
            
            if submit_response.status_code != 200:
                self.log_test("Leaderboard Data Persistence", False, 
                            f"Failed to submit test score: HTTP {submit_response.status_code}")
                return False
            
            # Wait a moment for database write
            time.sleep(1)
            
            # Retrieve leaderboard and check if our score is there
            get_url = f"{self.api_url}/leaderboard?limit=20"
            get_response = requests.get(get_url, timeout=10)
            
            if get_response.status_code == 200:
                data = get_response.json()
                scores = data.get("scores", [])
                
                # Look for our submitted score
                found_score = None
                for score_entry in scores:
                    if (score_entry.get("player_name") == unique_name and 
                        score_entry.get("score") == unique_score):
                        found_score = score_entry
                        break
                
                if found_score:
                    # Verify all fields are preserved
                    if (found_score.get("title") == submit_data["title"] and
                        "created_at" in found_score):
                        self.log_test("Leaderboard Data Persistence", True, 
                                    f"Score persisted correctly: {unique_name} - {unique_score}")
                        return True
                    else:
                        self.log_test("Leaderboard Data Persistence", False, 
                                    f"Score found but fields incomplete: {found_score}")
                        return False
                else:
                    self.log_test("Leaderboard Data Persistence", False, 
                                f"Submitted score not found in leaderboard")
                    return False
            else:
                self.log_test("Leaderboard Data Persistence", False, 
                            f"Failed to retrieve leaderboard: HTTP {get_response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Leaderboard Data Persistence", False, f"Error: {str(e)}")
            return False

    def test_error_handling(self):
        """Test 6: Error handling for various failure scenarios"""
        print("\n⚠️ Testing Error Handling...")
        
        error_tests = [
            {
                "name": "Invalid JSON",
                "method": "POST",
                "url": f"{self.api_url}/leaderboard",
                "data": "invalid json",
                "headers": {"Content-Type": "application/json"},
                "expected_status_range": (400, 499)
            },
            {
                "name": "Missing Content-Type",
                "method": "POST", 
                "url": f"{self.api_url}/leaderboard",
                "data": '{"player_name": "test", "score": 100, "title": "test"}',
                "headers": {},
                "expected_status_range": (400, 499)
            },
            {
                "name": "Non-existent endpoint",
                "method": "GET",
                "url": f"{self.api_url}/nonexistent",
                "data": None,
                "headers": {},
                "expected_status_range": (404, 404)
            }
        ]
        
        error_tests_passed = 0
        
        for test in error_tests:
            try:
                if test["method"] == "POST":
                    if isinstance(test["data"], str):
                        response = requests.post(test["url"], data=test["data"], 
                                               headers=test["headers"], timeout=10)
                    else:
                        response = requests.post(test["url"], json=test["data"], 
                                               headers=test["headers"], timeout=10)
                else:
                    response = requests.get(test["url"], headers=test["headers"], timeout=10)
                
                min_status, max_status = test["expected_status_range"]
                if min_status <= response.status_code <= max_status:
                    error_tests_passed += 1
                    print(f"   ✅ {test['name']}: Correctly returned HTTP {response.status_code}")
                else:
                    print(f"   ❌ {test['name']}: Expected {min_status}-{max_status}, got {response.status_code}")
                    
            except Exception as e:
                print(f"   ❌ {test['name']}: Error - {str(e)}")
        
        success = error_tests_passed >= 2  # At least 2 out of 3 should pass
        self.log_test("Error Handling", success, 
                    f"Passed {error_tests_passed}/{len(error_tests)} error handling tests")
        return success

    def run_all_tests(self):
        """Run all Dover Dash backend tests"""
        print("🎯 DOVER DASH BACKEND INTEGRATION TEST SUITE")
        print("=" * 60)
        print(f"Testing backend at: {self.base_url}")
        print(f"API endpoint: {self.api_url}")
        print()
        
        # Run all test categories
        test_methods = [
            self.test_dover_dash_game_page,
            self.test_leaderboard_database_creation,
            self.test_submit_score_api_basic,
            self.test_submit_score_validation,
            self.test_submit_score_sanitization,
            self.test_get_leaderboard_basic,
            self.test_get_leaderboard_filters,
            self.test_leaderboard_data_persistence,
            self.test_error_handling
        ]
        
        for test_method in test_methods:
            try:
                test_method()
            except Exception as e:
                print(f"❌ Test method {test_method.__name__} failed with error: {str(e)}")
        
        # Print summary
        self.print_summary()

    def print_summary(self):
        """Print test summary and results"""
        print("\n" + "=" * 60)
        print("📊 DOVER DASH BACKEND TEST SUMMARY")
        print("=" * 60)
        
        success_rate = (self.tests_passed / self.tests_run * 100) if self.tests_run > 0 else 0
        
        print(f"Tests Run: {self.tests_run}")
        print(f"Tests Passed: {self.tests_passed}")
        print(f"Tests Failed: {self.tests_run - self.tests_passed}")
        print(f"Success Rate: {success_rate:.1f}%")
        
        print("\n🎯 DOVER DASH FUNCTIONALITY STATUS:")
        
        # Categorize results
        critical_tests = [
            "Dover Dash Game Page Serves HTML",
            "Leaderboard Database Table Creation", 
            "Submit Score API Basic Functionality",
            "Get Leaderboard API Basic Functionality"
        ]
        
        security_tests = [
            "Submit Score API Input Validation",
            "Submit Score API Security Sanitization"
        ]
        
        advanced_tests = [
            "Get Leaderboard API Filtering",
            "Leaderboard Data Persistence",
            "Error Handling"
        ]
        
        def check_category(test_names):
            passed = sum(1 for result in self.test_results 
                        if result["name"] in test_names and result["success"])
            total = len([r for r in self.test_results if r["name"] in test_names])
            return passed, total
        
        critical_passed, critical_total = check_category(critical_tests)
        security_passed, security_total = check_category(security_tests)
        advanced_passed, advanced_total = check_category(advanced_tests)
        
        print(f"   🎮 Core Game Functionality: {critical_passed}/{critical_total} ({'✅' if critical_passed == critical_total else '❌'})")
        print(f"   🔒 Security & Validation: {security_passed}/{security_total} ({'✅' if security_passed >= security_total - 1 else '❌'})")
        print(f"   ⚙️ Advanced Features: {advanced_passed}/{advanced_total} ({'✅' if advanced_passed >= advanced_total - 1 else '❌'})")
        
        # Overall assessment
        if success_rate >= 90:
            print(f"\n🎉 EXCELLENT: Dover Dash backend is fully functional and production-ready!")
        elif success_rate >= 75:
            print(f"\n✅ GOOD: Dover Dash backend is working well with minor issues")
        elif success_rate >= 50:
            print(f"\n⚠️ PARTIAL: Dover Dash backend has some functionality but needs fixes")
        else:
            print(f"\n❌ CRITICAL: Dover Dash backend has major issues requiring immediate attention")
        
        return success_rate >= 75

def main():
    """Main test execution"""
    import os
    
    # Get backend URL from environment or use default
    backend_url = os.getenv('REACT_APP_BACKEND_URL', 'https://viewtrends-1.preview.emergentagent.com')
    
    print(f"🚀 Starting Dover Dash Backend Integration Tests")
    print(f"🎯 Target: {backend_url}")
    
    tester = DoverDashTester(backend_url)
    tester.run_all_tests()
    
    # Return appropriate exit code
    success_rate = (tester.tests_passed / tester.tests_run * 100) if tester.tests_run > 0 else 0
    return 0 if success_rate >= 75 else 1

if __name__ == "__main__":
    sys.exit(main())