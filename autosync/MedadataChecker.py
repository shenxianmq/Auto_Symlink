import os
import threading
import time
import queue
import urllib.parse
from utils.shentools import *


class MetadadaChecker:
    def __init__(
        self,
        cloud_path,
        source_folder,
        target_folder,
        allowed_extensions,
        num_threads=4,
    ):
        self.cloud_path = cloud_path
        self.source_folder = source_folder
        self.target_folder = target_folder
        self.allowed_extensions = allowed_extensions
        self.num_threads = num_threads
        self.total_num = 0
        self.broken_num = 0
        self.metadata_queue = queue.Queue()

    def check_and_remove_dead_metadata(self, metadata):
        self.total_num += 1
        source_metadata = metadata.replace(self.target_folder, self.source_folder)
        try:
            if os.path.exists(source_metadata):
                return
            elif os.path.exists(self.cloud_path):
                # 必须在cloud_path存在的情况下才会删除
                os.remove(metadata)
                print_message(f"已删除无效元数据: {metadata}")
                # logging.info(f"已删除无效元数据: {metadata}")
                self.broken_num += 1
        except Exception as e:
            print_message(f"检查元数据时出错: {metadata}, 错误: {e}")

    def get_metadata_files(self):
        for root, dirs, files in os.walk(self.target_folder):
            for name in files:
                if name.endswith(self.allowed_extensions):
                    metadata_path = os.path.join(root, name)
                    yield metadata_path

    def process_metadata_in_thread(self, thread_name):
        while True:
            metadata = self.metadata_queue.get()
            if metadata is None:
                break
            source_metadata = metadata.replace(self.target_folder, self.source_folder)
            self.check_and_remove_dead_metadata(metadata)
            self.metadata_queue.task_done()

    def process_metadata(self):
        metadata_generator = self.get_metadata_files()

        threads = []
        for i in range(self.num_threads):
            thread_name = f"Thread-{i + 1}"
            thread = threading.Thread(
                target=self.process_metadata_in_thread, args=(thread_name,)
            )
            threads.append(thread)
            thread.start()

        for metadata in metadata_generator:
            self.metadata_queue.put(metadata)

        for i in range(self.num_threads):
            self.metadata_queue.put(None)

        for thread in threads:
            thread.join()

    def run(self):
        # 记录程序运行时间
        start_time = time.time()
        print_message(f"开始清理无效元数据...")
        # logging.info(f"开始清理无效元数据...")
        self.process_metadata()
        end_time = time.time()
        total_time = end_time - start_time
        message = f"清除无效元数据:总耗时 {total_time:.2f} 秒, 总元数据数: {self.total_num}, 已清除无效元数据数: {self.broken_num}"
        print_message(f"完成::: 清除无效元数据")
        # logging.info(message)
        return total_time, message
