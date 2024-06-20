# CRUD per Managers
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from app.models import Product, User
from app.extensions import db
def add_manager_to_product(product_id, user_id):
    product = Product.query.get(product_id)
    manager = User.query.get(user_id)
    if product and manager:
        product.managers.append(manager)
        db.session.commit()
    return product

def remove_manager_from_product(product_id, user_id):
    product = Product.query.get(product_id)
    manager = User.query.get(user_id)
    if product and manager:
        product.managers.remove(manager)
        db.session.commit()
    return product