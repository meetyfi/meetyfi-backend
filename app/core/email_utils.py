# core/email_utils.py
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from pathlib import Path
from app.config import get_settings

settings = get_settings()

# Define email templates directory
EMAIL_TEMPLATES_DIR = Path(__file__).parent.parent / "templates" / "email"

# Create the templates directory if it doesn't exist
EMAIL_TEMPLATES_DIR.mkdir(parents=True, exist_ok=True)

class EmailService:
    def __init__(self):
        self.conf = ConnectionConfig(
            MAIL_USERNAME=settings.SMTP_USER,
            MAIL_PASSWORD=settings.SMTP_PASSWORD,
            MAIL_FROM=settings.SMTP_USER,
            MAIL_PORT=settings.SMTP_PORT,
            MAIL_SERVER=settings.SMTP_HOST,
            MAIL_STARTTLS=True,  # Added required field
            MAIL_SSL_TLS=False,
            
            VALIDATE_CERTS=True,  # Added for security
            USE_CREDENTIALS=True,
            TEMPLATE_FOLDER=str(EMAIL_TEMPLATES_DIR)
        )
        self.fastmail = FastMail(self.conf)
    
    async def send_verification_email(self, email: str, verification_code: str):
        html_content = f"""
        <html>
            <body style="font-family: Arial, sans-serif; padding: 20px; max-width: 600px; margin: auto;">
                <div style="background-color: #f8f9fa; padding: 20px; border-radius: 5px;">
                    <h2 style="color: #333; text-align: center;">Welcome to Meetyfi!</h2>
                    <p>Thank you for signing up. Please use the verification code below:</p>
                    <div style="background-color: #fff; padding: 15px; text-align: center; font-size: 24px; 
                              font-weight: bold; margin: 20px 0; border-radius: 5px;">
                        {verification_code}
                    </div>
                    <p>This code will expire in 10 minutes.</p>
                    <p>If you didn't request this code, please ignore this email.</p>
                    <hr style="border: 1px solid #eee; margin: 20px 0;">
                    <p style="text-align: center; color: #666; font-size: 12px;">
                        © 2024 Meetyfi. All rights reserved.
                    </p>
                </div>
            </body>
        </html>
        """
        
        message = MessageSchema(
            subject="Verify your Meetyfi account",
            recipients=[email],
            body=html_content,
            subtype="html"
        )
        
        await self.fastmail.send_message(message)

    async def send_meeting_notification(self, email: str, meeting_details: dict):
        html_content = f"""
        <html>
            <body style="font-family: Arial, sans-serif; padding: 20px; max-width: 600px; margin: auto;">
                <div style="background-color: #f8f9fa; padding: 20px; border-radius: 5px;">
                    <h2 style="color: #333; text-align: center;">New Meeting Scheduled</h2>
                    <div style="background-color: #fff; padding: 20px; border-radius: 5px; margin: 20px 0;">
                        <p><strong>Date:</strong> {meeting_details['date']}</p>
                        <p><strong>Time:</strong> {meeting_details['time']}</p>
                        <p><strong>Client:</strong> {meeting_details['client_name']}</p>
                        <p><strong>Location:</strong> {meeting_details['location']}</p>
                    </div>
                    <p>Please review and confirm the meeting details.</p>
                    <hr style="border: 1px solid #eee; margin: 20px 0;">
                    <p style="text-align: center; color: #666; font-size: 12px;">
                        © 2024 Meetyfi. All rights reserved.
                    </p>
                </div>
            </body>
        </html>
        """
        
        message = MessageSchema(
            subject="New Meeting Request",
            recipients=[email],
            body=html_content,
            subtype="html"
        )
        
        await self.fastmail.send_message(message)