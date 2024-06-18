from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import os

db = SQLAlchemy()
migrate = Migrate()

def create_app():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = "postgresql://postgres:1234@localhost:5432/Net4UInventory"
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = 'net4u'  # Cambia questa chiave in produzione
    db.init_app(app)
    migrate.init_app(app, db)
    from .views import main as main_blueprint
    app.register_blueprint(main_blueprint)
    print("app created")
    return app