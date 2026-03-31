import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-secret-key-change-me-123'
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://root:@localhost/medical_stock'
    SQLALCHEMY_TRACK_MODIFICATIONS = False