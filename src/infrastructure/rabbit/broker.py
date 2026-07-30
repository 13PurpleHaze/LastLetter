from dramatiq.brokers.rabbitmq import RabbitmqBroker

from config import settings

broker = RabbitmqBroker(
    host=settings.RABBITMQ_DEFAULT_HOST,
    port=settings.RABBITMQ_DEFAULT_PORT,
)
