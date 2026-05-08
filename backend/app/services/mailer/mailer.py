from __future__ import annotations

import smtplib
import uuid
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from app.models.emaillog import EmailLog
from app.email.renderer import TemplateRenderer
from app.config.settings import settings
from app.utils.logger import logger


class Mailer:
    def __init__(self):
        self.smtp_server = settings.email_host
        self.smtp_port = settings.email_port or 587
        self.username = settings.email_user
        self.password = settings.email_pass
        self.renderer = TemplateRenderer()

    def send_email(self, to_email, subject, template_name, context, user_id=None, db=None):
        tracking_id = str(uuid.uuid4())
        context['message_id'] = tracking_id
        context.setdefault('tracking_url', 'https://yourdomain.com/track')

        html_content = self.renderer.render_template(template_name, context)

        msg = MIMEMultipart('alternative')
        msg['Message-ID'] = f"<{tracking_id}@yourdomain.com>"
        msg['From'] = self.username
        msg['To'] = to_email
        msg['Subject'] = subject
        msg.attach(MIMEText(html_content, 'html'))

        email_log = EmailLog(
            user_id=user_id,
            subject=subject,
            event_type=context.get('event_type', 'unknown'),
            status='sent',
            message_id=tracking_id
        )

        if db:
            db.add(email_log)

        try:
            smtp_factory = smtplib.SMTP_SSL if self.smtp_port == 465 else smtplib.SMTP
            with smtp_factory(self.smtp_server, self.smtp_port, timeout=30) as server:
                if self.smtp_port != 465:
                    server.starttls()
                server.login(self.username, self.password)
                server.send_message(msg)

            if db:
                db.commit()

            return True

        except Exception as e:
            logger.error("Failed to send email: %s", e)

            email_log.status = 'failed'
            if db:
                db.commit()

            return False


def create_mailer() -> Mailer | None:
    if not all([settings.email_host, settings.email_user, settings.email_pass]):
        logger.warning("Mailer disabled: missing email config")
        return None
    return Mailer()