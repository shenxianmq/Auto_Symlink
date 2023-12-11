import os
import threading
import time
import queue
import logging
from print_message import print_message

class SymlinkChecker:
    def __init__(self, target_directory,num_threads=4):
        self.target_directory = target_directory
        self.num_threads = num_threads
        self.total_num = 0
        self.broken_num = 0
        self.link_queue = queue.Queue()

    def check_and_remove_dead_symlink(self, link):
        self.total_num += 1
        try:
            target = os.readlink(link)
            if not os.path.exists(target):
                os.remove(link)
                print_message(f"已删除无效软链接: {link}")
                # logging.info(f"已删除无效软链接: {link}")
                self.broken_num += 1
            else:
                print_message(f"已跳过有效软链接: {link}")
        except Exception as e:
            print_message(f"检查软链接时出错: {link}, 错误: {e}")

    def get_symlink_files(self):
        for root, dirs, files in os.walk(self.target_directory):
            for name in files:
                link_path = os.path.join(root, name)
                if os.path.islink(link_path):
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
            thread = threading.Thread(target=self.process_symlinks_in_thread, args=(thread_name,))
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
        print_message("开始清理无效软链接...")
        # logging.info("开始清理无效软链接...")
        self.process_symlinks()
        end_time = time.time()
        total_time = end_time - start_time
        message = f"总耗时: {total_time:.2f} 秒, 总软链接数: {self.total_num}, 已清除无效软链接数: {self.broken_num}"
        print_message(message)
        # logging.info(message)
        return total_time