FROM python:3.11-slim
WORKDIR /app
COPY nongyeguanlipingtai/houduan/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY nongyeguanlipingtai/houduan .
CMD ["sh", "-c", "gunicorn -w 2 -b 0.0.0.0:${PORT:-10000} --timeout 120 houduan_jichuxinxiguanli:app"]
