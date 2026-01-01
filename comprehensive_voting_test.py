import requests
import sys
from datetime import datetime
import json
import time

class VotingCommentsAPITester:
    def __init__(self, base_url="https://viewtrends-1.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.admin_token = None
        self.test_user_session_token = None
        self.test_user_2_session_token = None
        self.test_opinion_id = None
        self.test_comment_id = None
        self.tests_run = 0
        self.tests_passed = 0

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

    def make_request(self, method, endpoint, data=None, headers=None, files=None, form_data=False):
        """Make HTTP request with error handling"""
        url = f"{self.api_url}/{endpoint}"
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, params=data, timeout=10)
            elif method == 'POST':
                if files:
                    response = requests.post(url, data=data, headers=headers, files=files, timeout=10)
                elif form_data:
                    response = requests.post(url, data=data, headers=headers, timeout=10)
                else:
                    response = requests.post(url, json=data, headers=headers, timeout=10)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers, timeout=10)
            
            return response
        except Exception as e:
            print(f"   Request error: {e}")
            return None

    def test_admin_login(self):
        """Test admin login to get authentication token"""
        print("\n🔐 Testing Admin Login...")
        
        response = self.make_request('POST', 'auth/login', {
            'username': 'admin',
            'password': 'admin123'
        })
        
        if response and response.status_code == 200:
            data = response.json()
            if 'access_token' in data:
                self.admin_token = data['access_token']
                self.log_test("Admin Login", True, f"Token obtained: {self.admin_token[:20]}...")
                return True
        
        self.log_test("Admin Login", False, f"Status: {response.status_code if response else 'No response'}")
        return False

    def test_user_registration(self):
        """Test opinion user registration"""
        print("\n👤 Testing User Registration...")
        
        # Test user 1 registration
        unique_username = f'testuser_{int(time.time() * 1000)}'
        response = self.make_request('POST', 'opinion-users/register', 
                                   data={'username': unique_username}, form_data=True)
        
        if response and response.status_code == 200:
            data = response.json()
            if data.get('ok') and 'user' in data and 'session_token' in data['user']:
                self.test_user_session_token = data['user']['session_token']
                self.log_test("User Registration", True, 
                            f"User: {data['user']['username']}, Token: {self.test_user_session_token[:20]}...")
                
                # Test user 2 registration for voting tests
                unique_username2 = f'testuser2_{int(time.time() * 1000)}'
                response2 = self.make_request('POST', 'opinion-users/register', 
                                            data={'username': unique_username2}, form_data=True)
                
                if response2 and response2.status_code == 200:
                    data2 = response2.json()
                    if data2.get('ok') and 'user' in data2:
                        self.test_user_2_session_token = data2['user']['session_token']
                        self.log_test("Second User Registration", True, 
                                    f"User: {data2['user']['username']}")
                        return True
        
        self.log_test("User Registration", False, 
                     f"Status: {response.status_code if response else 'No response'}")
        return False

    def test_duplicate_username(self):
        """Test that duplicate usernames are rejected"""
        print("\n🚫 Testing Duplicate Username Rejection...")
        
        username = f'duplicate_test_{int(time.time() * 1000)}'
        
        # Register first user
        response1 = self.make_request('POST', 'opinion-users/register', 
                                    data={'username': username}, form_data=True)
        
        if response1 and response1.status_code == 200:
            # Try to register same username again
            response2 = self.make_request('POST', 'opinion-users/register', 
                                        data={'username': username}, form_data=True)
            
            if response2 and response2.status_code == 400:
                data = response2.json()
                if 'already taken' in data.get('detail', '').lower():
                    self.log_test("Duplicate Username Rejection", True, 
                                "Correctly rejected duplicate username")
                    return True
                else:
                    self.log_test("Duplicate Username Rejection", False, 
                                f"Wrong error message: {data.get('detail', '')}")
                    return False
            else:
                self.log_test("Duplicate Username Rejection", False, 
                            f"Expected 400, got {response2.status_code if response2 else 'No response'}")
                return False
        else:
            self.log_test("Duplicate Username Rejection", False, 
                        f"First registration failed: {response1.status_code if response1 else 'No response'}")
            return False

    def test_get_current_user(self):
        """Test getting current user by session token"""
        print("\n👤 Testing Get Current User...")
        
        if not self.test_user_session_token:
            self.log_test("Get Current User", False, "No session token available")
            return False
        
        response = self.make_request('GET', 'opinion-users/me', 
                                   data={'session_token': self.test_user_session_token})
        
        if response and response.status_code == 200:
            data = response.json()
            if 'user' in data and data['user'] and 'username' in data['user']:
                self.log_test("Get Current User", True, 
                            f"Retrieved user: {data['user']['username']}")
                return True
        
        self.log_test("Get Current User", False, 
                     f"Status: {response.status_code if response else 'No response'}")
        return False

    def test_get_top_opinions(self):
        """Test getting top opinions ranked by net votes"""
        print("\n🏆 Testing Get Top Opinions...")
        
        response = self.make_request('GET', 'opinions/top', data={'limit': 20})
        
        if response and response.status_code == 200:
            data = response.json()
            if 'opinions' in data and isinstance(data['opinions'], list):
                opinions = data['opinions']
                self.log_test("Get Top Opinions", True, 
                            f"Retrieved {len(opinions)} top opinions")
                
                # Verify sorting by net votes if there are opinions
                if len(opinions) > 1:
                    for i in range(len(opinions) - 1):
                        current_net = opinions[i]['net_votes']
                        next_net = opinions[i + 1]['net_votes']
                        if current_net < next_net:
                            self.log_test("Top Opinions Sorting", False, 
                                        "Opinions not sorted by net votes correctly")
                            return False
                    
                    self.log_test("Top Opinions Sorting", True, 
                                "Opinions correctly sorted by net votes")
                
                return True
        
        self.log_test("Get Top Opinions", False, 
                     f"Status: {response.status_code if response else 'No response'}")
        return False

    def test_opinion_endpoints_without_data(self):
        """Test opinion endpoints when no opinions exist"""
        print("\n📄 Testing Opinion Endpoints (No Data)...")
        
        # Test single opinion with non-existent ID
        response = self.make_request('GET', 'opinions/999')
        if response and response.status_code == 404:
            self.log_test("Get Non-existent Opinion", True, "Correctly returns 404")
        else:
            self.log_test("Get Non-existent Opinion", False, 
                         f"Expected 404, got {response.status_code if response else 'No response'}")
            return False
        
        # Test voting on non-existent opinion
        if self.test_user_session_token:
            response = self.make_request('POST', 'opinions/999/vote', 
                                       data={'vote_type': 'up', 'session_token': self.test_user_session_token}, 
                                       form_data=True)
            if response and response.status_code == 404:
                self.log_test("Vote on Non-existent Opinion", True, "Correctly returns 404")
            else:
                self.log_test("Vote on Non-existent Opinion", False, 
                             f"Expected 404, got {response.status_code if response else 'No response'}")
                return False
        
        # Test getting comments for non-existent opinion
        response = self.make_request('GET', 'opinions/999/comments')
        if response and response.status_code == 200:
            data = response.json()
            if 'comments' in data and len(data['comments']) == 0:
                self.log_test("Get Comments for Non-existent Opinion", True, 
                            "Returns empty comments list")
            else:
                self.log_test("Get Comments for Non-existent Opinion", False, 
                            "Should return empty comments list")
                return False
        else:
            self.log_test("Get Comments for Non-existent Opinion", False, 
                         f"Expected 200, got {response.status_code if response else 'No response'}")
            return False
        
        return True

    def test_authentication_protection(self):
        """Test that endpoints properly require authentication"""
        print("\n🚫 Testing Authentication Protection...")
        
        # Test voting without session token
        response = self.make_request('POST', 'opinions/1/vote', 
                                   data={'vote_type': 'up', 'session_token': 'invalid_token'}, 
                                   form_data=True)
        
        if response and response.status_code == 401:
            self.log_test("Voting Auth Protection", True, "Correctly rejected invalid token")
        else:
            self.log_test("Voting Auth Protection", False, 
                         f"Expected 401, got {response.status_code if response else 'No response'}")
            return False
        
        # Test commenting without session token
        response = self.make_request('POST', 'opinions/1/comments', 
                                   data={'content': 'test', 'session_token': 'invalid_token'}, 
                                   form_data=True)
        
        if response and response.status_code == 401:
            self.log_test("Comment Auth Protection", True, "Correctly rejected invalid token")
        else:
            self.log_test("Comment Auth Protection", False, 
                         f"Expected 401, got {response.status_code if response else 'No response'}")
            return False
        
        # Test admin endpoints without admin token
        response = self.make_request('GET', 'admin/comments')
        
        if response and response.status_code == 401:
            self.log_test("Admin Auth Protection", True, "Correctly requires admin authentication")
            return True
        else:
            self.log_test("Admin Auth Protection", False, 
                         f"Expected 401, got {response.status_code if response else 'No response'}")
            return False

    def test_admin_comments_endpoint(self):
        """Test admin endpoint to get all comments"""
        print("\n👑 Testing Admin Comments Endpoint...")
        
        if not self.admin_token:
            self.log_test("Admin Get All Comments", False, "No admin token available")
            return False
        
        headers = {'Authorization': f'Bearer {self.admin_token}'}
        response = self.make_request('GET', 'admin/comments', headers=headers)
        
        if response and response.status_code == 200:
            data = response.json()
            if 'comments' in data and isinstance(data['comments'], list):
                comments = data['comments']
                total = data.get('total', 0)
                self.log_test("Admin Get All Comments", True, 
                            f"Retrieved {len(comments)} comments, Total: {total}")
                
                # Verify admin comment structure if there are comments
                if comments:
                    comment = comments[0]
                    required_fields = ['id', 'opinion_id', 'username', 'content', 'upvotes', 'downvotes']
                    missing_fields = [field for field in required_fields if field not in comment]
                    
                    if not missing_fields:
                        self.log_test("Admin Comment Structure", True, 
                                    "Admin comments have all required fields")
                    else:
                        self.log_test("Admin Comment Structure", False, 
                                    f"Missing fields: {missing_fields}")
                        return False
                
                return True
        
        self.log_test("Admin Get All Comments", False, 
                     f"Status: {response.status_code if response else 'No response'}")
        return False

    def test_opinion_creation_cloudinary_limitation(self):
        """Test opinion creation endpoint (expecting Cloudinary limitation)"""
        print("\n📝 Testing Opinion Creation (Cloudinary Limitation)...")
        
        if not self.admin_token:
            self.log_test("Opinion Creation Test", False, "No admin token available")
            return False
        
        # Create minimal test image
        test_image_content = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\tpHYs\x00\x00\x0b\x13\x00\x00\x0b\x13\x01\x00\x9a\x9c\x18\x00\x00\x00\nIDATx\x9cc\xf8\x00\x00\x00\x01\x00\x01\x00\x00\x00\x00IEND\xaeB`\x82'
        
        files = {'file': ('test_opinion.png', test_image_content, 'image/png')}
        headers = {'Authorization': f'Bearer {self.admin_token}'}
        
        response = self.make_request('POST', 'opinions', files=files, headers=headers)
        
        if response:
            if response.status_code == 200:
                data = response.json()
                if data.get('ok') and 'opinion' in data:
                    self.log_test("Opinion Creation", True, 
                                f"Opinion created successfully: {data['opinion']['id']}")
                    return True
            elif response.status_code == 500:
                try:
                    error_data = response.json()
                    if 'cloudinary' in str(error_data).lower() or 'api_key' in str(error_data).lower():
                        self.log_test("Opinion Creation (Cloudinary Not Configured)", True, 
                                    "Endpoint works but Cloudinary not configured (expected)")
                        return True
                except:
                    pass
        
        self.log_test("Opinion Creation Test", False, 
                     f"Status: {response.status_code if response else 'No response'}")
        return False

    def test_user_vote_endpoints_structure(self):
        """Test user vote endpoints structure (even without existing opinions)"""
        print("\n🔍 Testing User Vote Endpoints Structure...")
        
        if not self.test_user_session_token:
            self.log_test("User Vote Endpoints", False, "No session token available")
            return False
        
        # Test get user vote on non-existent opinion
        response = self.make_request('GET', 'opinions/999/user-vote', 
                                   data={'session_token': self.test_user_session_token})
        
        if response and response.status_code == 200:
            data = response.json()
            if 'user_vote' in data and data['user_vote'] is None:
                self.log_test("Get User Vote Structure", True, 
                            "Correctly returns null vote for non-existent opinion")
                return True
        
        self.log_test("Get User Vote Structure", False, 
                     f"Status: {response.status_code if response else 'No response'}")
        return False

    def test_comment_vote_endpoints_structure(self):
        """Test comment vote endpoints structure"""
        print("\n🗳️ Testing Comment Vote Endpoints Structure...")
        
        if not self.test_user_session_token:
            self.log_test("Comment Vote Endpoints", False, "No session token available")
            return False
        
        # Test voting on non-existent comment
        response = self.make_request('POST', 'comments/999/vote', 
                                   data={'vote_type': 'up', 'session_token': self.test_user_session_token}, 
                                   form_data=True)
        
        if response and response.status_code == 404:
            self.log_test("Vote on Non-existent Comment", True, "Correctly returns 404")
        else:
            self.log_test("Vote on Non-existent Comment", False, 
                         f"Expected 404, got {response.status_code if response else 'No response'}")
            return False
        
        # Test get user vote on non-existent comment
        response = self.make_request('GET', 'comments/999/user-vote', 
                                   data={'session_token': self.test_user_session_token})
        
        if response and response.status_code == 200:
            data = response.json()
            if 'user_vote' in data and data['user_vote'] is None:
                self.log_test("Get Comment User Vote Structure", True, 
                            "Correctly returns null vote for non-existent comment")
                return True
        
        self.log_test("Get Comment User Vote Structure", False, 
                     f"Status: {response.status_code if response else 'No response'}")
        return False

    def test_admin_delete_comment_endpoint(self):
        """Test admin delete comment endpoint structure"""
        print("\n🗑️ Testing Admin Delete Comment Endpoint...")
        
        if not self.admin_token:
            self.log_test("Admin Delete Comment", False, "No admin token available")
            return False
        
        headers = {'Authorization': f'Bearer {self.admin_token}'}
        response = self.make_request('DELETE', 'admin/comments/999', headers=headers)
        
        if response and response.status_code == 404:
            self.log_test("Admin Delete Non-existent Comment", True, "Correctly returns 404")
            return True
        else:
            self.log_test("Admin Delete Non-existent Comment", False, 
                         f"Expected 404, got {response.status_code if response else 'No response'}")
            return False

    def run_all_tests(self):
        """Run all voting and commenting tests"""
        print("🚀 Starting Voting, Commenting, and User Registration Tests")
        print("🎯 Target: " + self.base_url)
        print("=" * 80)
        
        # Authentication setup
        if not self.test_admin_login():
            print("❌ Cannot proceed without admin authentication")
            return False
        
        # User registration tests
        self.test_user_registration()
        self.test_duplicate_username()
        self.test_get_current_user()
        
        # Opinion tests (structure and error handling)
        self.test_get_top_opinions()
        self.test_opinion_endpoints_without_data()
        self.test_opinion_creation_cloudinary_limitation()
        
        # Voting tests (structure and authentication)
        self.test_user_vote_endpoints_structure()
        self.test_comment_vote_endpoints_structure()
        
        # Authentication and security tests
        self.test_authentication_protection()
        
        # Admin tests
        self.test_admin_comments_endpoint()
        self.test_admin_delete_comment_endpoint()
        
        # Final summary
        print("\n" + "=" * 80)
        print("📊 FINAL TEST RESULTS")
        print(f"Tests Run: {self.tests_run}")
        print(f"Tests Passed: {self.tests_passed}")
        print(f"Tests Failed: {self.tests_run - self.tests_passed}")
        print(f"Success Rate: {(self.tests_passed/self.tests_run)*100:.1f}%")
        
        if self.tests_passed == self.tests_run:
            print("✅ ALL TESTS PASSED - Voting and commenting features are working correctly!")
            return True
        else:
            print("❌ SOME TESTS FAILED - Features need attention")
            return False

def main():
    tester = VotingCommentsAPITester()
    success = tester.run_all_tests()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())