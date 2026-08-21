"""
DAV Cloud Solutions - Database Module (MongoDB / PyMongo)
Tech Stack: Python Flask, MongoDB, PyMongo
File: utils/db.py
"""

import os
from datetime import datetime, timezone
from typing import Optional
from flask import current_app, g, Flask
from pymongo import MongoClient
from pymongo.database import Database
from pymongo.errors import ConnectionFailure, OperationFailure

from utils.auth import hash_password

# Global connection client pool for the process
_mongo_client: Optional[MongoClient] = None


def get_mongo_client() -> MongoClient:
    """
    Returns or initializes the global singleton MongoClient.
    Thread-safe connection pool managed directly by PyMongo.
    """
    global _mongo_client
    if _mongo_client is None:
        mongo_uri = current_app.config.get('MONGO_URI', 'mongodb://localhost:27017/dav_cloud_db')
        try:
            _mongo_client = MongoClient(
                mongo_uri,
                serverSelectionTimeoutMS=5000,
                maxPoolSize=50,
                minPoolSize=10
            )
            # Verify connectivity
            _mongo_client.admin.command('ping')
        except ConnectionFailure as e:
            current_app.logger.error(f"MongoDB Connection Failure: {e}")
            raise RuntimeError("Failed to connect to MongoDB. Check MONGO_URI in environment.")

    return _mongo_client


def get_db() -> Database:
    """
    Establishes and returns a MongoDB database instance stored in Flask's application context (g).
    """
    if 'db' not in g:
        client = get_mongo_client()
        db_name = current_app.config.get('MONGO_DBNAME', 'dav_cloud_db')
        g.db = client[db_name]

    return g.db


def init_db(app: Flask):
    """
    Initializes database indexes and runs initial collection integrity checks.
    """
    with app.app_context():
        try:
            db = get_db()
            
            # Unique Constraints & Fast Query Indexes
            db.users.create_index("email", unique=True)
            db.users.create_index("role")
            
            db.projects.create_index("category")
            db.projects.create_index("title")
            db.projects.create_index("user_id")
            
            db.inquiries.create_index("email")
            db.inquiries.create_index("created_at")
            
            db.reviews.create_index("rating")
            db.reviews.create_index("created_at")
            
            app.logger.info("MongoDB indexes verified successfully.")
            
            # Seed Default Curated Projects if collection is empty
            seed_curated_projects(db, app)
            
        except (OperationFailure, RuntimeError) as e:
            app.logger.warning(f"Database initialization note: {e}")


def init_admin(app: Flask):
    """
    Ensures a permanent master admin account always exists in MongoDB.
    """
    with app.app_context():
        try:
            db = get_db()
            admin_email = os.environ.get('ADMIN_EMAIL', 'contactdavcloudsolutions@gmail.com').strip().lower()
            admin_password = os.environ.get('ADMIN_PASSWORD', 'AdminPassword@2026')
            founder_name = app.config.get('FOUNDER_NAME', 'V Akhil')

            admin_user = db.users.find_one({'email': admin_email})

            if not admin_user:
                master_admin = {
                    'full_name': founder_name,
                    'email': admin_email,
                    'password_hash': hash_password(admin_password),
                    'role': 'admin',
                    'phone': '+91 9948685064',
                    'institution': None,
                    'business_info': None,
                    'is_verified': True,
                    'is_permanent_admin': True,
                    'created_at': datetime.now(timezone.utc)
                }
                db.users.insert_one(master_admin)
                app.logger.info(f"Permanent Master Admin created: {admin_email}")
            else:
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


def seed_curated_projects(db: Database, app: Flask):
    """
    Seeds initial reference records if the projects collection is empty.
    """
    try:
        if db.projects.count_documents({}) == 0:
            curated_defaults = [
                {
                    "title": "AgriVision: Plant Disease Detection & Cure Recommender",
                    "category": "AI & Machine Learning",
                    "description": "Real-time crop leaf disease segmentation using YOLOv8 with automated chemical and organic cure recommendations.",
                    "tech_stack": ["Python", "YOLOv8", "OpenCV", "Flask", "Cloud DB"],
                    "delivery_days": "5–7 Days",
                    "status": "Delivered",
                    "created_at": datetime.now(timezone.utc)
                },
                {
                    "title": "SLMS Pro: Multi-Tier Student Leave Management System",
                    "category": "Full-Stack Web & SaaS",
                    "description": "Enterprise workflow portal for student leave applications, automated warden/faculty approvals, and digital pass issuance.",
                    "tech_stack": ["Python", "Flask", "MongoDB Atlas", "RBAC Auth"],
                    "delivery_days": "4–5 Days",
                    "status": "Delivered",
                    "created_at": datetime.now(timezone.utc)
                },
                {
                    "title": "FinPredict: High-Cap Stock Forecasting & Volatility EDA",
                    "category": "Data Science & EDA",
                    "description": "Comprehensive statistical analysis and machine learning pipeline mapping historical market trends and risk metrics.",
                    "tech_stack": ["Python", "Pandas", "Statsmodels", "Plotly Dashboards"],
                    "delivery_days": "4–6 Days",
                    "status": "Delivered",
                    "created_at": datetime.now(timezone.utc)
                },
                {
                    "title": "SecureTrace: Digital Vehicle RC, Insurance & Police Verification",
                    "category": "Cloud Infrastructure",
                    "description": "Decentralized document verification system enabling law enforcement to audit vehicle licenses and insurance in seconds.",
                    "tech_stack": ["Python Backend", "QR Authentication", "Cloud DB"],
                    "delivery_days": "5–7 Days",
                    "status": "Delivered",
                    "created_at": datetime.now(timezone.utc)
                }
            ]
            db.projects.insert_many(curated_defaults)
            app.logger.info("Successfully seeded default reference projects.")
    except Exception as e:
        app.logger.warning(f"Project seeder check note: {e}")


def close_db_connection(e=None):
    """
    Cleans up context variables at the end of each request context.
    """
    g.pop('db', None)