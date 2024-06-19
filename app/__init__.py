from flask import Flask
from .extensions import db, migrate, login_manager
from .views import main_blueprint
from .models import User

def create_app():
    app = Flask(__name__, template_folder='./templates', static_folder='./static')
    app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:1234@localhost:5432/Net4UInventory'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = 'your-secret-key'  # Cambia questa chiave in produzione

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)

    login_manager.login_view = 'main.login'

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    app.register_blueprint(main_blueprint)

    from . import models  # Assicurati di importare i modelli dopo l'inizializzazione di db

    return app
