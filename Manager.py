from flask import Flask, render_template, request, jsonify, redirect, url_for, session
import mysql.connector
from mysql.connector import Error
from datetime import datetime
import os
import bcrypt

app = Flask(__name__)
app.secret_key = 'your_very_secure_secret_key_here'  # Change this for production

# Database connection function
def get_db_connection():
    try:
        connection = mysql.connector.connect(
            host='localhost',
            user='abel tiruneh',
            password='Ab1996@2468',
            database='Time_Internation_BANK'
        )
        return connection
    except Error as e:
        print(f"Error connecting to MySQL: {e}")
        return None

# Password hashing functions
def hash_password(password):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

def check_password(hashed_password, user_password):
    try:
        if isinstance(hashed_password, str):
            hashed_password = hashed_password.encode('utf-8')
        return bcrypt.checkpw(user_password.encode('utf-8'), hashed_password)
    except Exception as e:
        print(f"Password check error: {e}")
        return False

@app.route('/')
def home():
    session.clear()
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login():
    try:
        if not request.is_json:
            return jsonify({'error': 'Request must be JSON'}), 400

        data = request.get_json()
        username = data.get('username', '').strip()
        password = data.get('password', '').strip()

        if not username or not password:
            return jsonify({'error': 'Username and password required'}), 400

        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Database unavailable'}), 503

        with conn.cursor(dictionary=True) as cursor:
            cursor.execute("""
                SELECT e.*, d.dep_name 
                FROM employee e
                JOIN department d ON e.dep_id = d.dep_id
                WHERE username = %s
                LIMIT 1
            """, (username,))
            user = cursor.fetchone()

        if not user:
            return jsonify({'error': 'Invalid credentials'}), 401

        if not check_password(user['passwords'], password):
            return jsonify({'error': 'Invalid credentials'}), 401

        session.update({
            'user_id': user['emp_id'],
            'emp_id': user['emp_id'],
            'username': user['username'],
            'job_title': user['job_title'],
            'name': user['emp_name'],
            'department': user['dep_name']
        })

        return jsonify({
            'success': True,
            'job_title': user['job_title'],
            'department': user['dep_name']
        })

    except Exception as e:
        print(f"Login error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/manager-dashboard')
def manager_dashboard():
    if 'user_id' not in session:
        return redirect(url_for('home'))
    
    job_title = session.get('job_title', '').lower()
    department = session.get('department', '').lower()
    
    if 'manager' not in job_title and 'management' not in department:
        return redirect(url_for('home'))
    
    try:
        conn = get_db_connection()
        if conn is None:
            return "Database connection failed", 500
            
        cursor = conn.cursor(dictionary=True)
        
        # Get manager info
        cursor.execute("""
            SELECT e.*, d.dep_name
            FROM employee e
            JOIN department d ON e.dep_id = d.dep_id
            WHERE e.emp_id = %s
        """, (session['user_id'],))
        manager_info = cursor.fetchone()
        
        if not manager_info:
            return redirect(url_for('home'))
        
        # Get total employees count
        cursor.execute("SELECT COUNT(*) as total_employees FROM employee")
        total_employees = cursor.fetchone()['total_employees']
        
        # Get total accounts count
        cursor.execute("SELECT COUNT(*) as total_accounts FROM accounts")
        total_accounts = cursor.fetchone()['total_accounts']
        
        # Get total balance
        cursor.execute("SELECT SUM(balance) as total_balance FROM accounts")
        total_balance_result = cursor.fetchone()
        total_balance = total_balance_result['total_balance'] if total_balance_result['total_balance'] is not None else 0
        
        # Get recent employee actions (hiring/firing)
        cursor.execute("""
            SELECT ea.*, e.emp_name 
            FROM employee_actions ea
            JOIN employee e ON ea.emp_id = e.emp_id
            ORDER BY action_date DESC
            LIMIT 5
        """)
        recent_actions = cursor.fetchall()
        
        # Get employee list
        cursor.execute("""
            SELECT e.emp_id, e.emp_name, e.job_title, e.salary, d.dep_name
            FROM employee e
            JOIN department d ON e.dep_id = d.dep_id
            ORDER BY e.emp_name
        """)
        employee_list = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return render_template('Manager.html', 
                            manager_info=manager_info,
                            total_employees=total_employees,
                            total_accounts=total_accounts,
                            total_balance=total_balance,
                            recent_actions=recent_actions,
                            employee_list=employee_list,
                            session=session)
        
    except Error as e:
        print(f"Database error: {e}")
        return "An error occurred", 500

@app.route('/update-credentials', methods=['POST'])
def update_credentials():
    if 'user_id' not in session:
        return jsonify({'error': 'Not logged in'}), 401
        
    try:
        data = request.get_json()
        current_username = data.get('current_username')
        new_username = data.get('new_username')
        current_password = data.get('current_password')
        new_password = data.get('new_password')
        
        if not all([current_username, new_username, current_password, new_password]):
            return jsonify({'error': 'All fields are required'}), 400
            
        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Database unavailable'}), 503
            
        # Verify current credentials
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT passwords FROM employee WHERE emp_id = %s", (session['user_id'],))
        user = cursor.fetchone()
        
        if not user or not check_password(user['passwords'], current_password):
            return jsonify({'error': 'Current password is incorrect'}), 401
            
        # Hash new password
        hashed_password = hash_password(new_password)
        
        # Update credentials
        cursor.execute("""
            UPDATE employee 
            SET username = %s, passwords = %s 
            WHERE emp_id = %s
        """, (new_username, hashed_password, session['user_id']))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        # Update session
        session['username'] = new_username
        
        return jsonify({'success': True, 'message': 'Credentials updated successfully'})
        
    except Exception as e:
        print(f"Update credentials error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8000, debug=True)
