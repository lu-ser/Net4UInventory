from flask import Blueprint, render_template,session, redirect, url_for, flash, request, jsonify, current_app, get_flashed_messages
from flask_login import login_user, logout_user, current_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from itsdangerous import URLSafeSerializer, URLSafeTimedSerializer, SignatureExpired, BadSignature
import os
from sqlalchemy import  func
from .forms import LoginForm, RegistrationForm
from .models import User, Product, Category, Location, Project, ProductManager, Loan
from .extensions import db, upload_dir
import csv
from datetime import datetime
from .utils.inventory_helpers import get_reserved_quantity, get_active_loans
from datetime import datetime, timedelta
from .utils.utils import flash_message, send_email
import hashlib
from flask import make_response
import csv
from io import StringIO
import openpyxl
from openpyxl import Workbook
from openpyxl.worksheet.datavalidation import DataValidation
from flask import send_file
import io

main_blueprint = Blueprint('main', __name__)

@main_blueprint.route('/')
@login_required
def index():
    messages = get_flashed_messages(with_categories=True)
    return render_template('backend/index.html', messages=messages)

@main_blueprint.route('/logout')
@login_required  # Assicurati che solo gli utenti loggati possano accedere a questa route
def logout():
    logout_user()
    flash('Logged out successfully.', 'success')
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
        flash('Invalid role selected.','error')
        return redirect(url_for('main.show_register_page'))  # Assicurati di avere una route e una funzione per 'register_page'
    # Controlla che l'email non sia già utilizzata
    if User.query.filter_by(email=email).first() is not None:
        flash('Email already used.','error')
        return redirect(url_for('main.show_register_page'))
    # Crea un nuovo utente
    hashed_password = generate_password_hash(password)
    new_user = User(name=name, surname=surname, email=email, password_hash=hashed_password, role=role)
    db.session.add(new_user)
    db.session.commit()
    flash('User successfully registered.','success')
    return redirect(url_for('main.login'))



@main_blueprint.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            flash('Hello ' + user.name, category="success")
            return redirect(url_for('main.index'))
        else:
            flash('Invalid email or password.', 'error')
            return redirect(url_for('main.login'))
    return render_template('backend/auth-sign-in.html', messages=get_flashed_messages(with_categories=True))


@main_blueprint.route('/register')
def show_register_page():
    messages = get_flashed_messages(with_categories=True)
    return render_template('backend/register.html',messages=messages)

@main_blueprint.route('/lost_password')
def lost_password():
    messages = get_flashed_messages(with_categories=True)
    return render_template('backend/lost_password.html',messages=messages)

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
    print("Session in list_products:", dict(session))
    flash_message = session.pop('flash_message', None)
    if flash_message:
        flash(flash_message[1], flash_message[0])
    
    messages = get_flashed_messages(with_categories=True)
    return render_template('backend/page-list-product.html', products=products, messages=messages)


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
    is_owner_or_manager = current_user.id == product.owner_id or any(manager.user_id == current_user.id for manager in product.manager_associations)
    all_categories = Category.query.order_by(Category.name).all()
    all_projects = Project.query.all()
    all_locations = Location.query.order_by(Location.pavilion).all()
    all_users = User.query.order_by(User.name).all()
    selected_categories = [category.id for category in product.categories]
    selected_project = product.project_id if product.project else None
    assigned_manager_ids = {manager.user_id for manager in product.manager_associations}
    reserved_dates = get_reserved_dates(product.id)
    reserved_quantity = get_reserved_quantity(product.id, datetime.now())

    return render_template('backend/page-product.html',
                           encrypted_product_id=encrypted_id,
                           product=product,
                           all_categories=all_categories,
                           selected_categories=selected_categories,
                           all_users=all_users,
                           selected_managers=assigned_manager_ids,
                           all_projects=all_projects,
                           selected_project=selected_project,
                           all_locations=all_locations,
                           selected_location=product.location_id,
                           is_owner_or_manager=is_owner_or_manager,
                           reserved_dates=reserved_dates,
                           reserved_quantity=reserved_quantity)

