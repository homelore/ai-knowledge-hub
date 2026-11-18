FROM python:3.11-slim

WORKDIR /app

# Install dependencies first (better Docker layer caching)
COPY backend/requirements.txt ./backend/requirements.txt
# 使用阿里云 PyPI 镜像：国内服务器直连 pypi.org 经常在拉取中途断开
RUN pip install --no-cache-dir \
    -i https://mirrors.aliyun.com/pypi/simple/ \
    --timeout 60 --retries 3 \
    -r backend/requirements.txt

# Copy backend source code
COPY backend/ ./backend/

# Copy content (Markdown articles) — config.py reads from ../content/
COPY content/ ./content/

# Create data directory for SQLite
RUN mkdir -p ./backend/data

WORKDIR /app/backend

EXPOSE 8000

# Run uvicorn in production mode (no reload)
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
