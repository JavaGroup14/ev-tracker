from flask import Flask, redirect, url_for, session, request, render_template,jsonify
from flask_sqlalchemy import SQLAlchemy
from authlib.integrations.flask_client import OAuth
from dotenv import load_dotenv
import os, urllib
from email.message import EmailMessage
from datetime import datetime, timedelta, date,timezone
from sqlalchemy import text
import base64
import secrets
import json
from email.message import EmailMessage

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


# --- Configuration ---
# This is the email you authorized in Part 1
# All emails will be sent FROM this address.
SENDER_EMAIL = "evtracker3@gmail.com"
SCOPES = ["https://www.googleapis.com/auth/gmail.send"]
from urllib.parse import quote_plus
from flask_wtf import CSRFProtect
from flask_wtf.csrf import generate_csrf
import razorpay
from flask import jsonify

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

# Razor pay
razorpay_client = razorpay.Client(
    auth=(os.getenv("RAZORPAY_KEY_ID"), os.getenv("RAZORPAY_SECRET"))
)

csrf = CSRFProtect(app)
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
    curr_date_time = db.Column(db.DateTime, nullable=False)
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
@csrf.exempt
@app.route('/')
def index():
    return render_template("login.html")

# Triggered when login button is clicked 
@csrf.exempt
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
@csrf.exempt
@app.route('/login_google')
def login_google():
    redirect_uri = os.getenv("REDIRECT_URI")
    redirect_uri = os.getenv("REDIRECT_URI")
    return google.authorize_redirect(redirect_uri)

# Triggered when you click the link "don't have an account?"
@csrf.exempt
@app.route('/registration')
def reg():
    
    return render_template("registration.html")

# Callback route Google redirects to
@csrf.exempt
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
@csrf.exempt
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
        session['dateofjoin']=new_user.reg_date

        # 4. Redirect based on role
        if selected_role == 'student':
            return jsonify({"success":True,"redirect_url":url_for('student_ui')})
        elif selected_role == 'driver':
            return jsonify({"success":True,"redirect_url":url_for('driver_ui')})
        else:
            return jsonify({"success":True,"redirect_url":url_for('admin_ui')})

    # GET request → show registration form
    return render_template("registration2.html")

def get_gmail_service():
    """
    Loads credentials and builds the Gmail service object.
    This is the "Production" way to do it.
    """
    
    # 1. Load the token data from the environment variable
    token_json_str = os.getenv('GMAIL_TOKEN_JSON')
    if not token_json_str:
        print("ERROR: GMAIL_TOKEN_JSON environment variable not set.")
        return None
        
    try:
        # 2. Recreate the Credentials object from the JSON string
        creds_data = json.loads(token_json_str)
        creds = Credentials.from_authorized_user_info(creds_data, SCOPES)
    except json.JSONDecodeError:
        print(f"ERROR: Could not parse GMAIL_TOKEN_JSON.")
        return None
    except Exception as e:
        print(f"ERROR: Failed to load credentials: {e}")
        return None

    # 3. If the token is expired, refresh it
    if not creds.valid:
        if creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
                print("Credentials refreshed.")
                
                # IMPORTANT: You should update the stored env variable
                # with the new creds.to_json() content if it refreshes.
                # For simplicity, we skip that here, but it's
                # best practice for long-running apps.
                
            except Exception as e:
                print(f"ERROR: Could not refresh token: {e}")
                return None
        else:
            print("ERROR: Credentials are not valid and cannot be refreshed.")
            print("You may need to re-run the local script to get a new token.json.")
            return None

    # 4. Build the Gmail service
    try:
        service = build("gmail", "v1", credentials=creds)
        print("Gmail service created successfully.")
        return service
    except HttpError as error:
        print(f"An error occurred building the service: {error}")
        return None

def generate_otp():
    """Generates a secure 6-digit OTP."""
    otp_num = secrets.randbelow(900000) + 100000
    return str(otp_num)

