# CRUD for User
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from app.models import User
from app.extensions import db
from werkzeug.security import generate_password_hash, check_password_hash

def create_user(email, password, role):
    new_user = User(email=email, password=password, role=role)
    db.session.add(new_user)
    db.session.commit()
    return new_user

def update_user(user_id, email=None, password=None, role=None):
    user = User.query.get(user_id)
    if user:
        if email:
            user.email = email
        if password:
            user.password = password  # Il setter aggiornerà il hash della password
        if role:
            user.role = role
        db.session.commit()
        return user
    return None

def delete_user(user_id):
    user = User.query.get(user_id)
    if user:
        db.session.delete(user)
        db.session.commit()
        return True
    return False