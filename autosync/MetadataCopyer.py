import os
import threading
import time
import queue
import logging
import shutil
from shentools import *

class MetadataCopyer:
    def __init__(self, source_folder, target_folder,allowed_extensions, num_threads=8):
        self.source_folder = source_folder
        self.target_folder = target_folder
        self.metadata_extensions = allowed_extensions
        self.num_threads = num_threads
        self.copied_metadatas = 0
        self.existing_links = 0
        self.file_queue = queue.Queue()

    def copy_metadata(self, source, target_file, thread_name):
        try:
            if os.path.exists(target_file):
                source_timestamp = os.path.getmtime(source)
                target_timestamp = os.path.getmtime(target_file)
                if source_timestamp > target_timestamp:
                    os.makedirs(os.path.dirname(target_file), exist_ok=True)
                    shutil.copy2(source, target_file)
                    print_message(f"线程 {thread_name}: {source} 到 {target_file}")
                    # logging.info(f"线程 {thread_name}: {source} 到 {target_file}")
                    self.copied_metadatas += 1
                else:
                    # print_message(f"线程 {thread_name} 元数据已存在，跳过:{target_file}")
                    self.existing_links += 1
            else:
                os.makedirs(os.path.dirname(target_file), exist_ok=True)
                shutil.copy2(source, target_file)
                print_message(f"线程 {thread_name}: {source} 到 {target_file}")
                # logging.info(f"线程 {thread_name}: {source} 到 {target_file}")
                self.copied_metadatas += 1
        except Exception as e:
            print_message(f"元数据复制出错:{e}")

    def start_to_copy_metadata(self, thread_name):
        while True:
            source_file = self.file_queue.get()
            if source_file is None:
                break
            relative_path = os.path.relpath(source_file, self.source_folder)
            target_file = os.path.join(self.target_folder, relative_path)
            # 确保目标文件夹存在，如果不存在则创建
            os.makedirs(os.path.dirname(target_file), exist_ok=True)
            self.copy_metadata(source_file, target_file, thread_name)
            self.file_queue.task_done()

    def get_source_files(self):
        for dp, dn, filenames in os.walk(self.source_folder):
            for f in filenames:
                source_file = os.path.join(dp, f)
                if source_file.endswith(self.metadata_extensions):
                    yield source_file

    def run(self):
        start_time = time.time()
        print_message("开始更新元数据...")
        # logging.info("开始更新元数据...")
        threads = []

        for i in range(self.num_threads):
            thread_name = f"Thread-{i + 1}"
            thread = threading.Thread(target=self.start_to_copy_metadata, args=(thread_name,))
            threads.append(thread)
            thread.start()

        for source_file in self.get_source_files():
            self.file_queue.put(source_file)

        # 添加停止任务
        for i in range(self.num_threads):
            self.file_queue.put(None)

        for thread in threads:
            thread.join()

        end_time = time.time()
        total_time = end_time - start_time
        message = f"更新元数据:总耗时 {total_time:.2f} 秒, 共处理元数据数：{self.copied_metadatas + self.existing_links}个，共复制元数据数：{self.copied_metadatas}，共跳过元数据数：{self.existing_links}"
        print_message('完成::: 更新元数据')
        # logging.info(message)
        return total_time,message