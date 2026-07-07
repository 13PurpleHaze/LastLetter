import structlog
import logging
import sys
from opentelemetry import trace

from config import settings


def setup_logging(json_format: bool = True, log_level: str = "INFO"):
    shared_processors: list[structlog.types.Processor] = [
        structlog.contextvars.merge_contextvars,  # Контекст из contextvars
        structlog.stdlib.add_logger_name,  # Имя логгера
        structlog.stdlib.add_log_level,  # Уровень лога
        structlog.processors.TimeStamper(fmt="iso"),  # ISO timestamp
        add_trace_context,
        add_service_name,
    ]
    if json_format:
        renderer = structlog.processors.JSONRenderer()
    else:
        renderer = structlog.dev.ConsoleRenderer(colors=True)

    structlog.configure(
        processors=[
            *shared_processors,
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    formatter = structlog.stdlib.ProcessorFormatter(
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            renderer,
        ],
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.addHandler(handler)
    root_logger.setLevel(log_level)


def add_service_name(logger, method, event_dict):
    event_dict["service"] = settings.APP_NAME
    return event_dict


def add_trace_context(logger, method, event_dict):
    span = trace.get_current_span()
    if span.is_recording():
        ctx = span.get_span_context()
        event_dict["trace_id"] = format(ctx.trace_id, "032x")
        event_dict["span_id"] = format(ctx.span_id, "016x")
    return event_dict
