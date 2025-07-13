from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import os
from datetime import datetime, date, timedelta
import calendar

app = Flask(__name__)
CORS(app)

# File to store todos
TODOS_FILE = 'todos.json'

def load_todos():
    """Load todos from file"""
    if os.path.exists(TODOS_FILE):
        with open(TODOS_FILE, 'r') as f:
            return json.load(f)
    return []

def save_todos(todos):
    """Save todos to file"""
    with open(TODOS_FILE, 'w') as f:
        json.dump(todos, f, indent=2)

@app.route('/api/todos', methods=['GET'])
def get_todos():
    """Get all todos, optionally filtered by date"""
    todos = load_todos()
    date_filter = request.args.get('date')
    
    if date_filter:
        # Filter todos by specific date
        filtered_todos = [todo for todo in todos if todo.get('date') == date_filter]
        return jsonify(filtered_todos)
    
    return jsonify(todos)

@app.route('/api/todos', methods=['POST'])
def create_todo():
    """Create a new todo"""
    data = request.get_json()
    
    if not data or 'text' not in data:
        return jsonify({'error': 'Todo text is required'}), 400
    
    todos = load_todos()
    
    # Generate new ID
    new_id = max([todo['id'] for todo in todos], default=0) + 1
    
    # Use provided date or default to today
    todo_date = data.get('date', date.today().isoformat())
    
    new_todo = {
        'id': new_id,
        'text': data['text'],
        'completed': False,
        'date': todo_date,
        'time': data.get('time', ''),
        'created_at': datetime.now().isoformat()
    }
    
    todos.append(new_todo)
    save_todos(todos)
    
    return jsonify(new_todo), 201

@app.route('/api/todos/<int:todo_id>', methods=['PUT'])
def update_todo(todo_id):
    """Update a todo"""
    data = request.get_json()
    todos = load_todos()
    
    todo = next((t for t in todos if t['id'] == todo_id), None)
    if not todo:
        return jsonify({'error': 'Todo not found'}), 404
    
    # Update fields if provided
    if 'text' in data:
        todo['text'] = data['text']
    if 'completed' in data:
        todo['completed'] = data['completed']
    if 'date' in data:
        todo['date'] = data['date']
    if 'time' in data:
        todo['time'] = data['time']
    
    todo['updated_at'] = datetime.now().isoformat()
    save_todos(todos)
    
    return jsonify(todo)

@app.route('/api/todos/<int:todo_id>', methods=['DELETE'])
def delete_todo(todo_id):
    """Delete a todo"""
    todos = load_todos()
    
    todo = next((t for t in todos if t['id'] == todo_id), None)
    if not todo:
        return jsonify({'error': 'Todo not found'}), 404
    
    todos = [t for t in todos if t['id'] != todo_id]
    save_todos(todos)
    
    return jsonify({'message': 'Todo deleted successfully'})

@app.route('/api/calendar/<int:year>/<int:month>', methods=['GET'])
def get_calendar(year, month):
    """Get calendar data for a specific month"""
    try:
        # Get calendar for the month
        cal = calendar.monthcalendar(year, month)
        
        # Get todos for this month
        todos = load_todos()
        
        # Group todos by date
        todos_by_date = {}
        for todo in todos:
            todo_date = todo.get('date', '')
            if todo_date.startswith(f"{year:04d}-{month:02d}"):
                if todo_date not in todos_by_date:
                    todos_by_date[todo_date] = []
                todos_by_date[todo_date].append(todo)
        
        return jsonify({
            'year': year,
            'month': month,
            'month_name': calendar.month_name[month],
            'calendar': cal,
            'todos_by_date': todos_by_date
        })
    
    except ValueError:
        return jsonify({'error': 'Invalid year or month'}), 400

@app.route('/api/today', methods=['GET'])
def get_today():
    """Get today's date and todos"""
    today = date.today()
    todos = load_todos()
    
    # Filter todos for today
    today_todos = [todo for todo in todos if todo.get('date') == today.isoformat()]
    
    return jsonify({
        'date': today.isoformat(),
        'day_name': today.strftime('%A'),
        'formatted_date': today.strftime('%B %d, %Y'),
        'todos': today_todos
    })

@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Get todo statistics"""
    todos = load_todos()
    today = date.today().isoformat()
    
    total = len(todos)
    completed = len([t for t in todos if t['completed']])
    pending = total - completed
    
    # Today's stats
    today_todos = [t for t in todos if t.get('date') == today]
    today_total = len(today_todos)
    today_completed = len([t for t in today_todos if t['completed']])
    today_pending = today_total - today_completed
    
    return jsonify({
        'total': total,
        'completed': completed,
        'pending': pending,
        'today': {
            'total': today_total,
            'completed': today_completed,
            'pending': today_pending
        }
    })

if __name__ == '__main__':
    app.run(debug=True, port=5000)