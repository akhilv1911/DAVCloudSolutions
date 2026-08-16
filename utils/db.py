"""
DAV Cloud Solutions - Database Module (MongoDB / PyMongo)
Tech Stack: Python Flask, MongoDB, PyMongo
Founder: Akhil V
"""

import os
from datetime import datetime, timezone
from flask import current_app, g
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, OperationFailure

from utils.auth import hash_password


def get_db():
    """
    Establishes and returns a MongoDB database instance stored in Flask's application context (g).
    Reuses the connection if it already exists within the request context.
    """
    if 'db_client' not in g:
        mongo_uri = current_app.config.get('MONGO_URI', 'mongodb://localhost:27017/dav_cloud_db')
        
        try:
            # Initialize PyMongo Client with connection pooling
            g.db_client = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)
            
            # Ping database to confirm connection
            g.db_client.admin.command('ping')
            
            db_name = current_app.config.get('MONGO_DBNAME', 'dav_cloud_db')
            g.db = g.db_client[db_name]
            
        except ConnectionFailure as e:
            current_app.logger.error(f"MongoDB Connection Failure: {e}")
            raise RuntimeError("Failed to connect to MongoDB. Please check MONGO_URI in config.")

    return g.db


def init_db(app):
    """
    Initializes database indexes (e.g., unique constraints on email fields).
    Called during application startup in app.py.
    """
    with app.app_context():
        try:
            db = get_db()
            
            # Ensure unique email index on users collection
            db.users.create_index("email", unique=True)
            
            # Ensure index on projects by category and user_id for faster queries
            db.projects.create_index("category")
            db.projects.create_index("user_id")
            
            app.logger.info("MongoDB indexes verified successfully.")
        except (OperationFailure, RuntimeError) as e:
            app.logger.warning(f"Database initialization note: {e}")


def init_admin(app):
    """
    Ensures a permanent master admin account always exists in MongoDB.
    Runs on startup without duplicating or altering passwords unnecessarily.
    """
    with app.app_context():
        try:
            db = get_db()
            admin_email = os.environ.get('ADMIN_EMAIL', 'contactdavcloudsolutions@gmail.com').strip().lower()
            admin_password = os.environ.get('ADMIN_PASSWORD', 'AdminPassword@2026')
            founder_name = app.config.get('FOUNDER_NAME', 'V Akhil')

            # Check if the master admin user already exists
            admin_user = db.users.find_one({'email': admin_email})

            if not admin_user:
                master_admin = {
                    'full_name': founder_name,
                    'email': admin_email,
                    'password_hash': hash_password(admin_password),
                    'role': 'admin',
                    'phone': '+91 0000000000',
                    'institution': None,
                    'business_info': None,
                    'is_verified': True,
                    'is_permanent_admin': True,
                    'created_at': datetime.now(timezone.utc)
                }
                db.users.insert_one(master_admin)
                app.logger.info(f"Permanent Master Admin created: {admin_email}")
            else:
                # Guarantee the master account always retains the admin role and verified status
                db.users.update_one(
                    {'email': admin_email},
                    {'$set': {
                        'role': 'admin', 
                        'is_verified': True, 
                        'is_permanent_admin': True
                    }}
                )
                app.logger.info(f"Master Admin verified and active: {admin_email}")
        except Exception as e:
            app.logger.error(f"Failed to verify/initialize permanent admin: {e}")


def close_db_connection(e=None):
    """
    Closes the MongoDB connection at the end of the request.
    Registered in Flask teardown_appcontext.
    """
    db_client = g.pop('db_client', None)
    if db_client is not None:
        db_client.close()