@main_blueprint.route('/update_product/<encrypted_id>', methods=['POST']) #TODO Fix del bottone aggiungi location
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
        #session['flash_message'] = ('success', 'Product updated successfully!')
        flash('Invalid email or password.','success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error updating product: {str(e)}', 'error')
        session['flash_message'] = ('error', 'An error occured')
    return redirect(url_for('main.list_products'))




@main_blueprint.route('/set_product_unavailability/<encrypted_id>', methods=['POST'])
@login_required
def set_product_unavailability(encrypted_id):
    product_id = current_app.auth_s.loads(encrypted_id)
    product = Product.query.get_or_404(product_id)

    if current_user.id not in [product.owner_id] + [manager.user_id for manager in product.managers]:
        flash('You do not have permission to perform this action.', 'error')
        return redirect(url_for('main.index'))

    unavailability = Loan(
        product_id=product_id,
        borrower_id=current_user.id,
        manager_id=current_user.id,  # Considered as managed by self for unavailability
        start_date=request.form['start_date'],
        end_date=request.form['end_date'],
        status='unavailable',
        quantity=request.form['unavailability_quantity']
    )
    db.session.add(unavailability)
    try:
        db.session.commit()
        flash('Product set as unavailable successfully.', 'success')
    except:
        db.session.rollback()
        flash('Error setting product as unavailable.', 'error')

    return redirect(url_for('main.product_details', encrypted_id=encrypted_id))


@main_blueprint.route('/product_availability/<encrypted_id>')
@login_required
def product_availability(encrypted_id):
    try:
        product_id = current_app.auth_s.loads(encrypted_id)
    except Exception as e:
        return jsonify([])

    quantity_requested = int(request.args.get('quantity', 1))
    product = Product.query.get_or_404(product_id)
    loans = get_active_loans(product_id)

    events = []
    for loan in loans:
        if loan.quantity + quantity_requested > product.quantity:
            events.append({
                'title': 'Not Available',
                'start': loan.start_date.strftime('%Y-%m-%d'),
                'end': loan.end_date.strftime('%Y-%m-%d'),
                'color': 'red'
            })
        else:
            events.append({
                'title': 'Available',
                'start': loan.start_date.strftime('%Y-%m-%d'),
                'end': loan.end_date.strftime('%Y-%m-%d'),
                'color': 'green'
            })

    return jsonify(events)

@main_blueprint.route('/request_product/<encrypted_id>', methods=['POST'])
@login_required
def request_product(encrypted_id):
    try:
        product_id = current_app.auth_s.loads(encrypted_id)  # Decodifica l'ID
    except Exception as e:
        flash('Invalid product ID.', 'error')
        return redirect(url_for('main.index'))

    product = Product.query.get_or_404(product_id)

    request_quantity = int(request.form['request_quantity'])
    request_start_date = datetime.strptime(request.form['request_start_date'], '%Y-%m-%d').date()
    request_end_date = datetime.strptime(request.form['request_end_date'], '%Y-%m-%d').date()

    # Calcola le prenotazioni attive per questo prodotto
    active_loans = get_active_loans(product_id)

    # Logica per controllare la disponibilità del prodotto
    product_available = True
    for loan in active_loans:
        # Verifica se ci sono sovrapposizioni con le date di prenotazione richieste
        if (request_start_date <= loan.end_date and request_end_date >= loan.start_date):
            product_available = False
            break

    if product_available:
        # Salva la richiesta nel database o fai altro
        # Esempio: crea una nuova prenotazione nel database
        new_loan = Loan(
            product_id=product_id,
            borrower_id=current_user.id,
            manager_id=product.owner_id,
            start_date=request_start_date,
            end_date=request_end_date,
            quantity=request_quantity,
            status='pending'  # Può essere 'pending' o 'approved' a seconda della tua logica
        )
        db.session.add(new_loan)
        db.session.commit()

        flash('Product requested successfully!', 'success')
    else:
        flash('Product not available for the requested dates.', 'error')

    return redirect(url_for('main.view_product', encrypted_id=encrypted_id))

 #TODO verificare se le quantià corrispondono
    #TODO Vorrei vedere nel calendario quando il prodotto è disponibile e non ed in quanta misura. 
    # Cioè, dato il numero di oggetti che voglio, il calendario si deve aggiornare indicandomi quando posso richiederlo o no


