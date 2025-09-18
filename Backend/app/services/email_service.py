import os
from azure.communication.email import EmailClient


class EmailService:
    def __init__(self):
        connection_string = os.getenv('AZURE_COMMUNICATION_CONNECTION_STRING')
        self.sender_email = os.getenv('AZURE_EMAIL_SENDER')

        if not connection_string or not self.sender_email:
            raise ValueError("Azure Communication Services configuration missing in environment variables")

        self.client = EmailClient.from_connection_string(connection_string)

    def send_otp_email(self, recipient_email: str, otp_code: str, user_name: str = None) -> bool:
        """
        Send OTP email to the recipient

        Args:
            recipient_email: Email address to send OTP to
            otp_code: The 6-digit OTP code
            user_name: Optional user name for personalization

        Returns:
            bool: True if email was sent successfully, False otherwise
        """
        try:
            # Create email content
            subject = "Your Login Code - SentiFinance"

            # HTML email template
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <style>
                    body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5; }}
                    .container {{ max-width: 600px; margin: 0 auto; background-color: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
                    .header {{ text-align: center; margin-bottom: 30px; }}
                    .otp-code {{ font-size: 32px; font-weight: bold; color: #2563eb; text-align: center; letter-spacing: 4px; margin: 30px 0; padding: 20px; background-color: #f8fafc; border-radius: 8px; border: 2px dashed #2563eb; }}
                    .message {{ color: #374151; line-height: 1.6; margin-bottom: 20px; }}
                    .footer {{ color: #6b7280; font-size: 12px; text-align: center; margin-top: 30px; padding-top: 20px; border-top: 1px solid #e5e7eb; }}
                    .warning {{ color: #dc2626; font-size: 14px; margin-top: 15px; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1 style="color: #1f2937; margin: 0;">SentiFinance</h1>
                        <p style="color: #6b7280; margin: 5px 0 0 0;">Login Verification Code</p>
                    </div>

                    <div class="message">
                        <p>Hello{f" {user_name}" if user_name else ""},</p>
                        <p>Your login verification code is:</p>
                    </div>

                    <div class="otp-code">{otp_code}</div>

                    <div class="message">
                        <p>Enter this code on the login page to complete your sign-in.</p>
                        <p class="warning"><strong>Important:</strong> This code will expire in 24 hours. Do not share this code with anyone.</p>
                    </div>

                    <div class="footer">
                        <p>If you didn't request this code, please ignore this email.</p>
                        <p>&copy; 2025 SentiFinance. All rights reserved.</p>
                    </div>
                </div>
            </body>
            </html>
            """

            # Plain text version
            plain_text = f"""
            SentiFinance - Login Verification Code

            Hello{f" {user_name}" if user_name else ""},

            Your login verification code is: {otp_code}

            Enter this code on the login page to complete your sign-in.

            Important: This code will expire in 24 hours. Do not share this code with anyone.

            If you didn't request this code, please ignore this email.

            © 2025 SentiFinance. All rights reserved.
            """

            # Create email message using the new API structure
            message = {
                "senderAddress": self.sender_email,
                "recipients": {
                    "to": [{"address": recipient_email}]
                },
                "content": {
                    "subject": subject,
                    "plainText": plain_text,
                    "html": html_content
                }
            }

            # Send email
            poller = self.client.begin_send(message)

            result = poller.result()

            if hasattr(result, 'status'):
                return result.status == "Succeeded"
            elif isinstance(result, dict):
                return result.get('status') == "Succeeded"
            else:
                return True

        except Exception as e:
            print(f"Error sending OTP email: {str(e)}")
            return False

    def send_welcome_email(self, recipient_email: str, user_name: str, role: str) -> bool:
        """
        Send welcome email to new users (for future use when RMs add clients)

        Args:
            recipient_email: Email address of the new user
            user_name: Name of the user
            role: User role (Client/RM)

        Returns:
            bool: True if email was sent successfully, False otherwise
        """
        try:
            subject = "Welcome to SentiFinance"

            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <style>
                    body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5; }}
                    .container {{ max-width: 600px; margin: 0 auto; background-color: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
                    .header {{ text-align: center; margin-bottom: 30px; }}
                    .message {{ color: #374151; line-height: 1.6; margin-bottom: 20px; }}
                    .footer {{ color: #6b7280; font-size: 12px; text-align: center; margin-top: 30px; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1 style="color: #1f2937; margin: 0;">Welcome to SentiFinance</h1>
                    </div>

                    <div class="message">
                        <p>Hello {user_name},</p>
                        <p>Welcome to SentiFinance! Your account has been created as a <strong>{role}</strong>.</p>
                        <p>You can now log in using your email address. We use passwordless authentication with email verification codes for enhanced security.</p>
                        <p>To get started, simply visit the login page and enter your email address.</p>
                    </div>

                    <div class="footer">
                        <p>&copy; 2025 SentiFinance. All rights reserved.</p>
                    </div>
                </div>
            </body>
            </html>
            """

            message = {
                "senderAddress": self.sender_email,
                "recipients": {
                    "to": [{"address": recipient_email}]
                },
                "content": {
                    "subject": subject,
                    "html": html_content
                }
            }

            poller = self.client.begin_send(message)
            result = poller.result()

            if hasattr(result, 'status'):
                return result.status == "Succeeded"
            elif isinstance(result, dict):
                return result.get('status') == "Succeeded"
            else:
                return True

        except Exception as e:
            print(f"Error sending welcome email: {str(e)}")
            return False