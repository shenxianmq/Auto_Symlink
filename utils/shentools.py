import os
import sys
import re
import shlex
import pytz
import uuid
import yaml
import logging
from croniter import croniter
from logging.handlers import RotatingFileHandler
from datetime import datetime, timedelta

symlink_name_dict = {"symlink":"软链接","strm":"strm文件"}

def print_message(message):
    timestamp = datetime.now().strftime("[%Y/%m/%d %H:%M:%S]")
    trim_log_file('./config/auto_symlink.log')
    # print(f"{timestamp}{message}")
    logging.info(message)


def get_uuid():
    random_uuid = str(uuid.uuid4())
    return random_uuid

#读取配置文件
def read_config(config_path="./config/config.yaml"):
    try:
        with open(config_path, 'r', encoding='utf-8') as file:
            data = yaml.safe_load(file)
        return data
    except Exception as e:
        print_message(f"配置文件出现问题: {e}")
        return None

def read_last_sync_config(config_path="./config/last_sync.yaml"):
    try:
        with open(config_path, 'r', encoding='utf-8') as file:
            data = yaml.safe_load(file)
        if data:
            return data.get('last_sync_list',[])
        else:
            return []
    except Exception as e:
        print_message(f"配置文件出现问题:{e}")
        return []


def read_backup_list(config_path="./config/backup_list.yaml"):
    if not os.path.exists(config_path):
        with open(config_path, 'w') as file:
            yaml.dump('{}', file, default_flow_style=False, allow_unicode=True)
    try:
        with open(config_path, 'r') as file:
            data = yaml.safe_load(file)
        if data:
            return data
        else:
            return {}
    except Exception as e:
        print_message(f"配置文件出现问题:{config_path} => {e}")
        return {}

def yaml_load(yaml_path):
    with open(yaml_path, 'r')as file:
        data = yaml.safe_load(file)
    return data

def yaml_dump(yaml_path,data):
    with open(yaml_path, 'w') as file:
        yaml.dump(data, file, default_flow_style=False, allow_unicode=True)

def save_last_sync_config(sync_list):
    symlink_dirs = [entry.get('symlink_dir', '') for entry in sync_list]
    new_data = {'last_sync_list': symlink_dirs}
    with open('./config/last_sync.yaml', 'w') as file:
        yaml.dump(new_data, file, default_flow_style=False, allow_unicode=True)
    return new_data

def save_backup_list(config_path="./config/backup_list.yaml",data=""):
    with open(config_path, 'w') as file:
        yaml.dump(data, file, default_flow_style=False, allow_unicode=True)

def get_rsync_command(source_dir,target_dir,ext):
    include = ""
    if ";" in ext:
        try:
            ext = [f'*{item.strip()}' for item in ext.split(';')]
        except:
            ext = "*"
            print_message(f"定时备份后缀名配置不正确,默认备份全部文件,请检查相关配置:{source_dir}")
    if ext == "*":
        include = '--exclude="*.DS_Store"'
        command  = ["rsync","-avur","--delete",f'{source_dir}/',target_dir ]
    else:
        include = ' '.join([f'--include="{item}"' for item in ext]) + ' --exclude="*.*"'
        command  = ["rsync","-avur","--delete",include,shlex.quote(f'{source_dir}/'), shlex.quote(target_dir)]
    return command

#日志处理
def configure_logging(log_file='./config/auto_symlink.log', max_log_size_bytes=10 * 1024 * 1024, date_format='%Y-%m-%d %H:%M:%S'):
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

#确保日志大小在10m以内
def trim_log_file(log_file_path,max_log_size_bytes=10 * 1024 * 1024):
    if not os.path.exists(log_file_path):
        return
    max_log_size_bytes = 10 * 1024 * 1024  # 指定的最大日志文件大小，单位是字节
    retention_size_bytes = int(10 * 1024 * 1024 * 0.5)  # 保留的日志内容大小，单位是字节

    # 获取当前日志文件大小
    current_size = os.path.getsize(log_file_path)

    # 如果当前大小超过最大大小
    if current_size > max_log_size_bytes:
        # 读取日志文件内容
        with open(log_file_path, 'rb') as file:
            # 移动文件指针到倒数 retention_size_bytes 的位置
            file.seek(-retention_size_bytes, os.SEEK_END)
            # 读取剩余内容
            retained_content = file.read()

        # 将保留的内容写回文件
        with open(log_file_path, 'wb') as file:
            file.write(retained_content)

#重启事件
def send_restart_signal(method_list=[]):
    if method_list:
        if not isinstance(method_list,list):
            method_list = [method_list]
    else:
        method_list = []
    yaml_dump(yaml_path='./config/restart.yaml',data=method_list)


def restart_program():
    script_path = sys.argv[0]
    print(sys.executable, sys.executable, script_path, *sys.argv[1:])
    os.execl(sys.executable, sys.executable, script_path, *sys.argv[1:])

#定时任务处理
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

def get_next_run_time(seconds=10):
    """
    获取下一次运行时间（默认为当前时间后10秒）
    """
    current_time = datetime.now()
    next_run_time = current_time + timedelta(seconds=seconds)
    return next_run_time

def get_scheduled_time(expression,action="运行"):
 # 判断是否为纯数字
        if re.match(r'^\d+$', expression):
            seconds = int(expression)
            message = f'{action}间隔为{seconds}秒'
            return seconds,message  # 如果是纯数字,直接返回
        # 尝试使用 eval 计算数学表达式
        try:
            result = eval(expression)
            seconds = int(max(0, result))
            message = f'{action}间隔为{seconds}秒'
            return seconds,message
        except Exception:
            pass  # 不是数学表达式,继续检查是否为 cron 表达式

        # 判断是否为 cron 表达式
        try:
            current_time = datetime.now().timestamp()
            cron_iter = croniter(expression, start_time=datetime.fromtimestamp(current_time))
            next_run_date = cron_iter.get_next(datetime)
            next_run_time = next_run_date.timestamp()
            seconds = max(0, next_run_time - current_time)
            message = f'下次{action}时间为{next_run_date}'
            return seconds,message
        except ValueError:
            raise ValueError(f"cron表达式{expression}错误,请参照配置文件中的示例进行更改,不要通过在线生成工具生成cron表达式,程序可能无法识别")

if __name__ == '__main__':
    pass