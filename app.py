from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, IntegerField, FloatField, SelectField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, Email, Length, EqualTo, NumberRange
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import sqlite3
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'  # Change this in production
app.config['WTF_CSRF_ENABLED'] = True

# Register custom jinja filter for strftime
@app.template_filter('strftime')
def format_datetime(value, format='%B %d, %Y'):
    if isinstance(value, str) and value == 'now':
        value = datetime.now()
    elif isinstance(value, str):
        try:
            value = datetime.fromisoformat(value)
        except:
            return value
    if isinstance(value, datetime):
        return value.strftime(format)
    return value

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Database path
DATABASE = os.path.join(os.path.dirname(__file__), 'database.db')

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with app.app_context():
        conn = get_db()
        with open('database/schema.sql', 'r') as f:
            conn.executescript(f.read())
        
        # Add default admin user
        hashed_admin_password = generate_password_hash('admin123')
        conn.execute("INSERT OR IGNORE INTO users (name, email, password, role) VALUES ('Admin', 'admin@example.com', ?, 'admin')", (hashed_admin_password,))
        
        # Add sample schemes
        conn.execute('''INSERT OR IGNORE INTO schemes (name, description, income_limit, category_required, education_required, occupation_required, benefits, application_link) VALUES 
        ('Pradhan Mantri Jan Dhan Yojana', 'Financial inclusion and zero balance savings account scheme', 50000, 'All', 'All', 'All', 'Zero balance account, RuPay debit card, accident insurance up to ₹2 lakh', 'https://pmjdy.gov.in'),
        ('Mid Day Meal Scheme', 'Nutritional support for school children', 30000, 'All', 'All', 'Student', 'Free nutritious meals to school children', 'https://mdm.nic.in'),
        ('MGNREGA', 'Mahatma Gandhi National Rural Employment Guarantee Act', 20000, 'All', 'All', 'Unemployed', '100 days of guaranteed wage employment', 'https://nrega.nic.in'),
        ('Pradhan Mantri Awas Yojana', 'Housing for all scheme', 600000, 'SC', 'All', 'All', 'Subsidized housing loans and grants', 'https://pmaymis.gov.in')''')
        
        conn.commit()

# User class for Flask-Login
class User(UserMixin):
    def __init__(self, id, name, email, role):
        self.id = id
        self.name = name
        self.email = email
        self.role = role

@login_manager.user_loader
def load_user(user_id):
    if not user_id or not str(user_id).isdigit():
        return None
    conn = get_db()
    user = conn.execute('SELECT * FROM users WHERE id = ?', (int(user_id),)).fetchone()
    if user:
        return User(user['id'], user['name'], user['email'], user['role'])
    return None
# Admin Registration Route
@app.route('/register_admin', methods=['GET', 'POST'])
def register_admin():
    form = RegistrationForm()
    if form.validate_on_submit():
        conn = get_db()
        hashed_password = generate_password_hash(form.password.data)
        try:
            conn.execute('INSERT INTO users (name, email, password, role) VALUES (?, ?, ?, ?)',
                        (form.name.data, form.email.data, hashed_password, 'admin'))
            conn.commit()
            flash('Admin registration successful! Please login.', 'success')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash('Email already exists.', 'error')
    return render_template('register.html', form=form)

# Forms
class RegistrationForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired(), Length(min=2, max=100)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

class ProfileForm(FlaskForm):
    age = IntegerField('Age', validators=[DataRequired(), NumberRange(min=1, max=120)])
    income = FloatField('Annual Income', validators=[DataRequired(), NumberRange(min=0)])
    category = SelectField('Category', choices=[('General', 'General'), ('SC', 'SC'), ('ST', 'ST'), ('OBC', 'OBC')])
    education = SelectField('Education', choices=[('Below 10th', 'Below 10th'), ('10th Pass', '10th Pass'), ('12th Pass', '12th Pass'), ('Graduate', 'Graduate'), ('Post Graduate', 'Post Graduate')])
    occupation = SelectField('Occupation', choices=[('Student', 'Student'), ('Unemployed', 'Unemployed'), ('Self-Employed', 'Self-Employed'), ('Salaried', 'Salaried'), ('Farmer', 'Farmer')])
    location = StringField('Location', validators=[DataRequired()])
    submit = SubmitField('Save Profile')

