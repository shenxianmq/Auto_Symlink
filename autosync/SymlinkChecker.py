import os
import threading
import time
import queue
import urllib.parse
from utils.shentools import *


class SymlinkChecker:
    def __init__(
        self, cloud_path, source_folder, target_folder, symlink_mode, num_threads=4
    ):
        self.cloud_path = cloud_path
        self.source_folder = source_folder
        self.target_folder = target_folder
        self.symlink_mode = symlink_mode
        self.num_threads = num_threads
        self.total_num = 0
        self.broken_num = 0
        self.symlink_name = symlink_name_dict.get(self.symlink_mode)
        self.link_queue = queue.Queue()

    def check_and_remove_dead_symlink(self, link):
        self.total_num += 1
        try:
            if os.path.islink(link):
                target = os.readlink(link)
                # 必须在cloud_path存在的情况下才会删除
                if os.path.exists(self.cloud_path) and not os.path.exists(target):
                    os.remove(link)
                    print_message(f"已删除无效{self.symlink_name}: {link}")
                    # logging.info(f"已删除无效{self.symlink_name}: {link}")
                    self.broken_num += 1
            # 如果是strm文件,则读取文件内的链接,判断返回的状态码
            elif link.endswith("strm"):
                strm_in_use = self.check_strm(link)
                if os.path.exists(self.cloud_path) and not strm_in_use:
                    print_message(f"已删除无效{self.symlink_name}:{link}")
                    os.remove(link)
                    self.broken_num += 1
                # print_message(f"已跳过有效{self.symlink_name}: {link}")
                pass
            # 不是软链接也不是strm,文件，只能是无效视频了
            else:
                # 必须在cloud_path存在的情况下才会删除
                if os.path.exists(self.cloud_path) and not os.path.exists(target):
                    os.remove(link)
                    print_message(f"已删除无效{self.symlink_name}: {link}")
                    # logging.info(f"已删除无效{self.symlink_name}: {link}")
                    self.broken_num += 1

        except Exception as e:
            print_message(f"检查{self.symlink_name}/strm文件时出错: {link}, 错误: {e}")

    def check_strm(self, strm_path):
        with open(strm_path, "r") as f:
            strm_link = f.read().strip()
        strm_link = urllib.parse.quote(strm_link)
        file_extension = os.path.splitext(strm_link)[1]
        strm_media_path = strm_path.replace(".txt", "").replace(".strm", file_extension)
        source_file = strm_media_path.replace(self.target_folder, self.source_folder)
        if os.path.exists(source_file):
            return True
        else:
            return False

    def get_symlink_files(self):
        for root, dirs, files in os.walk(self.target_folder):
            for name in files:
                link_path = os.path.join(root, name)
                # symlink模式和strm模式只能留下对应的文件
                if (
                    self.symlink_mode == "symlink"
                    and link_path.lower().endswith(".strm")
                ) or (self.symlink_mode == "strm" and os.path.islink(link_path)):
                    os.remove(link_path)
                    continue
                if os.path.islink(link_path) or link_path.lower().endswith(".strm"):
                    yield link_path

    def process_symlinks_in_thread(self, thread_name):
        while True:
            symlink = self.link_queue.get()
            if symlink is None:
                break
            self.check_and_remove_dead_symlink(symlink)
            self.link_queue.task_done()

    def process_symlinks(self):
        symlink_generator = self.get_symlink_files()

        threads = []
        for i in range(self.num_threads):
            thread_name = f"Thread-{i + 1}"
            thread = threading.Thread(
                target=self.process_symlinks_in_thread, args=(thread_name,)
            )
            threads.append(thread)
            thread.start()

        for symlink in symlink_generator:
            self.link_queue.put(symlink)

        for i in range(self.num_threads):
            self.link_queue.put(None)

        for thread in threads:
            thread.join()

    def run(self):
        # 记录程序运行时间
        start_time = time.time()
        print_message(f"开始清理无效{self.symlink_name}...")
        # logging.info(f"开始清理无效{self.symlink_name}...")
        self.process_symlinks()
        end_time = time.time()
        total_time = end_time - start_time
        message = f"清除无效{self.symlink_name}:总耗时 {total_time:.2f} 秒, 总{self.symlink_name}数: {self.total_num}, 已清除无效{self.symlink_name}数: {self.broken_num}"
        print_message(f"完成::: 清除无效{self.symlink_name}")
        # logging.info(message)
        return total_time, message
