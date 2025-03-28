from flask import Flask, render_template, redirect, url_for, session, request, flash
from flask_mysqldb import MySQL
from werkzeug.security import generate_password_hash, check_password_hash
import config
import os
from werkzeug.utils import secure_filename
from flask import send_from_directory
import requests
import time 

app = Flask(__name__)
app.secret_key = 'your-secret-key-123'  # Change this for production!

# Database configuration
app.config['MYSQL_HOST'] = config.Config.MYSQL_HOST
app.config['MYSQL_USER'] = config.Config.MYSQL_USER
app.config['MYSQL_PASSWORD'] = config.Config.MYSQL_PASSWORD
app.config['MYSQL_DB'] = config.Config.MYSQL_DB
app.config['MYSQL_SSL_MODE'] = config.Config.MYSQL_SSL_MODE

mysql = MySQL(app)


def create_tables():
    try:
        with app.app_context():
            cur = mysql.connection.cursor()
            
            # Users table (already exists)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    email VARCHAR(255) NOT NULL UNIQUE,
                    password_hash VARCHAR(255) NOT NULL,
                    first_name VARCHAR(100) NOT NULL,
                    last_name VARCHAR(100) NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            mysql.connection.commit()
            cur.close()
    except Exception as e:
        print(f"Error creating tables: {e}")


@app.route('/')
def home():
    if 'user_id' not in session:
        return redirect(url_for('signin'))
    return render_template('index.html')

@app.route('/signin', methods=['GET', 'POST'])
def signin():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        try:
            cur = mysql.connection.cursor()
            cur.execute("SELECT id, first_name, last_name, password_hash FROM users WHERE email = %s", (email,))
            user = cur.fetchone()
            cur.close()
            
            if user and check_password_hash(user[3], password):
                session['user_id'] = user[0]
                session['user_name'] = f"{user[1]} {user[2]}"
                return redirect(url_for('home'))
            else:
                flash('Invalid email or password', 'error')
        except Exception as e:
            flash('Database error occurred', 'error')
            print(f"Database error: {e}")
    
    return render_template('signin.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        email = request.form['email']
        password = generate_password_hash(request.form['password'])
        
        try:
            cur = mysql.connection.cursor()
            cur.execute("""
                INSERT INTO users (first_name, last_name, email, password_hash)
                VALUES (%s, %s, %s, %s)
            """, (first_name, last_name, email, password))
            mysql.connection.commit()
            cur.close()
            
            flash('Account created successfully! Please sign in.', 'success')
            return redirect(url_for('signin'))
        except Exception as e:
            mysql.connection.rollback()
            flash('Email already exists or database error', 'error')
            print(f"Database error: {e}")
    
    return render_template('signup.html')

@app.route('/signout')
def signout():
    session.clear()
    flash('You have been signed out', 'info')
    return redirect(url_for('signin'))
