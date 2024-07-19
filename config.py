import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'supersecretkey'
    MAIL_SERVER = 'smtp.mail.yahoo.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USE_SSL = False
    MAIL_USERNAME = os.environ.get('workstation271s@yahoo.com')
    OAUTH2_FILE = os.environ.get('PERCORSO_FILE_OAUTH2')
    MAIL_DEFAULT_SENDER = os.environ.get('Inventory')
