import os
import threading
import time
import queue
import logging

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
                print(f"已删除无效软链接: {link}\n")
                logging.info(f"已删除无效软链接: {link}\n")
                self.broken_num += 1
            else:
                print(f"已跳过有效软链接: {link}\n")
        except Exception as e:
            print(f"检查软链接时出错: {link}, 错误: {e}")

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
        print("开始清理无效软链接...")
        logging.info("开始清理无效软链接...")
        self.process_symlinks()
        end_time = time.time()
        total_time = end_time - start_time
        message = f"总耗时: {total_time:.2f} 秒, 总软链接数: {self.total_num}, 已清除无效软链接数: {self.broken_num}"
        print(message)
        logging.info(message)
        return message

if __name__ == "__main__":
    # 配置日志
    log_path = 'auto_symlink.log'
    logging.basicConfig(filename=log_path, level=logging.INFO, format="%(asctime)s [%(levelname)s]: %(message)s")

    current_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    logging.info(f"程序运行开始时间: {current_time}")
    dir_dict = {}
    with open('config.txt', 'r') as file:
        for line in file:
            key, value = line.strip().split("=")
            dir_dict[key.strip()] = value.strip()

    target_dir = dir_dict['symlink_dir']
    print(target_dir)
    num_threads = 8  # 指定线程数
    symlink_checker = SymlinkChecker(target_dir, num_threads)
    symlink_checker.run()