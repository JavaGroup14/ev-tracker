## Project Setup and Deployment Guide

### Project github repo link : https://github.com/JavaGroup14/ev-tracker.git
----
This document outlines the steps required to set up and run the project locally. Our application is built using Flask, connects to an MSSQL database hosted on Azure, and integrates with several external APIs.

## Prerequisites
Before starting, ensure you have the following installed on your system:
1. Python 3.8+
2. Git (for cloning the repository)
3. Ngrok (required for secure HTTPS connection tunneling)
----
## 1. Environment Setup
### 1.1. Python Environment and Dependencies
This step involves creating a dedicated virtual environment for the project to manage dependencies cleanly.
1. **Navigate to the project directory**:
```bash
    cd /path/to/your/project
```
2. **Create a virtual environment named venv**:
```bash
    python -m venv venv
```
3. **Activate the virtual environment**:
- **Windows**:
```bash
    venv\Scripts\activate
```
- **macOS/Linux**:
```bash
    source venv/bin/activate
```
(The terminal prompt should now show (venv) indicating successful activation.)

4. **Install all required libraries**: The project dependencies are listed in requirements.txt. Install them using the following command:
```bash
    pip install -r requirements.txt
```

----

## 2. Configuration and Security (.env File)

The application uses environment variables for secure storage of secrets and configuration settings.

1. **Create the .env file**: In the project root directory, create a new file named .env.
2. **Fill in the required configuration**: You must populate this file with the correct values for database credentials, API keys, and application settings.


- **Application & Security**

| Key Name           | Purpose                                                                                                                     | Example                                                                              |
| ------------------ | --------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------ |
| **app_secret_key** | Cryptographic key used by Flask for session management and security.                                                        | A_Strong_Random_Key_For_Flask                                                        |
| **REDIRECT_URI**   | The complete URL where OAuth and payment services redirect after success. Must match the Ngrok HTTPS URL for local testing. | [https://your-ngrok-url.dev/auth/callback](https://your-ngrok-url.dev/auth/callback) |

- **Database (Azure MSSQL)**

| Key Name        | Purpose                                                   | Example                         |
| --------------- | --------------------------------------------------------- | ------------------------------- |
| **DB_SERVER**   | The hostname or IP address of the Azure MSSQL Server.     | yourserver.database.windows.net |
| **DB_NAME**     | The specific name of the database instance to connect to. | ProjectDatabaseName             |
| **DB_USER**     | MSSQL Login Username with appropriate access permissions. | YourDatabaseUser                |
| **DB_PASSWORD** | MSSQL Login Password.                                     | YourSecurePassword!             |

- **Google OAuth**

| Key Name                 | Purpose                                                       | Example                                 |
| ------------------------ | ------------------------------------------------------------- | --------------------------------------- |
| **google_client_id**     | Client ID obtained from Google Developer Console for sign-in. | 12345-abcdef.apps.googleusercontent.com |
| **google_client_secret** | Secret key corresponding to the OAuth Client ID.              | GOCSPX-YYYYYYYYYYYYYYYY                 |

- **Payment Gateway (Razorpay)**

| Key Name            | Purpose                                                                            | Example                    |
| ------------------- | ---------------------------------------------------------------------------------- | -------------------------- |
| **RAZORPAY_KEY_ID** | Public Key ID for the Razorpay API.                                                | rzp_test_XXXXXXXXXXXXXXXX  |
| **RAZORPAY_SECRET** | Secret Key for the Razorpay API.                                                   | XXXXXXXXXXXXXXXXXXXXXXXX   |
| **RECEIVER_UPI**    | UPI ID used for non-Razorpay payment flows or display purposes.                    | user@upi                   |
| **RECEIVER_NAME**   | Name associated with the UPI receiver.                                             | Project Team Lead          |
| **DEFAULT_AMOUNT**  | Default amount (in the smallest currency unit, e.g., paise) for test transactions. | 50000 (Represents ₹500.00) |

- **Email Service(Gmail)**

| Key Name             | Purpose                                                                      | Example                                                                        |
| -------------------- | ---------------------------------------------------------------------------- | ------------------------------------------------------------------------------ |
| **GMAIL_TOKEN_JSON** | The full content of the service account JSON key file or path for Gmail API. | Paste the entire JSON object here, or provide a path if your code reads files. |


----

## 3. Database Connection (Azure MSSQL)

Our database is hosted on Microsoft Azure. To connect, you need to ensure proper authorization.

1. **Administrative Access**: Ensure your Azure administrator has added your email address to the allowed users list and configured the Azure firewall to accept connections from your current IP address.

2. **Client Connection**: The required connection settings (server name, database name, user, password) are read from your .env file via the libraries installed in Step 1.

3. **Optional: VS Code MSSQL Extension**: For development and debugging, you may want to install the mssql extension in VS Code to visually connect and interact with the database using your registered credentials.

----

## 4. Setting up a Secure Tunnel with Ngrok

Many of the integrated APIs (especially OAuth and payment webhooks) require that the application's callback URLs use the secure HTTPS protocol. Ngrok provides a public HTTPS URL that tunnels traffic to your local Flask server.

1. **Install Ngrok**: Download and install the Ngrok client if you haven't already.

2. **Start the Ngrok Tunnel**: Open a separate terminal window (keep your main terminal free for the Flask app) and run the following command, targeting the default Flask port (5000):
```bash
    ngrok http 5000
```
3. **Note the Forwarding Link**: Ngrok will display a forwarding URL, such as:
Forwarding https://clemencia-multispiral-jimmie.ngrok-free.dev -> http://localhost:5000
4. **Update API Settings**: Crucially, you must use this Ngrok link to configure the "Authorized Redirect URIs" and "Webhook URLs" in the developer consoles for services like OAuth and Razorpay.

----

## 5. Running the Flask Application
Once the environment and configuration are ready, you can start the application.
1. **Ensure Environment is Active**: In your main terminal window, confirm the virtual environment is activated ((venv) is visible).
2. **Run the Flask App**: Execute the standard Flask run command:
```bash
    flask run
```
This will start the server, typically running on http://localhost:5000.
3. **Access the Application**: Go back to the Ngrok terminal window and click on the HTTPS forwarding link. This link is your secure access point to the application. The website should now be open and fully functional for demonstration.
