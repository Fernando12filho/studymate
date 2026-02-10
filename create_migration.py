"""
Database migration script for adding ResourceChunk model and Resource summary fields.

This script sets up Flask-Migrate (Alembic) for the project and creates
a migration for the new RAG-related database models.

Usage:
    python create_migration.py
"""

from app import create_app
from app.extensions import db
from flask_migrate import Migrate, init, migrate as create_migration, upgrade
import os

def setup_migrations():
    """Initialize Flask-Migrate and create migration for RAG models"""
    
    app = create_app()
    
    # Initialize Flask-Migrate
    migrate = Migrate(app, db)
    
    with app.app_context():
        migrations_dir = os.path.join(os.path.dirname(__file__), 'migrations')
        
        # Check if migrations directory exists
        if not os.path.exists(migrations_dir):
            print("Initializing Flask-Migrate...")
            try:
                # Initialize migrations directory
                os.system('flask db init')
                print("✓ Migrations directory created")
            except Exception as e:
                print(f"Error initializing migrations: {e}")
                return False
        else:
            print("✓ Migrations directory already exists")
        
        # Create migration for new models
        print("\nCreating migration for RAG models...")
        try:
            os.system('flask db migrate -m "Add ResourceChunk model and Resource summary fields for RAG"')
            print("✓ Migration created successfully")
            
            # Show the migration file location
            versions_dir = os.path.join(migrations_dir, 'versions')
            if os.path.exists(versions_dir):
                migration_files = [f for f in os.listdir(versions_dir) if f.endswith('.py')]
                if migration_files:
                    latest_migration = sorted(migration_files)[-1]
                    print(f"\nMigration file: migrations/versions/{latest_migration}")
            
            return True
        except Exception as e:
            print(f"Error creating migration: {e}")
            return False

def apply_migrations():
    """Apply pending migrations to the database"""
    print("\nApplying migrations to database...")
    try:
        os.system('flask db upgrade')
        print("✓ Migrations applied successfully")
        return True
    except Exception as e:
        print(f"Error applying migrations: {e}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("Database Migration Setup for RAG Models")
    print("=" * 60)
    
    # Setup Flask-Migrate and create migration
    if setup_migrations():
        print("\n" + "=" * 60)
        print("Migration created successfully!")
        print("=" * 60)
        
        # Ask if user wants to apply migrations now
        print("\nTo apply the migration to your database, run:")
        print("  flask db upgrade")
        print("\nOr to apply it now, press Enter (or type 'n' to skip): ", end="")
        
        response = input().strip().lower()
        if response != 'n':
            apply_migrations()
    else:
        print("\n" + "=" * 60)
        print("Migration setup failed!")
        print("=" * 60)
        print("\nPlease ensure:")
        print("  1. Flask-Migrate is installed: pip install Flask-Migrate")
        print("  2. Your app configuration is correct")
        print("  3. Database connection is working")
