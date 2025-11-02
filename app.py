from flask import Flask, redirect, url_for, session, request, render_template,jsonify
from flask_sqlalchemy import SQLAlchemy
from authlib.integrations.flask_client import OAuth
from dotenv import load_dotenv
import os, urllib
import smtplib,ssl,random,time
from email.message import EmailMessage
from datetime import datetime, timedelta, date
from sqlalchemy import text

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

# --- ADD THESE TWO LINES ---
app.config['SESSION_COOKIE_SECURE'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'None'

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
    reg_date = db.Column(db.DateTime,nullable=False)

class PreRegistered(db.Model):
    __tablename__ = "PreRegistered"
    __table_args__ = {'schema': 'Reg'}

    email = db.Column(db.String(100), primary_key=True)
    role = db.Column(db.String(20),nullable=False)

class Student(db.Model):
    __tablename__ = "Student"
    __table_args__ = {'schema':'Loc'}

    record_id = db.Column(db.Integer,primary_key=True)
    username = db.Column(db.String(20),nullable=False)
    latitude = db.Column(db.Numeric(9,6),nullable=False)
    longitude = db.Column(db.Numeric(9,6),nullable=False)
    curr_date = db.Column(db.DateTime, nullable=False)
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

    log_id = db.Column(db.Integer,primary_key=True)
    username = db.Column(db.String(20),nullable=False)
    curr_date = db.Column(db.Date,nullable=False)
    start_time = db.Column(db.Time,nullable=False)
    end_time = db.Column(db.Time,nullable=False)

class Payment_log(db.Model):
    __tablename__ = "Payment_log"
    __table_args__ = {'schema':'Work'}

    payment_id = db.Column(db.Integer,primary_key=True)
    username = db.Column(db.String(20),nullable=False)
    curr_date_time = db.Column(db.DateTime,nullable=False)
    amount = db.Column(db.Numeric(10,2),nullable=False)

class Feedback(db.Model):
    __tablename__ = "Feedback"
    __table_args__ = {'schema':'Management'}

    feedback_id = db.Column(db.Integer,primary_key=True)
    username = db.Column(db.String(20),nullable=False)
    role = db.Column(db.String(20),nullable=False)
    feedback_date = db.Column(db.Date,nullable=False)
    feedback = db.Column(db.String(1000),nullable=False)
 

# # -------------------- ROUTES --------------------
@app.route('/')
def index():
    return render_template("login.html")

# Triggered when login button is clicked 
@app.route('/login_button', methods=['POST'])
def login():
    username = request.form.get('username')
    password = request.form.get('password')

    user = Users.query.filter_by(username=username).first()

    if not user:
        return jsonify({"error": "User not found"}), 404

    if user.password != password:
        return jsonify({"error": "Incorrect username or password"}), 401

    # Set session
    session['username'] = user.username
    session['role'] = user.role
    session['dateofjoin'] = user.reg_date

    # Redirect by role (this triggers JS `response.redirected`)
    if user.role == 'student':
        return redirect(url_for('student_ui'))
    elif user.role == 'driver':
        return redirect(url_for('driver_ui'))
    elif user.role == 'admin':
        return redirect(url_for('admin_ui'))
    else:
        return jsonify({"error": "Unknown role"}), 400

# login by google button triggers this route
@app.route('/login_google')
def login_google():
    redirect_uri = os.getenv("REDIRECT_URI")
    redirect_uri = os.getenv("REDIRECT_URI")
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
            #added for sessions
        session['username'] = user.username
        session['role'] = user.role
        session['dateofjoin'] = user.reg_date
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
            return jsonify({"success":False,"error":"Username already taken"}), 400

        # 2. PreRegistered check for driver/admin
        if selected_role in ['driver', 'admin']:
            pre = PreRegistered.query.filter_by(email=google_email, role=selected_role).first()
            if not pre:
                return jsonify({"success":False,"error":"Email not authorized for this role"}), 400

        # 3. Save new user (password stored as plain text or optional)
        new_user = Users(
            username=form_username,
            email=google_email,
            password=raw_password,
            role=selected_role,
            reg_date = datetime.now()
        )
        db.session.add(new_user)
        db.session.commit()
        
        #added for sessions
        session['username'] = new_user.username
        session['role'] = new_user.role
        session['dataofjoin']=new_user.reg_date

        # 4. Redirect based on role
        if selected_role == 'student':
            return jsonify({"success":True,"redirect_url":url_for('student_ui')})
        elif selected_role == 'driver':
            return jsonify({"success":True,"redirect_url":url_for('driver_ui')})
        else:
            return jsonify({"success":True,"redirect_url":url_for('admin_ui')})

    # GET request → show registration form
    return render_template("registration2.html")

@app.route('/Role')
def roles():
    if 'username' not in session:
        return redirect(url_for('index'))
    
    cur_username=session.get('username')
    cur_role=session.get('role')
    user=Users.query.filter_by(username=cur_username).first()
    if not user:
        # If user not found, clear the bad session and send to login
        session.clear()
        return redirect(url_for('index'))
    
    return render_template('role.html',username=cur_username,role=cur_role,email=user.email,dateofjoin=user.reg_date)

@app.route('/Student')
def student_ui():
    return render_template("student.html")

@app.route('/Driver')
def driver_ui():
    return render_template("driver.html")

@app.route('/Admin')
def admin_ui():
    drivers = Users.query.filter_by(role="driver").all()
    active_usernames = {d.username for d in Driver.query.with_entities(Driver.username).all()}
    driver_data = [
        {
            "name": user.username,
            "status": "Active" if user.username in active_usernames else "Inactive"
        }
        for user in drivers
    ]
    return render_template("admin.html", drivers=driver_data)


@app.route('/Driver_log/<username>/<int:year>/<int:month>/<int:day>')
def driver_log(username, year, month, day):
    today = date(year, month, day)
    month_start = date(year, month, 1)
    next_month = (month_start.replace(day=28) + timedelta(days=4)).replace(day=1)
    month_end = next_month - timedelta(days=1)

    # Limit logs for current month up to yesterday
    if year == datetime.now().year and month == datetime.now().month:
        month_end = min(month_end, datetime.now().date() - timedelta(days=1))

    # Fetch logs from MSSQL
    sql = text("""
        SELECT 
            curr_date,
            SUM(DATEDIFF(MINUTE, start_time, end_time)) / 60.0 AS hours_worked
        FROM Work.Driver_work_log
        WHERE username = :username
          AND curr_date BETWEEN :month_start AND :month_end
        GROUP BY curr_date
        ORDER BY curr_date ASC
    """)

    result = db.session.execute(sql, {
        "username": username,
        "month_start": month_start,
        "month_end": month_end
    }).fetchall()

    logs = [{"date": r.curr_date, "hours_worked": round(r.hours_worked, 2)} for r in result]
    total_days = len(logs)
    total_hours = round(sum(log["hours_worked"] for log in logs), 2)

    # Month navigation logic
    current_year, current_month = datetime.now().year, datetime.now().month
    months_diff = (current_year - year) * 12 + (current_month - month)

    prev_disabled = months_diff >= 2  # older than 2 months → disable prev
    next_disabled = (year == current_year and month == current_month)

    # Calculate prev & next month
    prev_month_date = (month_start - timedelta(days=1)).replace(day=1)
    next_month_date = next_month

    return render_template(
        "driver_log.html",
        username=username,
        logs=logs,
        total_days=total_days,
        total_hours=total_hours,
        month_days=month_end.day,
        month_name=month_start.strftime("%B"),
        year=year,
        prev_year=prev_month_date.year,
        prev_month=prev_month_date.month,
        next_year=next_month_date.year,
        next_month=next_month_date.month,
        prev_disabled=prev_disabled,
        next_disabled=next_disabled
    )

@app.route('/pre_register', methods=['POST'])
def pre_register():
    email = request.form.get('email')
    role = request.form.get('role')  # driver/admin

    if not email or not role:
        return jsonify({"success": False, "error": "Missing email or role"}), 400

    # Check if email already pre-registered
    if PreRegistered.query.filter_by(email=email).first():
        return jsonify({"success": False, "error": "Email already pre-registered"}), 400

    # Add new pre-registration entry
    new_entry = PreRegistered(email=email, role=role)
    db.session.add(new_entry)
    db.session.commit()

    return jsonify({"success": True, "message": f"{role.capitalize()} pre-registered successfully!"})

@app.route('/Admin/payments')
def payment_logs_redirect():
    today = datetime.now()
    return redirect(url_for('payment_logs', year=today.year, month=today.month, day=today.day))

@app.route('/Admin/payments/<int:year>/<int:month>/<int:day>')
def payment_logs(year, month, day):
    today = date(year, month, day)
    month_start = date(year, month, 1)
    next_month = (month_start.replace(day=28) + timedelta(days=4)).replace(day=1)
    month_end = next_month - timedelta(days=1)

    sql = text("""
        SELECT 
            CAST(curr_date_time AS DATE) AS payment_date,
            SUM(amount) AS total_amount
        FROM Work.Payment_log
        WHERE curr_date_time BETWEEN :month_start AND :month_end
        GROUP BY CAST(curr_date_time AS DATE)
        ORDER BY payment_date ASC
    """)
    result = db.session.execute(sql, {
        "month_start": month_start,
        "month_end": month_end
    }).fetchall()

    logs = [{"date": r.payment_date, "amount": float(r.total_amount)} for r in result]
    total_amount = round(sum(l["amount"] for l in logs), 2)

    current_year, current_month = datetime.now().year, datetime.now().month
    months_diff = (current_year - year) * 12 + (current_month - month)
    prev_disabled = months_diff >= 2
    next_disabled = (year == current_year and month == current_month)

    prev_month_date = (month_start - timedelta(days=1)).replace(day=1)
    next_month_date = next_month

    return render_template(
        "payment_log.html",
        logs=logs,
        total_amount=total_amount,
        month_name=month_start.strftime("%B"),
        year=year,
        prev_year=prev_month_date.year,
        prev_month=prev_month_date.month,
        next_year=next_month_date.year,
        next_month=next_month_date.month,
        prev_disabled=prev_disabled,
        next_disabled=next_disabled
    )

@app.route('/Admin/feedbacks')
def admin_feedbacks():
    feedbacks = Feedback.query.order_by(Feedback.feedback_date.desc()).all()
    feedback_data = [
        {
            "username": fb.username,
            "role": fb.role,
            "date": fb.feedback_date.strftime("%d %b %Y"),
            "feedback": fb.feedback
        }
        for fb in feedbacks
    ]
    return render_template("feedbacks.html", feedbacks=feedback_data)
