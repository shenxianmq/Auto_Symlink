import time
import logging
import os
# import shenmail
from metadata_copyer import MetadataCopyer
from symlink_creater import SymlinkCreator
from symlink_checker import SymlinkChecker
from symlink_dir_checker import SymlinkDirChecker

working_directory = os.path.dirname(os.path.abspath(__file__))
os.chdir(working_directory)

def read_config():
    for root, _, files in os.walk('./config'):
        for file in files:
            if file.endswith('.txt'):
                file_path = os.path.join(root,file)
                yield file_path

def run():
    config_list = read_config()
    for config_file in config_list:
        dir_dict = {}
        with open(config_file, 'r') as file:
            for line in file:
                key, value = line.strip().split("=")
                dir_dict[key.strip()] = value.strip()
        num_threads = 8
        timeout_seconds = 5  # 线程解锁时间
        cloud_path = dir_dict['cloud_path']
        media_dir = dir_dict['media_dir']
        symlink_dir = dir_dict['symlink_dir']
        message_list = []

        if not os.path.exists(cloud_path):
            raise FileNotFoundError(f'挂载目录不存在，请检查挂载目录{cloud_path}')

        metadata_copyer = MetadataCopyer(media_dir, symlink_dir, num_threads)
        message = metadata_copyer.run()
        message_list.append(message)

        symlink_dir_checker = SymlinkDirChecker(symlink_dir, media_dir, num_threads, timeout_seconds)
        message = symlink_dir_checker.run()
        message_list.append(message)

        symlink_checker = SymlinkChecker(symlink_dir, num_threads)
        message = symlink_checker.run()
        message_list.append(message)

        symlink_creator = SymlinkCreator(media_dir, symlink_dir, num_threads)
        message = symlink_creator.run()
        message_list.append(message)
        # for message in message_list:
        # shenmail.send_bark(message)
        # time.sleep(0.5)

if __name__ == "__main__":
    # 配置日志
    log_path = 'auto_symlink.log'
    logging.basicConfig(filename=log_path, level=logging.INFO, format="%(asctime)s [%(levelname)s]: %(message)s")

    current_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    logging.info(f"程序运行开始时间: {current_time}")
    run()