def send_otp_email(service, recipient_email, otp_code):
    """
    Creates and sends the email message to any recipient.
    
    Args:
        service: The authorized Gmail service object.
        recipient_email: The user's email address (string).
        otp_code: The 6-digit OTP (string).
        
    Returns:
        True if successful, False otherwise.
    """
    try:
        message = EmailMessage()
        message.set_content(f"Your one-time password is: {otp_code}")
        message["To"] = recipient_email  # <-- THIS IS NOW DYNAMIC
        message["From"] = SENDER_EMAIL
        message["Subject"] = "Your OTP Code"

        encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
        create_message = {"raw": encoded_message}

        send_message = (
            service.users()
            .messages()
            .send(userId="me", body=create_message)
            .execute()
        )
        print(f'Message sent to {recipient_email}. Message Id: {send_message["id"]}')
        return True
    except HttpError as error:
        print(f"An error occurred sending email: {error}")
        return False
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return False

@app.route('/send-otp', methods=['POST'])
def send_otp():
    form_username = request.form['username']
    form_email = request.form['email']
    form_password = request.form['password']
    selected_role = request.form['role']
    
    # 1. Check username uniqueness
    if Users.query.filter_by(username=form_username).first():
        return jsonify({"success": False, "error": "Username already taken"}), 400
        
    # 2. Check email uniqueness
    if Users.query.filter_by(email=form_email).first():
        return jsonify({"success": False, "error": "Email already registered"}), 400

    # 3. PreRegistered check (same as your /registration2)
    if selected_role in ['driver', 'admin']:
        pre = PreRegistered.query.filter_by(email=form_email, role=selected_role).first()
        if not pre:
            return jsonify({"success": False, "error": "Email not authorized for this role"}), 403

    # 4. All checks passed, get service and generate OTP
    service = get_gmail_service()
    if not service:
        return jsonify({"success": False, "error": "Email service is down"}), 500
        
    otp_code = generate_otp()
    
    # 5. Store data in session for verification
    session['otp_code'] = otp_code
    session['otp_timestamp'] = datetime.now(timezone.utc)
    session['registration_data'] = {
        "username": form_username,
        "email": form_email,
        "password": form_password, # Note: Storing password in session is okay but clear it ASAP
        "role": selected_role
    }
    
    # 6. Send the email
    if send_otp_email(service, form_email, otp_code):
        return jsonify({"success": True, "message": "OTP sent!"})
    else:
        return jsonify({"success": False, "error": "Failed to send OTP"}), 500

# --- NEW ROUTE: To verify OTP and create account ---
@app.route('/verify-and-create', methods=['POST'])
def verify_and_create():
    user_otp = request.form.get('otp')
    
    # 1. Get data from session
    otp_code = session.get('otp_code')
    otp_timestamp = session.get('otp_timestamp')
    reg_data = session.get('registration_data')
    
    if not all([user_otp, otp_code, otp_timestamp, reg_data]):
        return jsonify({"success": False, "error": "Session expired. Please start over."}), 400

    # 2. Check OTP
    if user_otp != otp_code:
        return jsonify({"success": False, "error": "Invalid OTP"}), 400
        
    # 3. Check expiration (e.g., 5 minutes)
    if datetime.now(timezone.utc) - otp_timestamp > timedelta(minutes=5):
        return jsonify({"success": False, "error": "OTP expired"}), 400
        
    # 4. All checks passed, create user
    try:
        new_user = Users(
            username=reg_data['username'],
            email=reg_data['email'],
            password=reg_data['password'], # Note: You should hash this password!
            role=reg_data['role'],
            reg_date=datetime.now()
        )
        db.session.add(new_user)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"DB Error: {e}")
        # Check if it's a unique constraint error (race condition)
        if "UNIQUE constraint" in str(e):
             return jsonify({"success": False, "error": "Username or email was just taken."}), 409
        return jsonify({"success": False, "error": "Database error"}), 500

    # 5. Clear session data and log user in
    session.pop('otp_code', None)
    session.pop('otp_timestamp', None)
    session.pop('registration_data', None)
    
    session['username'] = new_user.username
    session['role'] = new_user.role
    session['dateofjoin'] = new_user.reg_date

    # 6. Send redirect URL based on role
    redirect_url = url_for(f"{new_user.role}_ui")
    return jsonify({"success": True, "redirect_url": redirect_url})

