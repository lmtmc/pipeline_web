#!/usr/bin/env python3
"""
Test web app authentication for specific PID
"""

import sys
import os

# Add the parent directory to Python path to access db module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the app components
from my_server import csv_auth_manager
from db.csv_users_mgt import authenticate_user
from config_loader import load_config

def test_web_authentication():
    """Test that the web app can authenticate the specific PID"""
    
    print("=== Testing Web App Authentication ===")
    
    # Check if CSV auth manager is initialized
    if not csv_auth_manager:
        print("❌ CSV authentication manager not initialized in web app")
        return False
    
    print("✅ CSV authentication manager initialized in web app")
    
    # Load configuration to show CSV file info
    config = load_config()
    csv_file = config.get('authentication', {}).get('csv_file', 'lmt_archive_user_info_20250702.csv')
    print(f"Using CSV file: {csv_file}")
    
    # Test the specific PID
    test_pid = "2023-S1-US-17"
    test_password = "mjinhtaftJ2*"
    
    print(f"\nTesting PID: {test_pid}")
    
    # Check if PID exists
    if csv_auth_manager.user_exists(test_pid):
        print("✅ PID exists in CSV")
    else:
        print("❌ PID not found in CSV")
        return False
    
    # Test authentication
    user = authenticate_user(test_pid, test_password)
    
    if user:
        print("✅ Authentication successful!")
        print(f"   PID: {user.pid}")
        print(f"   Username: {user.username}")
        print(f"   Email: {user.email}")
        print(f"   API Token: {user.api_token[:8]}...")
        print(f"   Expiration: {user.expiration}")
        
        # Test Flask-Login compatibility
        print(f"\n✅ Flask-Login compatibility:")
        print(f"   User ID: {user.get_id()}")
        print(f"   Is Authenticated: {user.is_authenticated}")
        
        return True
    else:
        print("❌ Authentication failed")
        return False

if __name__ == "__main__":
    success = test_web_authentication()
    if success:
        print("\n🎉 Web app authentication is working!")
        print("You should now be able to log in with PID: 2023-S1-US-17")
    else:
        print("\n❌ Web app authentication has issues") 