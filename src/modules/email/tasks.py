import dramatiq
from dramatiq.brokers.rabbitmq import RabbitmqBroker

from config import settings
from modules.email.service import EmailService
from modules.email.templates import EmailTemplates

broker = RabbitmqBroker(
    host=settings.RABBITMQ_DEFAULT_HOST, port=settings.RABBITMQ_DEFAULT_PORT
)
dramatiq.set_broker(broker)


@dramatiq.actor(
    queue_name="email_verification",
    max_retries=3,
    min_backoff=15000,
    max_backoff=300000,
    time_limit=60000,
)
def send_verification_link_email_task(
    link: str,
    to_email: str,
):
    EmailService.send_email(
        to_email=to_email,
        title=EmailTemplates.VERIFICATION_SUBJECT,
        text=EmailTemplates.VERIFICATION_TEXT.format(link=link),
    )


@dramatiq.actor(
    queue_name="email_password_reset",
    max_retries=5,
    min_backoff=30000,
    max_backoff=600000,
    time_limit=60000,
)
def send_password_reset_email_task(link: str, to_email: str):
    EmailService.send_email(
        to_email=to_email,
        title=EmailTemplates.PASSWORD_RESET_SUBJECT,
        text=EmailTemplates.PASSWORD_RESET_TEXT.format(link=link),
    )
