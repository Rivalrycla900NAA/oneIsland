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

# Configure upload folder (add to Config class)
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/upload_picture', methods=['POST'])
def upload_picture():
    if 'user_id' not in session:
        return redirect(url_for('signin'))
    
    if 'profile_pic' not in request.files:
        flash('No file selected', 'error')
        return redirect(url_for('profile'))
    
    file = request.files['profile_pic']
    if file.filename == '':
        flash('No file selected', 'error')
        return redirect(url_for('profile'))
    
    if file and allowed_file(file.filename):
        try:
            # Create upload folder if not exists
            os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
            
            # Generate secure filename
            ext = file.filename.rsplit('.', 1)[1].lower()
            filename = f"user_{session['user_id']}.{ext}"
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            
            # Save file
            file.save(filepath)
            
            # Update database - store relative path from static folder
            db_path = f"uploads/{filename}"
            cur = mysql.connection.cursor()
            cur.execute("""
                INSERT INTO user_profiles (user_id, profile_picture)
                VALUES (%s, %s)
                ON DUPLICATE KEY UPDATE profile_picture = %s
            """, (session['user_id'], db_path, db_path))
            mysql.connection.commit()
            
            flash('Profile picture updated!', 'success')
        except Exception as e:
            mysql.connection.rollback()
            print(f"Upload error: {e}")
            flash('Error uploading picture', 'error')
        finally:
            if 'cur' in locals():
                cur.close()
    else:
        flash('Allowed file types: png, jpg, jpeg, gif', 'error')
    
    return redirect(url_for('profile'))

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/background_check')
def background_check():
    if 'user_id' not in session:
        return redirect(url_for('signin'))
    
    # Check if already verified
    cur = mysql.connection.cursor()
    cur.execute("SELECT is_verified FROM user_profiles WHERE user_id = %s", (session['user_id'],))
    profile = cur.fetchone()
    
    if profile and profile[0]:
        flash('You are already verified', 'info')
        return redirect(url_for('profile'))
    
    # Render background check page
    return render_template('background_check.html')

# @app.route('/submit_background_check', methods=['POST'])
# def submit_background_check():
#     if 'user_id' not in session:
#         return redirect(url_for('signin'))
    
#     try:
#         # Get user data
#         cur = mysql.connection.cursor()
#         cur.execute("SELECT first_name, last_name FROM users WHERE id = %s", (session['user_id'],))
#         user_data = cur.fetchone()
        
#         if not user_data:
#             flash('User not found', 'error')
#             return redirect(url_for('profile'))
        
#         # Prepare API request
#         payload = {
#             "firstname": user_data[0],
#             "lastname": user_data[1],
#             "address": request.form.get('address', ''),
#             "contact": request.form.get('contact', ''),
#             "employment_status": request.form.get('employment_status', ''),
#             "income_range": request.form.get('income_range', ''),
#             "housing_type": request.form.get('housing_type', ''),
#             "investment_accounts": {
#                 "stocks": float(request.form.get('stocks', 0)),
#                 "crypto": float(request.form.get('crypto', 0))
#             },
#             "gross_income_last_year": float(request.form.get('gross_income', 0)),
#             "reference": request.form.get('reference', '')
#         }
        
#         # Call AWS Lambda API
#         response = requests.post(
#             'https://qj4tudodmb.execute-api.us-east-1.amazonaws.com/BackgroundCheckFunction',
#             json=payload,
#             headers={'Content-Type': 'application/json'}
#         )
        
#         if response.status_code == 200:
#             result = response.json()
#             is_eligible = result.get('eligible', False)
#             score = result.get('score', 0)
            
#             # Update database
#             cur.execute("""
#                 INSERT INTO background_checks (user_id, status, score)
#                 VALUES (%s, %s, %s)
#                 ON DUPLICATE KEY UPDATE 
#                     status = VALUES(status),
#                     score = VALUES(score),
#                     reviewed_at = CURRENT_TIMESTAMP
#             """, (
#                 session['user_id'],
#                 'approved' if is_eligible else 'rejected',
#                 score
#             ))
            
