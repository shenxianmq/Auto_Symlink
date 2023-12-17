import os
import time
import threading
from utils.shentools import *
from auto_symlink import AutoSync

configure_logging(log_file='./config/auto_symlink.log', max_log_size_bytes=10 * 1024 * 1024, date_format='%Y-%m-%d %H:%M:%S')

def main():
    auto_sync_instance = AutoSync()

    thread1 = threading.Thread(target=auto_sync_instance.restart_sync)
    thread1.start()
    thread1.join()

def keep_alive():
    while True:
        time.sleep(3600)  # 线程保持活动，防止容器退出

if __name__ == '__main__':
    working_directory = os.path.dirname(os.path.abspath(__file__))
    os.chdir(working_directory)
    time.sleep(3)
    # 启动主程序线程
    main_thread = threading.Thread(target=main)
    main_thread.start()

    # 启动保持活动的线程
    keep_alive_thread = threading.Thread(target=keep_alive)
    keep_alive_thread.start()

    # 等待主程序线程结束
    main_thread.join()

    # 主程序运行结束后，保持活动的线程也会结束
    keep_alive_thread.join()
