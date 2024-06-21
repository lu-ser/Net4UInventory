# CRUD for Category_product
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from app.models import Category, Product
from app.extensions import db

def add_category_to_product(product_id, category_id):
    product = Product.query.get(product_id)
    category = Category.query.get(category_id)
    if product and category and category not in product.categories:
        product.categories.append(category)
        db.session.commit()
        return True
    return False

def remove_category_from_product(product_id, category_id):
    product = Product.query.get(product_id)
    category = Category.query.get(category_id)
    if product and category and category in product.categories:
        product.categories.remove(category)
        db.session.commit()
        return True
    return False