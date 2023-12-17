import os
import sys
import time
import yaml
from utils.shentools import *
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class ConfigFileWatcher:
    def __init__(self, watching_folder='./config', config_filenames=["config.yaml", "last_sync.yaml"]):
        self.watching_folder = watching_folder
        self.config_filenames = config_filenames
        self.event_handler = ConfigFileHandler(watching_folder,config_filenames)
        self.observer = Observer()

    def start_watching(self):
        self.observer.schedule(self.event_handler, path=self.watching_folder, recursive=False)
        print_message('配置文件监测已经开启')
        self.observer.start()
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            self.observer.stop()
        self.observer.join()

class ConfigFileHandler(FileSystemEventHandler):
    def __init__(self,watching_folder,config_filenames):
        super().__init__()
        self.watching_folder = watching_folder
        self.config_files = [os.path.join(watching_folder,f) for f in config_filenames]
        self.config_filenames = config_filenames
        self.config_dict = {}
        self.initial_config()

    def initial_config(self):
        for config_file in self.config_files:
            try:
                with open(config_file, 'r', encoding='utf-8') as file:
                    data = yaml.safe_load(file)
                config_filename = os.path.split(config_file)[1]
                self.config_dict[config_filename] = data
            except Exception as e:
                self.config_dict[config_filename] = []

    def read_config(self,config_file):
        try:
            with open(config_file, 'r', encoding='utf-8') as file:
                data = yaml.safe_load(file)
            return data
        except Exception as e:
            return {}

    def on_modified(self, event):
        file_name = os.path.split(event.src_path)[1]
        #文件发生更改时，检测前后两次文件的配置是否一致，如果不一致，则重启程序
        if file_name in self.config_filenames:
            yaml_data = self.read_config(event.src_path)
            last_yaml_data = self.config_dict.get(file_name)
            if last_yaml_data != yaml_data:
                print_message(f'监测到配置文件发生更改,即将重启程序')
                self.config_dict[file_name] = yaml_data
                restart_program()

if __name__ == "__main__":
    working_directory = os.path.dirname(os.path.abspath(__file__))
    os.chdir(working_directory)
    watching_folder = "./config"
    config_filenames = ["config.yaml", "last_sync.yaml"]  # Replace with your actual config file paths
    watcher = ConfigFileWatcher(watching_folder, config_filenames)
    watcher.start_watching()
