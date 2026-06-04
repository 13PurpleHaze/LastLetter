from email.message import EmailMessage

import aiosmtplib

from config import settings


class EmailService:
    @staticmethod
    async def send_email(
        to_email: str, title: str, text: str, from_email: str = settings.MAIL_FROM
    ):
        message = EmailMessage()
        message["From"] = from_email
        message["To"] = to_email
        message["Subject"] = title
        message.set_content(text)

        await aiosmtplib.send(
            message, hostname=settings.MAIL_SERVER, port=settings.MAIL_PORT
        )