@main_blueprint.route('/fetch_availability/<encrypted_id>', methods=['GET'])
@login_required
def fetch_availability(encrypted_id):
    try:
        product_id = current_app.auth_s.loads(encrypted_id)
    except Exception as e:
        return jsonify([]), 400

    start_date = request.args.get('start')
    end_date = request.args.get('end')
    quantity = int(request.args.get('quantity', 1))

    if not start_date or not end_date:
        return jsonify([]), 400

    availability = get_availability(product_id, start_date, end_date, quantity)

    return jsonify(availability)

def get_availability(product_id, start_date, end_date, quantity):
    # Implementa la logica per ottenere la disponibilità del prodotto
    # Per esempio:
    product = Product.query.get(product_id)
    if not product:
        return []

    availability = []
    current_date = datetime.strptime(start_date, '%Y-%m-%d')
    end_date = datetime.strptime(end_date, '%Y-%m-%d')

    while current_date <= end_date:
        reserved_quantity = get_reserved_quantity(product_id, current_date)
        available = product.quantity - reserved_quantity >= quantity
        availability.append({'date': current_date.strftime('%Y-%m-%d'), 'available': available})
        current_date += timedelta(days=1)

    return availability

def get_reserved_quantity(product_id, date):
    reserved = db.session.query(func.sum(Loan.quantity)).filter(
        Loan.product_id == product_id,
        Loan.start_date <= date,
        Loan.end_date >= date
    ).scalar()

    return reserved if reserved else 0

def get_reserved_quantity_for_period(product_id, start_date, end_date):
    reserved_quantity = db.session.query(func.sum(Loan.quantity)).filter(
        Loan.product_id == product_id,
        Loan.start_date <= end_date,
        Loan.end_date >= start_date,
        Loan.status != 'returned'
    ).scalar()
    return reserved_quantity if reserved_quantity else 0

def get_reserved_dates(product_id):
    loans = Loan.query.filter_by(product_id=product_id).all()
    reserved_dates = {}
    for loan in loans:
        for date in daterange(loan.start_date, loan.end_date):
            reserved_dates[date.strftime('%Y-%m-%d')] = reserved_dates.get(date.strftime('%Y-%m-%d'), 0) + loan.quantity
    return reserved_dates

@main_blueprint.route('/process_booking/<encrypted_id>', methods=['POST'])
@login_required
def process_booking(encrypted_id):
    try:
        product_id = current_app.auth_s.loads(encrypted_id)
    except Exception as e:
        return jsonify({'status': 'error', 'message': 'Invalid product ID'}), 400

    start_date = datetime.strptime(request.form['start_date'], '%Y-%m-%d')
    end_date = datetime.strptime(request.form['end_date'], '%Y-%m-%d')
    quantity = int(request.form['quantity'])

    if not check_date_range_availability(product_id, start_date, end_date, quantity):
        return jsonify({'status': 'error', 'message': 'Not enough quantity available for the selected dates'}), 400

    product = Product.query.get(product_id)

    # Verifica se l'utente loggato è manager o owner del prodotto
    if current_user.id == product.owner_id or current_user in product.managers:
        status = 'unavailable'
    else:
        status = 'pending'

    new_loan = Loan(
        product_id=product_id,
        borrower_id=current_user.id,
        manager_id=current_user.id,
        start_date=start_date,
        end_date=end_date,
        quantity=quantity,
        status=status
    )
    db.session.add(new_loan)
    db.session.commit()

    return jsonify({'status': 'success', 'message': 'Booking successful'})

def daterange(start_date, end_date):
    for n in range(int((end_date - start_date).days) + 1):
        yield start_date + timedelta(n)

def check_date_range_availability(product_id, start_date, end_date, quantity):
    date = start_date
    while date <= end_date:
        reserved_quantity = get_reserved_quantity_for_day(product_id, date)
        product = Product.query.get(product_id)
        if product.quantity - reserved_quantity < quantity:
            return False
        date += timedelta(days=1)
    return True

