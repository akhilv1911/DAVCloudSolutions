"""
DAV Cloud Solutions - Configuration Module
Tech Stack: Python Flask, PyMongo, Environment Variables
Founder: Akhil V
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Config:
    """Base Configuration Class"""
    
    # Secret Key for Session Signing & CSRF Protection
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dav-cloud-solutions-secret-key-2026-akhil-v')
    SECURITY_PASSWORD_SALT = os.environ.get('SECURITY_PASSWORD_SALT', 'dav-cloud-security-salt-2026')

    # MongoDB Configuration
    MONGO_URI = os.environ.get('MONGO_URI', 'mongodb://localhost:27017/dav_cloud_db')
    MONGO_DBNAME = os.environ.get('MONGO_DBNAME', 'dav_cloud_db')

    # SMTP Mailer Configuration
    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', 587))
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'True').lower() in ['true', 'on', '1']
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME', 'contactdavcloudsolutions@gmail.com')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD', '')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER', 'contactdavcloudsolutions@gmail.com')

    # Application Metadata
    APP_NAME = "DAV Cloud Solutions"
    FOUNDER_NAME = "Akhil V"


class DevelopmentConfig(Config):
    """Development Environment Configuration"""
    DEBUG = True
    TESTING = False


class ProductionConfig(Config):
    """Production Environment Configuration"""
    DEBUG = False
    TESTING = False
    # Enforce strict secret key requirement in production
    SECRET_KEY = os.environ.get('SECRET_KEY')


# Configuration Dictionary Mapping
config_by_name = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}