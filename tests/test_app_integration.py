#!/usr/bin/env python3
"""
Test script to verify PID authentication works with the app
"""

import sys
import os

# Add the parent directory to Python path to access db module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db.csv_auth import init_csv_auth
from db.csv_users_mgt import authenticate_user

def test_app_integration():
    """Test that PID authentication works with the app"""
    
    print("=== Testing App Integration ===")
    
    # Load configuration
    from config_loader import load_config
    config = load_config()
    
    # Initialize CSV authentication
    csv_path = config.get('authentication', {}).get('csv_path', '.')
    csv_file = config.get('authentication', {}).get('csv_file', 'lmt_archive_user_info_20250702.csv')
    csv_file_path = os.path.join(os.path.dirname(__file__), csv_path, csv_file)
    auth_manager = init_csv_auth(csv_file_path)
    
    if not auth_manager:
        print("❌ Failed to initialize CSV authentication")
        return False
    
    print("✅ CSV authentication initialized")
    
    # Test with a real PID from your CSV
    test_pid = "2018-S1-MU-31"
    test_password = "willqjqvyW7$"
    
    print(f"\nTesting authentication for PID: {test_pid}")
    
    # Test authentication
    user = authenticate_user(test_pid, test_password)
    
    if user:
        print("✅ Authentication successful!")
        print(f"   PID: {user.pid}")
        print(f"   Username: {user.username}")
        print(f"   API Token: {user.api_token[:8]}...")
        print(f"   Expiration: {user.expiration}")
        print(f"   Is Admin: {user.is_admin}")
        
        # Test Flask-Login compatibility
        print(f"\n✅ Flask-Login compatibility:")
        print(f"   User ID: {user.get_id()}")
        print(f"   Is Authenticated: {user.is_authenticated}")
        
        return True
    else:
        print("❌ Authentication failed")
        return False

if __name__ == "__main__":
    success = test_app_integration()
    if success:
        print("\n🎉 PID authentication is ready for your app!")
        print("\nTo use in your app:")
        print("1. Users can log in with their PID and password")
        print("2. The system will automatically authenticate against the CSV")
        print("3. If CSV authentication fails, it falls back to database")
        print("4. All CSV users are regular users (not admin)")
    else:
        print("\n❌ There are issues with the authentication setup") 