@main_blueprint.route('/check_availability', methods=['POST'])
def check_availability():
    date = request.form['date']
    quantity = int(request.form['quantity'])
    product_id = int(request.form['product_id'])

    date = datetime.strptime(date, '%Y-%m-%d')

    reserved_quantity = get_reserved_quantity_for_day(product_id, date)
    product = Product.query.get(product_id)
    available_quantity = product.quantity - reserved_quantity

    return jsonify({'available': available_quantity >= quantity})

def get_reserved_quantity_for_day(product_id, date):
    reserved_quantity = db.session.query(func.sum(Loan.quantity)).filter(
        Loan.product_id == product_id,
        Loan.start_date <= date,
        Loan.end_date >= date,
        Loan.status != 'returned'
    ).scalar()
    return reserved_quantity if reserved_quantity else 0

@main_blueprint.route('/check_availability_range', methods=['POST'])
@login_required
def check_availability_range():
    try:
        product_id = current_app.auth_s.loads(request.form['encrypted_id'])
    except Exception as e:
        return jsonify({'status': 'error', 'message': 'Invalid product ID'}), 400

    start_date = datetime.strptime(request.form['start_date'], '%Y-%m-%d')
    end_date = datetime.strptime(request.form['end_date'], '%Y-%m-%d')
    quantity = int(request.form['quantity'])

    reserved_dates = {}
    date = start_date
    while date <= end_date:
        reserved_quantity = get_reserved_quantity_for_day(product_id, date)
        product = Product.query.get(product_id)
        available_quantity = product.quantity - reserved_quantity
        reserved_dates[date.strftime('%Y-%m-%d')] = {'available': available_quantity >= quantity}
        date += timedelta(days=1)

    return jsonify(reserved_dates)

@main_blueprint.route('/loan_requests')
@login_required
def loan_requests():
    status = request.args.get('status', 'all')
    
    # Get outgoing loan requests
    outgoing_requests_query = Loan.query.filter_by(borrower_id=current_user.id)
    
    if status == 'in_review_pending':
        outgoing_requests_query = outgoing_requests_query.filter(Loan.status.in_(['in_review', 'pending']))
    elif status != 'all':
        outgoing_requests_query = outgoing_requests_query.filter(Loan.status == status)
    
    outgoing_requests = outgoing_requests_query.all()
    return render_template('backend/page-list-requests.html', outgoing_requests=outgoing_requests)


@main_blueprint.route('/get_loan_details/<int:loan_id>', methods=['GET'])
@login_required
def get_loan_details(loan_id):
    loan = Loan.query.get_or_404(loan_id)
    if loan.borrower_id != current_user.id and loan.manager_id != current_user.id:
        return jsonify({'status': 'error', 'message': 'Unauthorized'}), 403

    loan_details = {
        'product_name': loan.product.name,
        'quantity': loan.quantity,
        'start_date': loan.start_date.strftime('%Y-%m-%d'),
        'end_date': loan.end_date.strftime('%Y-%m-%d'),
        'location': f"{loan.product.location.pavilion}, Room: {loan.product.location.room}, Cabinet: {loan.product.location.cabinet}",
        'description': loan.product.description,
        'managers': [{'name': manager.name, 'surname': manager.surname, 'email': manager.email} for manager in loan.product.managers]
    }
    return jsonify(loan_details)

@main_blueprint.route('/restore_unavailable/<int:loan_id>', methods=['POST'])
@login_required
def restore_unavailable(loan_id):
    loan = Loan.query.get_or_404(loan_id)
    if loan.status != 'unavailable':
        return jsonify({'status': 'error', 'message': 'Loan is not marked as unavailable'}), 400
    
    if current_user.id != loan.manager_id:
        return jsonify({'status': 'error', 'message': 'You are not authorized to perform this action'}), 403

    db.session.delete(loan)
    db.session.commit()
    
    return jsonify({'status': 'success', 'message': 'Product restored successfully'})

@main_blueprint.route('/cancel_request/<int:loan_id>', methods=['POST'])
@login_required
def cancel_request(loan_id):
    loan = Loan.query.get_or_404(loan_id)
    if loan.status != 'pending':
        return jsonify({'status': 'error', 'message': 'Only pending loans can be cancelled'}), 400

    if current_user.id != loan.borrower_id:
        return jsonify({'status': 'error', 'message': 'You are not authorized to perform this action'}), 403

    loan.status = 'cancelled'
    db.session.commit()

    return jsonify({'status': 'success', 'message': 'Loan request cancelled successfully'})
