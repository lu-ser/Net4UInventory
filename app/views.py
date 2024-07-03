from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, current_app
from flask_login import login_user, logout_user, current_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os
from .forms import LoginForm, RegistrationForm
from .models import User, Product, Category, Location, Project, ProductManager
from .extensions import db, upload_dir
import csv


main_blueprint = Blueprint('main', __name__)

@main_blueprint.route('/')
@login_required
def index():
    return render_template('backend/index.html')

@main_blueprint.route('/logout')
@login_required  # Assicurati che solo gli utenti loggati possano accedere a questa route
def logout():
    logout_user()
    return redirect(url_for('main.login'))  # Reindirizza l'utente alla pagina di login dopo il logout

@main_blueprint.route('/addUser', methods=['POST'])
def register_user():
    name = request.form.get('name')
    surname = request.form.get('surname')
    email = request.form.get('email')
    password = request.form.get('password')
    role = request.form.get('role')
    # Verifica che il ruolo sia uno di quelli permessi
    allowed_roles = {'Professor', 'RTD', 'Researcher', 'PhDStudent', 'Scholar'}
    if role not in allowed_roles:
        flash('Invalid role selected.')
        return redirect(url_for('main.register_page'))  # Assicurati di avere una route e una funzione per 'register_page'
    # Controlla che l'email non sia già utilizzata
    if User.query.filter_by(email=email).first() is not None:
        flash('Email already used.')
        return redirect(url_for('main.register_page'))
    # Crea un nuovo utente
    hashed_password = generate_password_hash(password)
    new_user = User(name=name, surname=surname, email=email, password_hash=hashed_password, role=role)
    db.session.add(new_user)
    db.session.commit()
    flash('User successfully registered.')
    return redirect(url_for('main.login'))



@main_blueprint.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:  # Controlla se l'utente è già loggato
        return redirect(url_for('main.index'))  # Redirigi alla dashboard se già loggato
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            return redirect(url_for('main.index'))  # Redirigi all'area protetta dopo il login
        else:
            flash('Invalid email or password.')
            return redirect(url_for('main.login'))

    return render_template('backend/auth-sign-in.html')

@main_blueprint.route('/register')
def show_register_page():
    return render_template('backend/register.html')


@main_blueprint.route('/add_product', methods=['POST', 'GET'])
@login_required
def add_product():
    if request.method == 'POST':
        name = request.form['name']
        unique_code = request.form['unique_code']
        description = request.form.get('description', '')
        location_id = request.form['location_id']
        project_id = request.form['project_id']
        category_ids = request.form.getlist('category_ids')
        
        if not category_ids:
            flash('You must select at least one category.')
            return redirect(url_for('add_product_page'))
        
        # Verifica l'esistenza delle categorie
        valid_categories = Category.query.filter(Category.id.in_(category_ids)).count()
        if valid_categories != len(category_ids):
            flash('One or more selected categories are invalid.')
            return redirect(url_for('add_product_page'))
        categories = Category.query.filter(Category.id.in_(category_ids)).all()
        quantity = int(request.form['quantity'])
        location = Location.query.get(location_id)
        project = Project.query.get(project_id)
        owner_id = current_user.id
        product = Product(
            name=name,
            unique_code=unique_code,
            description=description,
            location_id=location.id,
            project_id=project.id,
            quantity=quantity,
            owner_id=owner_id,
            categories=categories
        )
        
        db.session.add(product)
        db.session.commit()
        # Aggiungi il proprietario come manager
        product_manager = ProductManager(product_id=product.id, user_id=owner_id)
        db.session.add(product_manager)
        db.session.commit()

        flash('Product added successfully!', 'success')
        return redirect(url_for('main.add_product'))

    categories = Category.query.all()
    projects = Project.query.all()
    locations = Location.query.all()
    return render_template('backend/page-add-product.html', categories=categories, locations=locations, projects=projects)

@main_blueprint.route('/upload_csv', methods=['POST'])
@login_required
def upload_csv():
    if 'file' not in request.files:
        flash('No file part')
        return redirect(request.url)
    file = request.files['file']
    if file.filename == '':
        flash('No selected file')
        return redirect(request.url)
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file_path = os.path.join(upload_dir, filename)
        file.save(file_path)

        with open(file_path, mode='r') as csv_file:
            csv_reader = csv.DictReader(csv_file)
            for row in csv_reader:
                # Assuming that the CSV has columns that exactly match your product model's required fields
                product = Product(
                    name=row['name'],
                    unique_code=row['unique_code'],
                    description=row['description'],
                    category_id=int(row['category_id']),
                    quantity=int(row['quantity'])
                )
                db.session.add(product)
            db.session.commit()

        flash('Products uploaded successfully!', 'success')
        return redirect(url_for('main.page_list_product'))
    return render_template('backend/upload_csv.html')

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ['csv']


@main_blueprint.route('/add_category', methods=['POST'])
@login_required
def add_category():
    name = request.form['name']
    new_category = Category(name=name)
    db.session.add(new_category)
    try:
        db.session.commit()
        return jsonify({
            'status': 'success',
            'message': 'Category added successfully!',
            'entity': {'id': new_category.id, 'name': new_category.name}
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'status': 'error',
            'message': 'Error adding category',
            'error': str(e)
        }), 400


