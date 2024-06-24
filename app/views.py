from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, current_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os
from .forms import LoginForm, RegistrationForm
from .models import User, Product, Category
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


@main_blueprint.route('/add_product', methods=['POST','GET'])
def add_product():
    if request.method == 'POST':
        name = request.form['name']
        unique_code = request.form['unique_code']
        description = request.form.get('description', '')
        category_id = request.form['category_id']
        quantity = int(request.form['quantity'])
        # Assume you've a function to handle file saving
        image = request.files['pic']
        filename = secure_filename(image.filename)
        image.save(os.path.join(upload_dir, filename))

        # Creating the product instance
        product = Product(
            name=name,
            unique_code=unique_code,
            description=description,
            category_id=category_id,
            quantity=quantity,
            image=filename  # Assuming you want to save the filename
        )
        db.session.add(product)
        db.session.commit()
        flash('Product added successfully!', 'success')
        return redirect(url_for('page_list_product'))
    return render_template('backend/page-add-product.html')


@main_blueprint.route('/upload_csv', methods=['POST'])
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


@main_blueprint.route('/add_category', methods=['GET', 'POST'])
def add_category():
    print("HELlo")
    if request.method == 'POST':
        name = request.form['name']
        new_category = Category(name=name)
        db.session.add(new_category)
        try:
            db.session.commit()
            flash('Category added successfully!', 'success')
        except:
            db.session.rollback()
            flash('Error adding category. The name might already exist.', 'error')
        return redirect(url_for('main.add_category'))
    
    return render_template('backend/page-add-category.html')