#### Rotta per Segnare un Prestito come "Returned"
@main_blueprint.route('/mark_as_returned/<int:loan_id>', methods=['POST'])
@login_required
def mark_as_returned(loan_id):
    loan = Loan.query.get_or_404(loan_id)
    if loan.status != 'approved':
        return jsonify({'status': 'error', 'message': 'Only approved loans can be marked as returned'}), 400

    if current_user.id != loan.borrower_id:
        return jsonify({'status': 'error', 'message': 'You are not authorized to perform this action'}), 403

    loan.status = 'in_review'
    db.session.commit()

    return jsonify({'status': 'success', 'message': 'Loan marked as returned, awaiting review'})

@main_blueprint.route('/requests_for_my_products')
@login_required
def requests_for_my_products():
    status = request.args.get('status', 'all')
    
    incoming_requests_query = Loan.query.join(Product).filter(
        (Product.owner_id == current_user.id) |
        (Product.managers.any(User.id == current_user.id))
    )
    
    if status != 'all':
        incoming_requests_query = incoming_requests_query.filter(Loan.status == status)

    incoming_requests = incoming_requests_query.all()

    unavailable_products = Loan.query.filter(
        (Loan.manager_id == current_user.id) &
        (Loan.status == 'unavailable')
    ).all()

    return render_template(
        'backend/requests_for_my_products.html',
        incoming_requests=incoming_requests,
        unavailable_products=unavailable_products
    )


@main_blueprint.route('/approve_request/<int:request_id>', methods=['POST'])
@login_required
def approve_request(request_id):
    request = Loan.query.get(request_id)
    if request and (request.product.owner_id == current_user.id or request.product.manager_id == current_user.id):
        request.status = 'approved'
        db.session.commit()
        return jsonify({'status': 'success', 'message': 'Request approved successfully'})
    return jsonify({'status': 'error', 'message': 'Request not found or not authorized'}), 404

@main_blueprint.route('/reject_request/<int:request_id>', methods=['POST'])
@login_required
def reject_request(request_id):
    request = Loan.query.get(request_id)
    if request and (request.product.owner_id == current_user.id or request.product.manager_id == current_user.id):
        request.status = 'rejected'
        db.session.commit()
        return jsonify({'status': 'success', 'message': 'Request rejected successfully'})
    return jsonify({'status': 'error', 'message': 'Request not found or not authorized'}), 404

@main_blueprint.route('/extend_loan/<int:loan_id>', methods=['POST'])
@login_required
def extend_loan(loan_id):
    loan = Loan.query.get_or_404(loan_id)
    new_end_date = request.form.get('new_end_date')

    if not new_end_date:
        return jsonify({'status': 'error', 'message': 'New termination date is required'}), 400

    try:
        new_end_date = datetime.strptime(new_end_date, '%Y-%m-%d').date()
    except ValueError:
        return jsonify({'status': 'error', 'message': 'Invalid date format'}), 400

    if loan.product.owner_id != current_user.id and not current_user in loan.product.managers:
        return jsonify({'status': 'error', 'message': 'You are not authorized to extend this loan'}), 403

    loan.end_date = new_end_date
    db.session.commit()

    return jsonify({'status': 'success', 'message': 'Loan extended successfully'})

@main_blueprint.route('/reset_password_request', methods=['GET', 'POST'])
def reset_password_request():
    if request.method == 'POST':
        email = request.form.get('email')
        user = User.query.filter_by(email=email).first()
        if user:
            token = generate_confirmation_token(user.email)
            send_email('Reset Your Password', user.email, '/backend/reset_password', token=token)
            flash('An email has been sent with instructions to reset your password.', 'info')
            return redirect(url_for('main.login'))
        else:
            flash('Email address not found.', 'warning')
    return redirect(url_for('main.lost_password'))

def generate_confirmation_token(email):
    serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    return serializer.dumps(email, salt=current_app.config['SECURITY_PASSWORD_SALT'])

