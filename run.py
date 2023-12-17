import subprocess
import pathlib
import time
import sys
import os
from utils.shentools import *
from utils.create_config import check_config

def monitor_file(file_path, processes):
    while not pathlib.Path(file_path).exists():
        time.sleep(1)

    # 文件出现后，终止之前启动的子进程
    for process in processes:
        process.terminate()
        process.wait()

if __name__ == '__main__':
    working_directory = os.path.dirname(os.path.abspath(__file__))
    os.chdir(working_directory)
    check_config()
    # 启动四个不同的 Python 文件作为独立的进程
    processes = []
    task_commonds = ["ConfigFileWatcher start_watching",
                     "AutoSync start_observer",
                     "AutoSync start_sync_scheduled",
                     "AutoSync sync_new_list"]
    for task_command in task_commonds:
        commond = ['python','task_run.py'] + task_command.split(" ")
        process = subprocess.Popen(commond)
        processes.append(process)
        time.sleep(0.5)

    # 启动文件监控循环
    monitor_file_path = './config/restart.txt'
    monitor_file(monitor_file_path, processes)

    # 删除触发文件
    if os.path.exists(monitor_file_path):
        os.remove(monitor_file_path)

    # 重新启动当前程序
    script_path = sys.argv[0]
    os.execl(sys.executable, sys.executable, script_path, *sys.argv[1:])