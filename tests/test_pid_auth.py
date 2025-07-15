#!/usr/bin/env python3
"""
Test script for PID-based authentication
"""

import sys
import os

# Add the parent directory to Python path to access db module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db.csv_auth import init_csv_auth, get_csv_auth_manager
from db.csv_users_mgt import authenticate_user, list_all_users

def test_pid_authentication():
    """Test the PID-based authentication system"""
    
    print("=== Testing PID-Based Authentication ===")
    
    # Initialize CSV authentication
    csv_file_path = 'lmt_archive_user_info_20250702.csv'
    auth_manager = init_csv_auth(csv_file_path)
    
    if not auth_manager:
        print("❌ Failed to initialize CSV authentication manager")
        return False
    
    print("✅ CSV authentication manager initialized")
    
    # Test loading existing PIDs
    users = auth_manager.get_all_users()
    print(f"✅ Loaded {len(users)} PID users from CSV")
    
    # List first 5 users to show the structure
    print("\n=== Sample PID Users ===")
    for i, user in enumerate(users[:5]):
        print(f"PID: {user.pid}, Email: {user.email}, API Token: {user.api_token[:8]}...")
    
    # Test authentication with existing PIDs
    print("\n=== Testing PID Authentication ===")
    
    # Test with first PID from the list
    if users:
        test_pid = users[0].pid
        test_password = "willqjqvyW7$"  # Password from CSV for 2018-S1-MU-31
        
        print(f"Testing authentication for PID: {test_pid}")
        authenticated_user = authenticate_user(test_pid, test_password)
        
        if authenticated_user:
            print(f"✅ PID authentication successful: {authenticated_user.pid}")
            print(f"   Email: {authenticated_user.email}")
            print(f"   API Token: {authenticated_user.api_token[:8]}...")
            print(f"   Expiration: {authenticated_user.expiration}")
        else:
            print("❌ PID authentication failed")
    
    # Test invalid PID
    print("\n=== Testing Invalid PID ===")
    invalid_user = authenticate_user("INVALID-PID", "wrong_password")
    if invalid_user:
        print("❌ Invalid PID authentication should have failed")
    else:
        print("✅ Invalid PID authentication correctly rejected")
    
    # Test invalid password
    print("\n=== Testing Invalid Password ===")
    if users:
        test_pid = users[0].pid
        invalid_auth = authenticate_user(test_pid, "wrong_password")
        if invalid_auth:
            print("❌ Invalid password authentication should have failed")
        else:
            print("✅ Invalid password authentication correctly rejected")
    
    # Show all available PIDs
    print(f"\n=== Available PIDs ({len(users)} total) ===")
    pids = [user.pid for user in users]
    pids.sort()
    
    # Group PIDs by year
    pid_groups = {}
    for pid in pids:
        year = pid.split('-')[0]
        if year not in pid_groups:
            pid_groups[year] = []
        pid_groups[year].append(pid)
    
    for year in sorted(pid_groups.keys()):
        print(f"\n{year} ({len(pid_groups[year])} PIDs):")
        for pid in pid_groups[year][:5]:  # Show first 5 of each year
            print(f"  - {pid}")
        if len(pid_groups[year]) > 5:
            print(f"  ... and {len(pid_groups[year]) - 5} more")
    
    print("\n=== PID Authentication Test Complete ===")
    return True

if __name__ == "__main__":
    test_pid_authentication() 