class SchemeForm(FlaskForm):
    name = StringField('Scheme Name', validators=[DataRequired()])
    description = TextAreaField('Description', validators=[DataRequired()])
    income_limit = FloatField('Income Limit', validators=[DataRequired()])
    category_required = SelectField('Category Required', choices=[('All', 'All'), ('SC', 'SC'), ('ST', 'ST'), ('OBC', 'OBC'), ('General', 'General')])
    education_required = SelectField('Education Required', choices=[('All', 'All'), ('Below 10th', 'Below 10th'), ('10th Pass', '10th Pass'), ('12th Pass', '12th Pass'), ('Graduate', 'Graduate'), ('Post Graduate', 'Post Graduate')])
    occupation_required = SelectField('Occupation Required', choices=[('All', 'All'), ('Student', 'Student'), ('Unemployed', 'Unemployed'), ('Self-Employed', 'Self-Employed'), ('Salaried', 'Salaried'), ('Farmer', 'Farmer')])
    benefits = TextAreaField('Benefits', validators=[DataRequired()])
    application_link = StringField('Application Link')
    submit = SubmitField('Add Scheme')

# Eligibility logic
def check_eligibility(user_profile, scheme):
    if user_profile['income'] > scheme['income_limit']:
        return False
    if scheme['category_required'] != 'All' and user_profile['category'] != scheme['category_required']:
        return False
    if scheme['education_required'] != 'All' and user_profile['education'] != scheme['education_required']:
        return False
    if scheme['occupation_required'] != 'All' and user_profile['occupation'] != scheme['occupation_required']:
        return False
    return True

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        conn = get_db()
        hashed_password = generate_password_hash(form.password.data)
        try:
            conn.execute('INSERT INTO users (name, email, password) VALUES (?, ?, ?)',
                        (form.name.data, form.email.data, hashed_password))
            conn.commit()
            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash('Email already exists.', 'error')
    return render_template('register.html', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        conn = get_db()
        user = conn.execute('SELECT * FROM users WHERE email = ?', (form.email.data,)).fetchone()
        if user and check_password_hash(user['password'], form.password.data):
            user_obj = User(user['id'], user['name'], user['email'], user['role'])
            login_user(user_obj)
            return redirect(url_for('dashboard'))
        flash('Invalid email or password.', 'error')
    return render_template('login.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/dashboard', methods=['GET', 'POST'])
@login_required
def dashboard():
    form = ProfileForm()
    conn = get_db()
    profile = conn.execute('SELECT * FROM user_profile WHERE user_id = ?', (current_user.id,)).fetchone()
    
    if form.validate_on_submit():
        if profile:
            conn.execute('UPDATE user_profile SET age=?, income=?, category=?, education=?, occupation=?, location=? WHERE user_id=?',
                        (form.age.data, form.income.data, form.category.data, form.education.data, form.occupation.data, form.location.data, current_user.id))
        else:
            conn.execute('INSERT INTO user_profile (user_id, age, income, category, education, occupation, location) VALUES (?, ?, ?, ?, ?, ?, ?)',
                        (current_user.id, form.age.data, form.income.data, form.category.data, form.education.data, form.occupation.data, form.location.data))
        conn.commit()
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('dashboard'))
    
    if profile:
        form.age.data = profile['age']
        form.income.data = profile['income']
        form.category.data = profile['category']
        form.education.data = profile['education']
        form.occupation.data = profile['occupation']
        form.location.data = profile['location']
    
    # Get eligible schemes
    eligible_schemes = []
    if profile:
        schemes = conn.execute('SELECT * FROM schemes').fetchall()
        for scheme in schemes:
            if check_eligibility(profile, scheme):
                eligible_schemes.append(scheme)
    
    return render_template('dashboard.html', form=form, profile=profile, eligible_schemes=eligible_schemes)

@app.route('/schemes')
@login_required
def schemes():
    conn = get_db()
    all_schemes = conn.execute('SELECT * FROM schemes').fetchall()
    return render_template('schemes.html', schemes=all_schemes)

@app.route('/scheme/<int:scheme_id>')
@login_required
def scheme_details(scheme_id):
    conn = get_db()
    scheme = conn.execute('SELECT * FROM schemes WHERE id = ?', (scheme_id,)).fetchone()
    return render_template('scheme_details.html', scheme=scheme)

