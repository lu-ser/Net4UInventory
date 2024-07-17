from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from .extensions import db

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    name = db.Column(db.String(255), nullable=False)
    surname = db.Column(db.String(255), nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(100), nullable=False)
    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)



class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    unique_code = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text, nullable=True)
    location_id = db.Column(db.Integer, db.ForeignKey('location.id'), nullable=False)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)  # Aggiunto per tracciare lo stato di attivazione

    location = db.relationship('Location', backref=db.backref('products', lazy=True))
    project = db.relationship('Project', backref=db.backref('products', lazy=True))
    categories = db.relationship('Category', secondary='product_category', backref='products')
    loans = db.relationship('Loan', backref='product')
    managers = db.relationship('User', secondary='product_manager', backref='manages_products')


class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)

class ProductCategory(db.Model):
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), primary_key=True)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), primary_key=True)

class Location(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    pavilion = db.Column(db.String(100), nullable=False)
    room = db.Column(db.String(100), nullable=True)
    cabinet = db.Column(db.String(100), nullable=True)

class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    funding_body = db.Column(db.String(255), nullable=True)

class ProductManager(db.Model):
    __tablename__ = 'product_manager'
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)
    # Relationships
    product = db.relationship('Product', backref=db.backref('manager_associations', cascade='all, delete-orphan'))
    user = db.relationship('User', backref=db.backref('managed_products', cascade='all, delete-orphan'))


class Loan(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    borrower_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    manager_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    start_date = db.Column(db.DateTime, default=datetime.utcnow)
    end_date = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String(100), default='pending')  # Example: pending, approved, denied
    quantity = db.Column(db.Integer, nullable=False)
    # Requests for loan extension
    extension_requested = db.Column(db.Boolean, default=False)
    new_end_date = db.Column(db.DateTime, nullable=True)
    borrower = db.relationship('User', foreign_keys=[borrower_id], backref='borrowed_loans')
    manager = db.relationship('User', foreign_keys=[manager_id], backref='managed_loans')