@main_blueprint.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    try:
        email = confirm_token(token)
        if email is False:
            flash('The reset link is invalid or has expired.', 'danger')
            return redirect(url_for('main.reset_password_request'))
    except:
        flash('An error occurred. Please try again.', 'danger')
        return redirect(url_for('main.reset_password_request'))
    
    user = User.query.filter_by(email=email).first_or_404()

    if request.method == 'POST':
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        if password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return render_template('/backend/reset_password.html', token=token)

        # Debug: Print the password (solo per scopi di debugging, rimuovi in produzione)
        print(f"Password inserita: {password}")

        # Debug: Genera un hash della password con un metodo noto
        debug_hash = hashlib.sha256(password.encode()).hexdigest()
        print(f"Debug hash: {debug_hash}")

        # Salva la password
        user.password = password

        # Debug: Stampa l'hash della password salvata
        print(f"Hash salvato: {user.password_hash}")

        try:
            db.session.commit()
            
            # Debug: Verifica se la password può essere verificata correttamente
            if check_password_hash(user.password_hash, password):
                print("La password può essere verificata correttamente.")
            else:
                print("ERRORE: La password non può essere verificata.")
                
        except Exception as e:
            print(f"Errore durante il salvataggio: {str(e)}")
            db.session.rollback()
        
        flash('Your password has been updated!', 'success')
        return redirect(url_for('main.login'))
    
    return render_template('/backend/reset_password.html', token=token)

def confirm_token(token, expiration=3600):
    serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    try:
        email = serializer.loads(
            token,
            salt=current_app.config['SECURITY_PASSWORD_SALT'],
            max_age=expiration
        )
    except SignatureExpired:
        return False  # valid token, but expired
    except BadSignature:
        return False  # invalid token
    return email


@main_blueprint.route('/users')
@login_required
def users():
    return render_template('/backend/page-list-users.html', users=users)

@main_blueprint.route('/apiusers')
@login_required
def api_users():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '', type=str)
    per_page = 10

    if search:
        users_query = User.query.filter(
    (User.name.ilike(f'%{search}%')) |
    (User.surname.ilike(f'%{search}%')) |
    (User.role.ilike(f'%{search}%'))
)

    else:
        users_query = User.query

    users_pagination = users_query.paginate(page=page, per_page=per_page)
    users = users_pagination.items

    users_list = []
    for user in users:
        users_list.append({
            'name': user.name,
            'surname': user.surname,
            'email': user.email,
            'role':user.role
        })

    return jsonify({
        'users': users_list,
        'pagination': {
            'page': users_pagination.page,
            'pages': users_pagination.pages,
            'total': users_pagination.total,
            'prev_num': users_pagination.prev_num,
            'next_num': users_pagination.next_num,
            'has_prev': users_pagination.has_prev,
            'has_next': users_pagination.has_next,
        }
    })

@main_blueprint.route('/editProfile')
@login_required
def userprof():
    messages = get_flashed_messages(with_categories=True)
    return render_template('/backend/user-profile-edit.html',messages=messages)

@main_blueprint.route('/change_password_form', methods=['GET', 'POST'])
@login_required
def change_password_form():
    if request.method == 'POST':
        password = request.form.get('newpassword')
        confirm_password = request.form.get('validation')
        if password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return render_template('change_password.html')
        user = User.query.filter_by(email=current_user.email).first_or_404()
        if user:
            # Salva la nuova password
            user.password_hash = generate_password_hash(password)
            try:
                db.session.commit()
                
                # Debug: Verifica se la password può essere verificata correttamente
                if check_password_hash(user.password_hash, password):
                    print("La password può essere verificata correttamente.")
                else:
                    print("ERRORE: La password non può essere verificata.")
            except Exception as e:
                print(f"Errore durante il salvataggio: {str(e)}")
                db.session.rollback()
                flash('An error occurred while updating your password. Please try again.', 'danger')
                return render_template('change_password.html')

            flash('Your password has been updated!', 'success')
            return redirect(url_for('main.login'))
        else:
            flash('User not found.', 'danger')

    return render_template('change_password.html')



