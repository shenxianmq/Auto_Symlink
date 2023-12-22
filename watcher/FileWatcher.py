import os
import shutil
from pathlib import Path
import time
import yaml
import urllib.parse
from typing import Any
from utils.shentools import *
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer
from watchdog.observers.polling import PollingObserver


class FileMonitorHandler(FileSystemEventHandler):
    """
    目录监控响应类
    """

    def __init__(self, watching_path: str, cloud_path, file_change: Any, **kwargs):
        super(FileMonitorHandler, self).__init__(**kwargs)
        self._watching_path = watching_path
        self._cloud_path = cloud_path
        self.file_change = file_change

    def on_any_event(self, event):
        print_message(f"目录监控事件路径::: {event.src_path}")
        pass

    def on_created(self, event):
        print_message(f"目录监控created事件路径::: {event.src_path}")
        if not os.path.exists(self._cloud_path):
            while not os.path.exists(self._cloud_path):
                print_message(f"没有检测到云端挂载目录,请检查目录挂载情况::: {self._cloud_path}")
                time.sleep(3)
            print_message(f"成功检测到云端挂载目录,即将重新启动目录监控")
            send_restart_signal(["start_observer"])
        self.file_change.event_handler(
            event=event, source_dir=self._watching_path, event_path=event.src_path
        )

    def on_deleted(self, event):
        print_message(f"目录监控deleted事件路径 src_path::: {event.src_path}")
        if not os.path.exists(self._cloud_path):
            while not os.path.exists(self._cloud_path):
                print_message(f"没有检测到云端挂载目录,请检查目录挂载情况::: {self._cloud_path}")
                time.sleep(3)
            print_message(f"成功检测到云端挂载目录,即将重新启动目录监控")
            send_restart_signal(["start_observer"])
        self.file_change.event_handler(
            event=event, source_dir=self._watching_path, event_path=event.src_path
        )

    def on_moved(self, event):
        pass


