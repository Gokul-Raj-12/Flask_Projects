from flask import Flask, render_template, request, redirect, url_for, jsonify,flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import logout_user, login_required
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from flask_migrate import Migrate
import os
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
migrate = Migrate(app, db)


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    phone = db.Column(db.String(20))
    address = db.Column(db.String(255))
    tasks = db.relationship('Task', back_populates='assigned_to')

class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    datetime = db.Column(db.DateTime, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    assigned_to = db.relationship('User', back_populates='tasks')
    status = db.Column(db.String(20), default='Pending')

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form['username']).first()
        if user and check_password_hash(user.password, request.form['password']):
            login_user(user)
            return redirect(url_for('dashboard'))
    return render_template('login.html')

@app.route('/logout', methods=['GET', 'POST'])
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        hashed_password = generate_password_hash(request.form['password'])
        new_user = User(username=request.form['username'], 
                        email=request.form['email'],
                        password=hashed_password,
                        phone=request.form['phone'],
                        address=request.form['address'])
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/dashboard')
@login_required
def dashboard():
    tasks = Task.query.filter_by(user_id=current_user.id).all()
    return render_template('dashboard.html', tasks=tasks)

@app.route('/add_task', methods=['GET', 'POST'])
@login_required
def add_task():
    if request.method == 'POST':
        try:
            name = request.form['name']
            datetime_str = request.form['datetime']
            assigned_to = request.form['assigned_to']
            
            task_datetime = datetime.strptime(datetime_str, '%Y-%m-%dT%H:%M')
            
            new_task = Task(name=name,
                            datetime=task_datetime,
                            user_id=int(assigned_to),
                            status='Pending')
            
            db.session.add(new_task)
            db.session.commit()
            flash('Task added successfully', 'success')
            return redirect(url_for('dashboard'))
        except KeyError as e:
            flash(f'Missing required field: {str(e)}', 'error')
        except ValueError:
            flash('Invalid date format', 'error')
        except Exception as e:
            flash(f'An error occurred: {str(e)}', 'error')
        
        return redirect(url_for('add_task'))

    users = User.query.all()
    return render_template('add_task.html', users=users)
# API routes
@app.route('/api/login', methods=['POST'])
def api_login():
    data = request.json
    user = User.query.filter_by(username=data['username']).first()
    if user and check_password_hash(user.password, data['password']):
        return jsonify({'message': 'Login successful'}), 200
    return jsonify({'message': 'Invalid credentials'}), 401

@app.route('/api/register', methods=['POST'])
def api_register():
    data = request.json
    hashed_password = generate_password_hash(data['password'])
    new_user = User(username=data['username'], 
                    email=data['email'],
                    password=hashed_password,
                    phone=data['phone'],
                    address=data['address'])
    db.session.add(new_user)
    db.session.commit()
    return jsonify({'message': 'User registered successfully'}), 201

@app.route('/api/add_task', methods=['POST'])
@login_required
def api_add_task():
    data = request.json
    new_task = Task(name=data['name'],
                    datetime=data['datetime'],
                    user_id=data['assigned_to'])
    db.session.add(new_task)
    db.session.commit()
    return jsonify({'message': 'Task added successfully'}), 201

@app.route('/api/view_tasks')
@login_required
def api_view_tasks():
    tasks = Task.query.filter_by(user_id=current_user.id).all()
    return jsonify([{'id': task.id, 'name': task.name, 'datetime': task.datetime} for task in tasks])

@app.route('/update_task_status/<int:task_id>', methods=['POST'])
@login_required
def update_task_status(task_id):
    task = Task.query.get_or_404(task_id)
    if task.user_id == current_user.id:
        if task.status == 'Completed':
            task.status = 'Pending'
            flash('Task marked as pending', 'success')
        else:
            task.status = 'Completed'
            flash('Task marked as completed', 'success')
        db.session.commit()
    else:
        flash('You are not authorized to update this task', 'error')
    return redirect(url_for('dashboard'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
    
    
    
