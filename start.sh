#!/bin/sh
set -e

# 在启动应用前，先执行数据库初始化和数据迁移
# 使用绝对路径 /usr/local/bin/flask 来避免 "flask: not found" 错误
echo "Attempting to initialize the database using absolute path..."
/usr/local/bin/flask init-db --migrate-data

# 启动 Gunicorn 服务
echo "Starting Gunicorn server..."
/usr/local/bin/gunicorn --bind 0.0.0.0:${PORT:-5000} --timeout 300 --workers 2 --worker-class gevent --access-logfile - --error-logfile - wsgi:app
