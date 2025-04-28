import sys
import os

# Add the parent directory to the Python path
# sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from my_server import server, db, User, Job
from datetime import datetime
import re
import getpass

def validate_email(email):
    """Validate email format."""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_username(username):
    """Validate username format."""
    # Username should be at least 3 characters long and contain only letters, numbers, and -_
    pattern = r'^[a-zA-Z0-9_-]{3,}$'
    return re.match(pattern, username) is not None

def add_user(username, password, email, is_admin=False):
    """Add a new user to the database."""
    try:
        with server.app_context():
            if check_user(username):
                raise ValueError(f"User {username} already exists")
            
            # Validate email format
            if not validate_email(email):
                raise ValueError("Invalid email format")
            
            # Validate username format
            if not validate_username(username):
                raise ValueError("Invalid username format")
            
            # Validate password length
            if len(password) < 6:
                raise ValueError("Password must be at least 6 characters long")
            
            new_user = User(username=username, password=password, email=email, is_admin=is_admin)
            db.session.add(new_user)
            db.session.commit()
            return True
    except Exception as e:
        print(f"Error adding user: {e}")
        db.session.rollback()
        return False

def delete_user(username, admin_user=None):
    """Delete a user from the database."""
    try:
        with server.app_context():
            user_to_delete = User.query.filter_by(username=username).first()
            if not user_to_delete:
                print(f"User {username} not found.")
                return False
                
            # Only admin can delete other admin users
            if user_to_delete.is_admin and (not admin_user or not admin_user.is_admin):
                print("Error: Only administrators can delete admin users.")
                return False
                
            db.session.delete(user_to_delete)
            db.session.commit()
            return True
    except Exception as e:
        print(f"Error deleting user: {e}")
        db.session.rollback()
        return False

def check_user(username):
    """Check if a user exists in the database."""
    try:
        with server.app_context():
            return User.query.filter_by(username=username).first()
    except Exception as e:
        print(f"Error checking user: {e}")
        return None

def get_all_users():
    """Get all users from the database."""
    try:
        with server.app_context():
            return User.query.all()
    except Exception as e:
        print(f"Error getting users: {e}")
        return []

def modify_user(username, admin_user=None):
    """Modify user information (email and password)."""
    try:
        with server.app_context():
            user = User.query.filter_by(username=username).first()
            if not user:
                print(f"User {username} not found.")
                return False

            # Check if user has permission to modify
            if not admin_user and user.is_admin:
                print("Error: Only administrators can modify admin users.")
                return False

            print(f"\n=== Modifying User: {username} ===")
            print("Current email:", user.email)
            print("Admin status:", "Yes" if user.is_admin else "No")
            print("\nWhat would you like to modify?")
            print("1. Email")
            print("2. Password")
            print("3. Both")
            if admin_user and admin_user.is_admin:
                print("4. Admin Status")
                print("5. Cancel")
            else:
                print("4. Cancel")

            max_choice = 5 if admin_user and admin_user.is_admin else 4
            choice = input(f"\nEnter your choice (1-{max_choice}): ").strip()

            if choice in ['1', '3']:
                while True:
                    new_email = input("Enter new email address: ").strip()
                    if not validate_email(new_email):
                        print("Invalid email format. Please try again.")
                        continue
                    user.email = new_email
                    break

            if choice in ['2', '3']:
                while True:
                    if not admin_user:
                        current_password = getpass.getpass("Enter current password: ")
                        if not user.check_password(current_password):
                            print("Incorrect current password. Please try again.")
                            continue

                    new_password = getpass.getpass("Enter new password (minimum 6 characters): ")
                    if len(new_password) < 6:
                        print("Password too short. Please use at least 6 characters.")
                        continue

                    confirm_password = getpass.getpass("Confirm new password: ")
                    if new_password != confirm_password:
                        print("Passwords don't match. Please try again.")
                        continue

                    user.password = new_password
                    break

            if choice == '4' and admin_user and admin_user.is_admin:
                new_admin_status = input("Make user admin? (y/n): ").strip().lower() == 'y'
                user.is_admin = new_admin_status

            if choice in ['1', '2', '3'] or (choice == '4' and admin_user and admin_user.is_admin):
                db.session.commit()
                print(f"\nUser {username} information updated successfully!")
                return True
            else:
                print("\nModification cancelled.")
                return False

    except Exception as e:
        print(f"Error modifying user: {e}")
        db.session.rollback()
        return False

