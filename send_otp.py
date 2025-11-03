import base64
import os.path
import secrets  # <-- For generating the OTP
from email.message import EmailMessage

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# --- Configuration ---
# This scope grants permission *only* to send emails.
SCOPES = ["https://www.googleapis.com/auth/gmail.send"]

# The email you are sending FROM (must be the one you log in with)
SENDER_EMAIL = "evtracker3@gmail.com"  

# The email you are sending TO
RECIPIENT_EMAIL = "akarthiksagar74@gmail.com" 
# --- --- --- --- ---

def generate_otp():
    """Generates a secure 6-digit OTP."""
    otp_num = secrets.randbelow(900000) + 100000
    return str(otp_num)

def get_gmail_service():
    """
    Authenticates with the Gmail API.
    This handles the *entire* OAuth 2.0 flow.
    """
    creds = None
    # The file token.json stores your permission.
    # It's created automatically on the first run.
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)

    # If there are no (valid) credentials, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            # This uses your 'credentials.json' (the "Desktop app" file)
            # to start the login process.
            flow = InstalledAppFlow.from_client_secrets_file(
                "credentials.json", SCOPES
            )
            # This line will OPEN YOUR BROWSER for you to log in
            creds = flow.run_local_server(port=0)

        # Save the permission (the token) for next time
        with open("token.json", "w") as token:
            token.write(creds.to_json())

    try:
        service = build("gmail", "v1", credentials=creds)
        print("Gmail service created successfully.")
        return service
    except HttpError as error:
        print(f"An error occurred building the service: {error}")
        return None

def send_email(service, otp_code):
    """Creates and sends the email message."""
    try:
        message = EmailMessage()
        message.set_content(f"Your one-time password is: {otp_code}")
        message["To"] = RECIPIENT_EMAIL
        message["From"] = SENDER_EMAIL
        message["Subject"] = "Your OTP Code"

        # Encode the message in base64
        encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
        create_message = {"raw": encoded_message}

        # Use the Gmail API to send the email
        send_message = (
            service.users()
            .messages()
            .send(userId="me", body=create_message)
            .execute()
        )
        print(f'Message Id: {send_message["id"]}')
        return send_message

    except HttpError as error:
        print(f"An error occurred sending the email: {error}")
        return None
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return None

# --- --- --- ---
#  MAIN EXECUTION
# --- --- --- ---
if __name__ == "__main__":

    # 1. Generate the OTP
    my_otp = generate_otp()
    print(f"Generated OTP: {my_otp}")

    # 2. Authenticate and get the Gmail service
    #    (This will open your browser ONCE)
    gmail_service = get_gmail_service()

    # 3. If authentication worked, send the email
    if gmail_service:
        print(f"Sending OTP to {RECIPIENT_EMAIL}...")
        send_email(gmail_service, my_otp)
        print("Email sent.")