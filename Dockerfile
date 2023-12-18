# 使用官方 Python 镜像作为基础镜像
FROM shenxianmq/autosymlink_env:latest

# 设置工作目录
WORKDIR /app

# 将当前目录下的所有文件复制到工作目录
COPY . /app

# 安装依赖
# RUN pip install -i https://pypi.tuna.tsinghua.edu.cn/simple --no-cache-dir -r requirements.txt
# RUN pip install --no-cache-dir -r requirements.txt

# 设置环境变量
ENV PYTHONUNBUFFERED 1

# 赋予脚本执行权限
RUN chmod +x /app/start.sh
RUN chmod +x /app/run.py
RUN chmod +x /app/web.py

# 定义容器启动命令
CMD ["/app/start.sh"]
