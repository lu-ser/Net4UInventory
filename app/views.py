from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_user, logout_user, current_user, login_required
from .forms import LoginForm, RegistrationForm
from .models import User
from .extensions import db

main_blueprint = Blueprint('main', __name__)

@main_blueprint.route('/')
def index():
    return render_template('index.html')

@main_blueprint.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('.index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and user.verify_password(form.password.data):
            login_user(user)
            return redirect(url_for('.index'))
        else:
            flash('Invalid email or password.')
    return render_template('login.html', form=form)

@main_blueprint.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('.index'))

@main_blueprint.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('.index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(email=form.email.data, role=form.role.data)
        user.password = form.password.data  # Usa il setter per hashare la password
        db.session.add(user)
        db.session.commit()
        flash('You are now registered and can login.')
        return redirect(url_for('.login'))
    return render_template('register.html', form=form)
