import smtplib
import uuid
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from urllib.parse import urlparse

from app.models.emaillog import EmailLog
from app.email.renderer import TemplateRenderer
from app.config.settings import settings
from app.utils.logger import logger





def create_mailer() -> Mailer | None:
    """Create a mailer instance if email settings are configured."""
    if not all([settings.email_host, settings.email_user, settings.email_pass]):
        logger.warning("Mailer is disabled because one or more email settings are missing.")
        return None
    return Mailer()

class Mailer:
    def __init__(self):
        self.smtp_server = settings.email_host
        self.smtp_port = settings.email_port or 587
        self.username = settings.email_user
        self.password = settings.email_pass
        self.renderer = TemplateRenderer()

    def send_email(self, to_email, subject, template_name, context, user_id=None, db=None):
        # Render the email content using Jinja2 templates
       # Prepare tracking data
        tracking_id = str(uuid.uuid4())
        context['message_id'] = tracking_id
    # Optionally set a default tracking_url if not provided
        context.setdefault('tracking_url', 'https://yourdomain.com/track')

        html_content = self.renderer.render_template(template_name, context)

        # Create the email message
        msg = MIMEMultipart('alternative')
        msg['Message-ID'] = f"<{tracking_id}@yourdomain.com>"   # good practice
        msg['From'] = self.username
        msg['To'] = to_email
        msg['Subject'] = subject
        msg.attach(MIMEText(html_content, 'html'))

        # Log the email sending attempt in the database
        email_log = EmailLog(
            user_id=user_id,
            subject=subject,
            event_type=context.get('event_type', 'unknown'),
            status='sent',  # Will be updated if sending fails
            message_id=tracking_id
        )
        if db:
            db.add(email_log)

        try:
            # Connect to the SMTP server and send the email
            smtp_factory = smtplib.SMTP_SSL if self.smtp_port == 465 else smtplib.SMTP
            with smtp_factory(self.smtp_server, self.smtp_port, timeout=30) as server:
                if self.smtp_port != 465:
                    server.starttls()
                server.login(self.username, self.password)
                server.send_message(msg)

            # Email sent successfully
            if db:
                db.commit()  # Commit the successful email log
            return True

        except Exception as e:
            logger.error(
                "Failed to send email: to=%s subject=%s error=%s: %s",
                to_email,
                subject,
                type(e).__name__,
                e,
            )
            # Update the log to reflect failure
            email_log.status = 'failed'
            if db:
                db.commit()  # Commit the failed email log
            return False
