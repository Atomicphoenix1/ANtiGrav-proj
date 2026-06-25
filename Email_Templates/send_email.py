import smtplib
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# --- CONFIGURATION ---
SMTP_SERVER = "smtp.gmail.com" # Change if using Outlook (smtp-mail.outlook.com)
SMTP_PORT = 587
SENDER_EMAIL = "your-email@gmail.com"
SENDER_PASSWORD = "your-app-password" # Use a Google "App Password", NOT your main password

RECIPIENT_EMAIL = "doctor-email@college.edu"
SUBJECT = "Update: College Materials / أهلاً دكتور"

HTML_FILE = "newsletter_template.html"

def send_email():
    if not os.path.exists(HTML_FILE):
        print(f"Error: {HTML_FILE} not found!")
        return

    # 1. Create the message
    message = MIMEMultipart("alternative")
    message["Subject"] = SUBJECT
    message["From"] = SENDER_EMAIL
    message["To"] = RECIPIENT_EMAIL

    # 2. Read the randomized HTML
    with open(HTML_FILE, "r", encoding="utf-8") as f:
        html_content = f.read()

    # 3. Attach HTML
    part = MIMEText(html_content, "html")
    message.attach(part)

    # 4. Connect and send
    try:
        print("Connecting to server...")
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls() # Secure the connection
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.sendmail(SENDER_EMAIL, RECIPIENT_EMAIL, message.as_string())
        server.quit()
        print(f"✅ Email successfully sent to {RECIPIENT_EMAIL}!")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    print("--- QUIRKY EMAIL SENDER ---")
    # Uncomment the line below to actually send
    # send_email()
    print("Please edit the script with your credentials first!")
