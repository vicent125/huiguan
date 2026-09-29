FROM python:3.11-slim
WORKDIR /app
COPY system_report_whether/backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY system_report_whether/backend .
CMD ["sh", "-c", "gunicorn -w 2 -b 0.0.0.0:${PORT:-10000} --timeout 120 'app:create_app()'"]
