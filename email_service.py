"""
Email Service for Vehicle Detection App
Handles sending email notifications
"""
from flask_mail import Mail, Message
from flask import current_app
import logging

logger = logging.getLogger(__name__)


class EmailService:
    """Service for sending email notifications"""
    
    def __init__(self, mail=None):
        """
        Initialize email service
        
        Args:
            mail: Flask-Mail instance
        """
        self.mail = mail
    
    def send_detection_complete_email(self, to_email, username, detection_type, vehicle_count):
        """
        Send email when detection is complete
        
        Args:
            to_email: Recipient email
            username: Username
            detection_type: Type of detection (image, video, live)
            vehicle_count: Number of vehicles detected
        
        Returns:
            Tuple of (success, message)
        """
        try:
            msg = Message(
                subject=f'Vehicle Detection Complete - {detection_type.title()}',
                recipients=[to_email],
                sender=current_app.config.get('MAIL_DEFAULT_SENDER', 'noreply@vehicledetection.com')
            )
            
            msg.html = f"""
            <html>
            <head>
                <style>
                    body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                    .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                    .header {{ background: #002542; color: white; padding: 20px; text-align: center; }}
                    .content {{ padding: 20px; background: #f9f9f9; }}
                    .stats {{ background: white; padding: 15px; margin: 15px 0; border-radius: 5px; }}
                    .footer {{ text-align: center; padding: 20px; color: #666; font-size: 12px; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>🚗 Vehicle Detection Complete</h1>
                    </div>
                    <div class="content">
                        <p>Hello <strong>{username}</strong>,</p>
                        <p>Your {detection_type} detection has been completed successfully.</p>
                        
                        <div class="stats">
                            <h3>Detection Results:</h3>
                            <p><strong>Vehicle Type:</strong> {detection_type.title()}</p>
                            <p><strong>Vehicles Detected:</strong> {vehicle_count}</p>
                        </div>
                        
                        <p>You can view the detailed results by logging into your account.</p>
                        
                        <p>Thank you for using our Vehicle Detection System!</p>
                    </div>
                    <div class="footer">
                        <p>This is an automated email. Please do not reply.</p>
                    </div>
                </div>
            </body>
            </html>
            """
            
            self.mail.send(msg)
            logger.info(f"Email sent to {to_email}: Detection complete")
            return True, "Email sent successfully"
            
        except Exception as e:
            logger.error(f"Failed to send email: {str(e)}")
            return False, f"Failed to send email: {str(e)}"
    
    def send_backup_complete_email(self, to_email, username, backup_type):
        """
        Send email when backup is complete
        
        Args:
            to_email: Recipient email
            username: Username
            backup_type: Type of backup (database, full)
        
        Returns:
            Tuple of (success, message)
        """
        try:
            msg = Message(
                subject='Database Backup Complete',
                recipients=[to_email],
                sender=current_app.config.get('MAIL_DEFAULT_SENDER', 'noreply@vehicledetection.com')
            )
            
            msg.html = f"""
            <html>
            <head>
                <style>
                    body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                    .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                    .header {{ background: #002542; color: white; padding: 20px; text-align: center; }}
                    .content {{ padding: 20px; background: #f9f9f9; }}
                    .footer {{ text-align: center; padding: 20px; color: #666; font-size: 12px; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>💾 Backup Complete</h1>
                    </div>
                    <div class="content">
                        <p>Hello <strong>{username}</strong>,</p>
                        <p>Your {backup_type} backup has been completed successfully.</p>
                        <p>The backup file is available in your backup directory.</p>
                        <p>Thank you for using our Vehicle Detection System!</p>
                    </div>
                    <div class="footer">
                        <p>This is an automated email. Please do not reply.</p>
                    </div>
                </div>
            </body>
            </html>
            """
            
            self.mail.send(msg)
            logger.info(f"Email sent to {to_email}: Backup complete")
            return True, "Email sent successfully"
            
        except Exception as e:
            logger.error(f"Failed to send email: {str(e)}")
            return False, f"Failed to send email: {str(e)}"
    
    def send_alert_email(self, to_email, username, alert_type, message):
        """
        Send alert email
        
        Args:
            to_email: Recipient email
            username: Username
            alert_type: Type of alert (error, warning, info)
            message: Alert message
        
        Returns:
            Tuple of (success, message)
        """
        try:
            subject = f'Alert: {alert_type}'
            if alert_type == 'error':
                subject = f'⚠️ Error Alert - Vehicle Detection'
            elif alert_type == 'warning':
                subject = f'⚡ Warning - Vehicle Detection'
            
            msg = Message(
                subject=subject,
                recipients=[to_email],
                sender=current_app.config.get('MAIL_DEFAULT_SENDER', 'noreply@vehicledetection.com')
            )
            
            msg.html = f"""
            <html>
            <head>
                <style>
                    body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                    .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                    .header {{ background: #002542; color: white; padding: 20px; text-align: center; }}
                    .content {{ padding: 20px; background: #f9f9f9; }}
                    .alert {{ padding: 15px; margin: 15px 0; border-radius: 5px; }}
                    .error {{ background: #fee; border: 1px solid #fcc; }}
                    .warning {{ background: #fff3cd; border: 1px solid #ffeeba; }}
                    .info {{ background: #d1ecf1; border: 1px solid #bee5eb; }}
                    .footer {{ text-align: center; padding: 20px; color: #666; font-size: 12px; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>🔔 System Alert</h1>
                    </div>
                    <div class="content">
                        <p>Hello <strong>{username}</strong>,</p>
                        <div class="alert {alert_type}">
                            <p><strong>{alert_type.upper()}:</strong></p>
                            <p>{message}</p>
                        </div>
                        <p>Please check your account for more details.</p>
                    </div>
                    <div class="footer">
                        <p>This is an automated email. Please do not reply.</p>
                    </div>
                </div>
            </body>
            </html>
            """
            
            self.mail.send(msg)
            logger.info(f"Email sent to {to_email}: Alert - {alert_type}")
            return True, "Email sent successfully"
            
        except Exception as e:
            logger.error(f"Failed to send email: {str(e)}")
            return False, f"Failed to send email: {str(e)}"
