import os
import shutil
import threading
import time
import queue
import logging

class SymlinkDirChecker:
    def __init__(self, source_root, target_root, num_threads=8, timeout_seconds=300):
        self.source_root = source_root
        self.target_root = target_root
        self.num_threads = num_threads
        self.timeout_seconds = timeout_seconds
        self.error_dirs_num = 0
        self.total_num = 0
        self.file_queue = queue.Queue()

    def remove_error_dir(self, thread_name):
        while True:
            dir_path = self.file_queue.get()
            if dir_path is None:
                break

            try:
                relative_path = os.path.relpath(dir_path, self.source_root)
                target_dir = os.path.join(self.target_root, relative_path)
                self.total_num += 1
                if not os.path.exists(target_dir):
                    self.error_dirs_num += 1
                    shutil.rmtree(dir_path)
                    print(f"线程 {thread_name}: 删除失效文件夹 => {dir_path} \n")
                    logging.info(f"线程 {thread_name}: 删除失效文件夹 => {dir_path} \n")
                else:
                    print(f"线程 {thread_name}: 跳过{dir_path} \n")
            except Exception as e:
                print(f"线程 {thread_name}: 发生异常 => {e}")

            self.file_queue.task_done()

    def thread_timeout_handler(self):
        print("线程运行超时，停止该线程")
        for thread in self.threads:
            thread.join()

    def get_dirs(self):
        for root, dirnames, __ in os.walk(self.source_root):
            for dirname in dirnames:
                dir_path = os.path.join(root, dirname)
                yield dir_path

    def run(self):
        start_time = time.time()
        print(f"开始清理无效文件夹...")
        logging.info(f"开始清理无效文件夹...")
        self.threads = []

        for i in range(self.num_threads):
            thread_name = f"Thread-{i + 1}"
            thread = threading.Thread(target=self.remove_error_dir, args=(thread_name,))
            self.threads.append(thread)
            thread.start()

        timer = threading.Timer(self.timeout_seconds, self.thread_timeout_handler)

        try:
            timer.start()

            for dir_path in self.get_dirs():
                self.file_queue.put(dir_path)

            for i in range(self.num_threads):
                self.file_queue.put(None)

            for thread in self.threads:
                thread.join()

        finally:
            timer.cancel()

        end_time = time.time()
        total_time = end_time - start_time
        message = f"总耗时: {total_time:.2f} 秒, 共处理文件夹数：{self.total_num}, 共清理失效文件夹数：{self.error_dirs_num}"
        print(message)
        logging.info(message)
        return message

if __name__ == "__main__":
    log_path = 'auto_symlink.log'
    logging.basicConfig(filename=log_path, level=logging.INFO, format="%(asctime)s [%(levelname)s]: %(message)s")

    current_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    logging.info(f"程序运行开始时间: {current_time}")
    dir_dict = {}
    with open('config.txt', 'r') as file:
        for line in file:
            key, value = line.strip().split("=")
            dir_dict[key.strip()] = value.strip()
    target_root = dir_dict['media_dir']
    source_root = dir_dict['symlink_dir']
    num_threads = 8
    timeout_seconds = 5  # 线程解锁时间
    symlink_dir_checker = SymlinkDirChecker(source_root, target_root, num_threads, timeout_seconds)
    symlink_dir_checker.run()
