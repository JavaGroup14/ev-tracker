from flask import Flask, redirect, url_for, session, request, render_template
from flask_sqlalchemy import SQLAlchemy
from authlib.integrations.flask_client import OAuth
from dotenv import load_dotenv
import os

load_dotenv()

app=Flask(__name__)
app.secret_key = os.getenv("app_secret_key")    # Required for sessions

# -------------------- DATABASE CONFIG --------------------

# Path to your .mdf file
db_path = r"D:\Java\JavaProject\Database\EvTracker.mdf"

# SQLAlchemy connection string for LocalDB
app.config['SQLALCHEMY_DATABASE_URI'] = (
    rf"mssql+pyodbc:///?odbc_connect="
    rf"Driver={{SQL Server}};"
    rf"Server=(LocalDB)\MSSQLLocalDB;" 
    rf"AttachDbFilename={db_path};"
    rf"Trusted_Connection=yes;"
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

"""
    Part	                                         Meaning
mssql+pyodbc://	                Tells SQLAlchemy to use the MSSQL dialect with the pyodbc driver
odbc_connect=	                Means you're going to specify all ODBC parameters manually
Driver={SQL Server}	            Use Microsoft SQL Server driver
Server=(LocalDB)\MSSQLLocalDB	Connect to your local SQL Server instance
AttachDbFilename=...	        Attach the specific .mdf file (your database)
Trusted_Connection=yes	        Use Windows Authentication instead of username/password

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    -> This just disables a warning — SQLAlchemy otherwise listens to every object change, which slows things down.

"""

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

# -------------------- GOOGLE OAUTH --------------------
google = oauth.register(
    name='google',
    client_id=os.getenv("google_client_id"),
    client_secret=os.getenv("google_client_secret"),
    access_token_url='https://accounts.google.com/o/oauth2/token',
    authorize_url='https://accounts.google.com/o/oauth2/auth',
    api_base_url='https://www.googleapis.com/oauth2/v1/',
    client_kwargs={'scope': 'openid email profile'}
)

# -------------------- MODELS --------------------

class Users(db.Model):
    __tablename__ = "Users"
    __table_args__ = {'schema': 'Reg'}

    username = db.Column(db.String(20), primary_key=True)
    email = db.Column(db.String(30), unique=True)
    password = db.Column(db.String(30), nullable=True)
    role = db.Column(db.String(20))

class PreRegistered(db.Model):
    __tablename__ = "PreRegistered"
    __table_args__ = {'schema': 'Reg'}

    email = db.Column(db.String(30), primary_key=True)
    role = db.Column(db.String(20))

# -------------------- ROUTES --------------------

@app.route('/')
def index():
    return render_template("index.html")

# Triggered when login button is clicked 
@app.route('/login_button',methods=['GET','POST'])
def login():
    username = request.form.get('username')
    password = request.form.get('password')
    # check in our users table whether this is registered and correct 
    user = Users.query.filter_by(username=username)
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
    redirect_uri = url_for('authorize_google', _external=True)
    return google.authorize_redirect(redirect_uri)

# Triggered when you click the link "don't have an account?"
@app.route('/registration')
def reg():
    return render_template("registration.html")

# Callback route Google redirects to
@app.route('/authorize_google')
def authorize_google():
    token = google.authorize_access_token()
    resp = google.get('userinfo')
    user_info = resp.json()
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
        raw_password = request.form.get('password')  # optional
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
    return render_template("student_ui.html")

@app.route('/Driver')
def driver_ui():
    return render_template("driver_ui.html")

@app.route('/Admin')
def admin_ui():
    return render_template("admin_ui.html")