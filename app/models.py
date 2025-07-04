from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from .extensions import db


wishlist_association = db.Table('user_wishlist',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('product_id', db.Integer, db.ForeignKey('product.id'), primary_key=True)
)

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    name = db.Column(db.String(255), nullable=False)
    surname = db.Column(db.String(255), nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(100), nullable=False)
    profile_image = db.Column(db.String(255), nullable=True)
    wishlist = db.relationship('Product', secondary=wishlist_association, backref='wishlisted_by')

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
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    
    image_path = db.Column(db.String(255), nullable=True)

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
    has_comment = db.Column(db.Boolean, nullable=False, default=False, server_default='false')
    

class ReminderNotification(db.Model):
    """Traccia le notifiche di promemoria inviate per evitare duplicati"""
    id = db.Column(db.Integer, primary_key=True)
    loan_id = db.Column(db.Integer, db.ForeignKey('loan.id'), nullable=False)
    reminder_type = db.Column(db.String(50), nullable=False)  # 'week_before', 'day_before', 'day_of'
    sent_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    recipient_email = db.Column(db.String(255), nullable=False)
    
    # Relationships
    loan = db.relationship('Loan', backref=db.backref('reminder_notifications', cascade='all, delete-orphan'))
    
    # Indice composto per evitare notifiche duplicate
    __table_args__ = (
        db.UniqueConstraint('loan_id', 'reminder_type', name='unique_loan_reminder'),
    )


class Comment(db.Model):
    """Modello per i commenti sui prestiti al momento della restituzione"""
    id = db.Column(db.Integer, primary_key=True)
    loan_id = db.Column(db.Integer, db.ForeignKey('loan.id'), nullable=False)
    borrower_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    
    # Contenuto del commento
    comment_text = db.Column(db.Text, nullable=False)
    
    # Valutazione opzionale (1-5 stelle)
    rating = db.Column(db.Integer, nullable=True)  # Range 1-5
    
    # Timestamp
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # Flag per indicare se è stato visto dal manager
    seen_by_manager = db.Column(db.Boolean, default=False, nullable=False)
    
    # Relationships
    loan = db.relationship('Loan', backref=db.backref('comments', cascade='all, delete-orphan'))
    borrower = db.relationship('User', foreign_keys=[borrower_id], backref='comments_made')
    product = db.relationship('Product', backref='comments')
    
    def __repr__(self):
        return f'<Comment {self.id} for Loan {self.loan_id}>'