class FileMonitor:
    # 直接创建在类下面就是类属性，哪怕新建不同的实例，照样能共享这些数据
    # _symlink_dir = {}
    # _observer_mode = {}
    # _cloud_path = {}
    # _symlink_ext = {}
    # _metadata_ext = {}
    # _symlink_creator = {}
    # _metadata_copyer = {}
    # _sync_enabled = {}
    # _observer_enabled = {}

    def __init__(self, sync_list=[]):
        """
        初始化参数
        """
        # 存储目录监控配置
        self._symlink_dir = {}
        self._observer_mode = {}
        self._cloud_path = {}
        self._symlink_ext = {}
        self._metadata_ext = {}
        self._symlink_creator = {}
        self._metadata_copyer = {}
        self._sync_enabled = {}
        self._observer_enabled = {}
        self._symlink_mode = {}
        self._clouddrive2_path = {}
        self._alist_path = {}
        self._cloud_url = {}
        self._cloud_type = {}
        self._observer = {}
        self.config_path = "./config/config.yaml"
        # 从配置文件中获取相关参数
        self.add_monitor_conf(sync_list)

    def start(self):
        """
        启动目录监控
        """
        if not self._symlink_dir or not self._symlink_dir.keys():
            raise ValueError("未找到目录监控配置，请检查配置文件。")

        timeout = 10
        for source_dir in self._symlink_dir.keys():
            if not self._observer_enabled.get(source_dir):
                print_message(
                    f'目录未处于监控状态::: {source_dir}。若要启用，请在config.yaml的sync_list中将"observer_enabled"设置为"true"'
                )
                continue

            cloud_path = self._cloud_path.get(source_dir)
            if not os.path.exists(cloud_path):
                print_message(f"挂载目录不存在，请检查挂载状态::: {cloud_path}")
                continue

            monitoring_mode = self._observer_mode.get(source_dir)
            cloud_path = self._cloud_path.get(source_dir)
            observer = (
                PollingObserver(timeout=timeout)
                if str(monitoring_mode) == "compatibility"
                else Observer(timeout=timeout)
            )
            observer.schedule(
                event_handler=FileMonitorHandler(str(source_dir), cloud_path, self),
                path=str(source_dir),
                recursive=True,
            )
            print_message(
                f"开始监控文件夹::: {str(source_dir)} 转移方式::: {str(monitoring_mode)}"
            )
            self._observer[source_dir] = observer
            observer.daemon = True
            try:
                observer.start()
            except ConnectionAbortedError:
                print_message(f"监控程序发生错误。重新启动目录监控::: {source_dir}")
                observer.stop()
                send_restart_signal(["start_observer"])

    def add_monitor_conf(self, monitor_confs: list):
        # 存储目录监控配置
        for monitor_conf in monitor_confs:
            source_dir = monitor_conf.get("media_dir")
            if not source_dir:
                print_message(f"目录不存在，请检查目录位置::: {monitor_conf}")
                return
            self._symlink_dir[source_dir] = monitor_conf.get("symlink_dir")
            self._observer_mode[source_dir] = monitor_conf.get(
                "observer_mode", "compatibility"
            )
            self._cloud_path[source_dir] = monitor_conf.get("cloud_path")
            self._symlink_ext[source_dir] = monitor_conf.get(
                "symlink_ext",
                ".mkv;.iso;.ts;.mp4;.avi;.rmvb;.wmv;.m2ts;.mpg;.flv;.rm;.mov",
            )
            self._metadata_ext[source_dir] = monitor_conf.get(
                "metadata_ext", ".nfo;.jpg;.png;.svg;.ass;.srt;.sup"
            )
            self._symlink_creator[source_dir] = monitor_conf.get(
                "symlink_creator", True
            )
            self._metadata_copyer[source_dir] = monitor_conf.get(
                "metadata_copyer", True
            )
            self._sync_enabled[source_dir] = monitor_conf.get("sync_enabled", True)
            self._observer_enabled[source_dir] = monitor_conf.get(
                "observer_enabled", True
            )
            self._symlink_mode[source_dir] = monitor_conf.get("symlink_mode", "")
            self._clouddrive2_path[source_dir] = monitor_conf.get(
                "clouddrive2_path", ""
            )
            self._alist_path[source_dir] = monitor_conf.get("alist_path", "")
            self._cloud_url[source_dir] = monitor_conf.get("cloud_url", "")
            self._cloud_type[source_dir] = monitor_conf.get("cloud_type", "")

    def event_handler(self, event, source_dir: str, event_path: str):
        """
        文件变动handler
        :param event:
        :param source_dir:
        :param event_path:
        """
        # 回收站及隐藏的文件不处理
        if (
            event_path.find("/@Recycle") != -1
            or event_path.find("/#recycle") != -1
            or event_path.find("/.") != -1
            or event_path.find("/@eaDir") != -1
        ):
            print_message(f"{event_path} 是回收站或隐藏的文件，跳过处理")
            return

        # 原盘文件夹不处理
        if event_path.find("/BDMV") != -1 or event_path.find("/CERTIFICATE") != -1:
            print_message(f"{event_path} 是原盘文件夹，跳过处理")
            return
        if event.event_type == "created":
            if os.path.exists(event_path):
                self.event_handler_created(event, event_path, source_dir)
            else:
                print_message(f"created事件出错::: 该文件并不存在,即将重新启动目录监控 => {event_path}")
                send_restart_signal(["start_observer"])
                while True:
                    time.sleep(1)
        if event.event_type == "deleted":
            self.event_handler_deleted(event_path, source_dir)

    def event_handler_created(self, event, event_path: str, source_dir: str):
        try:
            # 转移路径
            symlink_dir = self._symlink_dir.get(source_dir)
            symlink_ext = self.__parse_extensions(self._symlink_ext.get(source_dir))
            metadata_ext = self.__parse_extensions(self._metadata_ext.get(source_dir))
            symlink_creator = self._symlink_creator.get(source_dir)
            metadata_copyer = self._metadata_copyer.get(source_dir)
            cloud_type = self._cloud_type.get(source_dir)
            cloud_url = self._cloud_url.get(source_dir)
            if cloud_type == "cd2":
                cloud_root_path = self._clouddrive2_path.get(source_dir)
            elif cloud_type == "alist":
                cloud_root_path = self._alist_path.get(source_dir)

            # 文件夹同步创建
            if event.is_directory:
                target_path = event_path.replace(source_dir, symlink_dir)
                # 目标文件夹不存在则创建
                if not Path(target_path).exists():
                    print_message(f"创建目标文件夹 {target_path}")
                    os.makedirs(target_path)
            else:
                if event_path.lower().endswith(symlink_ext):
                    if not symlink_creator:
                        print_message(f"创建软链接/strm文件未开启，跳过创建::: {event_path}")
                    else:
                        # 创建软链接
                        if self._symlink_mode.get(source_dir) == "symlink":
                            self.__create_symlink(
                                source_dir=source_dir,
                                target_dir=symlink_dir,
                                source_file=event_path,
                            )
                        elif self._symlink_mode.get(source_dir) == "strm":
                            self.__create_strm_file(
                                source_dir=source_dir,
                                target_dir=symlink_dir,
                                source_file=event_path,
                                cloud_type=cloud_type,
                                cloud_path=cloud_root_path,
                                cloud_url=cloud_url,
                            )
                        else:
                            print_message(f"当前目录symlink_mode配置错误:{self._symlink_mode}")
                elif event_path.lower().endswith(metadata_ext):
                    if not metadata_copyer:
                        print_message(f"元数据处理未开，跳过处理::: {event_path} ")
                        return
                    self.__media_copyer(
                        source_dir=source_dir,
                        target_dir=symlink_dir,
                        source_file=event_path,
                    )
        except Exception as e:
            print_message(f"event_handler_created error: {e}")

    def event_handler_deleted(self, event_path: str, source_dir: str):
        # cloud_path = self._cloud_path.get(source_dir)
        if event_path == source_dir:
            print_message("检测到media_dir删除事件,可能发生掉盘事件")
            print_message("为了本地数据安全，即将重启目录监控")
            send_restart_signal(["start_observer"])
            # 添加while循环阻塞线程,确保先重启
            while True:
                time.sleep(1)
        symlink_mode = self._symlink_mode.get(source_dir)
        dest_dir = self._symlink_dir.get(source_dir)
        # 如果是strm模式,并且是指定的视频后缀就替换为.strm后缀
        if symlink_mode == "strm" and event_path.lower().endswith(
            self._symlink_ext.get(source_dir)
        ):
            # 构造替换后的路径
            base_name = os.path.splitext(os.path.basename(event_path))[0]
            dir_path = os.path.dirname(event_path).replace(source_dir, dest_dir)
            deleted_target_path = os.path.join(dir_path, f"{base_name}.strm")
        else:
            deleted_target_path = event_path.replace(source_dir, dest_dir)
        deleted_path = Path(deleted_target_path)
        if os.path.exists(event_path):
            print_message(f"源路径存在，跳过删除::: {deleted_target_path}")
            print_message("原因为可能快速重启了挂载工具(如CloudDrive2)")
            print_message("为了本地数据安全，即将重启目录监控::: {source_dir}")
            send_restart_signal(["start_observer"])
            while True:
                time.sleep(1)
        # 只删除存在的软链接或都路径
        if not deleted_path.is_symlink() and not deleted_path.exists():
            print_message(f"目标路径不存在，跳过删除::: {deleted_target_path}")
        else:
            if deleted_path.is_symlink():
                # 如果是符号链接，直接删除
                deleted_path.unlink()
                print_message(f"成功删除软链接::: {deleted_target_path}")
            elif deleted_path.is_file():
                deleted_path.unlink()
                print_message(f"成功删除文件::: {deleted_target_path}")
            elif deleted_path.is_dir():
                # 非根目录，才删除目录
                shutil.rmtree(deleted_target_path)
                print_message(f"成功删除目录::: {deleted_target_path}")
        if event_path != source_dir:
            self.__delete_empty_parent_directory(event_path)

    @staticmethod
    def __delete_empty_parent_directory(file_path):
        parent_dir = Path(file_path).parent
        if not os.path.exists(parent_dir):
            print_message(f"父文件夹已经删除::: {parent_dir}")
            return
        if (
            parent_dir != Path("/")
            and parent_dir.is_dir()
            and not any(parent_dir.iterdir())
            and parent_dir.exists()
        ):
            try:
                parent_dir.rmdir()
                print_message(f"删除空的父文件夹::: {parent_dir}")
            except OSError as e:
                print_message(f"删除空父目录失败::: {e}")

    @staticmethod
    def __create_symlink(source_dir: str, target_dir: str, source_file: str):
        """
        创建软链接
        """
        try:
            relative_path = os.path.relpath(source_file, source_dir)
            target_file = os.path.join(target_dir, relative_path)
            # 确保目标文件夹存在，如果不存在则创建
            os.makedirs(os.path.dirname(target_file), exist_ok=True)
            if os.path.exists(target_file):
                print_message(f"软链接已存在，跳过::: {target_file}")
            else:
                os.symlink(source_file, target_file)
                print_message(f"成功创建软链接::: {source_file} => {target_file}")
        except Exception as e:
            print_message(f"创建软链接失败::: {e}")

    @staticmethod
    def __media_copyer(source_dir: str, target_dir: str, source_file: str):
        # 图片文件复制
        relative_path = os.path.relpath(source_file, source_dir)
        target_file = os.path.join(target_dir, relative_path)
        # 确保目标文件夹存在，如果不存在则创建
        os.makedirs(os.path.dirname(target_file), exist_ok=True)
        try:
            if os.path.exists(target_file):
                source_timestamp = os.path.getmtime(source_file)
                target_timestamp = os.path.getmtime(target_file)
                if source_timestamp > target_timestamp:
                    os.makedirs(os.path.dirname(target_file), exist_ok=True)
                    shutil.copy2(source_file, target_file)
                    print_message(f"成功复制元数据::: {source_file} 到 {target_file}")
                else:
                    print_message(f"元数据已存在，跳过::: {target_file}")
            else:
                os.makedirs(os.path.dirname(target_file), exist_ok=True)
                shutil.copy2(source_file, target_file)
                print_message(f"成功复制元数据: {source_file} 到 {target_file}")

        except Exception as e:
            print_message(f"复制元数据失败::: {source_file} 到 {target_file}")
            print_message(f"error::: {e}")

    @staticmethod
    def __create_strm_file(
        source_dir: str,
        target_dir: str,
        source_file: str,
        cloud_type: str = None,
        cloud_root_path: str = None,
        cloud_url: str = None,
    ):
        try:
            # 获取视频文件名和目录
            target_file = source_file.replace(source_dir, target_dir)
            video_name = Path(target_file).name
            # 获取视频目录
            dest_path = Path(target_file).parent

            if not dest_path.exists():
                os.makedirs(str(dest_path), exist_ok=True)

            # 构造.strm文件路径
            strm_path = os.path.join(
                dest_path, f"{os.path.splitext(video_name)[0]}.strm"
            )

            # 云盘模式
            if cloud_type:
                # 替换路径中的\为/
                target_file = source_file.replace("\\", "/")
                target_file = target_file.replace(cloud_root_path, "")
                # 对盘符之后的所有内容进行url转码
                target_file = urllib.parse.quote(target_file, safe="")
                if str(cloud_type) == "cd2":
                    # 将路径的开头盘符"/mnt/user/downloads"替换为"http://localhost:19798/static/http/localhost:19798/False/"
                    target_file = f"http://{cloud_url}/static/http/{cloud_url}/False/{target_file}"
                elif str(cloud_type) == "alist":
                    target_file = f"http://{cloud_url}/d/{target_file}"
                else:
                    print_message(f"云盘类型 {cloud_type} 错误")
                    return

            # 写入.strm文件
            with open(strm_path, "w") as f:
                f.write(target_file)
            print_message(f"成功创建strm文件::: {source_file} => {strm_path}")
        except Exception as e:
            print_message(f"创建strm文件失败::: {source_file}")
            print_message(f"error::: {e}")

    @staticmethod
    def __parse_extensions(extensions_str: str):
        # 去掉前后的空格,并使用分号分隔
        extensions_list = extensions_str.strip().split(";")
        # 去掉空的元素
        extensions_list = [ext.strip() for ext in extensions_list if ext.strip()]
        # 返回一个元组
        return tuple(extensions_list)


def read_config(config_path):
    try:
        with open(config_path, "r") as file:
            data = yaml.safe_load(file)
        return data
    except Exception as e:
        print_message(f"配置文件出现问题::: {e}")
        return None


if __name__ == "__main__":
    working_directory = os.path.dirname(os.path.abspath(__file__))
    os.chdir("/Users/shenxian/PycharmProjects/Auto_Symlink")
    yaml_data = read_config("./config/config.yaml")
    sync_list = yaml_data.get("sync_list")
    FileMonitor(sync_list).start()
    while True:
        time.sleep(3600)
