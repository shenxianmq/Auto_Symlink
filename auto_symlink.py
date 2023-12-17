import os
import yaml
import re
from datetime import datetime
from croniter import croniter
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from watcher.FileWatcher import FileMonitor
from utils.shentools import get_timezone,print_message
from autosync.MetadataCopyer import MetadataCopyer
from autosync.SymlinkCreator import SymlinkCreator
from autosync.SymlinkChecker import SymlinkChecker
from autosync.SymlinkDirChecker import SymlinkDirChecker

class AutoSync:
    def __init__(self, config_path='./config/config.yaml',last_sync_path='./config/last_sync.yaml'):
        self.config_path = config_path
        self.last_sync_path = last_sync_path
        self.symlink_ext = (".mkv", ".iso", ".ts", ".mp4", ".avi", ".rmvb", ".wmv", ".m2ts", ".mpg", ".flv", ".rm", ".mov")
        self.metadata_ext = (".nfo", ".jpg", ".png", ".svg", ".ass", ".srt", ".sup")
        self.yaml_data = self.read_config()
        self.last_sync_list = self.read_last_sync_config()
        self.symlink_ext = self.yaml_data.get('symlink_ext','.mkv;.iso;.ts;.mp4;.avi;.rmvb;.wmv;.m2ts;.mpg;.flv;.rm;.mov')
        self.metadata_ext = self.yaml_data.get('metadata_ext','.nfo;.jpg;.png;.svg;.ass;.srt;.sup')
        self.func_list = sorted(self.yaml_data["func_order"], key=self.yaml_data["func_order"].get)
        self._scheduler = BackgroundScheduler(timezone=get_timezone())

    def read_config(self):
        try:
            with open(self.config_path, 'r', encoding='utf-8') as file:
                data = yaml.safe_load(file)
            return data
        except Exception as e:
            print_message(f"配置文件出现问题: {e}")
            return None

    def read_last_sync_config(self):
        try:
            with open(self.last_sync_path, 'r', encoding='utf-8') as file:
                data = yaml.safe_load(file)
            if data:
                return data.get('last_sync_list',[])
            else:
                return []
        except Exception as e:
            print_message(f"配置文件出现问题:{e}")
            return []

    def write_stop_file(self):
        with open('./config/stop.txt','w',encoding='utf-8') as f:
            f.write('')

    def save_last_sync_config(self,sync_list):
        symlink_dirs = [entry.get('symlink_dir', '') for entry in sync_list]
        new_data = {'last_sync_list': symlink_dirs}
        with open(self.last_sync_path, 'w') as file:
            yaml.dump(new_data, file, default_flow_style=False, allow_unicode=True)
        return new_data

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

    def sync_new_list(self):
        if not self.yaml_data:
            print_message('无法正确读取配置文件"./config/config.yaml"的信息,请检查配置文件,或根据提示重置配置文件')
            return
        sync_enabled = self.yaml_data.get('sync_enabled',False) #默认同步关闭
        sync_list = self.yaml_data.get('sync_list', [])
        if not sync_list:
            print_message('并未检测到同步目录配置,请到"./config/config.yaml"的sync_list项下进行目录配置')
            return
        num_threads = self.yaml_data.get('num_threads',8)

        if self.last_sync_list:
            try:
                new_sync_list = [item for item in sync_list if item.get('symlink_dir','') not in self.last_sync_list]
            except Exception as e:
                print_message(f'配置文件"./config/last_sync.yaml错误",请检查配置文件后重启容器.')
        else:
            new_sync_list = [item for item in sync_list]

        if new_sync_list:
            if sync_enabled:
                print_message('开始同步新增目录')
                total_time = self.auto_symlink(new_sync_list,num_threads,new_sync=True)
                print_message(f'同步完成,共耗时{total_time:.2f}秒.')
        else:
            print_message('不存在新增目录,无须同步')

    def start_observer(self):
            if not self.yaml_data:
                print_message('无法正确读取配置文件"./config/config.yaml"的信息,请检查配置文件,或根据提示重置配置文件')
                return
            observer_enabled = self.yaml_data.get('observer_enabled',False) #默认目录监控关闭
            sync_list = self.yaml_data.get('sync_list', [])
            if not sync_list:
                print_message('并未检测到同步目录配置,请到"./config/config.yaml"的sync_list项下进行目录配置')
                return

            #开始目录监控

            if observer_enabled:
                print_message('准备开始目录监控')
                FileMonitor(sync_list).start()
            else:
                print_message('未开启监控状态,如需开启,请至config.yaml中将全局设置中的"observer_enabled"设为"true"')

    def restart_sync(self):
        if not self.yaml_data:
            print_message('无法正确读取配置文件"./config/config.yaml"的信息,请检查配置文件,或根据提示重置配置文件')
            return
        sync_enabled = self.yaml_data.get('sync_enabled',False) #默认同步关闭
        restart_sync_enabled = self.yaml_data.get('restart_sync_enabled',False) #默认重启同步关闭
        if not restart_sync_enabled:
            print_message('未开启重启全同步状态,如需开启,请至config.yaml中将全局设置中的"restart_sync_enabled"设为"true"')
            return

        sync_list = self.yaml_data.get('sync_list', [])
        num_threads = self.yaml_data.get('num_threads',8)
        if self.last_sync_list:
            try:
                existing_sync_list = [item for item in sync_list if item.get('symlink_dir','') in self.last_sync_list]
            except Exception as e:
                print_message(f'配置文件"./config/last_sync.yaml错误",请检查配置文件后重启容器.')
        else:
            existing_sync_list = []

        if existing_sync_list:
            restart_sync_list = [item for item in existing_sync_list if item.get('restart_sync_enabled',False)]
        else:
            restart_sync_list = []

        if restart_sync_list:
            if sync_enabled:
                print_message('开始对指定目录进行全同步')
                total_time = self.auto_symlink(restart_sync_list,num_threads)
                print_message(f'同步完成,共耗时{total_time:.2f}秒.')
            else:
                print_message('未开启全局同步状态,如需开启,请至config.yaml中将全局设置中的"sync_enabled"设为"true"')

    def start_sync_scheduled(self):
        if not self.yaml_data:
            print_message('无法正确读取配置文件"./config/config.yaml"的信息,请检查配置文件,或根据提示重置配置文件')
            return
        sync_scheduled = self.yaml_data.get('sync_scheduled',False)
        if not sync_scheduled:
            print_message('未开启定时同步,如需开启,请至config.yaml中将全局设置中的"sync_scheduled"设为"true"')
            return
        sync_list = self.yaml_data.get('sync_list',[])
        num_threads = self.yaml_data.get('num_threads',8)
        if sync_list:
            cron = self.yaml_data.get('sync_time').strip()
            if cron.count(" ") == 4:
                message = self.calculate_seconds(cron)[1]
                print_message(f'定时同步::: {message}')
                try:
                    self._scheduler.add_job(func=self.auto_symlink,
                                            args=[sync_list,num_threads],
                                            trigger=CronTrigger.from_crontab(cron))
                    self._scheduler.start()
                except Exception as err:
                    print_message(f'定时同步时间 "{cron}" 格式不正确：{str(err)}')
            else:
                seconds,message = self.calculate_seconds(cron)
                print_message(f'定时同步::: {message}')
                try:
                    self._scheduler.add_job(func=self.auto_symlink,
                                            args=[sync_list,num_threads],
                                            trigger='interval',
                                            seconds=seconds,)
                    self._scheduler.start()
                except Exception as err:
                    print_message(f'定时同步时间 "{cron}" 格式不正确：{str(err)}')

    def calculate_seconds(self,expression):
        # 判断是否为纯数字
        if re.match(r'^\d+$', expression):
            seconds = int(expression)
            message = f'同步间隔为{seconds}秒'
            return seconds,message  # 如果是纯数字,直接返回

        # 尝试使用 eval 计算数学表达式
        try:
            result = eval(expression)
            seconds = int(max(0, result))
            message = f'同步间隔为{seconds}秒'
            return seconds,message
        except Exception:
            pass  # 不是数学表达式,继续检查是否为 cron 表达式

        # 判断是否为 cron 表达式
        try:
            current_time = datetime.now().timestamp()
            cron_iter = croniter(expression, start_time=datetime.fromtimestamp(current_time))
            next_run_date = cron_iter.get_next(datetime)
            next_run_time = next_run_date.timestamp()
            seconds = max(0, next_run_time - current_time)
            message = f'下次同步时间为{next_run_date}'
            return seconds,message
        except ValueError:
            raise ValueError(f"cron表达式{expression}错误,请参照配置文件中的示例进行更改,不要通过在线生成工具生成cron表达式,程序可能无法识别")

    def parse_extensions(self,extensions_str):
        # 去掉前后的空格,并使用分号分隔
        extensions_list = extensions_str.strip().split(';')
        # 去掉空的元素
        extensions_list = [ext.strip() for ext in extensions_list if ext.strip()]
        # 返回一个元组
        return tuple(extensions_list)

    def auto_symlink(self, dict_list,num_threads=8,new_sync=False):
        total_time = 0
        for dir_dict in dict_list:
            try:
                timeout_seconds = 5  # 线程解锁时间
                cloud_path = dir_dict.get('cloud_path','')
                media_dir = dir_dict.get('media_dir','')
                symlink_dir = dir_dict.get('symlink_dir','')
                symlink_dir_checker_flag = dir_dict.get('symlink_dir_checker',False)
                symlink_checker_flag = dir_dict.get('symlink_checker',False)
                symlink_creator_flag = dir_dict.get('symlink_creator',False)
                metadata_copyer_flag = dir_dict.get('metadata_copyer',False)
                symlink_mode = dir_dict.get('symlink_mode','symlink')
                cloud_type = dir_dict.get('cloud_type','symlink')
                cloud_url = dir_dict.get('cloud_url','')
                symlink_mode = dir_dict.get('symlink_mode','')
                cloud_root_path = dir_dict.get('symlink_mode','')
                if cloud_type == "cd2":
                    cloud_root_path = dir_dict.get('clouddrive2_path','')
                elif cloud_type == "alist":
                    cloud_root_path = dir_dict.get('alist_path','')


                symlink_ext = self.parse_extensions(dir_dict.get('symlink_ext',self.symlink_ext))
                metadata_ext = self.parse_extensions(dir_dict.get('metadata_ext',self.metadata_ext))
                sync_enabled = dir_dict.get('sync_enabled',True)
                if not sync_enabled:
                    print_message(f'目录同步未开启:{media_dir} => {symlink_dir}')
                    return 0
                print_message(f'开始同步目录:{media_dir} => {symlink_dir}')

                if not os.path.exists(cloud_path):
                    raise FileNotFoundError(f'挂载目录不存在,请检查挂载目录{cloud_path}')
                message_list = []
                for func_name in self.func_list:
                    if func_name == 'MetadataCopyer' and metadata_copyer_flag:
                        metadata_copyer = MetadataCopyer(media_dir, symlink_dir,metadata_ext, num_threads)
                        cost_time,message = metadata_copyer.run()
                        total_time += cost_time
                        message_list.append(message)

                    if func_name == 'SymlinkDirChecker' and symlink_dir_checker_flag:
                        symlink_dir_checker = SymlinkDirChecker(symlink_dir, media_dir, num_threads, timeout_seconds)
                        cost_time,message = symlink_dir_checker.run()
                        total_time += cost_time
                        message_list.append(message)

                    if func_name == 'SymlinkChecker' and symlink_checker_flag:
                        symlink_checker = SymlinkChecker(symlink_dir,symlink_mode, num_threads)
                        cost_time,message = symlink_checker.run()
                        total_time += cost_time
                        message_list.append(message)

                    if func_name == 'SymlinkCreator' and symlink_creator_flag:
                        symlink_creator = SymlinkCreator(media_dir, symlink_dir,symlink_ext,symlink_mode,cloud_type,cloud_root_path,cloud_url,num_threads)
                        cost_time,message = symlink_creator.run()
                        total_time += cost_time
                        message_list.append(message)
                if message_list:
                    print_message(f'全同步完成::: {media_dir} => {symlink_dir}')
                    print_message(f'总耗时::: {total_time:.2f} 秒,下面是各项程序耗时')
                    for message in message_list:
                        print_message(message)
                if new_sync:
                    sync_list = self.yaml_data.get('sync_list',[])
                    self.last_sync_list = self.save_last_sync_config(sync_list)
            except Exception as e:
                print_message(f'error:{e}')
                return 0
        return total_time


if __name__ == "__main__":
    working_directory = os.path.dirname(os.path.abspath(__file__))
    os.chdir(working_directory)
    auto_sync = AutoSync()
    auto_sync.run()
    # auto_sync.start_sync_scheduled()
