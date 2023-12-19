from typing import Mapping
from watcher.FileWatcher import FileMonitor
from utils.shentools import *
import os
import time

if __name__ == '__main__':
    working_directory = os.path.dirname(os.path.abspath(__file__))
    os.chdir("/Users/shenxian/PycharmProjects/Auto_Symlink")
    yaml_data = read_config('./config/config.yaml')
    sync_list = yaml_data.get('sync_list')
    configure_logging(log_file='./config/auto_symlink.log', max_log_size_bytes=10 * 1024 * 1024, date_format='%Y-%m-%d %H:%M:%S')
    FileMonitor(sync_list).start()
    while True:
        time.sleep(3600)