#             # Update user verification status
#             cur.execute("""
#                 UPDATE user_profiles
#                 SET is_verified = %s
#                 WHERE user_id = %s
#             """, (is_eligible, session['user_id']))
            
#             mysql.connection.commit()
            
#             if is_eligible:
#                 flash('Background check approved! You are now verified.', 'success')
#             else:
#                 flash(f'Background check completed (Score: {score}). Not necessarily in financial need.', 'warning')
#         else:
#             flash('Error processing background check', 'error')
        
#     except Exception as e:
#         mysql.connection.rollback()
#         print(f"Background check error: {e}")
#         flash('Error submitting background check', 'error')
#     finally:
#         if 'cur' in locals():
#             cur.close()
    
#     return redirect(url_for('profile'))

@app.route('/submit_background_check', methods=['POST'])
def submit_background_check():
    if 'user_id' not in session:
        print("ERROR: No user_id in session")
        flash('Session expired', 'error')
        return redirect(url_for('signin'))

    try:
        # Debug: Print all form data
        print(f"\n===== FORM DATA RECEIVED =====")
        for key, value in request.form.items():
            print(f"{key}: {value}")
        
        # Get user data
        cur = mysql.connection.cursor()
        cur.execute("SELECT first_name, last_name FROM users WHERE id = %s", (session['user_id'],))
        user_data = cur.fetchone()
        
        if not user_data:
            print("ERROR: User not found in database")
            flash('User not found', 'error')
            return redirect(url_for('profile'))

        # Prepare API payload
        payload = {
            "firstname": user_data[0],
            "lastname": user_data[1],
            "address": request.form.get('address', ''),
            "contact": request.form.get('contact', ''),
            "employment_status": request.form.get('employment_status', ''),
            "income_range": request.form.get('income_range', ''),
            "housing_type": request.form.get('housing_type', ''),
            "investment_accounts": {
                "stocks": float(request.form.get('stocks', 0)),
                "crypto": float(request.form.get('crypto', 0))
            },
            "gross_income_last_year": float(request.form.get('gross_income', 0)),
            "reference": request.form.get('reference', '')
        }

        print(f"\n===== API PAYLOAD =====")
        print(payload)

        # Call AWS Lambda API
        try:
            print("\n===== CALLING BACKGROUND CHECK API =====")
            response = requests.post(
                'https://qj4tudodmb.execute-api.us-east-1.amazonaws.com/BackgroundCheckFunction',
                json=payload,
                headers={'Content-Type': 'application/json'},
                timeout=10  # 10 second timeout
            )
            print(f"API Response Status: {response.status_code}")
            print(f"API Response Body: {response.text}")

            if response.status_code != 200:
                print(f"API Error: {response.status_code} - {response.text}")
                flash('Background check service unavailable', 'error')
                return redirect(url_for('profile'))

            result = response.json()
            print(f"API Result: {result}")

            is_eligible = result.get('eligible', False)
            score = result.get('score', 0)

            # Update database
            cur.execute("""
                INSERT INTO background_checks (user_id, status, score)
                VALUES (%s, %s, %s)
                ON DUPLICATE KEY UPDATE 
                    status = VALUES(status),
                    score = VALUES(score),
                    reviewed_at = CURRENT_TIMESTAMP
            """, (
                session['user_id'],
                'approved' if is_eligible else 'rejected',
                score
            ))

            # Update user verification status
            cur.execute("""
                UPDATE user_profiles
                SET is_verified = %s
                WHERE user_id = %s
            """, (is_eligible, session['user_id']))

            mysql.connection.commit()

            if is_eligible:
                flash('Background check approved! You are now verified.', 'success')
            else:
                flash(f'Background check completed (Score: {score}). Not necessarily in financial need.', 'warning')

        except requests.exceptions.RequestException as api_error:
            print(f"\n===== API CALL FAILED =====")
            print(f"Error Type: {type(api_error)}")
            print(f"Error Details: {str(api_error)}")
            flash('Error connecting to background check service', 'error')
            mysql.connection.rollback()
            
        except ValueError as json_error:
            print(f"\n===== INVALID API RESPONSE =====")
            print(f"Response Content: {response.text}")
            print(f"JSON Error: {str(json_error)}")
            flash('Invalid response from background check service', 'error')
            mysql.connection.rollback()

    except Exception as e:
        print(f"\n===== SERVER ERROR =====")
        print(f"Error Type: {type(e)}")
        print(f"Error Details: {str(e)}")
        import traceback
        traceback.print_exc()
        flash('Error processing background check', 'error')
        mysql.connection.rollback()
        
    finally:
        if 'cur' in locals():
            cur.close()

    return redirect(url_for('profile'))


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
            
            # New tables for profile features
            cur.execute("""
                CREATE TABLE IF NOT EXISTS user_profiles (
                    user_id INT PRIMARY KEY,
                    profile_picture VARCHAR(255),
                    bio TEXT,
                    city VARCHAR(100),
                    country VARCHAR(100),
                    is_verified BOOLEAN DEFAULT FALSE,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            """)
            
            cur.execute("""
                CREATE TABLE IF NOT EXISTS donations (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id INT,
                    amount DECIMAL(10,2),
                    cause VARCHAR(255),
                    donation_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS background_checks (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id INT UNIQUE,
                    status ENUM('pending', 'approved', 'rejected') DEFAULT 'pending',
                    submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    reviewed_at TIMESTAMP NULL,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            """)
            
            cur.execute("""
                CREATE TABLE IF NOT EXISTS comments (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    item_id INT NOT NULL,
                    user_id INT NOT NULL,
                    content TEXT NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (item_id) REFERENCES item_donations(id),
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            """)
                        
            cur.execute("""
                CREATE TABLE IF NOT EXISTS user_badges (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id INT,
                    badge_name VARCHAR(100),
                    awarded_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            """)
            
            cur.execute("""
                CREATE TABLE IF NOT EXISTS item_donations (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id INT NOT NULL,
                    title VARCHAR(100) NOT NULL,
                    description TEXT NOT NULL,
                    image_path VARCHAR(255) NOT NULL,
                    location VARCHAR(100) NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    status ENUM('available', 'claimed', 'completed') DEFAULT 'available',
                    FOREIGN KEY (user_id) REFERENCES users(id)
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

# Protected routes
@app.route('/marketplace')
def marketplace():
    if 'user_id' not in session:
        return redirect(url_for('signin'))
    
    try:
        cur = mysql.connection.cursor()
        
        # Get all available donations
        cur.execute("""
            SELECT d.id, d.title, d.description, d.image_path, d.location, 
                d.created_at, u.first_name, u.last_name, u.id AS user_id, d.status
            FROM item_donations d
            JOIN users u ON d.user_id = u.id
            WHERE d.status = 'available'
            ORDER BY d.created_at DESC
        """)
        donations = cur.fetchall()
        
        return render_template('marketplace.html', donations=donations)
        
    except Exception as e:
        print(f"Error loading marketplace: {e}")
        flash('Error loading marketplace', 'error')
        return redirect(url_for('home'))
    finally:
        if 'cur' in locals():
            cur.close()



#=====================================================================
@app.route('/item/<int:item_id>', methods=['GET'])
def item_details(item_id):
    try:
        # Check if user_id is in the session
        if 'user_id' not in session:
            return redirect(url_for('signin'))  # Redirect to signin if not logged in

        # Fetch item details from the database
        cur = mysql.connection.cursor()
        cur.execute("""
            SELECT d.id AS item_id, d.user_id, d.title, d.description, d.image_path, 
                   d.location, d.created_at, d.status,
                   u.first_name, u.last_name
            FROM item_donations d
            JOIN users u ON d.user_id = u.id
            WHERE d.id = %s
        """, (item_id,))
        item = cur.fetchone()

        if not item:
            flash("Item not found!", "error")
            return redirect(url_for('marketplace'))

        # Create a dictionary from the tuple for easier access
        item_dict = {
            'id': item[0],  # item_id
            'user_id': item[1],
            'title': item[2],
            'description': item[3],
            'image_path': item[4],
            'location': item[5],
            'created_at': item[6],
            'status': item[7],
            'owner_first_name': item[8],
            'owner_last_name': item[9]
        }

        # Fetch comments for the item
        cur.execute("SELECT c.content, c.timestamp, u.first_name, u.last_name "
                    "FROM comments c JOIN users u ON c.user_id = u.id WHERE c.item_id = %s", (item_id,))
        comments = cur.fetchall()

        # Get the current user's ID from the session
        current_user_id = session['user_id']

        cur.close()
        
        # Pass the item_dict to the template
        return render_template('item_details.html', 
                               item=item_dict, 
                               comments=comments, 
                               current_user_id=current_user_id)

    except Exception as e:
        print(f"ERROR: {e}")
        flash("An error occurred while loading item details.", "error")
        return redirect(url_for('marketplace'))




@app.route('/item/<int:item_id>/comment', methods=['POST'])
def add_comment(item_id):
    # Check if user_id is in the session
    if 'user_id' not in session:
        flash("You need to be logged in to leave a comment.", "error")
        return redirect(url_for('signin'))

    content = request.form.get('content')
    user_id = session['user_id']

    # Save to DB
    try:
        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO comments (user_id, item_id, content) VALUES (%s, %s, %s)", (user_id, item_id, content))
        mysql.connection.commit()
        cur.close()
        flash("Comment added successfully!", "success")
    except Exception as e:
        print(f"ERROR: {e}")
        flash("An error occurred while adding your comment.", "error")

    return redirect(url_for('item_details', item_id=item_id))



@app.route('/user/<int:user_id>')
def user_profile(user_id):
    try:
        cur = mysql.connection.cursor()

        # Fetch user details
        cur.execute("SELECT first_name, last_name, email, created_at FROM users WHERE id = %s", (user_id,))
        user_data = cur.fetchone()

        if not user_data:
            flash("User not found!", "error")
            return redirect(url_for('home'))

        # Fetch profile details
        cur.execute("""
            SELECT profile_picture, bio, city, country, is_verified 
            FROM user_profiles 
            WHERE user_id = %s
        """, (user_id,))
        profile_data = cur.fetchone()

        profile_dict = {
            'profile_picture': profile_data[0] if profile_data else None,
            'bio': profile_data[1] if profile_data else "No bio available",
            'city': profile_data[2] if profile_data else "Unknown",
            'country': profile_data[3] if profile_data else "Unknown",
            'is_verified': bool(profile_data[4]) if profile_data else False
        }

        # Fetch donation stats
        cur.execute("SELECT COALESCE(SUM(amount), 0) FROM donations WHERE user_id = %s", (user_id,))
        donations_total = float(cur.fetchone()[0])

        # Fetch active listings
        cur.execute("SELECT id, title, image_path, status FROM item_donations WHERE user_id = %s;", (user_id,))
        active_listings = cur.fetchall()

        # Fetch total donations count
        cur.execute("SELECT COUNT(*) FROM item_donations WHERE user_id = %s", (user_id,))
        donations_count = cur.fetchone()[0]

        # Background check status
        background_check_status = None
        background_check_score = None
        try:
            cur.execute("SELECT status, score FROM background_checks WHERE user_id = %s", (user_id,))
            bg_check = cur.fetchone()
            if bg_check:
                background_check_status, background_check_score = bg_check
        except:
            pass  # Ignore if no background check data

        cur.close()

        return render_template('user_profile.html',
            user={
                'first_name': user_data[0],
                'last_name': user_data[1],
                'email': user_data[2],
                'created_at': user_data[3]
            },
            user_profile=profile_dict,
            donations_total=donations_total,
            followers_count=0,  # Placeholder for now
            following_count=0,  # Placeholder for now
            active_listings=active_listings,
            donations_count=donations_count,
            background_check_status=background_check_status,
            background_check_score=background_check_score
        )

    except Exception as e:
        print(f"ERROR: {e}")
        flash("An error occurred while loading the profile.", "error")
        return redirect(url_for('home'))



@app.route('/profile')
def profile():
    if 'user_id' not in session:
        print("DEBUG: No user_id in session - redirecting to signin")
        return redirect(url_for('signin'))
    
    try:
        print(f"DEBUG: Loading profile for user_id {session['user_id']}")
        cur = None
        cur = mysql.connection.cursor()
        
        # Get user data
        print("DEBUG: Fetching user data...")
        cur.execute("SELECT first_name, last_name, email FROM users WHERE id = %s", (session['user_id'],))
        user_data = cur.fetchone()
        
        if not user_data:
            print("DEBUG: No user found in database")
            flash('User not found', 'error')
            return redirect(url_for('home'))
        
        print(f"DEBUG: User data found: {user_data}")
        
        # Get profile data
        print("DEBUG: Fetching profile data...")
        cur.execute("""
            SELECT profile_picture, bio, city, country, is_verified 
            FROM user_profiles 
            WHERE user_id = %s
        """, (session['user_id'],))
        profile_data = cur.fetchone()
        
        profile_dict = {
            'profile_picture': profile_data[0] if profile_data else None,
            'bio': profile_data[1] if profile_data else None,
            'city': profile_data[2] if profile_data else None,
            'country': profile_data[3] if profile_data else None,
            'is_verified': bool(profile_data[4]) if profile_data else False
        }
        print(f"DEBUG: Profile data: {profile_dict}")
        
        # Get donation stats
        print("DEBUG: Fetching donation data...")
        cur.execute("SELECT COALESCE(SUM(amount), 0) FROM donations WHERE user_id = %s", (session['user_id'],))
        donations_total = float(cur.fetchone()[0])
        print(f"DEBUG: Donations total: {donations_total}")
        
        # Get active item donations
        print("DEBUG: Fetching active item donations...")
        cur.execute("""
            SELECT id, title, image_path, status 
            FROM item_donations 
            WHERE user_id = %s AND status = 'available'
            ORDER BY created_at DESC
            LIMIT 5
        """, (session['user_id'],))
        active_donations = cur.fetchall()
        print(f"DEBUG: Found {len(active_donations)} active donations")
        
        # Connect to the database
        cur = mysql.connection.cursor()

        # Count the number of entries in item_donations for the logged-in user
        cur.execute("SELECT COUNT(*) FROM item_donations WHERE user_id = %s", (session['user_id'],))
        donations_count = cur.fetchone()[0]  # Get the count of rows

        # Query for active listings in item_donations for the logged-in user
        try:
            # cur.execute("SELECT id, title, description, status FROM item_donations WHERE user_id = %s AND status = 'active'", (session['user_id'],))
            cur.execute("SELECT id, title, description, image_path, status FROM item_donations WHERE user_id = %s;", (session['user_id'],))

            active_listings = cur.fetchall()  # Fetch all active listings
        except Exception as e:
            print("Error fetching active listings:", e)
            active_listings = []  # Fallback to an empty list
        print("DEBUG: Active Listings Data:", )
        # Get background check status (with error handling)
        background_check_status = None
        background_check_score = None
        try:
            print("DEBUG: Fetching background check data...")
            cur.execute("""
                SELECT status, score 
                FROM background_checks 
                WHERE user_id = %s
            """, (session['user_id'],))
            bg_check = cur.fetchone()
            if bg_check:
                background_check_status = bg_check[0]
                background_check_score = bg_check[1]
            print(f"DEBUG: Background check - Status: {background_check_status}, Score: {background_check_score}")
        except Exception as bg_error:
            print(f"DEBUG: Error fetching background check (might not exist): {str(bg_error)}")
            # Not critical if background check doesn't exist yet
        
        return render_template('profile.html',
            user={
                'first_name': user_data[0],
                'last_name': user_data[1],
                'email': user_data[2]
            },
            user_profile=profile_dict,
            donations_total=donations_total,
            followers_count=0,
            following_count=0,
            active_listings=active_listings,
            donations_count=donations_count,
            background_check_status=background_check_status,
            background_check_score=background_check_score
        )
        
    except Exception as e:
        import traceback
        print(f"ERROR: Profile loading failed: {e}")
        traceback.print_exc()  # This will print the full traceback
        flash('Error loading profile data', 'error')
        return redirect(url_for('home'))
    finally:
        if cur:
            cur.close()

@app.route('/item/<int:item_id>/update_status', methods=['POST'])
def update_item_status(item_id):
    if 'user_id' not in session:
        flash("You need to be logged in to update the status.", "error")
        return redirect(url_for('signin'))

    new_status = request.form.get('status')

    try:
        cur = mysql.connection.cursor()
        cur.execute("UPDATE item_donations SET status = %s WHERE id = %s", (new_status, item_id))
        mysql.connection.commit()
        cur.close()
        flash("Item status updated successfully!", "success")
    except Exception as e:
        print(f"ERROR: {e}")
        flash("An error occurred while updating the item status.", "error")

    return redirect(url_for('item_details', item_id=item_id))

#=================================================================================================
@app.route('/update_bio', methods=['POST'])
def update_bio():
    if 'user_id' not in session:
        return redirect(url_for('signin'))
    
    bio = request.form.get('bio', '')
    
    try:
        cur = mysql.connection.cursor()
        # Use parameterized query to prevent SQL injection
        cur.execute("""
            INSERT INTO user_profiles (user_id, bio)
            VALUES (%s, %s)
            ON DUPLICATE KEY UPDATE bio = VALUES(bio)
        """, (session['user_id'], bio))
        mysql.connection.commit()
        flash('Bio updated successfully!', 'success')
    except Exception as e:
        mysql.connection.rollback()
        print(f"BIO UPDATE ERROR: {str(e)}")
        flash('Error updating bio', 'error')
    finally:
        if 'cur' in locals():
            cur.close()
    
    return redirect(url_for('profile'))


@app.route('/update_location', methods=['POST'])
def update_location():
    if 'user_id' not in session:
        return redirect(url_for('signin'))
    
    city = request.form.get('city', '')
    country = request.form.get('country', '')
    
    try:
        cur = mysql.connection.cursor()
        cur.execute("""
            INSERT INTO user_profiles (user_id, city, country)
            VALUES (%s, %s, %s)
            ON DUPLICATE KEY UPDATE 
                city = VALUES(city),
                country = VALUES(country)
        """, (session['user_id'], city, country))
        mysql.connection.commit()
        flash('Location updated successfully!', 'success')
    except Exception as e:
        mysql.connection.rollback()
        print(f"LOCATION UPDATE ERROR: {str(e)}")
        flash('Error updating location', 'error')
    finally:
        if 'cur' in locals():
            cur.close()
    
    return redirect(url_for('profile'))

@app.route('/donate', methods=['GET', 'POST'])
def donate():
    if 'user_id' not in session:
        return redirect(url_for('signin'))
    
    if request.method == 'POST':
        try:
            # Validate required fields
            title = request.form.get('title', '').strip()
            description = request.form.get('description', '').strip()
            location = request.form.get('location', '').strip()
            
            if not all([title, description, location]):
                flash('Please fill all required fields', 'error')
                return redirect(url_for('donate'))
            
            # Handle file upload
            if 'photo' not in request.files:
                flash('No photo uploaded', 'error')
                return redirect(url_for('donate'))
                
            photo = request.files['photo']
            if photo.filename == '':
                flash('No selected photo', 'error')
                return redirect(url_for('donate'))
                
            if photo and allowed_file(photo.filename):
                # Create uploads directory if not exists
                os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
                
                # Generate unique filename
                ext = photo.filename.rsplit('.', 1)[1].lower()
                filename = f"donation_{session['user_id']}_{int(time.time())}.{ext}"
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                
                # Save file
                photo.save(filepath)
                
                # Save to database
                cur = mysql.connection.cursor()
                cur.execute("""
                    INSERT INTO item_donations (user_id, title, description, image_path, location)
                    VALUES (%s, %s, %s, %s, %s)
                """, (
                    session['user_id'],
                    title,
                    description,
                    f"uploads/{filename}",  # Store relative path
                    location
                ))
                mysql.connection.commit()
                cur.close()
                
                flash('Donation posted successfully!', 'success')
                return redirect(url_for('profile'))
            else:
                flash('Allowed file types: png, jpg, jpeg, gif', 'error')
                
        except Exception as e:
            mysql.connection.rollback()
            print(f"Error posting donation: {e}")
            flash('Error posting donation', 'error')
    
    return render_template('donate.html')

if __name__ == '__main__':
    create_tables() 
    app.run(host='0.0.0.0', port=5000, debug=True)