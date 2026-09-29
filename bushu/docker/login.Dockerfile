FROM python:3.11-slim
WORKDIR /app
COPY denglu_shouye_xietong/backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY denglu_shouye_xietong/backend .
CMD ["sh", "-c", "gunicorn -w 2 -b 0.0.0.0:${PORT:-10000} --timeout 120 'app:chuangjian_yingyong()'"]
