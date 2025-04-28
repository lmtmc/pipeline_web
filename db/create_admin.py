from db.users_mgt import add_user
from my_server import server

def create_admin_user():
    """Create a new admin user with proper validation."""
    username = input("Enter admin username: ")
    password = input("Enter admin password: ")
    email = input("Enter admin email: ")
    
    with server.app_context():
        if add_user(username, password, email, is_admin=True):
            print(f"Admin user '{username}' created successfully!")
        else:
            print("Failed to create admin user.")

if __name__ == "__main__":
    create_admin_user() 