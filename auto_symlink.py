import os
import time
import subprocess
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from watcher.FileWatcher import FileMonitor
from utils.shentools import *
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
        self.yaml_data = read_config(config_path=config_path)
        self.last_sync_list = read_last_sync_config(config_path=last_sync_path)
        self.symlink_ext = self.yaml_data.get('symlink_ext','.mkv;.iso;.ts;.mp4;.avi;.rmvb;.wmv;.m2ts;.mpg;.flv;.rm;.mov')
        self.metadata_ext = self.yaml_data.get('metadata_ext','.nfo;.jpg;.png;.svg;.ass;.srt;.sup')
        self.func_list = sorted(self.yaml_data["func_order"], key=self.yaml_data["func_order"].get)
        self._scheduler = BackgroundScheduler(timezone=get_timezone())

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
                print_message(f'开始备份新增目录...')
                self.start_backup(new_sync_list)
                print_message(f'新增目录备份完毕,准备重启定时备份...')
                send_restart_signal(["start_backup_scheduled"])
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
                print_message(f'全同步完成,共耗时{total_time:.2f}秒.')
            else:
                print_message('未开启全局同步状态,如需开启,请至config.yaml中将全局设置中的"sync_enabled"设为"true"')
        else:
            print_message('当前没有需要重启全同步的目录')

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
        self.set_scheduled(action="同步",key_name="sync_time",func=self.auto_symlink,args=[sync_list,num_threads])

    def start_backup_scheduled(self):
        if not self.yaml_data:
            print_message('无法正确读取配置文件"./config/config.yaml"的信息,请检查配置文件,或根据提示重置配置文件')
            return
        backup_scheduled = self.yaml_data.get('backup_scheduled',False)
        if not backup_scheduled:
            print_message('未开启定时备份,如需开启,请至config.yaml中将全局设置中的"backup_scheduled"设为"true"')
            return
        #只定时备份已经全同步过的目录
        sync_list = self.yaml_data.get('sync_list', [])
        if self.last_sync_list:
            try:
                existing_sync_list = [item for item in sync_list if item.get('symlink_dir','') in self.last_sync_list]
            except Exception as e:
                print_message(f'配置文件"./config/last_sync.yaml错误",请检查配置文件后重启容器.')
        else:
            existing_sync_list = []

        if existing_sync_list:
            sync_backup_list = [item for item in existing_sync_list if item.get('backup_scheduled',False)]
        else:
            sync_backup_list = []
        self.set_scheduled(action="备份",key_name="backup_time",func=self.start_backup,args=[sync_backup_list,])

    def set_scheduled(self,action,key_name,func,args):
        sync_list = self.yaml_data.get('sync_list',[])
        if not sync_list:
            return
        cron = self.yaml_data.get(key_name).strip()
        if cron.count(" ") == 4:
            message = get_scheduled_time(cron,action=action)[1]
            print_message(f'定时{action}::: {message}')
            try:
                self._scheduler.add_job(func=func,
                                        args=[sync_list],
                                        trigger=CronTrigger.from_crontab(cron))
                self._scheduler.start()
            except Exception as err:
                print_message(f'定时{action}时间 "{cron}" 格式不正确：{str(err)}')
        else:
            seconds,message = get_scheduled_time(cron,action=action)
            print_message(f'定时{action}::: {message}')
            try:
                self._scheduler.add_job(func=func,
                                        args=args,
                                        trigger='interval',
                                        seconds=seconds,)
                self._scheduler.start()
            except Exception as err:
                print_message(f'定时{action}时间 "{cron}" 格式不正确：{str(err)}')

    def start_backup(self,sync_list):
        backup_list = read_backup_list()
        if not sync_list:
            return
        for item in sync_list:
            backup_scheduled = item.get('backup_scheduled',False)
            if not backup_scheduled:
                print_message(f'当前目录没有开始定时备份,跳过::: {backup_scheduled}')
            source_dir = item.get('symlink_dir','')
            target_dir = backup_list.get(source_dir,'')
            backup_ext = item.get('backup_ext','*')
            if not backup_list or not target_dir:
                folder_name = get_uuid()
                target_dir = os.path.abspath(os.path.join('./backup',folder_name))
                backup_list[source_dir] = target_dir
                save_backup_list(data=backup_list)
            print_message(f'开始备份目录::: {source_dir} => {target_dir}')
            start_time = time.time()
            command = get_rsync_command (source_dir,target_dir,backup_ext)
            process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            #等待进程结束，并获取输出
            try:
                stdout, stderr = process.communicate()
                stdout = stdout.decode('utf-8', 'ignore')
                stderr = stderr.decode('utf-8', 'ignore')
            except UnicodeDecodeError as e:
                stdout = ""
                print(f"Error decoding output: {e}")
            end_time = time.time()
            total_time = start_time - end_time
            if total_time <= 0:
                total_time = 0.5
            print_message(f'备份成功::: {source_dir} => {target_dir}')
            print(f"总耗时: {total_time:.2f} 秒")
            if stdout:
                print_backup_message(stdout)

    def restore_backup(self,source_dir,backup_dir):
        command = get_rsync_command (backup_dir,source_dir,'*')
        print_message(f'开始从恢复目录::: {backup_dir} => {source_dir}')
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        #等待进程结束，并获取输出
        stdout, stderr = process.communicate()
        process.wait()
        print_message(stdout)
        print_message(f'恢复备份成功::: {backup_dir} => {source_dir}')

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
                        symlink_dir_checker = SymlinkDirChecker(cloud_path,symlink_dir, media_dir, num_threads, timeout_seconds)
                        cost_time,message = symlink_dir_checker.run()
                        total_time += cost_time
                        message_list.append(message)

                    if func_name == 'SymlinkChecker' and symlink_checker_flag:
                        symlink_checker = SymlinkChecker(cloud_path,symlink_dir,symlink_mode, num_threads)
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
                    self.last_sync_list = save_last_sync_config(sync_list)
            except Exception as e:
                print_message(f'error:{e}')
                return 0
        return total_time

if __name__ == "__main__":
    working_directory = os.path.dirname(os.path.abspath(__file__))
    os.chdir(working_directory)
    auto_sync = AutoSync()
    auto_sync.sync_new_list()
    while True:
        pass
    # auto_sync.start_sync_scheduled()
