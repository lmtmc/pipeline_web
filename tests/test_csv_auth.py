#!/usr/bin/env python3
"""
Test script for CSV-based authentication
"""

import sys
import os

# Add the parent directory to Python path to access db module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db.csv_auth import init_csv_auth, get_csv_auth_manager
from db.csv_users_mgt import authenticate_user, add_user, list_all_users

def test_csv_authentication():
    """Test the CSV authentication system"""
    
    print("=== Testing CSV Authentication ===")
    
    # Initialize CSV authentication
    csv_file_path = 'lmt_archive_user_info_20250702.csv'
    auth_manager = init_csv_auth(csv_file_path)
    
    if not auth_manager:
        print("❌ Failed to initialize CSV authentication manager")
        return False
    
    print("✅ CSV authentication manager initialized")
    
    # Test loading existing users
    users = auth_manager.get_all_users()
    print(f"✅ Loaded {len(users)} users from CSV")
    
    # List all users
    print("\n=== Current Users ===")
    list_all_users()
    
    # Test authentication with existing users
    print("\n=== Testing Authentication ===")
    
    # Test with first PID from the list
    if users:
        test_pid = users[0].pid
        test_password = "willqjqvyW7$"  # Password from CSV for 2018-S1-MU-31
        
        print(f"Testing authentication for PID: {test_pid}")
        authenticated_user = authenticate_user(test_pid, test_password)
        
        if authenticated_user:
            print(f"✅ PID authentication successful: {authenticated_user.pid}")
            print(f"   API Token: {authenticated_user.api_token[:8]}...")
            print(f"   Expiration: {authenticated_user.expiration}")
        else:
            print("❌ PID authentication failed")
    else:
        print("❌ No users found to test authentication")
    
    # Test invalid credentials
    invalid_user = authenticate_user('invalid_user', 'wrong_password')
    if invalid_user:
        print("❌ Invalid authentication should have failed")
    else:
        print("✅ Invalid authentication correctly rejected")
    
    # Test adding a new user
    print("\n=== Testing User Addition ===")
    new_user_success = add_user(
        pid='test_pid_001',
        password='testpass123',
        api_token='test_token_123',
        expiration='2025-12-31'
    )
    
    if new_user_success:
        print("✅ New user added successfully")
        
        # Test authentication with new user
        new_user = authenticate_user('test_pid_001', 'testpass123')
        if new_user:
            print(f"✅ New user authentication successful: {new_user.pid}")
            print(f"   API Token: {new_user.api_token}")
            print(f"   Expiration: {new_user.expiration}")
        else:
            print("❌ New user authentication failed")
    else:
        print("❌ Failed to add new user")
    
    # List users again to show the new user
    print("\n=== Updated Users List ===")
    list_all_users()
    
    print("\n=== CSV Authentication Test Complete ===")
    return True

if __name__ == "__main__":
    test_csv_authentication() 