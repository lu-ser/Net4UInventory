from flask import Flask, current_app
from .extensions import db, migrate, login_manager, upload_dir
from .extensions import mail
from .views import main_blueprint
from .category_routes import category_blueprint
from itsdangerous import URLSafeSerializer
from .models import User
from flask_session import Session
from flask import Flask
from flask_mail import Mail
from config import Config

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def create_app(config_name=None):
    app = Flask(__name__, template_folder='./templates', static_folder='./static')
    if config_name == 'testing':
        app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:1234@localhost:5432/Net4UInventory_test2'
    else:
        app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:1234@localhost:5432/Net4UInventory_test2'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = 'your-secret-key'
    app.config['SESSION_TYPE'] = 'filesystem'
    app.config['SECURITY_PASSWORD_SALT']="net4u_salt"
    mail.init_app(app)
    Session(app)
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    login_manager.login_view = 'main.login'
    
    # Inizializza il serializer e aggiungilo come attributo dell'app per accesso globale
    app.auth_s = URLSafeSerializer(app.config['SECRET_KEY'])

    # Context processor per rendere auth_s disponibile nei template
    @app.context_processor
    def context_processor():
        return dict(auth_s=app.auth_s)

    app.register_blueprint(main_blueprint)
    app.register_blueprint(category_blueprint, url_prefix='/category')
    app.config['UPLOAD_FOLDER'] = upload_dir

    from . import models  # Importa i modelli dopo l'inizializzazione di db

    return app
