import os

class Config:
    # Basic MySQL configuration (matches what works in MySQL Workbench)
    MYSQL_HOST = 'donateplus.mysql.database.azure.com'
    MYSQL_USER = 'ravalry'
    MYSQL_PASSWORD = 'god1mode$'
    MYSQL_DB = 'charity_pulse'
    
    # SSL configuration (simplified approach)
    MYSQL_SSL_MODE = 'REQUIRED'  # Enables SSL without certificate files
    
    UPLOAD_FOLDER = 'static/uploads'  # For donation images
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max upload size