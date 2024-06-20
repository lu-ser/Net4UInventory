# CRUD for Category
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from app.models import Category
from app.extensions import db
def create_category(name):
    new_category = Category(name=name)
    db.session.add(new_category)
    db.session.commit()
    return new_category

def update_category(category_id, new_name):
    category = Category.query.get(category_id)
    if category:
        category.name = new_name
        db.session.commit()
        return category
    return None

def delete_category(category_id):
    category = Category.query.get(category_id)
    if category:
        db.session.delete(category)
        db.session.commit()
        return True
    return False