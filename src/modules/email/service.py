from email.message import EmailMessage
import smtplib

from config import settings


class EmailService:
    @staticmethod
    def send_email(
        to_email: str, title: str, text: str, from_email: str = settings.MAIL_FROM
    ):
        message = EmailMessage()
        message["From"] = from_email
        message["To"] = to_email
        message["Subject"] = title
        message.set_content(text)

        with smtplib.SMTP(settings.MAIL_SERVER, settings.MAIL_PORT) as server:
            server.send_message(message)
