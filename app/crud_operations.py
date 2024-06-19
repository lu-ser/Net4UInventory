from .models import Category, Location, Project
from .extensions import db

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