@csrf.exempt
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

@csrf.exempt
@app.route('/Driver')
def driver_ui():
    return render_template("driver.html")

@csrf.exempt
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

@csrf.exempt
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

@csrf.exempt
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

@csrf.exempt
@app.route('/Admin/payments')
def payment_logs_redirect():
    today = datetime.now()
    return redirect(url_for('payment_logs', year=today.year, month=today.month, day=today.day))

@csrf.exempt
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

@csrf.exempt
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

@app.route('/save_student_location', methods=['POST'])
def save_student_location():
    if 'username' not in session:
        return jsonify({"error": "User not logged in"}), 401

    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Invalid JSON"}), 400

    try:
        lat = float(data.get('latitude'))
        lon = float(data.get('longitude'))
    except (TypeError, ValueError):
        return jsonify({"error": "Invalid coordinates"}), 400

    if not (-90 <= lat <= 90 and -180 <= lon <= 180):
        return jsonify({"error": "Coordinates out of range"}), 400

    username = session['username']

    # Save to Loc.Student table
    new_loc = Student(
        username=username,
        latitude=lat,
        longitude=lon,
        curr_date_time=datetime.now(),
        status="waiting"
    )

    db.session.add(new_loc)
    db.session.commit()

    return jsonify({
        "success": True,
        "message": "Student location saved successfully",
        "latitude": lat,
        "longitude": lon
    })

# Optional route to generate CSRF token for JS use 
@app.route('/get_csrf_token')
def get_csrf_token():
    token = generate_csrf()
    return jsonify({'csrf_token': token})

# ---- PAYMENT INTEGRATION ----
@csrf.exempt
@app.route('/create_order', methods=['POST'])
def create_order():
    amount = int(os.getenv('DEFAULT_AMOUNT')) * 100  # ₹10 in paise
    currency = 'INR'

    order = razorpay_client.order.create({
        'amount': amount,
        'currency': currency,
        'payment_capture': 1
    })
    return jsonify({'order_id': order['id'], 'razorpay_key': os.getenv('RAZORPAY_KEY_ID')})

@csrf.exempt
@app.route('/verify_payment', methods=['POST'])
def verify_payment():
    data = request.get_json()
    params_dict = {
        'razorpay_order_id': data['razorpay_order_id'],
        'razorpay_payment_id': data['razorpay_payment_id'],
        'razorpay_signature': data['razorpay_signature']
    }

    try:
        razorpay_client.utility.verify_payment_signature(params_dict)
    except:
        return jsonify({'success': False, 'message': 'Payment verification failed'}), 400

    username = session.get('username')
    if username:
        # Log successful payment
        payment = Payment_log(
            username=username,
            curr_date_time=datetime.now(),
            amount=int(os.getenv('DEFAULT_AMOUNT'))
        )
        db.session.add(payment)

        # Update student's status
        student = Student.query.filter_by(username=username, status='waiting').order_by(Student.record_id.desc()).first()
        if student:
            student.status = 'accepted'
        db.session.commit()

    return jsonify({'success': True, 'message': 'Payment verified and student accepted'})

@app.route('/cancel_student_ride',methods=['POST'])
def cancel_student_ride():
    if 'username' not in session:
        return jsonify({"success":False, "error":"User not logged in"}), 401
    
    username = session['username']

    try:
        student_record = Student.query.filter(
            Student.username == username,
            Student.status == 'waiting'
        ).order_by(
            Student.record_id.desc()
        ).first()

        if not student_record:
            return jsonify({"success":False, "error":"No active ride to cancel"}), 404
        
        student_record.status = 'cancelled'
        db.session.commit()

        return jsonify({
            "success": True,
            "message": "Ride successfully cancelled", 
            "record_id": student_record.record_id
        })
    except Exception as e:
        db.session.rollback()
        print(f"Database error during cancellation: {e}")
        return jsonify({"success": False, "error":"A server error occured during cancellation"}),500
