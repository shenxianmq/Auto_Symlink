import time
import os
import yaml
from print_message import print_message
from create_config import create_config
from metadata_copyer import MetadataCopyer
from symlink_creator import SymlinkCreator
from symlink_checker import SymlinkChecker
from symlink_dir_checker import SymlinkDirChecker

working_directory = os.path.dirname(os.path.abspath(__file__))
os.chdir(working_directory)

if not os.path.exists('./config/config_done.txt'):
    create_config()

class AutoSync:
    def __init__(self, config_path='./config/config.yaml',sync_temp_path='./config/sync_temp.yaml'):
        self.config_path = config_path
        self.sync_temp_path = sync_temp_path
        self.symlink_ext = (".mkv", ".iso", ".ts", ".mp4", ".avi", ".rmvb", ".wmv", ".m2ts", ".mpg", ".flv", ".rm", ".mov")
        self.metadata_ext = (".nfo", ".jpg", ".png", ".svg", ".ass", ".srt", ".sup")
        self.last_sync_list = self.read_sync_temp_config()

    def read_config(self):
        try:
            with open(self.config_path, 'r', encoding='utf-8') as file:
                data = yaml.safe_load(file)
            return data
        except Exception as e:
            print_message(f"配置文件出现问题: {e}")
            return None

    def read_sync_temp_config(self):
        try:
            with open(self.sync_temp_path, 'r', encoding='utf-8') as file:
                data = yaml.safe_load(file)
            if data:
                return data.get('last_sync_list',[])
            else:
                return []
        except Exception as e:
            print_message(f"配置文件出现问题:{e}")
            return []

    def caculate_time(self, input_str):
        try:
            if '*' in input_str:
                # 如果输入字符串中包含 '*' 符号,执行乘法运算
                result = eval(input_str)
                return result
            else:
                # 如果输入字符串中没有 '*' 符号,尝试转换成整数
                result = int(input_str)
                return result
        except Exception as e:
            # 处理其他异常情况
            print_message(f"Error: {e}")
            return 86400

    def run(self):
        yaml_data = self.read_config()
        if not yaml_data:
            return
        sync_enabled = yaml_data.get('sync_enabled',True)
        if not sync_enabled:
            print_message('当前并未开启同步状态,如需开启,请至config.yaml中将sync_enabled设为true')
            return
        sync_status = yaml_data.get('sync_status', False)
        if sync_status:
            while True:
                # 等待指定秒数
                sync_time = self.caculate_time(yaml_data.get('sync_time'))
                self.run_once()
                time.sleep(sync_time)
        else:
            self.run_once()

    def run_once(self):
        total_time = 0
        current_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        print_message(f"程序运行开始时间: {current_time}")
        yaml_data = self.read_config()
        if not yaml_data:
            return
        sync_list = yaml_data.get('sync_list', [])
        num_threads = yaml_data.get('num_threads',8)
        new_sync_list = self.get_update_list(sync_list)
        self.symlink_ext = yaml_data.get('symlink_ext','.mkv;.iso;.ts;.mp4;.avi;.rmvb;.wmv;123.m2ts;.mpg;.flv;.rm;.mov')
        self.metadata_ext = yaml_data.get('metadata_ext','.nfo;.jpg;.png;.svg;.ass;.srt;.sup')
        self.func_list = sorted(yaml_data["func_order"], key=yaml_data["func_order"].get)

        if new_sync_list:
            print_message('开始同步新增目录...')
            total_time = self.auto_symlink(new_sync_list,num_threads)
            yaml_dict = {}
            yaml_dict['last_sync_list'] = sync_list
            with open(self.sync_temp_path, 'w', encoding='utf-8') as file:
                    yaml.dump(yaml_dict, file, default_flow_style=False, allow_unicode=True)
        else:
            total_time = self.auto_symlink(sync_list,num_threads)
        self.last_sync_list = sync_list
        print_message(f'同步完成,共耗时{total_time:.2f}秒.')

    def get_update_list(self, current_sync_list):
        new_elements = [item for item in current_sync_list if item not in self.last_sync_list]
        return new_elements

    def parse_extensions(self,extensions_str):
        # 去掉前后的空格,并使用分号分隔
        extensions_list = extensions_str.strip().split(';')
        # 去掉空的元素
        extensions_list = [ext.strip() for ext in extensions_list if ext.strip()]
        # 返回一个元组
        return tuple(extensions_list)

    def auto_symlink(self, dict_list,num_threads=8):
        total_time = 0
        for dir_dict in dict_list:
            try:
                timeout_seconds = 5  # 线程解锁时间
                cloud_path = dir_dict.get('cloud_path')
                media_dir = dir_dict.get('media_dir')
                symlink_dir = dir_dict.get('symlink_dir')
                symlink_dir_checker_flag = dir_dict.get('symlink_dir_checker')
                symlink_checker_flag = dir_dict.get('symlink_checker')
                symlink_creator_flag = dir_dict.get('symlink_creator')
                metadata_copyer_flag = dir_dict.get('metadata_copyer')
                symlink_ext = self.parse_extensions(dir_dict.get('symlink_ext',self.symlink_ext))
                metadata_ext = self.parse_extensions(dir_dict.get('metadata_ext',self.metadata_ext))
                upload_enabled = dir_dict.get('upload_enabled',True)
                if not upload_enabled:
                    print_message(f'目录同步未开启:{media_dir} => = {symlink_dir}')
                    return 0
                print_message(f'开始同步目录:{media_dir} => = {symlink_dir}')

                if not os.path.exists(cloud_path):
                    raise FileNotFoundError(f'挂载目录不存在,请检查挂载目录{cloud_path}')
                for func_name in self.func_list:
                    if func_name == 'MetadataCopyer' and metadata_copyer_flag:
                        metadata_copyer = MetadataCopyer(media_dir, symlink_dir,metadata_ext, num_threads)
                        total_time += metadata_copyer.run()

                    if func_name == 'SymlinkDirChecker' and symlink_dir_checker_flag:
                        symlink_dir_checker = SymlinkDirChecker(symlink_dir, media_dir, num_threads, timeout_seconds)
                        total_time += symlink_dir_checker.run()

                    if func_name == 'SymlinkChecker' and symlink_checker_flag:
                        symlink_checker = SymlinkChecker(symlink_dir, num_threads)
                        total_time += symlink_checker.run()

                    if func_name == 'SymlinkCreator' and symlink_creator_flag:
                        symlink_creator = SymlinkCreator(media_dir, symlink_dir,symlink_ext, num_threads)
                        total_time += symlink_creator.run()
            except Exception as e:
                print_message(f'error:{e}')
                return 0
        return total_time

if __name__ == "__main__":
    auto_sync = AutoSync()
    while True:
        auto_sync.run()
        time.sleep(999999)
