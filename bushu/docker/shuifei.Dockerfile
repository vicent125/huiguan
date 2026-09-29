FROM python:3.11-slim
WORKDIR /app
COPY zhineng_shuifei/backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY zhineng_shuifei/backend .
COPY zhineng_shuifei/web ./web
CMD ["sh", "-c", "gunicorn -w 2 -b 0.0.0.0:${PORT:-10000} --timeout 120 yingyong:app"]
