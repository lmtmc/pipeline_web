from my_server import server, db, User

def check_and_fix_admin():
    """Check admin user status and fix if needed."""
    try:
        with server.app_context():
            # Check if admin user exists
            admin_user = User.query.filter_by(username='admin').first()
            
            if admin_user:
                print(f"Admin user found. Current admin status: {admin_user.is_admin}")
                if not admin_user.is_admin:
                    print("Fixing admin status...")
                    admin_user.is_admin = True
                    db.session.commit()
                    print("Admin status fixed!")
            else:
                print("Admin user not found. Creating admin user...")
                from db.users_mgt import add_user
                if add_user('admin', 'admin123', 'admin@example.com', is_admin=True):
                    print("Admin user created successfully!")
                else:
                    print("Failed to create admin user.")
            
            # Verify admin status
            admin_user = User.query.filter_by(username='admin').first()
            if admin_user and admin_user.is_admin:
                print("\nAdmin user is properly configured:")
                print(f"Username: {admin_user.username}")
                print(f"Email: {admin_user.email}")
                print(f"Admin status: {admin_user.is_admin}")
            else:
                print("\nAdmin user is not properly configured!")
                
    except Exception as e:
        print(f"Error: {e}")

if __name__ == '__main__':
    check_and_fix_admin() 