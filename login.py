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

        # Create session
        session.update({
            'user_id': user['emp_id'],
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
# Dashboard routes
@app.route('/hr-dashboard')
def hr_dashboard():
    if 'user_id' not in session:
        return redirect(url_for('home'))
    
    job_title = session.get('job_title', '').lower()
    department = session.get('department', '').lower()
    
    if 'hr' not in job_title and 'hr' not in department:
        return redirect(url_for('home'))
    
    try:
        conn = get_db_connection()
        if conn is None:
            return "Database connection failed", 500
            
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT d.dep_name, COUNT(e.emp_id) as employee_count
            FROM department d
            LEFT JOIN employee e ON d.dep_id = e.dep_id
            GROUP BY d.dep_name
        """)
        dept_counts = cursor.fetchall()
        
        cursor.execute("""
            SELECT ea.*, e.emp_name 
            FROM employee_actions ea
            JOIN employee e ON ea.emp_id = e.emp_id
            ORDER BY action_date DESC
            LIMIT 5
        """)
        recent_actions = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        user_info = {
            'name': session.get('name'),
            'emp_id': session.get('emp_id'),
            'role': session.get('job_title'),
            'department': session.get('department')
        }
        
        return render_template('HR_Dashboard.html', 
                            user=user_info,
                            dept_counts=dept_counts,
                            recent_actions=recent_actions)
        
    except Error as e:
        return str(e), 500

@app.route('/accountant-dashboard')
def accountant_dashboard():
    if 'user_id' not in session:
        return redirect(url_for('home'))
    
    job_title = session.get('job_title', '').lower()
    department = session.get('department', '').lower()
    
    if 'accountant' not in job_title and 'finance' not in department:
        return redirect(url_for('home'))
    
    try:
        conn = get_db_connection()
        if conn is None:
            return "Database connection failed", 500
            
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT 
                COUNT(*) as total_accounts,
                SUM(balance) as total_balance,
                AVG(balance) as avg_balance,
                MIN(balance) as min_balance,
                MAX(balance) as max_balance
            FROM accounts
            WHERE account_status = 'Active'
        """)
        account_summary = cursor.fetchone()
        
        cursor.execute("""
            SELECT t.*, a.cust_id, c.cust_name
            FROM transactions t
            JOIN accounts a ON t.account_no = a.account_no
            JOIN customer c ON a.cust_id = c.cust_id
            WHERE t.transaction_type IN ('Deposit', 'Withdrawal')
            ORDER BY transaction_date DESC
            LIMIT 5
        """)
        recent_transactions = cursor.fetchall()
        
        cursor.execute("""
            SELECT t.*, a.cust_id, c.cust_name
            FROM transactions t
            JOIN accounts a ON t.account_no = a.account_no
            JOIN customer c ON a.cust_id = c.cust_id
            WHERE t.transaction_status = 'Pending'
            ORDER BY transaction_date DESC
        """)
        pending_transactions = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        user_info = {
            'name': session.get('name'),
            'emp_id': session.get('emp_id'),
            'role': session.get('job_title'),
            'department': session.get('department')
        }
        
        return render_template('accountant_dashboard.html', 
                            user=user_info,
                            account_summary=account_summary,
                            recent_transactions=recent_transactions,
                            pending_transactions=pending_transactions)
        
    except Error as e:
        return str(e), 500

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
        
        cursor.execute("""
            SELECT * FROM notifications
            WHERE emp_id = %s
            ORDER BY notification_date DESC
            LIMIT 5
        """, (session['user_id'],))
        notifications = cursor.fetchall()
        
        cursor.execute("""
            SELECT e.*, d.dep_name, b.branch_name
            FROM employee e
            JOIN department d ON e.dep_id = d.dep_id
            JOIN employee_branch eb ON e.emp_id = eb.emp_id
            JOIN branch b ON eb.branch_id = b.branch_id
            WHERE e.emp_id = %s
        """, (session['user_id'],))
        employee_info = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        user_info = {
            'name': session.get('name'),
            'emp_id': session.get('emp_id'),
            'role': session.get('job_title'),
            'department': session.get('department')
        }
        
        return render_template('Manager.html', 
                            user=user_info,
                            notifications=notifications,
                            employee_info=employee_info)
        
    except Error as e:
        return str(e), 500

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8000, debug=True)