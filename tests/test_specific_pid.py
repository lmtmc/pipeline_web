#!/usr/bin/env python3
"""
Test script to debug specific PID login issue
"""

import sys
import os

# Add the parent directory to Python path to access db module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db.csv_auth import init_csv_auth
from db.csv_users_mgt import authenticate_user

def test_specific_pid():
    """Test authentication for 2023-S1-US-17"""
    
    print("=== Testing PID: 2023-S1-US-17 ===")
    
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
    
    # Test PID
    test_pid = "2023-S1-US-17"
    test_password = "mjinhtaftJ2*"
    
    print(f"PID: {test_pid}")
    print(f"Password: {test_password}")
    
    # Check if PID exists
    if auth_manager.user_exists(test_pid):
        print("✅ PID exists in CSV")
        user = auth_manager.get_user(test_pid)
        print(f"   Raw password from CSV: {user.password_hash}")
    else:
        print("❌ PID not found in CSV")
        return False
    
    # Test authentication
    print(f"\nTesting authentication...")
    user = authenticate_user(test_pid, test_password)
    
    if user:
        print("✅ Authentication successful!")
        print(f"   PID: {user.pid}")
        print(f"   Username: {user.username}")
        print(f"   API Token: {user.api_token[:8]}...")
        print(f"   Expiration: {user.expiration}")
        return True
    else:
        print("❌ Authentication failed")
        
        # Try to debug the issue
        print("\nDebugging authentication failure:")
        user_obj = auth_manager.get_user(test_pid)
        if user_obj:
            print(f"   User object found: {user_obj}")
            print(f"   Password check result: {user_obj.check_password(test_password)}")
        
        return False

if __name__ == "__main__":
    test_specific_pid() 