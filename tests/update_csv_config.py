#!/usr/bin/env python3
"""
Script to update CSV authentication configuration
"""

import yaml
import os

def update_csv_config(csv_file=None, csv_path=None):
    """Update the CSV configuration in config.yaml"""
    
    config_file = 'config.yaml'
    
    # Read current config
    with open(config_file, 'r') as f:
        config = yaml.safe_load(f)
    
    # Initialize authentication section if it doesn't exist
    if 'authentication' not in config:
        config['authentication'] = {}
    
    # Update values if provided
    if csv_file:
        config['authentication']['csv_file'] = csv_file
        print(f"Updated CSV file to: {csv_file}")
    
    if csv_path:
        config['authentication']['csv_path'] = csv_path
        print(f"Updated CSV path to: {csv_path}")
    
    # Write back to config file
    with open(config_file, 'w') as f:
        yaml.dump(config, f, default_flow_style=False, sort_keys=False)
    
    print(f"Configuration updated in {config_file}")
    
    # Show current configuration
    print("\nCurrent authentication configuration:")
    auth_config = config.get('authentication', {})
    print(f"  CSV File: {auth_config.get('csv_file', 'Not set')}")
    print(f"  CSV Path: {auth_config.get('csv_path', 'Not set')}")

def show_current_config():
    """Show the current CSV configuration"""
    
    config_file = 'config.yaml'
    
    if not os.path.exists(config_file):
        print(f"Config file {config_file} not found")
        return
    
    with open(config_file, 'r') as f:
        config = yaml.safe_load(f)
    
    auth_config = config.get('authentication', {})
    
    print("Current authentication configuration:")
    print(f"  CSV File: {auth_config.get('csv_file', 'Not set')}")
    print(f"  CSV Path: {auth_config.get('csv_path', 'Not set')}")
    
    # Check if file exists
    csv_path = auth_config.get('csv_path', '.')
    csv_file = auth_config.get('csv_file', 'lmt_archive_user_info_20250702.csv')
    full_path = os.path.join(csv_path, csv_file)
    
    if os.path.exists(full_path):
        print(f"  ✅ CSV file exists: {full_path}")
    else:
        print(f"  ❌ CSV file not found: {full_path}")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "show":
            show_current_config()
        elif command == "update":
            csv_file = sys.argv[2] if len(sys.argv) > 2 else None
            csv_path = sys.argv[3] if len(sys.argv) > 3 else None
            update_csv_config(csv_file, csv_path)
        else:
            print("Usage:")
            print("  python update_csv_config.py show")
            print("  python update_csv_config.py update [csv_file] [csv_path]")
    else:
        show_current_config()
        print("\nTo update configuration:")
        print("  python update_csv_config.py update new_file.csv new_path") 