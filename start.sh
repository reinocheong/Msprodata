#!/bin/sh
set -e

# 在启动应用前，先执行数据库初始化和数据迁移
# 我们将错误输出重定向到标准输出，这样可以在Render日志中看到所有信息
echo "Attempting to initialize the database..."
flask init-db --migrate-data 2>&1 || echo "Database initialization failed, continuing to start app..."

# 启动 Gunicorn 服务
echo "Starting Gunicorn server..."
/usr/local/bin/gunicorn --bind 0.0.0.0:${PORT:-5000} --timeout 300 --workers 2 --worker-class gevent --access-logfile - --error-logfile - wsgi:app
