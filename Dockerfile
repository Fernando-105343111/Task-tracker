FROM python:3.12-slim AS base
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app ./app

FROM base AS test
COPY requirements-dev.txt .
RUN pip install --no-cache-dir -r requirements-dev.txt
COPY pyproject.toml .
COPY tests ./tests
RUN mkdir /reports
CMD ["python", "-m", "pytest", "--cov=app", "--cov-fail-under=80", "--cov-report=term-missing", "--cov-report=xml:/reports/coverage.xml", "--cov-report=html:/reports/htmlcov", "--junitxml=/reports/junit.xml"]

FROM base AS runtime
ARG COMMIT_SHA=development
ENV COMMIT_SHA=$COMMIT_SHA
LABEL org.opencontainers.image.revision=$COMMIT_SHA
RUN groupadd --gid 10001 appuser && useradd --uid 10001 --gid 10001 --no-create-home appuser
USER appuser
EXPOSE 8000
HEALTHCHECK --interval=10s --timeout=5s --start-period=20s --retries=6 CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/ready', timeout=3)" || exit 1
CMD ["sh", "-c", "python -m flask --app app init-db && exec gunicorn --bind 0.0.0.0:8000 --workers 2 --access-logfile - --error-logfile - 'app:create_app()'"]
