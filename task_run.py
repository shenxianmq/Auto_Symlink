import sys
import os
import time
from utils.shentools import *
from auto_symlink import AutoSync
from watcher.ConfigWatcher import ConfigFileWatcher

class_dict = {'AutoSync':AutoSync,
            'ConfigFileWatcher':ConfigFileWatcher}

def task_run(class_name, method_name):
    if class_name in class_dict:
        # 通过类名获取类
        class_ = class_dict[class_name]
        # 创建类的实例
        instance = class_()
        # 获取并调用指定方法
        method = getattr(instance, method_name)
        #不用try方法,这样能看到完整的报错信息
        method()
    else:
        print(f"Class not found: {class_name}")

if __name__ == '__main__':
    if len(sys.argv) != 3:
        print("Usage: python your_script.py task_run ClassName MethodName")
    class_name = sys.argv[1]
    method_name = sys.argv[2]

    working_directory = os.path.dirname(os.path.abspath(__file__))
    os.chdir(working_directory)
    configure_logging(log_file='./config/auto_symlink.log', max_log_size_bytes=10 * 1024 * 1024, date_format='%Y-%m-%d %H:%M:%S')
    task_run(class_name, method_name)

    while True:
        time.sleep(3600)
