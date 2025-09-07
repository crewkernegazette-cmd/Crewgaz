#!/usr/bin/env python3
"""
Dover Dash Leaderboard API Testing Script
Tests the leaderboard functionality to identify score submission failures
"""

import requests
import json
import sys
from datetime import datetime
import time

class DoverDashLeaderboardTester:
    def __init__(self, base_url="http://localhost:8001"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.errors = []

    def log_result(self, test_name, success, details=""):
        """Log test result"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {test_name}: PASSED")
            if details:
                print(f"   {details}")
        else:
            print(f"❌ {test_name}: FAILED")
            if details:
                print(f"   {details}")
            self.errors.append(f"{test_name}: {details}")

    def test_database_connection(self):
        """Test if the backend can connect to the database"""
        print("\n🔍 Testing Database Connection...")
        
        try:
            # Test a simple endpoint that would use the database
            response = requests.get(f"{self.api_url}/articles", timeout=10)
            
            if response.status_code == 200:
                self.log_result("Database Connection", True, "Backend can connect to database successfully")
                return True
            elif response.status_code == 500:
                try:
                    error_data = response.json()
                    self.log_result("Database Connection", False, f"Database error: {error_data}")
                except:
                    self.log_result("Database Connection", False, f"Database error: {response.text}")
                return False
            else:
                self.log_result("Database Connection", False, f"Unexpected status: {response.status_code}")
                return False
                
        except requests.exceptions.ConnectionError:
            self.log_result("Database Connection", False, "Cannot connect to backend server")
            return False
        except Exception as e:
            self.log_result("Database Connection", False, f"Connection error: {str(e)}")
            return False

    def test_leaderboard_table_creation(self):
        """Test if leaderboard table can be created/accessed"""
        print("\n🔍 Testing Leaderboard Table Access...")
        
        try:
            # Try to get leaderboard - this should create the table if it doesn't exist
            response = requests.get(f"{self.api_url}/leaderboard", timeout=10)
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    if 'scores' in data and 'message' in data:
                        self.log_result("Leaderboard Table Access", True, f"Table accessible, message: {data['message']}")
                        return True
                    else:
                        self.log_result("Leaderboard Table Access", False, f"Invalid response format: {data}")
                        return False
                except json.JSONDecodeError:
                    self.log_result("Leaderboard Table Access", False, f"Invalid JSON response: {response.text}")
                    return False
            else:
                self.log_result("Leaderboard Table Access", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_result("Leaderboard Table Access", False, f"Error: {str(e)}")
            return False

    def test_score_submission(self):
        """Test score submission with sample data"""
        print("\n🔍 Testing Score Submission...")
        
        # Test data as specified in the review request
        test_data = {
            "player_name": "TestPM",
            "score": 150,
            "title": "Dover Guardian"
        }
        
        try:
            response = requests.post(
                f"{self.api_url}/leaderboard",
                json=test_data,
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
            
            print(f"   Request URL: {self.api_url}/leaderboard")
            print(f"   Request Data: {test_data}")
            print(f"   Response Status: {response.status_code}")
            print(f"   Response Headers: {dict(response.headers)}")
            
            if response.status_code == 200:
                try:
                    response_data = response.json()
                    print(f"   Response Body: {response_data}")
                    
                    if response_data.get('ok') == True or 'successfully' in response_data.get('message', '').lower():
                        self.log_result("Score Submission", True, f"Score submitted successfully: {response_data}")
                        return True, response_data
                    else:
                        self.log_result("Score Submission", False, f"Unexpected response: {response_data}")
                        return False, response_data
                        
                except json.JSONDecodeError:
                    self.log_result("Score Submission", False, f"Invalid JSON response: {response.text}")
                    return False, response.text
                    
            elif response.status_code == 422:
                try:
                    error_data = response.json()
                    self.log_result("Score Submission", False, f"Validation error: {error_data}")
                    return False, error_data
                except:
                    self.log_result("Score Submission", False, f"Validation error: {response.text}")
                    return False, response.text
                    
            elif response.status_code == 500:
                try:
                    error_data = response.json()
                    self.log_result("Score Submission", False, f"Server error: {error_data}")
                    return False, error_data
                except:
                    self.log_result("Score Submission", False, f"Server error: {response.text}")
                    return False, response.text
            else:
                self.log_result("Score Submission", False, f"HTTP {response.status_code}: {response.text}")
                return False, response.text
                
        except requests.exceptions.ConnectionError:
            self.log_result("Score Submission", False, "Cannot connect to backend server")
            return False, "Connection error"
        except Exception as e:
            self.log_result("Score Submission", False, f"Error: {str(e)}")
            return False, str(e)

    def test_leaderboard_retrieval(self):
        """Test leaderboard retrieval and verify data format"""
        print("\n🔍 Testing Leaderboard Retrieval...")
        
        try:
            response = requests.get(f"{self.api_url}/leaderboard", timeout=10)
            
            print(f"   Request URL: {self.api_url}/leaderboard")
            print(f"   Response Status: {response.status_code}")
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    print(f"   Response Data: {data}")
                    
                    # Verify response structure
                    if 'scores' in data and 'message' in data:
                        scores = data['scores']
                        if isinstance(scores, list):
                            self.log_result("Leaderboard Retrieval", True, f"Retrieved {len(scores)} scores successfully")
                            
                            # Check if our test score is there
                            test_score_found = False
                            for score in scores:
                                if score.get('player_name') == 'TestPM' and score.get('score') == 150:
                                    test_score_found = True
                                    print(f"   ✅ Test score found in leaderboard: {score}")
                                    break
                            
                            if test_score_found:
                                print(f"   ✅ Score persistence verified")
                            else:
                                print(f"   ⚠️  Test score not found in leaderboard (may have been submitted in previous run)")
                            
                            return True, data
                        else:
                            self.log_result("Leaderboard Retrieval", False, f"Invalid scores format: {type(scores)}")
                            return False, data
                    else:
                        self.log_result("Leaderboard Retrieval", False, f"Missing required fields in response: {data}")
                        return False, data
                        
                except json.JSONDecodeError:
                    self.log_result("Leaderboard Retrieval", False, f"Invalid JSON response: {response.text}")
                    return False, response.text
            else:
                self.log_result("Leaderboard Retrieval", False, f"HTTP {response.status_code}: {response.text}")
                return False, response.text
                
        except Exception as e:
            self.log_result("Leaderboard Retrieval", False, f"Error: {str(e)}")
            return False, str(e)

    def test_leaderboard_with_parameters(self):
        """Test leaderboard with query parameters"""
        print("\n🔍 Testing Leaderboard with Parameters...")
        
        # Test with limit parameter
        try:
            response = requests.get(f"{self.api_url}/leaderboard?limit=5", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                scores = data.get('scores', [])
                if len(scores) <= 5:
                    self.log_result("Leaderboard Limit Parameter", True, f"Limit parameter working, got {len(scores)} scores")
                else:
                    self.log_result("Leaderboard Limit Parameter", False, f"Limit not respected, got {len(scores)} scores")
            else:
                self.log_result("Leaderboard Limit Parameter", False, f"HTTP {response.status_code}")
                
        except Exception as e:
            self.log_result("Leaderboard Limit Parameter", False, f"Error: {str(e)}")
        
        # Test with weekly parameter
        try:
            response = requests.get(f"{self.api_url}/leaderboard?weekly=true", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                message = data.get('message', '')
                if 'weekly' in message.lower():
                    self.log_result("Leaderboard Weekly Parameter", True, f"Weekly parameter working: {message}")
                else:
                    self.log_result("Leaderboard Weekly Parameter", True, f"Weekly parameter accepted: {message}")
            else:
                self.log_result("Leaderboard Weekly Parameter", False, f"HTTP {response.status_code}")
                
        except Exception as e:
            self.log_result("Leaderboard Weekly Parameter", False, f"Error: {str(e)}")

    def test_score_validation(self):
        """Test score submission validation"""
        print("\n🔍 Testing Score Validation...")
        
        # Test invalid data
        invalid_tests = [
            {"data": {"player_name": "", "score": 100, "title": "Test"}, "reason": "Empty player name"},
            {"data": {"player_name": "Test", "score": -1, "title": "Test"}, "reason": "Negative score"},
            {"data": {"player_name": "A" * 25, "score": 100, "title": "Test"}, "reason": "Player name too long"},
            {"data": {"score": 100, "title": "Test"}, "reason": "Missing player name"},
            {"data": {"player_name": "Test", "title": "Test"}, "reason": "Missing score"},
            {"data": {"player_name": "Test", "score": 100}, "reason": "Missing title"},
        ]
        
        validation_working = True
        
        for test_case in invalid_tests:
            try:
                response = requests.post(
                    f"{self.api_url}/leaderboard",
                    json=test_case["data"],
                    headers={'Content-Type': 'application/json'},
                    timeout=10
                )
                
                if response.status_code == 422:
                    print(f"   ✅ Validation working for: {test_case['reason']}")
                elif response.status_code == 500:
                    print(f"   ❌ Server error for: {test_case['reason']} - {response.text}")
                    validation_working = False
                else:
                    print(f"   ⚠️  Unexpected status {response.status_code} for: {test_case['reason']}")
                    
            except Exception as e:
                print(f"   ❌ Error testing {test_case['reason']}: {str(e)}")
                validation_working = False
        
        self.log_result("Score Validation", validation_working, "Input validation checks")

    def test_frontend_url_configuration(self):
        """Test frontend URL configuration"""
        print("\n🔍 Testing Frontend URL Configuration...")
        
        # Read frontend .env file
        try:
            with open('/app/frontend/.env', 'r') as f:
                env_content = f.read()
            
            backend_url = None
            for line in env_content.split('\n'):
                if line.startswith('REACT_APP_BACKEND_URL='):
                    backend_url = line.split('=', 1)[1]
                    break
            
            if backend_url:
                print(f"   Frontend configured URL: {backend_url}")
                
                if "None" in backend_url:
                    self.log_result("Frontend URL Configuration", False, f"Frontend URL contains 'None': {backend_url}")
                    return False
                else:
                    # Test if the configured URL works
                    try:
                        response = requests.get(f"{backend_url}/api/leaderboard", timeout=5)
                        if response.status_code == 200:
                            self.log_result("Frontend URL Configuration", True, f"Frontend URL is accessible: {backend_url}")
                            return True
                        else:
                            self.log_result("Frontend URL Configuration", False, f"Frontend URL returns {response.status_code}: {backend_url}")
                            return False
                    except Exception as e:
                        self.log_result("Frontend URL Configuration", False, f"Frontend URL not accessible: {backend_url} - {str(e)}")
                        return False
            else:
                self.log_result("Frontend URL Configuration", False, "REACT_APP_BACKEND_URL not found in frontend .env")
                return False
                
        except Exception as e:
            self.log_result("Frontend URL Configuration", False, f"Error reading frontend .env: {str(e)}")
            return False

    def run_comprehensive_test(self):
        """Run all Dover Dash leaderboard tests"""
        print("🎮 DOVER DASH LEADERBOARD API TESTING")
        print("=" * 50)
        print(f"Target URL: {self.base_url}")
        print(f"API URL: {self.api_url}")
        print(f"Test Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Test 1: Database Connection
        db_connected = self.test_database_connection()
        
        # Test 2: Leaderboard Table Access
        table_accessible = self.test_leaderboard_table_creation()
        
        # Test 3: Score Submission (main focus)
        score_submitted, submission_result = self.test_score_submission()
        
        # Test 4: Leaderboard Retrieval
        leaderboard_working, retrieval_result = self.test_leaderboard_retrieval()
        
        # Test 5: Parameter Testing
        self.test_leaderboard_with_parameters()
        
        # Test 6: Validation Testing
        self.test_score_validation()
        
        # Test 7: Frontend URL Configuration
        frontend_config_ok = self.test_frontend_url_configuration()
        
        # Summary
        print("\n" + "=" * 50)
        print("🔍 DOVER DASH LEADERBOARD TEST SUMMARY")
        print("=" * 50)
        
        print(f"Tests Run: {self.tests_run}")
        print(f"Tests Passed: {self.tests_passed}")
        print(f"Tests Failed: {self.tests_run - self.tests_passed}")
        print(f"Success Rate: {(self.tests_passed/self.tests_run)*100:.1f}%")
        
        print(f"\n📊 KEY FINDINGS:")
        print(f"   Database Connection: {'✅' if db_connected else '❌'}")
        print(f"   Leaderboard Table: {'✅' if table_accessible else '❌'}")
        print(f"   Score Submission: {'✅' if score_submitted else '❌'}")
        print(f"   Score Retrieval: {'✅' if leaderboard_working else '❌'}")
        
        if self.errors:
            print(f"\n🚨 ERRORS FOUND:")
            for i, error in enumerate(self.errors, 1):
                print(f"   {i}. {error}")
        
        # Diagnosis
        print(f"\n🔬 DIAGNOSIS:")
        if not db_connected:
            print("   🚨 CRITICAL: Database connection failure - this is likely the root cause")
            print("   💡 Check database configuration and connectivity")
        elif not table_accessible:
            print("   🚨 CRITICAL: Leaderboard table cannot be created/accessed")
            print("   💡 Check database permissions and SQL execution")
        elif not score_submitted:
            print("   🚨 CRITICAL: Score submission is failing")
            print("   💡 Check API endpoint implementation and data validation")
        elif not leaderboard_working:
            print("   🚨 CRITICAL: Leaderboard retrieval is failing")
            print("   💡 Check data persistence and query logic")
        else:
            print("   ✅ All core functionality appears to be working!")
            print("   💡 If users report issues, check frontend integration")
        
        return self.tests_passed == self.tests_run

def main():
    """Main test execution"""
    tester = DoverDashLeaderboardTester()
    
    success = tester.run_comprehensive_test()
    
    if success:
        print("\n🎉 All Dover Dash leaderboard tests passed!")
        return 0
    else:
        print(f"\n⚠️  Some Dover Dash leaderboard tests failed ({tester.tests_run - tester.tests_passed} failures)")
        return 1

if __name__ == "__main__":
    sys.exit(main())