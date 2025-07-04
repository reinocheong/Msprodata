from flask import Blueprint, render_template, redirect, url_for, request, flash
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, logout_user, login_required
from models import User
from app import db

auth = Blueprint('auth', __name__)

@auth.route('/login', methods=['GET', 'POST'])
def login():
    """
    Handles user login.
    """
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        user = User.query.filter_by(email=email).first()
        
        if not user or not check_password_hash(user.password, password):
            flash('Please check your login details and try again.', 'danger')
            return redirect(url_for('auth.login'))
            
        login_user(user)
        return redirect(url_for('main.index'))
        
    return render_template('login.html')

@auth.route('/signup', methods=['GET', 'POST'])
def signup():
    """
    Handles new user registration.
    """
    if request.method == 'POST':
        email = request.form.get('email')
        name = request.form.get('name')
        password = request.form.get('password')
        
        user = User.query.filter_by(email=email).first()
        
        if user:
            flash('Email address already exists.', 'warning')
            return redirect(url_for('auth.signup'))
            
        new_user = User(
            email=email, 
            name=name, 
            password=generate_password_hash(password, method='pbkdf2:sha256')
        )
        
        db.session.add(new_user)
        db.session.commit()
        
        flash('Account created successfully! Please log in.', 'success')
        return redirect(url_for('auth.login'))
        
    return render_template('signup.html')

@auth.route('/logout')
@login_required
def logout():
    """
    Handles user logout.
    """
    logout_user()
    return redirect(url_for('main.index'))