from flask import Blueprint, request, redirect, url_for, render_template, flash
from .crud.category_crud import create_category, update_category, delete_category
category_blueprint = Blueprint('category', __name__)
@category_blueprint.route('/add_category', methods=['POST'])
def add_category():
    name = request.form.get('name')
    if name:
        create_category(name)  # Assume this function adds the category successfully
        flash('Category created successfully!')
    else:
        flash('Category name is required.')
    return redirect(url_for('category.index'))

@category_blueprint.route('/update_category/<int:category_id>', methods=['POST'])
def update_existing_category(category_id):
    new_name = request.form.get('name')
    if new_name:
        update_category(category_id, new_name)
        flash('Category updated successfully!')
    return redirect(url_for('index'))

@category_blueprint.route('/delete_category/<int:category_id>')
def remove_category(category_id):
    if delete_category(category_id):
        flash('Category deleted successfully!')
    else:
        flash('Category not found!')
    return redirect(url_for('index'))

@category_blueprint.route('/index')
def index():
    return "Welcome to the Category Index!"