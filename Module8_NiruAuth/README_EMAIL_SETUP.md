# Email Service Setup Guide

This guide explains how to configure the email service for AmaniQuery to send verification emails and notifications via Gmail SMTP.

## Prerequisites

1. A Gmail account: `amaniquery@gmail.com`
2. Gmail App Password (required for SMTP authentication)

## Setting Up Gmail App Password

Since Gmail requires app-specific passwords for SMTP access, follow these steps:

1. **Enable 2-Step Verification** (if not already enabled):
   - Go to your Google Account settings
   - Navigate to Security
   - Enable 2-Step Verification

2. **Generate App Password**:
   - Go to Google Account → Security
   - Under "2-Step Verification", click "App passwords"
   - Select "Mail" as the app and "Other" as the device
   - Enter "AmaniQuery" as the custom name
   - Click "Generate"
   - Copy the 16-character password (you'll need this for the environment variable)

## Environment Variables

Add the following environment variables to your `.env` file:

```env
# Gmail SMTP Configuration
GMAIL_SENDER_EMAIL=amaniquery@gmail.com
GMAIL_APP_PASSWORD=your_16_character_app_password_here

# Optional: Customize SMTP settings (defaults shown)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
EMAIL_SENDER_NAME=AmaniQuery

# Frontend URL for email links
FRONTEND_URL=http://localhost:3000  # Change to your production URL
```

## Email Features

The email service supports:

1. **Email Verification**: Sent automatically when users register
2. **Password Reset**: Sent when users request password reset
3. **Welcome Email**: Sent after successful email verification
4. **General Notifications**: Can be used for any custom notifications

## Usage in Code

```python
from Module8_NiruAuth.services.email_service import get_email_service

# Get email service instance
email_service = get_email_service()

# Send verification email
email_service.send_verification_email(
    to_email="user@example.com",
    verification_token="token_here"
)

# Send password reset email
email_service.send_password_reset_email(
    to_email="user@example.com",
    reset_token="token_here"
)

# Send welcome email
email_service.send_welcome_email(
    to_email="user@example.com",
    name="User Name"
)

# Send custom notification
email_service.send_notification_email(
    to_email="user@example.com",
    subject="Custom Subject",
    message="Your custom message here"
)
```

## Email Templates

All emails use HTML templates with:
- Responsive design
- AmaniQuery branding
- Clear call-to-action buttons
- Plain text fallback

## Troubleshooting

### Email Not Sending

1. **Check App Password**: Ensure the Gmail app password is correctly set in environment variables
2. **Check 2-Step Verification**: Make sure 2-Step Verification is enabled on the Gmail account
3. **Check Logs**: Review application logs for SMTP error messages
4. **Test Connection**: Verify SMTP server and port settings

### Common Errors

- **SMTPAuthenticationError**: Invalid app password or 2-Step Verification not enabled
- **SMTPException**: Network issues or incorrect SMTP server/port
- **Connection Timeout**: Firewall blocking SMTP port 587

## Security Notes

- Never commit the Gmail app password to version control
- Use environment variables for all sensitive credentials
- Consider using a dedicated email service (SendGrid, AWS SES) for production
- Regularly rotate app passwords

## Production Recommendations

For production environments, consider:
1. Using a dedicated email service (SendGrid, AWS SES, Mailgun)
2. Implementing email queue system for reliability
3. Adding email delivery tracking
4. Setting up bounce and complaint handling
5. Using a custom domain for sender email