def register_user(admin_user=None):
    """Interactive user registration with validation."""
    print("\n=== User Registration ===")
    
    # Get and validate username
    while True:
        username = input("Enter username (minimum 3 characters, only letters, numbers, - and _): ").strip()
        if not validate_username(username):
            print("Invalid username format. Please try again.")
            continue
        if check_user(username):
            print("Username already exists. Please choose another.")
            continue
        break

    # Get and validate email
    while True:
        email = input("Enter email address: ").strip()
        if not validate_email(email):
            print("Invalid email format. Please try again.")
            continue
        break

    # Get and validate password
    while True:
        password = getpass.getpass("Enter password (minimum 6 characters): ")
        if len(password) < 6:
            print("Password too short. Please use at least 6 characters.")
            continue
        
        confirm_password = getpass.getpass("Confirm password: ")
        if password != confirm_password:
            print("Passwords don't match. Please try again.")
            continue
        break

    # Set admin status if registering user is admin
    is_admin = False
    if admin_user and admin_user.is_admin:
        is_admin = input("Make this user an admin? (y/n): ").strip().lower() == 'y'

    # Add user to database
    if add_user(username, password, email, is_admin):
        print(f"\nUser {username} successfully registered!")
        return True
    else:
        print("\nFailed to register user. Please try again.")
        return False

def list_users():
    """List all registered users."""
    users = get_all_users()
    if users:
        print("\n=== Registered Users ===")
        for user in users:
            print(f"Username: {user.username}, Email: {user.email}, Admin: {'Yes' if user.is_admin else 'No'}")
    else:
        print("\nNo users registered.")

def authenticate_user():
    """Authenticate user for admin access."""
    username = input("Enter username: ").strip()
    password = getpass.getpass("Enter password: ")
    
    user = check_user(username)
    if user and user.check_password(password):
        return user
    return None

def admin_menu(admin_user):
    """Admin menu with additional privileges."""
    while True:
        print(f"\n=== Admin Management System (Logged in as: {admin_user.username}) ===")
        print("1. Register new user")
        print("2. List all users")
        print("3. Modify user")
        print("4. Delete user")
        print("5. Create admin user")
        print("6. Logout")
        
        choice = input("\nEnter your choice (1-6): ").strip()
        
        if choice == '1':
            register_user(admin_user)
        elif choice == '2':
            list_users()
        elif choice == '3':
            username = input("Enter username to modify: ").strip()
            modify_user(username, admin_user)
        elif choice == '4':
            username = input("Enter username to delete: ").strip()
            if delete_user(username, admin_user):
                print(f"User {username} deleted successfully.")
            else:
                print(f"Failed to delete user {username}.")
        elif choice == '5':
            register_user(admin_user)
        elif choice == '6':
            print("Logging out...")
            return
        else:
            print("Invalid choice. Please try again.")

def user_menu(current_user):
    """Regular user menu with limited privileges."""
    while True:
        print(f"\n=== User Management System (Logged in as: {current_user.username}) ===")
        print("1. View my information")
        print("2. Modify my information")
        print("3. Logout")
        
        choice = input("\nEnter your choice (1-3): ").strip()
        
        if choice == '1':
            print(f"\nUsername: {current_user.username}")
            print(f"Email: {current_user.email}")
        elif choice == '2':
            modify_user(current_user.username)
        elif choice == '3':
            print("Logging out...")
            return
        else:
            print("Invalid choice. Please try again.")

