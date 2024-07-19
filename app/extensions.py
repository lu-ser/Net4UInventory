from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from itsdangerous import URLSafeSerializer
key_dangerous = 'net4u'  # Cambia questa chiave in produzione
from flask_mail import Mail

db = SQLAlchemy()
upload_dir = "./upload"
migrate = Migrate()
login_manager = LoginManager()
auth_s = URLSafeSerializer(key_dangerous)
mail  = Mail()
