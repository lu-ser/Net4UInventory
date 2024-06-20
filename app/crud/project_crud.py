# CRUD per Project
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from app.models import Project
from app.extensions import db

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