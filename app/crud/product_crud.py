# CRUD for Product
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from app.models import Product, Category
from app.extensions import db

# CRUD for Product

def create_product(name, unique_code, description, location_id, project_id, quantity, owner_id, category_ids):
    new_product = Product(name=name, unique_code=unique_code, description=description,
                          location_id=location_id, project_id=project_id, quantity=quantity, owner_id=owner_id)
    db.session.add(new_product)
    db.session.flush()  # Flush per ottenere l'id prima del commit se necessario
    for category_id in category_ids:
        new_product.categories.append(Category.query.get(category_id))
    db.session.commit()
    return new_product

def update_product(product_id, **kwargs):
    product = Product.query.get(product_id)
    if product:
        for key, value in kwargs.items():
            setattr(product, key, value)  # Aggiorna i campi in base ai kwargs forniti
        db.session.commit()
        return product
    return None

def delete_product(product_id):
    product = Product.query.get(product_id)
    if product:
        db.session.delete(product)
        db.session.commit()
        return True
    return False
