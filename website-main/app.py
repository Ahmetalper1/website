from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.utils import secure_filename
import os
import sqlite3
from functools import wraps

app = Flask(__name__)
app.secret_key = 'supersecretkey'
app.config['UPLOAD_FOLDER'] = 'static/uploads'

DATABASE = 'database.db'

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    with conn:
        conn.execute('CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE, password TEXT, age INTEGER, profile_pic TEXT)')
        conn.execute('CREATE TABLE IF NOT EXISTS notes (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, note TEXT, FOREIGN KEY(user_id) REFERENCES users(id))')
        conn.execute('CREATE TABLE IF NOT EXISTS tasks (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, task TEXT, is_completed BOOLEAN, FOREIGN KEY(user_id) REFERENCES users(id))')
    conn.close()

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = get_db()
        user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
        if user and user['password'] == password:
            session['username'] = username
            return redirect(url_for('home'))
        flash("Invalid credentials. Please try again.")
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = get_db()
        if conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone():
            flash("User already exists. Please login.")
        else:
            conn.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, password))
            conn.commit()
            session['username'] = username
            return redirect(url_for('home'))
    return render_template('register.html')

@app.route('/home', methods=['GET', 'POST'])
@login_required
def home():
    conn = get_db()
    user = conn.execute('SELECT * FROM users WHERE username = ?', (session['username'],)).fetchone()
    notes = conn.execute('SELECT * FROM notes WHERE user_id = ?', (user['id'],)).fetchall()
    tasks = conn.execute('SELECT * FROM tasks WHERE user_id = ?', (user['id'],)).fetchall()

    if request.method == 'POST':
        if 'note' in request.form:
            note = request.form['note']
            conn.execute('INSERT INTO notes (user_id, note) VALUES (?, ?)', (user['id'], note))
            conn.commit()
            flash("Note added successfully.")
            return redirect(url_for('home'))
        elif 'task' in request.form:
            task = request.form['task']
            conn.execute('INSERT INTO tasks (user_id, task, is_completed) VALUES (?, ?, ?)', (user['id'], task, False))
            conn.commit()
            flash("Task added successfully.")
            return redirect(url_for('home'))

    return render_template('home.html', username=session['username'], notes=notes, tasks=tasks)

@app.route('/complete_task/<int:task_id>')
@login_required
def complete_task(task_id):
    conn = get_db()
    conn.execute('UPDATE tasks SET is_completed = ? WHERE id = ?', (True, task_id))
    conn.commit()
    flash("Task marked as completed.")
    return redirect(url_for('home'))

@app.route('/delete_task/<int:task_id>')
@login_required
def delete_task(task_id):
    conn = get_db()
    conn.execute('DELETE FROM tasks WHERE id = ?', (task_id,))
    conn.commit()
    flash("Task deleted.")
    return redirect(url_for('home'))

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    conn = get_db()
    user = conn.execute('SELECT * FROM users WHERE username = ?', (session['username'],)).fetchone()

    if request.method == 'POST':
        age = request.form['age']
        if request.form.get('update_age'):
            conn.execute('UPDATE users SET age = ? WHERE username = ?', (age, session['username']))
            conn.commit()
            flash("Age updated successfully.")
            return redirect(url_for('profile'))
        if 'profile_pic' in request.files:
            profile_pic = request.files['profile_pic']
            if profile_pic.filename != '':
                filename = secure_filename(profile_pic.filename)
                profile_pic.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                conn.execute('UPDATE users SET age = ?, profile_pic = ? WHERE username = ?', (age, filename, session['username']))
            else:
                conn.execute('UPDATE users SET age = ? WHERE username = ?', (age, session['username']))
        else:
            conn.execute('UPDATE users SET age = ? WHERE username = ?', (age, session['username']))
        conn.commit()
        flash("Profile updated successfully.")
        return redirect(url_for('profile'))

    return render_template('profile.html', user=user)

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))

if __name__ == "__main__":
    init_db()
    app.run(debug=True)
