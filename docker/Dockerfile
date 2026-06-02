FROM python:3.13-slim-trixie

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY poetry.lock pyproject.toml /app/

RUN pip install poetry && \
    poetry config virtualenvs.create false && \
    poetry install --no-root

COPY src/ .

EXPOSE 8000

CMD alembic upgrade head && uvicorn entrypoint:app --host 0.0.0.0 --port 8000 --reload
