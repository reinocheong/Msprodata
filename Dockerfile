FROM python:3.9-slim

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    libpango-1.0-0 \
    libharfbuzz0b \
    libpangoft2-1.0-0 \
    libcairo2 \
    procps \
    && rm -rf /var/lib/apt/lists/*

# 设置非root用户
RUN useradd -m myuser && \
    mkdir -p /app && \
    chown myuser:myuser /app

WORKDIR /app

# 先安装依赖（优化构建缓存）
COPY --chown=myuser:myuser requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 拷贝代码
COPY --chown=myuser:myuser . .

# 设置权限
RUN if [ -d "/app/msprodata/excel_data" ]; then chmod -R a+r /app/msprodata/excel_data; fi

# 切换到非root用户
USER myuser

# 启动命令（适配工厂模式）
CMD ["gunicorn", \
    "--bind", "0.0.0.0:5000", \
    "--timeout", "300", \
    "--workers", "2", \
    "--worker-class", "gevent", \
    "--access-logfile", "-", \
    "--error-logfile", "-", \
    "app:app"]  # 假设已按方法1暴露app变量