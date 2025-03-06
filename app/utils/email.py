import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import logging
from typing import List, Optional, Union
import random
import string
from datetime import datetime, timedelta

from app.config import settings

logger = logging.getLogger(__name__)

def generate_otp(length: int = 6) -> str:
    """Generate a random OTP of specified length"""
    return ''.join(random.choices(string.digits, k=length))

def generate_verification_token(length: int = 64) -> str:
    """Generate a random verification token"""
    chars = string.ascii_letters + string.digits
    return ''.join(random.choices(chars, k=length))

def send_email(
    recipient_email: str,
    subject: str,
    html_content: str,
    text_content: Optional[str] = None
) -> bool:
    """
    Send an email to the specified recipient
    
    Args:
        recipient_email: Email address of the recipient
        subject: Email subject
        html_content: HTML content of the email
        text_content: Plain text content of the email (optional)
        
    Returns:
        bool: True if email was sent successfully, False otherwise
    """
    if not text_content:
        text_content = "Please view this email in an HTML compatible email client."
    
    message = MIMEMultipart("alternative")
    message["Subject"] = subject
    message["From"] = settings.EMAIL_FROM
    message["To"] = recipient_email
    
    # Add text and HTML parts to the message
    part1 = MIMEText(text_content, "plain")
    part2 = MIMEText(html_content, "html")
    message.attach(part1)
    message.attach(part2)
    
    try:
        with smtplib.SMTP(settings.SMTP_SERVER, settings.SMTP_PORT) as server:
            server.starttls()
            server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
            server.sendmail(settings.EMAIL_FROM, recipient_email, message.as_string())
        logger.info(f"Email sent successfully to {recipient_email}")
        return True
    except Exception as e:
        logger.error(f"Failed to send email to {recipient_email}: {str(e)}")
        return False

def send_otp_email(email: str, otp: str, name: str = None) -> bool:
    """
    Send OTP verification email to manager
    
    Args:
        email: Email address to send the OTP to
        otp: One-time password for verification
        name: User's name (optional)
    """
    subject = "Verify Your Account - OTP"
    
    # Personalize the greeting if name is provided
    greeting = f"Hello {name}," if name else "Hello,"
    
    html_content = f"""
    <html>
    <body>
        <h2>Account Verification</h2>
        <p>{greeting}</p>
        <p>Thank you for registering with our service. Please use the following OTP to verify your account:</p>
        <h3 style="background-color: #f0f0f0; padding: 10px; text-align: center; font-size: 24px;">{otp}</h3>
        <p>This OTP is valid for 10 minutes.</p>
        <p>If you did not request this verification, please ignore this email.</p>
    </body>
    </html>
    """
    
    text_content = f"{greeting}\n\nYour OTP for account verification is: {otp}. This OTP is valid for 10 minutes."
    
    return send_email(email, subject, html_content, text_content)

def send_employee_verification_email(email: str, manager_name: str, company_name: str, verification_token: str) -> bool:
    """Send invitation email to employee with verification token"""
    
    subject = f"Invitation to join {company_name}"
    html_content = f"""
    <html>
    <body>
        <h2>You've been invited!</h2>
        <p>Hello,</p>
        <p>{manager_name} from {company_name} has invited you to join their team.</p>
        <p>Please use the following verification key to set up your account:</p>
        <p><strong>{verification_token}</strong></p>
        <p>This key will expire in 7 days.</p>
        <p>If you did not expect this invitation, please ignore this email.</p>
    </body>
    </html>
    """
    text_content = f"""
    Hello,
    
    {manager_name} from {company_name} has invited you to join their team.
    
    Please use the following verification key to set up your account:
    {verification_token}
    
    This token will expire in 7 days.
    
    If you did not expect this invitation, please ignore this email.
    """
    
    return send_email(email, subject, html_content, text_content)




