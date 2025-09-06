# 基于官方 Python 镜像
FROM python:3.10-slim

# 设置工作目录
WORKDIR /app

# 复制项目文件
COPY . /app

# 升级 pip 并安装依赖
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# 安装 playwright 浏览器
RUN python -m playwright install --with-deps

# 暴露端口（FastAPI 8000, Flower 5555）
EXPOSE 8000 5555

# 默认命令：启动 uvicorn
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
