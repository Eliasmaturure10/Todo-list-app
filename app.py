from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os
from functools import wraps

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///todo_app.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
migrate = Migrate(app, db)

# User model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    todos = db.relationship('Todo', backref='user', lazy=True, cascade='all, delete-orphan')

# Todo model
class Todo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    completed = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    due_date = db.Column(db.DateTime)
    tags = db.Column(db.String(200))
    status = db.Column(db.String(50), default='Not Started')
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

# Create tables
with app.app_context():
    db.create_all()

# Helper function to check if user is logged in
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password_hash, password):
            session['user_id'] = user.id
            session['username'] = user.username
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password', 'error')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        
        # Check if user already exists
        if User.query.filter_by(username=username).first():
            flash('Username already exists', 'error')
            return render_template('register.html')
        
        if User.query.filter_by(email=email).first():
            flash('Email already exists', 'error')
            return render_template('register.html')
        
        # Create new user
        password_hash = generate_password_hash(password)
        new_user = User(username=username, email=email, password_hash=password_hash)
        
        db.session.add(new_user)
        db.session.commit()
        
        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out', 'info')
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    user_id = session['user_id']
    tag_filter = request.args.get('tag')
    
    if tag_filter:
        todos = Todo.query.filter_by(user_id=user_id, tags=tag_filter).order_by(Todo.created_at.desc()).all()
    else:
        todos = Todo.query.filter_by(user_id=user_id).order_by(Todo.created_at.desc()).all()
        
    return render_template('dashboard.html', todos=todos)

@app.route('/add_todo', methods=['POST'])
@login_required
def add_todo():
    title = request.form.get('title')
    description = request.form.get('description', '')
    due_date_str = request.form.get('due_date')
    tags = request.form.get('tags')
    user_id = session['user_id']

    if not title:
        flash('Title is required!', 'error')
        return redirect(url_for('dashboard'))

    due_date = datetime.strptime(due_date_str, '%Y-%m-%d') if due_date_str else None

    try:
        new_todo = Todo(
            title=title,
            description=description,
            due_date=due_date,
            tags=tags,
            user_id=user_id
        )
        db.session.add(new_todo)
        db.session.commit()
        flash('Todo added successfully!', 'success')
    except Exception as e:
        flash('Error adding todo. Please try again.', 'error')

    return redirect(url_for('dashboard'))

@app.route('/toggle_todo/<int:todo_id>')
@login_required
def toggle_todo(todo_id):
    todo = Todo.query.get_or_404(todo_id)
    
    # Make sure user owns this todo
    if todo.user_id != session['user_id']:
        flash('Unauthorized action', 'error')
        return redirect(url_for('dashboard'))
    
    todo.completed = not todo.completed
    db.session.commit()
    
    return redirect(url_for('dashboard'))

@app.route('/update_status/<int:todo_id>/<status>')
@login_required
def update_status(todo_id, status):
    todo = Todo.query.get_or_404(todo_id)

    if todo.user_id != session['user_id']:
        flash('Unauthorized action', 'error')
        return redirect(url_for('dashboard'))

    todo.status = status
    db.session.commit()

    return redirect(url_for('dashboard'))

@app.route('/delete_todo/<int:todo_id>')
@login_required
def delete_todo(todo_id):
    todo = Todo.query.get_or_404(todo_id)
    
    # Make sure user owns this todo
    if todo.user_id != session['user_id']:
        flash('Unauthorized action', 'error')
        return redirect(url_for('dashboard'))
    
    db.session.delete(todo)
    db.session.commit()
    
    flash('Todo deleted successfully!', 'success')
    return redirect(url_for('dashboard'))

@app.route('/api/todos')
@login_required
def api_todos():
    user_id = session['user_id']
    todos = Todo.query.filter_by(user_id=user_id).all()
    
    events = []
    for todo in todos:
        if todo.due_date:
            events.append({
                'title': todo.title,
                'start': todo.due_date.isoformat(),
                'allDay': True
            })
            
    return jsonify(events)

if __name__ == '__main__':
    app.run(debug=True)