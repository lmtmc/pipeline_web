import csv
import os
import pandas as pd
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
import logging

logger = logging.getLogger(__name__)

class CSVUser(UserMixin):
    """User class for CSV-based authentication"""
    
    def __init__(self, pid, password_hash, api_token="", expiration=""):
        self.id = pid  # Use PID as ID
        self.pid = pid  # Project ID
        self.username = pid  # PID is the username
        self.password_hash = password_hash
        self.api_token = api_token
        self.expiration = expiration
        self.is_admin = False  # All CSV users are regular users
    
    def check_password(self, password):
        """Check if the provided password matches the stored hash"""
        return check_password_hash(self.password_hash, password)
    
    def get_id(self):
        """Return the user ID (username)"""
        return self.username

class CSVAuthManager:
    """Manager for CSV-based user authentication"""
    
    def __init__(self, csv_file_path):
        self.csv_file_path = csv_file_path
        self.users = {}
        self.load_users()
    
    def load_users(self):
        """Load users from CSV file"""
        try:
            if not os.path.exists(self.csv_file_path):
                logger.warning(f"CSV file not found: {self.csv_file_path}")
                return
            
            df = pd.read_csv(self.csv_file_path)
            self.users = {}
            
            for _, row in df.iterrows():
                pid = row['username']  # PID is stored in username column
                password = row['password']
                api_token = row.get('api_token', '')
                expiration = row.get('expiration', '')
                
                # Hash the password if it's not already hashed
                if not password.startswith('pbkdf2:sha256:'):
                    password_hash = generate_password_hash(password, method='pbkdf2:sha256')
                else:
                    password_hash = password
                
                # Create user with PID-based authentication
                self.users[pid] = CSVUser(
                    pid=pid,
                    password_hash=password_hash,
                    api_token=api_token,
                    expiration=expiration
                )
            
            logger.info(f"Loaded {len(self.users)} PID users from CSV")
            
        except Exception as e:
            logger.error(f"Error loading users from CSV: {e}")
            self.users = {}
    
    def reload_users(self):
        """Reload users from CSV file"""
        self.load_users()
    
    def get_user(self, pid):
        """Get user by PID"""
        return self.users.get(pid)
    
    def get_user_by_pid(self, pid):
        """Get user by PID (alias for get_user)"""
        return self.get_user(pid)
    
    def get_user_by_pid(self, pid):
        """Get user by PID (alias for get_user)"""
        return self.get_user(pid)
    
    def authenticate_user(self, pid, password):
        """Authenticate user with PID and password"""
        user = self.get_user(pid)
        if user and user.check_password(password):
            return user
        return None
    
    def authenticate_by_pid(self, pid, password):
        """Authenticate by PID (alias for authenticate_user)"""
        return self.authenticate_user(pid, password)
    
    def add_user(self, pid, password, api_token="", expiration=""):
        """Add a new user to CSV"""
        try:
            # Check if user already exists
            if pid in self.users:
                raise ValueError(f"PID {pid} already exists")
            
            # Hash the password
            password_hash = generate_password_hash(password, method='pbkdf2:sha256')
            
            # Add to memory
            self.users[pid] = CSVUser(
                pid=pid,
                password_hash=password_hash,
                api_token=api_token,
                expiration=expiration
            )
            
            # Save to CSV
            self.save_to_csv()
            
            logger.info(f"Added PID: {pid}")
            return True
            
        except Exception as e:
            logger.error(f"Error adding PID: {e}")
            return False
    
    def update_user(self, username, **kwargs):
        """Update user information"""
        try:
            user = self.get_user(username)
            if not user:
                raise ValueError(f"User {username} not found")
            
            # Update fields
            for key, value in kwargs.items():
                if hasattr(user, key):
                    if key == 'password':
                        # Hash the password
                        setattr(user, 'password_hash', generate_password_hash(value, method='pbkdf2:sha256'))
                    else:
                        setattr(user, key, value)
            
            # Save to CSV
            self.save_to_csv()
            
            logger.info(f"Updated user: {username}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating user: {e}")
            return False
    
    def delete_user(self, username):
        """Delete user from CSV"""
        try:
            if username not in self.users:
                raise ValueError(f"User {username} not found")
            
            # Remove from memory
            del self.users[username]
            
            # Save to CSV
            self.save_to_csv()
            
            logger.info(f"Deleted user: {username}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting user: {e}")
            return False
    
    def save_to_csv(self):
        """Save users to CSV file"""
        try:
            data = []
            for user in self.users.values():
                data.append({
                    'username': user.pid,
                    'password': user.password_hash,
                    'api_token': user.api_token,
                    'expiration': user.expiration
                })
            
            df = pd.DataFrame(data)
            df.to_csv(self.csv_file_path, index=False)
            
            logger.info(f"Saved {len(data)} PID users to CSV")
            
        except Exception as e:
            logger.error(f"Error saving to CSV: {e}")
    
    def get_all_users(self):
        """Get all users"""
        return list(self.users.values())
    
    def user_exists(self, username):
        """Check if user exists"""
        return username in self.users
    
    def pid_exists(self, pid):
        """Check if PID exists"""
        return pid in self.users

# Global instance
csv_auth_manager = None

def init_csv_auth(csv_file_path):
    """Initialize CSV authentication manager"""
    global csv_auth_manager
    csv_auth_manager = CSVAuthManager(csv_file_path)
    return csv_auth_manager

def get_csv_auth_manager():
    """Get the CSV authentication manager instance"""
    return csv_auth_manager 