@app.route('/admin', methods=['GET', 'POST'])
@login_required
def admin():
    if current_user.role != 'admin':
        flash('Access denied.', 'error')
        return redirect(url_for('dashboard'))
    
    form = SchemeForm()
    if form.validate_on_submit():
        conn = get_db()
        conn.execute('INSERT INTO schemes (name, description, income_limit, category_required, education_required, occupation_required, benefits, application_link) VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
                    (form.name.data, form.description.data, form.income_limit.data, form.category_required.data, form.education_required.data, form.occupation_required.data, form.benefits.data, form.application_link.data))
        conn.commit()
        flash('Scheme added successfully!', 'success')
        return redirect(url_for('admin'))
    
    conn = get_db()
    all_schemes = conn.execute('SELECT * FROM schemes').fetchall()
    return render_template('admin.html', form=form, schemes=all_schemes)

@app.route('/delete_scheme/<int:scheme_id>', methods=['POST'])
@login_required
def delete_scheme(scheme_id):
    if current_user.role != 'admin':
        return jsonify({'error': 'Access denied'}), 403
    conn = get_db()
    conn.execute('DELETE FROM schemes WHERE id = ?', (scheme_id,))
    conn.commit()
    return jsonify({'success': True})

@app.route('/admin/users')
@login_required
def admin_users():
    if current_user.role != 'admin':
        flash('Access denied.', 'error')
        return redirect(url_for('dashboard'))
    
    conn = get_db()
    users = conn.execute('''
        SELECT u.id, u.name, u.email, u.role, p.age, p.income, p.category, p.education, p.occupation, p.location
        FROM users u
        LEFT JOIN user_profile p ON u.id = p.user_id
    ''').fetchall()
    return render_template('admin_users.html', users=users)

@app.route('/admin/user/<int:user_id>')
@login_required
def admin_user_details(user_id):
    if current_user.role != 'admin':
        flash('Access denied.', 'error')
        return redirect(url_for('dashboard'))
    
    conn = get_db()
    user = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
    profile = conn.execute('SELECT * FROM user_profile WHERE user_id = ?', (user_id,)).fetchone()
    
    # Get eligible schemes for this user
    eligible_schemes = []
    if profile:
        schemes = conn.execute('SELECT * FROM schemes').fetchall()
        for scheme in schemes:
            if check_eligibility(profile, scheme):
                eligible_schemes.append(scheme)
    
    return render_template('admin_user_details.html', user=user, profile=profile, eligible_schemes=eligible_schemes)

@app.route('/admin/delete_user/<int:user_id>', methods=['POST'])
@login_required
def delete_user(user_id):
    if current_user.role != 'admin':
        return jsonify({'error': 'Access denied'}), 403
    
    if user_id == current_user.id:
        return jsonify({'error': 'Cannot delete your own account'}), 400
    
    conn = get_db()
    conn.execute('DELETE FROM user_profile WHERE user_id = ?', (user_id,))
    conn.execute('DELETE FROM users WHERE id = ?', (user_id,))
    conn.commit()
    return jsonify({'success': True})

@app.route('/admin/database')
@login_required
def admin_database():
    if current_user.role != 'admin':
        flash('Access denied.', 'error')
        return redirect(url_for('dashboard'))
    
    conn = get_db()
    users_count = conn.execute('SELECT COUNT(*) as count FROM users').fetchone()['count']
    profiles_count = conn.execute('SELECT COUNT(*) as count FROM user_profile').fetchone()['count']
    schemes_count = conn.execute('SELECT COUNT(*) as count FROM schemes').fetchone()['count']
    
    # Get all data
    users = conn.execute('SELECT * FROM users').fetchall()
    profiles = conn.execute('SELECT * FROM user_profile').fetchall()
    schemes = conn.execute('SELECT * FROM schemes').fetchall()
    
    return render_template('admin_database.html', 
                         users_count=users_count, 
                         profiles_count=profiles_count, 
                         schemes_count=schemes_count,
                         users=users, 
                         profiles=profiles, 
                         schemes=schemes)

if __name__ == '__main__':
    init_db()
    app.run(debug=True)