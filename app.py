from flask import Flask, redirect, url_for, session, request, render_template
from flask_sqlalchemy import SQLAlchemy
from authlib.integrations.flask_client import OAuth
from dotenv import load_dotenv
import os, urllib

load_dotenv()

# Build ODBC connection string safely
params = urllib.parse.quote_plus(
    f"Driver={{ODBC Driver 17 for SQL Server}};"
    f"Server={os.getenv('DB_SERVER')};"
    f"Database={os.getenv('DB_NAME')};"
    f"Uid={os.getenv('DB_USER')};"
    f"Pwd={os.getenv('DB_PASSWORD')};"
    f"Encrypt=yes;"
    f"TrustServerCertificate=no;"
)

"""
# Run this to check installed sql server drivers in your devices.
import pyodbc
print(pyodbc.drivers())
"""

app=Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = f"mssql+pyodbc:///?odbc_connect={params}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

"""
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    -> This just disables a warning — SQLAlchemy otherwise listens to every object change, which slows things down.
"""

app.secret_key = os.getenv("app_secret_key")    # Required for sessions

db = SQLAlchemy(app)
"""
This creates the bridge between your Flask app and your database.
db gives you tools to:
    Define models (tables)
    Run queries
    Commit changes
"""

"""
SQLAlchemy is an Object-Relational Mapper (ORM), meaning:
    Each class = one table
    Each object (instance) = one row
    Each class attribute = one column

So SQLAlchemy needs one Python class per table to know:
    What the table is called
    What columns exist
    What types they are
    What relationships (foreign keys) connect them
"""

oauth = OAuth(app)

# It’s a fixed public URL provided by Google that contains all OAuth-related URLs (like authorization, token, and userinfo endpoints).
CONF_URL = 'https://accounts.google.com/.well-known/openid-configuration'

# -------------------- GOOGLE OAUTH --------------------
google = oauth.register(
    name='google',
    client_id=os.getenv("google_client_id"),
    client_secret=os.getenv("google_client_secret"),
    
    # This one line replaces all the manual URLs
    server_metadata_url=CONF_URL,
    
    client_kwargs={'scope': 'openid email profile'}
)

# # -------------------- MODELS --------------------

class Users(db.Model):
    __tablename__ = "Users"
    __table_args__ = {'schema': 'Reg'}

    username = db.Column(db.String(20), primary_key=True)
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20),nullable=False)

class PreRegistered(db.Model):
    __tablename__ = "PreRegistered"
    __table_args__ = {'schema': 'Reg'}

    email = db.Column(db.String(100), primary_key=True)
    role = db.Column(db.String(20),nullable=False)

class Student(db.Model):
    __tablename__ = "Student"
    __table_args__ = {'schema':'Loc'}

    username = db.Column(db.String(20), db.ForeignKey('Reg.Users.username'), primary_key=True)
    latitude = db.Column(db.Numeric(9,6),nullable=False)
    longitude = db.Column(db.Numeric(9,6),nullable=False)
    status = db.Column(db.String(20),nullable=False)

class Driver(db.Model):
    __tablename__ = "Driver"
    __table_args__ = {'schema':'Loc'}

    username = db.Column(db.String(20), db.ForeignKey('Reg.Users.username'), primary_key=True)
    latitude = db.Column(db.Numeric(9,6),nullable=False)
    longitude = db.Column(db.Numeric(9,6),nullable=False)
    status = db.Column(db.String(20),nullable=False)

class Driver_work_log(db.Model):
    __tablename__ = "Driver_work_log"
    __table_args__ = {'schema':'Work'}

    username = db.Column(db.String(20),primary_key=True)
    curr_date = db.Column(db.Date,nullable=False)
    start_time = db.Column(db.Time,nullable=False)
    end_time = db.Column(db.Time,nullable=False)

class Payment_log(db.Model):
    __tablename__ = "Payment_log"
    __table_args__ = {'schema':'Work'}

    payment_id = db.Column(db.Integer,primary_key=True)
    username = db.Column(db.String(20))
    curr_date_time = db.Column(db.DateTime,nullable=False)
    amount = db.Column(db.Numeric(10,2),nullable=False)

# # -------------------- ROUTES --------------------

@app.route('/')
def index():
    return render_template("login.html")

# Triggered when login button is clicked 
@app.route('/login_button',methods=['GET','POST'])
def login():
    username = request.form.get('username')
    password = request.form.get('password')
    # check in our users table whether this is registered and correct 
    user = Users.query.filter_by(username=username).first()
    if user:
        if user.password == password:
            # Password matches, set session and redirect based on role
            session['username'] = user.username
            session['role'] = user.role
            if user.role == 'student':
                return redirect('/Student')
            elif user.role == 'driver':
                return redirect('/Driver')
            elif user.role == 'admin':
                return redirect('/Admin')
            else:
                return "Unknown role", 400
        else:
            # Password mismatch
            return "Incorrect Username or password", 401
    else:
        # User not found
        return "User not found", 404
    

# login by google button triggers this route
@app.route('/login_google')
def login_google():
    redirect_uri = "https://disconnected-babette-trivially.ngrok-free.dev/authorize_google"
    return google.authorize_redirect(redirect_uri)

# Triggered when you click the link "don't have an account?"
@app.route('/registration')
def reg():
    return render_template("registration.html")

# Callback route Google redirects to
@app.route('/authorize_google')
def authorize_google():
    token = google.authorize_access_token()
    user_info = token['userinfo']
    google_email = user_info['email']
    session['google_email'] = google_email  # store in session
    # Check if user exists
    user = Users.query.filter_by(email=google_email).first()
    if user:
        # Already registered → redirect based on role
        if user.role == 'student':
            return redirect('/Student')
        elif user.role == 'driver':
            return redirect('/Driver')
        elif user.role == 'admin':
            return redirect('/Admin')
    else:
        # Not registered → lead to registration2 page
        return redirect('/registration2')

# Registration2 route for new users (manual username + role selection)
@app.route('/registration2', methods=['GET','POST'])
def registration2():
    if request.method == 'POST':
        form_username = request.form['username']
        selected_role = request.form['role']  # student/driver/admin
        raw_password = request.form['password'] 
        google_email = session.get('google_email')

        # 1. Check username uniqueness
        if Users.query.filter_by(username=form_username).first():
            return "Username already taken. Choose another.", 400

        # 2. PreRegistered check for driver/admin
        if selected_role in ['driver', 'admin']:
            pre = PreRegistered.query.filter_by(email=google_email, role=selected_role).first()
            if not pre:
                return "Email not authorized for this role", 400

        # 3. Save new user (password stored as plain text or optional)
        new_user = Users(
            username=form_username,
            email=google_email,
            password=raw_password,
            role=selected_role
        )
        db.session.add(new_user)
        db.session.commit()

        # 4. Redirect based on role
        if selected_role == 'student':
            return redirect('/Student')
        elif selected_role == 'driver':
            return redirect('/Driver')
        else:
            return redirect('/Admin')

    # GET request → show registration form
    return render_template("registration2.html")

@app.route('/Student')
def student_ui():
    return render_template("student.html")

@app.route('/Driver')
def driver_ui():
    return render_template("driver.html")

@app.route('/Admin')
def admin_ui():
    return render_template("admin.html")