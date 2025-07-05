from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import os
from datetime import datetime

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend communication

# File to store todos (in a real app, you'd use a database)
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
    """Get all todos"""
    todos = load_todos()
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
    
    new_todo = {
        'id': new_id,
        'text': data['text'],
        'completed': False,
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

@app.route('/api/todos/clear-completed', methods=['DELETE'])
def clear_completed():
    """Clear all completed todos"""
    todos = load_todos()
    todos = [t for t in todos if not t['completed']]
    save_todos(todos)
    
    return jsonify({'message': 'Completed todos cleared'})

@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Get todo statistics"""
    todos = load_todos()
    total = len(todos)
    completed = len([t for t in todos if t['completed']])
    pending = total - completed
    
    return jsonify({
        'total': total,
        'completed': completed,
        'pending': pending
    })

if __name__ == '__main__':
    app.run(debug=True, port=5000)