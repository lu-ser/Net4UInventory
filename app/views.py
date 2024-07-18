from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, current_app
from flask_login import login_user, logout_user, current_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os
from sqlalchemy import  func
from .forms import LoginForm, RegistrationForm
from .models import User, Product, Category, Location, Project, ProductManager, Loan
from .extensions import db, upload_dir
import csv
from datetime import datetime
from .utils.inventory_helpers import get_reserved_quantity, get_active_loans
from datetime import datetime, timedelta

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
    # Get outgoing loan requests
    outgoing_requests = Loan.query.filter_by(borrower_id=current_user.id).all()
    
    # Get products marked as unavailable by the manager or owner
    unavailable_loans = Loan.query.filter(
        Loan.manager_id == current_user.id,
        Loan.status == 'unavailable'
    ).all()
    
    return render_template('backend/page-list-requests.html', outgoing_requests=outgoing_requests, unavailable_loans=unavailable_loans)


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
    incoming_requests = Loan.query.join(Product).filter(
        (Product.owner_id == current_user.id) | 
        (Product.managers.any(User.id == current_user.id))
    ).filter(Loan.status != 'unavailable').all()

    unavailable_products = Loan.query.join(Product).filter(
        (Product.owner_id == current_user.id) | 
        (Product.managers.any(User.id == current_user.id))
    ).filter(Loan.status == 'unavailable').all()

    return render_template('backend/requests_for_my_products.html', incoming_requests=incoming_requests, unavailable_products=unavailable_products)


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