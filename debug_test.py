import requests
import sys
from datetime import datetime
import json
import time

# Simple test to debug the issue
def test_single_endpoint():
    url = "https://viewtrends-1.preview.emergentagent.com/api/opinions/999"
    
    print(f"Testing URL: {url}")
    
    try:
        response = requests.get(url, timeout=30)
        print(f"Status Code: {response.status_code}")
        print(f"Response Text: {response.text}")
        print(f"Response Headers: {dict(response.headers)}")
        return response
    except Exception as e:
        print(f"Error: {e}")
        return None

def test_duplicate_username():
    url = "https://viewtrends-1.preview.emergentagent.com/api/opinion-users/register"
    username = f'duplicate_test_{int(time.time() * 1000)}'
    
    print(f"Testing duplicate username with: {username}")
    
    # First registration
    try:
        response1 = requests.post(url, data={'username': username}, timeout=30)
        print(f"First registration - Status: {response1.status_code}, Response: {response1.text}")
        
        if response1.status_code == 200:
            # Second registration (should fail)
            response2 = requests.post(url, data={'username': username}, timeout=30)
            print(f"Second registration - Status: {response2.status_code}, Response: {response2.text}")
            return response2
        else:
            print("First registration failed")
            return None
    except Exception as e:
        print(f"Error: {e}")
        return None

if __name__ == "__main__":
    print("=== Testing Single Endpoint ===")
    test_single_endpoint()
    
    print("\n=== Testing Duplicate Username ===")
    test_duplicate_username()