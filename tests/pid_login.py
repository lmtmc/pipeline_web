#!/usr/bin/env python3
"""
Simple PID-based login interface
"""

import sys
import os
import getpass

# Add the parent directory to Python path to access db module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db.csv_auth import init_csv_auth
from db.csv_users_mgt import authenticate_user, list_all_users

def pid_login_interface():
    """Simple PID-based login interface"""
    
    print("=== LMT Pipeline Web - PID Login ===")
    
    # Load configuration
    from config_loader import load_config
    config = load_config()
    
    # Initialize CSV authentication
    csv_path = config.get('authentication', {}).get('csv_path', '.')
    csv_file = config.get('authentication', {}).get('csv_file', 'lmt_archive_user_info_20250702.csv')
    csv_file_path = os.path.join(os.path.dirname(__file__), csv_path, csv_file)
    auth_manager = init_csv_auth(csv_file_path)
    
    if not auth_manager:
        print("❌ Failed to initialize authentication system")
        return None
    
    # Get all available PIDs
    users = auth_manager.get_all_users()
    if not users:
        print("❌ No PIDs found in the system")
        return None
    
    print(f"✅ System loaded with {len(users)} available PIDs")
    
    # Show available PIDs grouped by year
    print("\nAvailable PIDs by year:")
    pid_groups = {}
    for user in users:
        year = user.pid.split('-')[0]
        if year not in pid_groups:
            pid_groups[year] = []
        pid_groups[year].append(user.pid)
    
    for year in sorted(pid_groups.keys()):
        print(f"\n{year} ({len(pid_groups[year])} PIDs):")
        for pid in pid_groups[year][:3]:  # Show first 3 of each year
            print(f"  - {pid}")
        if len(pid_groups[year]) > 3:
            print(f"  ... and {len(pid_groups[year]) - 3} more")
    
    print("\n" + "="*50)
    
    # Login loop
    while True:
        try:
            # Get PID
            pid = input("Enter PID (or 'quit' to exit): ").strip()
            
            if pid.lower() == 'quit':
                print("Goodbye!")
                break
            
            if not pid:
                print("❌ PID cannot be empty")
                continue
            
            # Check if PID exists
            if not auth_manager.user_exists(pid):
                print(f"❌ PID '{pid}' not found in the system")
                continue
            
            # Get password
            password = getpass.getpass(f"Enter password for {pid}: ")
            
            if not password:
                print("❌ Password cannot be empty")
                continue
            
            # Authenticate
            user = authenticate_user(pid, password)
            
            if user:
                print(f"\n✅ Login successful!")
                print(f"Welcome, {user.pid}!")
                print(f"Email: {user.email}")
                print(f"API Token: {user.api_token[:8]}...")
                print(f"Expiration: {user.expiration}")
                
                # Here you would typically redirect to the main application
                print("\n🎉 You are now logged in and can access the pipeline web interface!")
                return user
            else:
                print("❌ Invalid password. Please try again.")
                
        except KeyboardInterrupt:
            print("\n\nGoodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")
    
    return None

if __name__ == "__main__":
    logged_in_user = pid_login_interface()
    if logged_in_user:
        print(f"\nUser {logged_in_user.pid} is ready to use the application.")
    else:
        print("\nNo user logged in.") 