@main_blueprint.route('/download_excel_template', methods=['GET'])
@login_required
def download_excel_template():
    # Recupera i dati dal database
    categories = Category.query.all()
    projects = Project.query.all()
    locations = Location.query.all()
    managers = User.query.all()  # Aggiungi questa riga per recuperare gli utenti

    # Crea un nuovo workbook e attiva il foglio
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Product Template"

    # Definisci le intestazioni
    headers = ["Name", "Unique Code", "Description", "Pavilion", "Room", "Cabinet", "Project", "Categories", "Quantity", "Managers"]
    ws.append(headers)

    # Aggiungi un esempio
    example = ["Example Name", "Example Code", "Example Description", "Example Pavilion", "Example Room", "Example Cabinet", "Example Project", "Example Category", 1, "Example Manager"]
    ws.append(example)

    # Aggiungi una nuova scheda per i valori dei menu a tendina
    ws_data = wb.create_sheet(title="Data")
    ws_data.sheet_state = 'hidden'  # Nascondi la scheda

    # Aggiungi i dati di validazione
    category_list = [category.name for category in categories]
    project_list = [project.name for project in projects]
    pavilion_list = list(set([location.pavilion for location in locations]))
    room_list = list(set([location.room for location in locations if location.room]))
    cabinet_list = list(set([location.cabinet for location in locations if location.cabinet]))
    manager_list = [f"{user.name} {user.surname}" for user in managers]

    # Inserisci i dati nella scheda nascosta
    for idx, category in enumerate(category_list, start=1):
        ws_data[f'A{idx}'] = category
    for idx, project in enumerate(project_list, start=1):
        ws_data[f'B{idx}'] = project
    for idx, pavilion in enumerate(pavilion_list, start=1):
        ws_data[f'C{idx}'] = pavilion
    for idx, room in enumerate(room_list, start=1):
        ws_data[f'D{idx}'] = room
    for idx, cabinet in enumerate(cabinet_list, start=1):
        ws_data[f'E{idx}'] = cabinet
    for idx, manager in enumerate(manager_list, start=1):
        ws_data[f'F{idx}'] = manager

    # Definisci gli intervalli di nomi
    category_range = f'Data!$A$1:$A${len(category_list)}'
    project_range = f'Data!$B$1:$B${len(project_list)}'
    pavilion_range = f'Data!$C$1:$C${len(pavilion_list)}'
    room_range = f'Data!$D$1:$D${len(room_list)}'
    cabinet_range = f'Data!$E$1:$E${len(cabinet_list)}'
    manager_range = f'Data!$F$1:$F${len(manager_list)}'

    # Aggiungi la validazione dei dati
    dv_categories = DataValidation(type="list", formula1=category_range, allow_blank=True)
    dv_projects = DataValidation(type="list", formula1=project_range, allow_blank=True)
    dv_pavilions = DataValidation(type="list", formula1=pavilion_range, allow_blank=True)
    dv_rooms = DataValidation(type="list", formula1=room_range, allow_blank=True)
    dv_cabinets = DataValidation(type="list", formula1=cabinet_range, allow_blank=True)
    dv_managers = DataValidation(type="list", formula1=manager_range, allow_blank=True)

    ws.add_data_validation(dv_categories)
    ws.add_data_validation(dv_projects)
    ws.add_data_validation(dv_pavilions)
    ws.add_data_validation(dv_rooms)
    ws.add_data_validation(dv_cabinets)
    ws.add_data_validation(dv_managers)

    # Applica la validazione delle colonne appropriate
    max_row = ws.max_row + 1000  # aggiunge 1000 righe per validazione
    dv_categories.add(f'H2:H{max_row}')
    dv_projects.add(f'G2:G{max_row}')
    dv_pavilions.add(f'D2:D{max_row}')
    dv_rooms.add(f'E2:E{max_row}')
    dv_cabinets.add(f'F2:F{max_row}')
    dv_managers.add(f'J2:J{max_row}')

    # Salva il workbook in un oggetto BytesIO
    output = io.BytesIO()
    wb.save(output)
    output.seek(0)

    return send_file(
        output,
        as_attachment=True,
        download_name='product_template.xlsx',
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )


