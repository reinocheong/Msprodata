#!/bin/sh
set -e

# 在启动应用前，先执行数据库初始化和数据迁移
# 使用 --app wsgi:app 来明确指定应用入口，解决 ImportError
echo "Attempting to initialize the database by specifying app entrypoint..."
/usr/local/bin/flask --app wsgi:app init-db --migrate-data

# 启动 Gunicorn 服务
echo "Starting Gunicorn server..."
/usr/local/bin/gunicorn --bind 0.0.0.0:${PORT:-5000} --timeout 300 --workers 2 --worker-class gevent --access-logfile - --error-logfile - wsgi:app
