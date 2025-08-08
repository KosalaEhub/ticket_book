from flask import Flask, render_template, request, redirect, session, url_for, flash, send_from_directory
from werkzeug.utils import secure_filename
from pymongo import MongoClient
import os
import bcrypt
from functools import wraps

app = Flask(__name__)
app.secret_key = 'your_secret_key'

UPLOAD_FOLDER = os.path.join(app.root_path, 'static', 'uploads')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

if os.path.exists(UPLOAD_FOLDER):
    if not os.path.isdir(UPLOAD_FOLDER):
        raise Exception(f"Path '{UPLOAD_FOLDER}' exists and is not a directory.")
else:
    os.makedirs(UPLOAD_FOLDER)

try:
    client = MongoClient("mongodb://host.docker.internal:27017/", serverSelectionTimeoutMS=5000)

    client.server_info()
    print("✅ Connected to MongoDB successfully!")
except Exception as e:
    print("❌ Connection error:", e)

db = client['profile']
users = db.users
contacts = db.contact  # New collection for contact form

login_attempts = {}
MAX_ATTEMPTS = 3

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'email' not in session:
            flash("Please login first.")
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def home():
    return render_template('Home.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/booking')
def booking():
    return render_template('booking.html')

@app.route('/destinations')
def destinations():
    return render_template('Destinations.html')

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        subject = request.form.get('subject')
        message = request.form.get('message')

        contacts.insert_one({
            "name": name,
            "email": email,
            "subject": subject,
            "message": message
        })

        flash("✅ Message sent successfully! We'll get back to you soon.", "success")
        return redirect(url_for('contact'))

    return render_template('contact.html')

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        fname = request.form['fname']
        lname = request.form['lname']
        email = request.form['email'].lower().strip()
        phone = request.form['phone']
        country = request.form['country']
        city = request.form['city']
        password = request.form['password']
        confirm = request.form['confirm']
        photo = request.files['photo']

        if users.find_one({"email": email}):
            flash('Email already registered!')
            return redirect(url_for('register'))

        if password != confirm:
            flash('Passwords do not match!')
            return redirect(url_for('register'))

        if not (photo and allowed_file(photo.filename)):
            flash('Invalid file type! Only png, jpg, jpeg allowed.')
            return redirect(url_for('register'))

        filename = secure_filename(email + "_" + photo.filename)
        photo.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

        hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

        users.insert_one({
            "fname": fname,
            "lname": lname,
            "email": email,
            "phone": phone,
            "country": country,
            "city": city,
            "password": hashed,
            "photo": filename
        })

        flash('Registration successful! Please login.')
        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email'].lower().strip()
        password = request.form['password']

        if email not in login_attempts:
            login_attempts[email] = 0

        if login_attempts[email] >= MAX_ATTEMPTS:
            flash('Account locked due to too many failed login attempts.')
            return redirect(url_for('login'))

        user = users.find_one({"email": email})
        if user and bcrypt.checkpw(password.encode('utf-8'), user['password']):
            session['email'] = user['email']
            login_attempts[email] = 0
            flash('Login successful!')
            return redirect(url_for('dashboard'))
        else:
            login_attempts[email] += 1
            remaining = MAX_ATTEMPTS - login_attempts[email]
            if remaining <= 0:
                flash('Account locked due to too many failed login attempts.')
            else:
                flash(f'Invalid email or password! {remaining} attempts left.')
            return redirect(url_for('login'))
    return render_template('login.html')

@app.route('/dashboard')
@login_required
def dashboard():
    user = users.find_one({"email": session['email']})
    welcome_name = user['fname'] if user else "User"
    return render_template('dashboard.html', welcome_name=welcome_name, user=user)

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    user = users.find_one({"email": session['email']})

    if request.method == 'POST':
        fname = request.form['fname']
        lname = request.form['lname']
        phone = request.form['phone']
        country = request.form['country']
        city = request.form['city']

        users.update_one({"email": session['email']}, {
            "$set": {
                "fname": fname,
                "lname": lname,
                "phone": phone,
                "country": country,
                "city": city
            }
        })
        flash('Profile updated successfully!')
        return redirect(url_for('profile'))

    return render_template('profile.html', user=user)

@app.route('/delete_profile')
@login_required
def delete_profile():
    users.delete_one({"email": session['email']})
    session.pop('email', None)
    flash('Profile deleted successfully!')
    return redirect(url_for('register'))

@app.route('/logout')
@login_required
def logout():
    session.pop('email', None)
    flash('Logged out successfully!')
    return redirect(url_for('login'))

@app.route('/update', methods=['GET', 'POST'])
@login_required
def update():
    user = users.find_one({"email": session['email']})
    
    if request.method == 'POST':
        fname = request.form['fname']
        lname = request.form['lname']
        phone = request.form['phone']
        country = request.form['country']
        city = request.form['city']

        users.update_one({"email": session['email']}, {
            "$set": {
                "fname": fname,
                "lname": lname,
                "phone": phone,
                "country": country,
                "city": city
            }
        })

        flash('Profile updated successfully!')
        return redirect(url_for('profile'))

    return render_template('update.html', user=user)

if __name__ == '__main__':
    app.run(debug=True)
