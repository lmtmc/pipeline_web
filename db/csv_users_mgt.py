import sys
import os
import re
import pandas as pd

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db.csv_auth import get_csv_auth_manager
import logging

logger = logging.getLogger(__name__)

def validate_pid(pid):
    """Validate PID format."""
    # PID should contain alphanumeric characters, hyphens, and underscores
    pattern = r'^[a-zA-Z0-9_-]+$'
    return re.match(pattern, pid) is not None

def validate_username(username):
    """Validate username format."""
    # Username should be at least 3 characters long and contain only letters, numbers, and -_
    pattern = r'^[a-zA-Z0-9_-]{3,}$'
    return re.match(pattern, username) is not None

def add_user(pid, password, api_token="", expiration=""):
    """Add a new PID to the CSV file."""
    try:
        auth_manager = get_csv_auth_manager()
        if not auth_manager:
            raise ValueError("CSV authentication manager not initialized")
        
        if auth_manager.user_exists(pid):
            raise ValueError(f"PID {pid} already exists")
        
        # Validate PID format
        if not validate_pid(pid):
            raise ValueError("Invalid PID format")
        
        # Validate password length
        if len(password) < 6:
            raise ValueError("Password must be at least 6 characters long")
        
        success = auth_manager.add_user(
            pid=pid,
            password=password,
            api_token=api_token,
            expiration=expiration
        )
        
        if success:
            logger.info(f"Successfully added PID: {pid}")
            return True
        else:
            logger.error(f"Failed to add PID: {pid}")
            return False
            
    except Exception as e:
        logger.error(f"Error adding PID: {e}")
        return False

def delete_user(pid, admin_user=None):
    """Delete a PID from the CSV file."""
    try:
        auth_manager = get_csv_auth_manager()
        if not auth_manager:
            raise ValueError("CSV authentication manager not initialized")
        
        user_to_delete = auth_manager.get_user(pid)
        if not user_to_delete:
            logger.warning(f"PID {pid} not found.")
            return False
        
        # Only admin can delete other admin users
        if user_to_delete.is_admin and (not admin_user or not admin_user.is_admin):
            logger.error("Error: Only administrators can delete admin users.")
            return False
        
        success = auth_manager.delete_user(pid)
        
        if success:
            logger.info(f"Successfully deleted PID: {pid}")
            return True
        else:
            logger.error(f"Failed to delete PID: {pid}")
            return False
            
    except Exception as e:
        logger.error(f"Error deleting PID: {e}")
        return False

def check_user(pid):
    """Check if a PID exists in the CSV file."""
    try:
        auth_manager = get_csv_auth_manager()
        if not auth_manager:
            return None
        
        return auth_manager.get_user(pid)
    except Exception as e:
        logger.error(f"Error checking PID: {e}")
        return None

def get_all_users():
    """Get all users from the CSV file."""
    try:
        auth_manager = get_csv_auth_manager()
        if not auth_manager:
            return []
        
        return auth_manager.get_all_users()
    except Exception as e:
        logger.error(f"Error getting users: {e}")
        return []

def modify_user(pid, admin_user=None, **kwargs):
    """Modify PID information."""
    try:
        auth_manager = get_csv_auth_manager()
        if not auth_manager:
            raise ValueError("CSV authentication manager not initialized")
        
        user = auth_manager.get_user(pid)
        if not user:
            logger.warning(f"PID {pid} not found.")
            return False
        
        # Check if user has permission to modify
        if not admin_user and user.is_admin:
            logger.error("Error: Only administrators can modify admin users.")
            return False
        
        # Validate password length if provided
        if 'password' in kwargs and len(kwargs['password']) < 6:
            raise ValueError("Password must be at least 6 characters long")
        
        success = auth_manager.update_user(pid, **kwargs)
        
        if success:
            logger.info(f"Successfully updated PID: {pid}")
            return True
        else:
            logger.error(f"Failed to update PID: {pid}")
            return False
            
    except Exception as e:
        logger.error(f"Error modifying PID: {e}")
        return False

def authenticate_user(pid, password):
    """Authenticate user with PID and password."""
    try:
        auth_manager = get_csv_auth_manager()
        if not auth_manager:
            return None
        
        return auth_manager.authenticate_user(pid, password)
    except Exception as e:
        logger.error(f"Error authenticating user: {e}")
        return None

