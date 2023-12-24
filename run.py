import subprocess
import pathlib
import time
import sys
import os
from utils.shentools import *
from utils.create_config import check_config


def monitor_signal(file_path):
    global processes, task_commands
    while not pathlib.Path(file_path).exists():
        time.sleep(1)

    method_list = yaml_load(file_path)
    # 文件出现后，终止之前启动的子进程
    # 删除触发文件
    if os.path.exists(file_path):
        os.remove(file_path)
    # 如果method_list中有任务名,就重启指定任务,如果为空就重启全部任务
    if method_list:
        for method_name in method_list:
            process = processes.get(method_name)
            process.terminate()
            process.wait()
            class_name = task_commands.get(method_name)
            command = ["python", "task_run.py", class_name, method_name]
            process = subprocess.Popen(command)
            processes[method_name] = process
            # 重启进程完成,重新接收重启信号
        monitor_signal(file_path)
    else:
        for method_name, process in processes.items():
            process.terminate()
            process.wait()
            # 重新启动当前程序
        script_path = sys.argv[0]
        os.execl(sys.executable, sys.executable, script_path, *sys.argv[1:])


if __name__ == "__main__":
    working_directory = os.path.dirname(os.path.abspath(__file__))
    os.chdir(working_directory)
    # 移除上次启动留下的重启文件
    monitor_file_path = "./config/restart.yaml"
    if os.path.exists(monitor_file_path):
        os.remove(monitor_file_path)
    if not os.path.exists("./config"):
        os.mkdir("./config")
    configure_logging(
        log_file="./config/auto_symlink.log",
        max_log_size_bytes=10 * 1024 * 1024,
        date_format="%Y-%m-%d %H:%M:%S",
    )
    check_config()
    # 启动四个不同的 Python 文件作为独立的进程
    yaml_data = read_config()
    start_delay = int(yaml_data.get("start_delay: 0", 0))
    if start_delay < 0:
        start_delay = 0
    time.sleep(start_delay)
    processes = {}
    task_commands = {
        "start_watching": "ConfigFileWatcher",
        "restart_sync": "AutoSync",
        "start_observer": "AutoSync",
        "start_sync_scheduled": "AutoSync",
        "start_backup_scheduled": "AutoSync",
        "sync_new_list": "AutoSync",
    }
    for method_name, class_name in task_commands.items():
        command = ["python", "task_run.py", class_name, method_name]
        process = subprocess.Popen(command)
        processes[method_name] = process
        time.sleep(0.5)
    # 启动文件监控循环
    monitor_signal(monitor_file_path)
