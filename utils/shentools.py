import sys
import pytz
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime, timedelta

symlink_name_dict = {"symlink":"软链接","strm":"strm文件"}

def configure_logging(log_file='./config/auto_symlink.py', max_log_size_bytes=10 * 1024 * 1024, date_format='%Y-%m-%d %H:%M:%S'):
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
    )

    # 创建 RotatingFileHandler，设置日志文件大小
    handler = RotatingFileHandler(log_file, maxBytes=max_log_size_bytes)
    handler.setLevel(logging.INFO)
    handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', datefmt=date_format))

    # 将 handler 添加到 root logger
    logging.getLogger('').addHandler(handler)

def print_message(message):
    timestamp = datetime.now().strftime("[%Y/%m/%d %H:%M:%S]")
    # print(f"{timestamp}{message}")
    logging.info(message)

def restart_program():
    # script_path = sys.argv[0]
    # print(sys.executable, sys.executable, script_path, *sys.argv[1:])
    # os.execl(sys.executable, sys.executable, script_path, *sys.argv[1:])
    with open('./config/restart.txt','w',encoding='utf-8') as f:
        f.write('')
    # sys.exit()

def get_next_run_time(seconds=10):
    """
    获取下一次运行时间（默认为当前时间后10秒）
    """
    current_time = datetime.now()
    next_run_time = current_time + timedelta(seconds=seconds)
    return next_run_time

def get_timezone():
    """
    获取当前环境的时区信息
    """
    local_timezone = pytz.timezone('UTC')  # 默认为UTC，可以根据需要修改

    try:
        # 获取本地时区
        local_timezone = pytz.timezone(pytz.country_timezones['CN'][0])  # 以中国时区为例
    except Exception as e:
        # 如果获取失败，仍然使用UTC
        print(f"Failed to get local timezone: {e}")

    return local_timezone