def authenticate_by_pid(pid, password):
    """Authenticate by PID (alias for authenticate_user)."""
    return authenticate_user(pid, password)

def user_exists(pid):
    """Check if PID exists."""
    try:
        auth_manager = get_csv_auth_manager()
        if not auth_manager:
            return False
        
        return auth_manager.user_exists(pid)
    except Exception as e:
        logger.error(f"Error checking if PID exists: {e}")
        return False

def pid_exists(pid):
    """Check if PID exists (alias for user_exists)."""
    return user_exists(pid)

def pid_exists(pid):
    """Check if PID exists."""
    try:
        auth_manager = get_csv_auth_manager()
        if not auth_manager:
            return False
        
        return auth_manager.pid_exists(pid)
    except Exception as e:
        logger.error(f"Error checking if PID exists: {e}")
        return False

def list_all_users():
    """List all PIDs with their details."""
    try:
        users = get_all_users()
        if not users:
            print("No PIDs found.")
            return
        
        print("\n=== All PIDs ===")
        print(f"{'PID':<20} {'API Token':<15} {'Expiration':<20} {'Admin':<5}")
        print("-" * 65)
        
        for user in users:
            admin_status = "Yes" if user.is_admin else "No"
            api_token_short = user.api_token[:8] + "..." if user.api_token else "N/A"
            print(f"{user.pid:<20} {api_token_short:<15} {user.expiration:<20} {admin_status:<5}")
        
        print(f"\nTotal PIDs: {len(users)}")
        
    except Exception as e:
        logger.error(f"Error listing PIDs: {e}")

def search_users(search_term):
    """Search PIDs by PID."""
    try:
        users = get_all_users()
        if not users:
            return []
        
        search_term = search_term.lower()
        matching_users = []
        
        for user in users:
            if search_term in user.pid.lower():
                matching_users.append(user)
        
        return matching_users
        
    except Exception as e:
        logger.error(f"Error searching PIDs: {e}")
        return []

def reload_users():
    """Reload PIDs from CSV file."""
    try:
        auth_manager = get_csv_auth_manager()
        if not auth_manager:
            raise ValueError("CSV authentication manager not initialized")
        
        auth_manager.reload_users()
        logger.info("PIDs reloaded from CSV file")
        return True
        
    except Exception as e:
        logger.error(f"Error reloading PIDs: {e}")
        return False

def export_users_to_csv(output_file):
    """Export PIDs to a new CSV file."""
    try:
        users = get_all_users()
        if not users:
            logger.warning("No PIDs to export")
            return False
        
        data = []
        for user in users:
            data.append({
                'username': user.pid,
                'password': user.password_hash,
                'api_token': user.api_token,
                'expiration': user.expiration
            })
        
        df = pd.DataFrame(data)
        df.to_csv(output_file, index=False)
        
        logger.info(f"Exported {len(data)} PIDs to {output_file}")
        return True
        
    except Exception as e:
        logger.error(f"Error exporting PIDs: {e}")
        return False

def import_users_from_csv(input_file):
    """Import PIDs from a CSV file."""
    try:
        if not os.path.exists(input_file):
            raise ValueError(f"File not found: {input_file}")
        
        df = pd.read_csv(input_file)
        required_columns = ['username', 'password']
        
        # Check if required columns exist
        for col in required_columns:
            if col not in df.columns:
                raise ValueError(f"Required column '{col}' not found in CSV")
        
        auth_manager = get_csv_auth_manager()
        if not auth_manager:
            raise ValueError("CSV authentication manager not initialized")
        
        imported_count = 0
        for _, row in df.iterrows():
            pid = row['username']
            password = row['password']
            api_token = row.get('api_token', '')
            expiration = row.get('expiration', '')
            
            # Skip if PID already exists
            if auth_manager.user_exists(pid):
                logger.warning(f"PID {pid} already exists, skipping")
                continue
            
            # Add PID
            if auth_manager.add_user(pid, password, api_token, expiration):
                imported_count += 1
        
        logger.info(f"Imported {imported_count} PIDs from {input_file}")
        return imported_count
        
    except Exception as e:
        logger.error(f"Error importing PIDs: {e}")
        return 0 