def send_meeting_notification(
    email: str,
    meeting_title: str,
    meeting_date: Union[datetime, List[datetime]],  # Can be a single date or list of dates
    meeting_location: str,
    created_by: str,
    is_request: bool = False
) -> bool:
    """Send meeting notification email"""
    # Handle single date or multiple proposed dates
    if isinstance(meeting_date, list):
        # Format multiple proposed dates
        formatted_dates = "<ul>"
        for date in meeting_date:
            formatted_dates += f"<li>{date.strftime('%A, %B %d, %Y at %I:%M %p')}</li>"
        formatted_dates += "</ul>"
        date_display = f"Proposed dates: {formatted_dates}"

        # Plain text version
        plain_dates = "\n".join([f"- {date.strftime('%A, %B %d, %Y at %I:%M %p')}" for date in meeting_date])
        plain_date_display = f"Proposed dates:\n{plain_dates}"
    else:
        # Format single date
        formatted_date = meeting_date.strftime("%A, %B %d, %Y at %I:%M %p")
        date_display = f"Date & Time: {formatted_date}"
        plain_date_display = f"Date & Time: {formatted_date}"

    if is_request:
        subject = f"New Meeting Request: {meeting_title}"
        action_text = "requested a meeting"
    else:
        subject = f"New Meeting Scheduled: {meeting_title}"
        action_text = "scheduled a meeting"

    html_content = f"""
    <html>
    <body>
        <h2>{subject}</h2>
        <p>{created_by} has {action_text} with you:</p>
        <div style="background-color: #f0f0f0; padding: 15px; margin: 10px 0;">
            <p><strong>Title:</strong> {meeting_title}</p>
            <p><strong>{date_display}</strong></p>
            <p><strong>Location:</strong> {meeting_location}</p>
        </div>
        <p>Please log in to your account to view more details or respond to this meeting.</p>
    </body>
    </html>
    """

    text_content = f"""
    {subject}

    {created_by} has {action_text} with you:

    Title: {meeting_title}
    {plain_date_display}
    Location: {meeting_location}

    Please log in to your account to view more details or respond to this meeting.
    """

    return send_email(email, subject, html_content, text_content)

def send_meeting_status_update(
    email: str,
    meeting_title: str,
    meeting_date: datetime,
    status: str,
    reason: Optional[str] = None
) -> bool:
    """Send meeting status update email"""
    formatted_date = meeting_date.strftime("%A, %B %d, %Y at %I:%M %p")
    
    status_map = {
        "accepted": "accepted",
        "rejected": "declined",
        "cancelled": "cancelled"
    }
    
    status_text = status_map.get(status.lower(), status)
    subject = f"Meeting {status_text.capitalize()}: {meeting_title}"
    
    html_content = f"""
    <html>
    <body>
        <h2>Meeting Update</h2>
        <p>Your meeting has been <strong>{status_text}</strong>:</p>
        <div style="background-color: #f0f0f0; padding: 15px; margin: 10px 0;">
            <p><strong>Title:</strong> {meeting_title}</p>
            <p><strong>Date & Time:</strong> {formatted_date}</p>
        </div>
    """
    
    text_content = f"""
    Meeting Update
    
    Your meeting has been {status_text}:
    
    Title: {meeting_title}
    Date & Time: {formatted_date}
    """
    
    if reason:
        html_content += f"<p><strong>Reason:</strong> {reason}</p>"
        text_content += f"\nReason: {reason}"
    
    html_content += """
        <p>Please log in to your account to view more details.</p>
    </body>
    </html>
    """
    
    text_content += "\nPlease log in to your account to view more details."
    
    return send_email(email, subject, html_content, text_content)

def send_manager_approval_email(recipient_email: str, recipient_name: str):
    """
    Send an email notification when a manager's account is approved.

    :param recipient_email: Email address of the manager
    :param recipient_name: Name of the manager
    :return: True if the email was sent successfully, False otherwise
    """
    subject = "Your Manager Account Has Been Approved"

    # Create the email content
    content = f"""
    <html>
    <body>
        <h2>Account Approval</h2>
        <p>Hello {recipient_name},</p>
        <p>We are pleased to inform you that your manager account has been approved.</p>
        <p>You can now log in to the MeetyFi platform and start managing your team.</p>
        <p>If you have any questions or need assistance, please don't hesitate to contact our support team.</p>
        <p>Thank you for choosing MeetyFi!</p>
        <p>Best regards,<br>MeetyFi Team</p>
    </body>
    </html>
    """

    try:
        send_email(recipient_email, subject, content)
        return True
    except Exception as e:
        print(f"Error sending manager approval email: {str(e)}")
        return False

def send_manager_rejection_email(recipient_email: str, recipient_name: str, reason: str = None):
    """
    Send an email notification when a manager's account is rejected.

    :param recipient_email: Email address of the manager
    :param recipient_name: Name of the manager
    :param reason: Reason for rejection (optional)
    :return: True if the email was sent successfully, False otherwise
    """
    subject = "Your Manager Account Application Status"

    # Create the email content
    content = f"""
    <html>
    <body>
        <h2>Account Application Status</h2>
        <p>Hello {recipient_name},</p>
        <p>We regret to inform you that your application for a manager account has not been approved at this time.</p>
    """

    if reason:
        content += f"<p><strong>Reason:</strong> {reason}</p>"

    content += """
        <p>If you believe this decision was made in error or if you would like to provide additional information, 
        please contact our support team.</p>
        <p>Thank you for your interest in MeetyFi.</p>
        <p>Best regards,<br>MeetyFi Team</p>
    </body>
    </html>
    """

    try:
        send_email(recipient_email, subject, content)
        return True
    except Exception as e:
        print(f"Error sending manager rejection email: {str(e)}")
        return False