#!/bin/sh
set -e

# 使用 python 脚本来初始化数据库
echo "Attempting to initialize the database via Python script..."
/usr/local/bin/python run_init_db.py

# 启动 Gunicorn 服务
echo "Starting Gunicorn server..."
/usr/local/bin/gunicorn --bind 0.0.0.0:${PORT:-5000} --timeout 300 --workers 2 --worker-class gevent --access-logfile - --error-logfile - wsgi:app
