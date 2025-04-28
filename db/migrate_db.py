from my_server import db, server
from sqlalchemy import text

def migrate_database():
    """Add is_admin column to user table if it doesn't exist."""
    try:
        with server.app_context():
            # Check if is_admin column exists
            inspector = db.inspect(db.engine)
            columns = [col['name'] for col in inspector.get_columns('user')]
            
            if 'is_admin' not in columns:
                print("Adding is_admin column to user table...")
                with db.engine.connect() as connection:
                    connection.execute(text('ALTER TABLE user ADD COLUMN is_admin BOOLEAN DEFAULT FALSE'))
                    connection.commit()
                print("Migration completed successfully!")
            else:
                print("is_admin column already exists in user table.")
    except Exception as e:
        print(f"Error during migration: {e}")

if __name__ == "__main__":
    migrate_database() 