from .models import Category, Location, Project, Product, User, Loan
from .extensions import db
from werkzeug.security import generate_password_hash, check_password_hash

# CRUD for Category
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

# CRUD for Location
def create_location(pavilion, room, cabinet):
    new_location = Location(pavilion=pavilion, room=room, cabinet=cabinet)
    db.session.add(new_location)
    db.session.commit()
    return new_location

def update_location(location_id, pavilion=None, room=None, cabinet=None):
    location = Location.query.get(location_id)
    if location:
        location.pavilion = pavilion if pavilion is not None else location.pavilion
        location.room = room if room is not None else location.room
        location.cabinet = cabinet if cabinet is not None else location.cabinet
        db.session.commit()
        return location
    return None

def delete_location(location_id):
    location = Location.query.get(location_id)
    if location:
        db.session.delete(location)
        db.session.commit()
        return True
    return False

# CRUD for Project
def create_project(name, funding_body):
    new_project = Project(name=name, funding_body=funding_body)
    db.session.add(new_project)
    db.session.commit()
    return new_project

def update_project(project_id, name=None, funding_body=None):
    project = Project.query.get(project_id)
    if project:
        project.name = name if name is not None else project.name
        project.funding_body = funding_body if funding_body is not None else project.funding_body
        db.session.commit()
        return project
    return None

def delete_project(project_id):
    project = Project.query.get(project_id)
    if project:
        db.session.delete(project)
        db.session.commit()
        return True
    return False


# CRUD for User

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

# CRUD per LOAN

def create_loan(product_id, borrower_id, manager_id, start_date, end_date, status='pending', extension_requested=False, new_end_date=None):
    """Crea un nuovo prestito con specifiche complete."""
    new_loan = Loan(
        product_id=product_id,
        borrower_id=borrower_id,
        manager_id=manager_id,
        start_date=start_date,
        end_date=end_date,
        status=status,
        extension_requested=extension_requested,
        new_end_date=new_end_date
    )
    db.session.add(new_loan)
    db.session.commit()
    return new_loan

def update_loan(loan_id, **kwargs):
    """Aggiorna le proprietà di un prestito esistente."""
    loan = Loan.query.get(loan_id)
    if loan:
        for key, value in kwargs.items():
            setattr(loan, key, value)
        db.session.commit()
        return loan
    return None

def delete_loan(loan_id):
    """Elimina un prestito specificato dall'ID."""
    loan = Loan.query.get(loan_id)
    if loan:
        db.session.delete(loan)
        db.session.commit()
        return True
    return False
# CRUD per Managers

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