def main():
    """Main menu for user management."""
    while True:
        print("\n=== User Management System ===")
        print("1. Login")
        print("2. Register new user")
        print("3. Exit")
        
        choice = input("\nEnter your choice (1-3): ").strip()
        
        if choice == '1':
            user = authenticate_user()
            if user:
                if user.is_admin:
                    admin_menu(user)
                else:
                    user_menu(user)
            else:
                print("Invalid username or password.")
        elif choice == '2':
            register_user()
        elif choice == '3':
            print("Goodbye!")
            sys.exit(0)
        else:
            print("Invalid choice. Please try again.")

def check_admin_status(username):
    """Check if a user is an admin and display their information."""
    try:
        with server.app_context():
            user = User.query.filter_by(username=username).first()
            if user:
                print("\n=== User Information ===")
                print(f"Username: {user.username}")
                print(f"Email: {user.email}")
                print(f"Admin Status: {'Yes' if user.is_admin else 'No'}")
                return user.is_admin
            else:
                print(f"User {username} not found.")
                return False
    except Exception as e:
        print(f"Error checking admin status: {e}")
        return False

def has_project_layout_access(user):
    """Check if a user has access to the project layout."""
    try:
        with server.app_context():
            if not user:
                return False
            return user.is_admin
    except Exception as e:
        print(f"Error checking project layout access: {e}")
        return False

def get_user_permissions(user):
    """Get all permissions for a user."""
    try:
        with server.app_context():
            if not user:
                return {}
            return {
                'is_admin': user.is_admin,
                'has_project_layout_access': has_project_layout_access(user)
            }
    except Exception as e:
        print(f"Error getting user permissions: {e}")
        return {}

def search_users(search_term):
    """Search users by username or email."""
    try:
        with server.app_context():
            # Search in both username and email fields
            users = User.query.filter(
                (User.username.ilike(f'%{search_term}%')) | 
                (User.email.ilike(f'%{search_term}%'))
            ).all()
            return users
    except Exception as e:
        print(f"Error searching users: {e}")
        return []

def user_exists(username):
    """Check if a user exists in the database."""
    try:
        with server.app_context():
            user = User.query.filter_by(username=username).first()
            return user is not None
    except Exception as e:
        print(f"Error checking user existence: {e}")
        return False

def list_all_users():
    """List all users in the database with their details."""
    try:
        with server.app_context():
            users = User.query.all()
            if not users:
                print("No users found in the database.")
                return
            
            print("\n=== All Users ===")
            print(f"{'Username':<20} {'Email':<30} {'Admin':<10}")
            print("-" * 60)
            for user in users:
                print(f"{user.username:<20} {user.email:<30} {'Yes' if user.is_admin else 'No'}")
    except Exception as e:
        print(f"Error listing users: {e}")

if __name__ == '__main__':
    # Create initial admin user if no users exist
    try:
        with server.app_context():
            if not get_all_users():
                add_user('admin', 'admin123', 'admin@example.com', is_admin=True)
                print("Initial admin user created:")
                print("Username: admin")
                print("Password: admin123")
    except Exception as e:
        print(f"Error creating initial admin user: {e}")
    
    # Check if username provided as argument
    if len(sys.argv) > 1:
        username = sys.argv[1]
        is_admin = check_admin_status(username)
        if is_admin:
            admin_menu(check_user(username))
        else:
            user_menu(check_user(username))
    else:
        main()

    # Example: Search for users
    search_term = input("Enter search term (username or email): ")
    found_users = search_users(search_term)
    if found_users:
        print("\nFound users:")
        for user in found_users:
            print(f"Username: {user.username}, Email: {user.email}, Admin: {'Yes' if user.is_admin else 'No'}")
    else:
        print("No users found matching the search term.")

    # Example: Check if a user exists
    username = input("\nEnter username to check: ")
    if user_exists(username):
        print(f"User '{username}' exists in the database.")
    else:
        print(f"User '{username}' does not exist in the database.")

    # List all users
    list_all_users()
