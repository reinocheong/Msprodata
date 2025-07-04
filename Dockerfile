# 使用官方 Python 运行时作为父镜像 (改用标准版以确保所有工具链可用)
FROM python:3.11

# 设置容器内的工作目录
WORKDIR /app

# 防止 Python 将 .pyc 文件写入磁盘
ENV PYTHONDONTWRITEBYTECODE 1
# 确保 Python 输出直接发送到终端，不进行缓冲
ENV PYTHONUNBUFFERED 1

# 将 pip 安装可执行文件的目录添加到 PATH 环境变量
# 这是解决 "gunicorn: not found" 错误的关键修复
ENV PATH="/root/.local/bin:${PATH}"

# 安装 WeasyPrint 和其他包所需的系统依赖项
RUN apt-get update && apt-get install -y \
    build-essential \
    python3-dev \
    pango1.0-tools \
    libpangocairo-1.0-0 \
    wkhtmltopdf \
    --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

# 将依赖描述文件复制到容器中
COPY requirements.txt .

# 安装 requirements.txt 中指定的所有 Python 包
RUN pip install --no-cache-dir -r requirements.txt

# 将应用程序的其余代码复制到容器中
COPY . .

# 使用 Gunicorn 运行应用程序的命令
CMD ["/usr/local/bin/python", "-m", "gunicorn", "--bind", "0.0.0.0:10000", "wsgi:app"]