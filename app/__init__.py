from flask import Flask, current_app
from .extensions import db, migrate, login_manager, upload_dir
from .views import main_blueprint
from .category_routes import category_blueprint
from itsdangerous import URLSafeSerializer
from .models import User
from flask_session import Session

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def create_app(config_name=None):
    app = Flask(__name__, template_folder='./templates', static_folder='./static')
    if config_name == 'testing':
        app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:1234@localhost:5432/Net4UInventory_test'
    else:
        app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:1234@localhost:5432/Net4UInventory'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = 'your-secret-key'
    app.config['SESSION_TYPE'] = 'filesystem'
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
