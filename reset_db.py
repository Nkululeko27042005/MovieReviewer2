#!/usr/bin/env python
"""Reset the database by dropping all tables and recreating them."""
import os
import sys

# Set up the app context first
os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def reset_database():
    """Drop all tables and recreate them from the models."""
    from app import create_app, db
    import app.models  # This imports all models and registers them
    
    app = create_app(os.environ.get('FLASK_CONFIG', 'default'))
    
    with app.app_context():
        print("Dropping all tables...")
        try:
            db.drop_all()
            print("✓ Tables dropped")
        except Exception as e:
            print(f"Note: {e}")
        
        print("Creating all tables...")
        db.create_all()
        print("✓ Tables created")
        print("✓ Database reset complete!")

if __name__ == '__main__':
    reset_database()
