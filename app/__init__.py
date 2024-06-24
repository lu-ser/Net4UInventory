from flask import Flask
from .extensions import db, migrate, login_manager, upload_dir
from .views import main_blueprint
from .category_routes import category_blueprint

from .models import User
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
    app.config['SECRET_KEY'] = 'net4u'  # Cambia questa chiave in produzione

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)

    login_manager.login_view = 'main.login'

    

    app.register_blueprint(main_blueprint)
    app.register_blueprint(category_blueprint, url_prefix='/category')
    app.config['UPLOAD_FOLDER'] = upload_dir
    from . import models  # Assicurati di importare i modelli dopo l'inizializzazione di db

    return app
