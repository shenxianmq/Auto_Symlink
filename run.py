import os
import time
import threading
import concurrent.futures
from shentools import *
from create_config import create_config
from auto_symlink import AutoSync
from watcher.ConfigWatcher import ConfigFileWatcher

def main():
    current_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    print_message(f"程序运行开始时间: {current_time}")
    auto_sync_instance = AutoSync()
    watching_folder = "./config"
    config_filenames = ["config.yaml", "last_sync.yaml"]  # Replace with your actual config file paths

    # 创建更新目录线程，定时同步线程，目录监控线程
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        executor.submit(ConfigFileWatcher(watching_folder, config_filenames).start_watching)
        executor.submit(auto_sync_instance.start_sync_scheduled)
        executor.submit(auto_sync_instance.run)

def keep_alive(exit_event):
    while not exit_event.is_set():
        time.sleep(3600)  # 线程保持活动，防止容器退出

if __name__ == '__main__':
    working_directory = os.path.dirname(os.path.abspath(__file__))
    os.chdir(working_directory)
    configure_logging(log_file='./config/auto_symlink.log', max_log_size_bytes=10 * 1024 * 1024, date_format='%Y-%m-%d %H:%M:%S')
    if not os.path.exists('./config/config_done.txt'):
        create_config()
    # 使用 threading.Event 作为退出信号
    exit_event = threading.Event()

    # 启动主程序线程
    main_thread = threading.Thread(target=main)
    main_thread.start()

    # 启动保持活动的线程
    keep_alive_thread = threading.Thread(target=keep_alive, args=(exit_event,))
    keep_alive_thread.start()

    # 等待主程序线程结束
    main_thread.join()

    # 设置退出信号
    exit_event.set()

    # 主程序运行结束后，保持活动的线程也会结束
    keep_alive_thread.join()