@main_blueprint.route('/add_location', methods=['POST'])
@login_required
def add_location():
    pavilion = request.form.get('pavilion')
    room = request.form.get('room', '')
    cabinet = request.form.get('cabinet', '')
    if not pavilion:
        return jsonify({'error': 'Pavilion is required'}), 400
    location = Location(pavilion=pavilion, room=room, cabinet=cabinet)
    db.session.add(location)
    try:
        db.session.commit()
        return jsonify({
            'status': 'success',
            'message': 'Location added successfully',
            'entity': {'id': location.id, 'name': f"{location.pavilion} - {location.room} - {location.cabinet}"}
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'status': 'error',
            'message': 'Error adding location',
            'error': str(e)
        }), 400

@main_blueprint.route('/add_project', methods=['POST'])
@login_required
def add_project():
    name = request.form.get('name')
    funding_body = request.form.get('funding_body', '')
    if not name:
        return jsonify({'error': 'Project name is required'}), 400
    project = Project(name=name, funding_body=funding_body)
    db.session.add(project)
    try:
        db.session.commit()
        return jsonify({
            'status': 'success',
            'message': 'Project added successfully',
            'entity': {'name': f"{project.name}"}
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'status': 'error',
            'message': 'Error adding the project',
            'error': str(e)
        }), 400

@main_blueprint.route('/list_products')
@login_required
def list_products():
    user_only = request.args.get('user_only', 'false').lower() in ['true', '1', 't']
    if user_only:
        # Mostra solo i prodotti attivi dell'utente e quelli per cui è manager
        products = Product.query.filter(Product.owner_id == current_user.id).all()
        # Includere anche i prodotti gestiti dall'utente
        managed_products = Product.query.join(Product.managers).filter(User.id == current_user.id, Product.is_active == True).all()
        products.extend(managed_products)
    else:
        # Mostra tutti i prodotti sulla piattaforma
        products = Product.query.filter(Product.is_active == True)

    return render_template('backend/page-list-product.html', products=products)


@main_blueprint.route('/toggle_product/<int:product_id>', methods=['POST'])
@login_required
def toggle_product(product_id):
    product = Product.query.get_or_404(product_id)
    if current_user.id == product.owner_id or current_user in product.managers:
        product.is_active = not product.is_active
        db.session.commit()
        return jsonify({'success': 'Product visibility updated', 'is_active': product.is_active})
    return jsonify({'error': 'Unauthorized'}), 403


@main_blueprint.route('/product/<encrypted_id>')
@login_required
def view_product(encrypted_id):
    try:
        product_id = current_app.auth_s.loads(encrypted_id)  # Decodifica l'ID
    except Exception as e:
        flash('Invalid product ID.', 'error')
        return redirect(url_for('main.index'))

    product = Product.query.get_or_404(product_id)

    # Verifica se l'utente corrente è il proprietario o un manager
    is_owner_or_manager = current_user.id == product.owner_id or \
                          any(manager.user_id == current_user.id for manager in product.manager_associations)

    # Ottieni tutte le categorie e i progetti
    all_categories = Category.query.order_by(Category.name).all()
    all_projects = Project.query.all()
    all_locations = Location.query.order_by(Location.pavilion).all()

    # Evidenzia le selezioni attuali
    selected_categories = [category.id for category in product.categories]
    selected_project = product.project_id if product.project else None

    # Ottieni tutti gli utenti per la selezione dei manager
    all_users = User.query.order_by(User.name).all()

    # Prepara la lista degli ID dei manager già assegnati al prodotto
    assigned_manager_ids = {manager.user_id for manager in product.manager_associations}

    return render_template('backend/page-product.html',
                        product=product,
                        all_categories=all_categories,
                        selected_categories=selected_categories,
                        all_users=all_users,
                        selected_managers=assigned_manager_ids,
                        all_projects=all_projects,
                        selected_project=selected_project,
                        all_locations=all_locations,
                        selected_location=product.location_id,
                        is_owner_or_manager=is_owner_or_manager)


@main_blueprint.route('/update_product/<encrypted_id>', methods=['POST']) #TODO Fix del bottone aggiungi location
#TODO Aggiungere bottone add category, project
@login_required
def update_product(encrypted_id):
    try:
        product_id = current_app.auth_s.loads(encrypted_id)  # Decodifica l'ID
    except Exception as e:
        flash('Invalid product ID.', 'error')
        return redirect(url_for('main.index'))
    product = Product.query.get_or_404(product_id)
    if product.owner_id != current_user.id:
        flash('You do not have permission to edit this product.', 'error')
        return redirect(url_for('main.list_products'))

    product.name = request.form['name']
    product.description = request.form['description']
    product.quantity = request.form['quantity']
    category_ids = request.form.getlist('category_ids[]')
    product.categories = Category.query.filter(Category.id.in_(category_ids)).all()
    # Assicurati che il proprietario sia sempre un manager
    manager_ids = request.form.getlist('managers[]')
    project_id = request.form.get('project_id')
    product.project_id = project_id
    if str(product.owner_id) not in manager_ids:
        manager_ids.append(str(product.owner_id))
    product.location_id = request.form['location_id']
    # Update manager associations
    product.managers = [User.query.get(manager_id) for manager_id in manager_ids if User.query.get(manager_id)]

    try:
        db.session.commit()
        flash('Product updated successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error updating product: {str(e)}', 'error')

    return redirect(url_for('main.list_products'))


