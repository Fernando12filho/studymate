#!/usr/bin/env python3
"""
Database Connection Test Script
Run this to verify your database connection is working properly.
"""

import os
import sys

def test_database():
    print("=" * 60)
    print("DATABASE CONNECTION TEST")
    print("=" * 60)
    
    try:
        from app import create_app
        from app.extensions import db
        from app.models import User, Topic, Resource
        
        app = create_app()
        
        # Test 1: Configuration
        print("\n1. Configuration Check:")
        print(f"   DB URI: {app.config['SQLALCHEMY_DATABASE_URI']}")
        db_path = app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')
        print(f"   DB Path: {db_path}")
        print(f"   DB File Exists: {os.path.exists(db_path)}")
        if os.path.exists(db_path):
            print(f"   DB Readable: {os.access(db_path, os.R_OK)}")
            print(f"   DB Writable: {os.access(db_path, os.W_OK)}")
        
        # Test 2: Connection
        print("\n2. Connection Test:")
        with app.app_context():
            db.session.execute(db.text('SELECT 1'))
            print("   ✓ Connection successful!")
        
        # Test 3: Tables
        print("\n3. Table Check:")
        with app.app_context():
            user_count = db.session.execute(db.text('SELECT COUNT(*) FROM user_table')).scalar()
            topic_count = db.session.execute(db.text('SELECT COUNT(*) FROM topic')).scalar()
            resource_count = db.session.execute(db.text('SELECT COUNT(*) FROM resource')).scalar()
            
            print(f"   ✓ user_table: {user_count} rows")
            print(f"   ✓ topic: {topic_count} rows")
            print(f"   ✓ resource: {resource_count} rows")
        
        # Test 4: ORM
        print("\n4. ORM Test:")
        with app.app_context():
            users = User.query.all()
            print(f"   ✓ User.query.all() returned {len(users)} users")
            
        print("\n" + "=" * 60)
        print("✓ ALL TESTS PASSED - Database is working correctly!")
        print("=" * 60)
        return True
        
    except Exception as e:
        print(f"\n✗ ERROR: {type(e).__name__}: {e}")
        import traceback
        print("\nFull traceback:")
        traceback.print_exc()
        print("\n" + "=" * 60)
        print("✗ TESTS FAILED")
        print("=" * 60)
        return False

if __name__ == "__main__":
    success = test_database()
    sys.exit(0 if success else 1)
