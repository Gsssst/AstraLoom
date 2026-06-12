FROM python:3.12-slim

WORKDIR /app

ARG APT_MIRROR=https://mirrors.aliyun.com/debian
ARG PIP_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple

# 系统依赖
RUN set -eux; \
    sed -i "s|http://deb.debian.org/debian|${APT_MIRROR}|g" /etc/apt/sources.list.d/debian.sources; \
    apt-get update \
      -o Acquire::Retries=5 \
      -o Acquire::http::Timeout=30 \
      -o Acquire::https::Timeout=30; \
    apt-get install -y --no-install-recommends \
      -o Acquire::Retries=5 \
      -o Acquire::http::Timeout=30 \
      -o Acquire::https::Timeout=30 \
      build-essential \
      libpq-dev \
      texlive-latex-base \
      texlive-latex-recommended \
      texlive-fonts-recommended \
    && rm -rf /var/lib/apt/lists/*

# Python 依赖
COPY requirements.txt .
RUN pip install --no-cache-dir \
    --index-url "${PIP_INDEX_URL}" \
    --retries 5 \
    --timeout 120 \
    -r requirements.txt

# 应用代码
COPY . .

RUN chmod +x /app/scripts/docker-start-backend.sh

# 静态文件上传目录
RUN mkdir -p /app/uploads

EXPOSE 8000

# 启动命令
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