@main_blueprint.route('/upload_excel', methods=['POST'])
@login_required
def upload_excel():
    if 'file' not in request.files:
        flash('No file part', 'error')
        return redirect(url_for('main.add_product'))
    
    file = request.files['file']
    if file.filename == '':
        flash('No selected file', 'error')
        return redirect(url_for('main.add_product'))
    
    if file and file.filename.endswith(('.xlsx', '.xls')):
        filename = secure_filename(file.filename)
        
        # Crea la cartella 'temp' se non esiste
        temp_folder = os.path.join(current_app.root_path, 'temp')
        os.makedirs(temp_folder, exist_ok=True)
        
        file_path = os.path.join(temp_folder, filename)
        file.save(file_path)
        
        try:
            wb = openpyxl.load_workbook(file_path)
            ws = wb.active
            
            products_data = []
            for row in ws.iter_rows(min_row=2, values_only=True):
                if not any(row):  # Skip empty rows
                    continue
                name, code, description, pavilion, room, cabinet, project, categories, quantity, managers = row
                
                products_data.append({
                    'name': name,
                    'code': code,
                    'description': description,
                    'pavilion': pavilion,
                    'room': room,
                    'cabinet': cabinet,
                    'project': project,
                    'categories': categories.split(',') if categories else [],
                    'quantity': quantity,
                    'managers': managers.split(',') if managers else []
                })
        except Exception as e:
            flash(f'Error processing file: {str(e)}', 'error')
            return redirect(url_for('main.add_product'))
        finally:
            os.remove(file_path)  # Remove the temporary file
        
        return render_template('backend/confirm_products.html', products=products_data)
    else:
        flash('Invalid file type. Please upload an Excel file.', 'error')
        return redirect(url_for('main.add_product'))
    
@main_blueprint.route('/process_products', methods=['POST'])
@login_required
def process_products():
    products_count = int(request.form.get('products_count', 0))
    for i in range(products_count):
        name = request.form.get(f'name_{i}')
        code = request.form.get(f'code_{i}')
        description = request.form.get(f'description_{i}')
        pavilion = request.form.get(f'pavilion_{i}')
        room = request.form.get(f'room_{i}')
        cabinet = request.form.get(f'cabinet_{i}')
        project_name = request.form.get(f'project_{i}')
        categories = request.form.get(f'categories_{i}').split(',')
        quantity = int(request.form.get(f'quantity_{i}'))
        managers = request.form.getlist(f'managers_{i}')

        # Find or create location
        location = Location.query.filter_by(pavilion=pavilion, room=room, cabinet=cabinet).first()
        if not location:
            location = Location(pavilion=pavilion, room=room, cabinet=cabinet)
            db.session.add(location)

        # Find or create project
        project = Project.query.filter_by(name=project_name).first()
        if not project:
            project = Project(name=project_name)
            db.session.add(project)

        # Find or create categories
        category_objects = []
        for cat_name in categories:
            category = Category.query.filter_by(name=cat_name.strip()).first()
            if not category:
                category = Category(name=cat_name.strip())
                db.session.add(category)
            category_objects.append(category)

        # Create product
        product = Product(
            name=name,
            unique_code=code,
            description=description,
            location=location,
            project=project,
            categories=category_objects,
            quantity=quantity,
            owner_id=current_user.id
        )
        db.session.add(product)

        # Add managers
        for manager_name in managers:
            name_parts = manager_name.strip().split()
            if len(name_parts) >= 2:
                user = User.query.filter_by(name=name_parts[0], surname=name_parts[-1]).first()
                if user:
                    product_manager = ProductManager(product=product, user=user)
                    db.session.add(product_manager)
                else:
                    flash(f'Manager not found: {manager_name}', 'warning')

    db.session.commit()
    flash('Products created successfully!', 'success')
    return redirect(url_for('main.add_product'))


@main_blueprint.route('/search_managers', methods=['GET'])
@login_required
def search_managers():
    term = request.args.get('term', '')
    managers = User.query.filter(
        (User.name.ilike(f'%{term}%') | User.surname.ilike(f'%{term}%')) &
        (User.id != current_user.id)
    ).all()
    return jsonify([{'id': m.id, 'name': m.name, 'surname': m.surname} for m in managers])