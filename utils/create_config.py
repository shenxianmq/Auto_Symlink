import os
import shutil
from utils.shentools import *

def check_config():
    print_message('开始初始化配置文件...')
    if os.path.exists('./config/config_done.txt'):
        if not os.path.exists('./config/config.yaml'):
            create_config_yaml()
        if not os.path.exists('./config/last_sync.yaml'):
            create_last_sync_yaml()
    else:
        shutil.rmtree('./config')
        os.mkdir('./config')
        create_config_yaml()
        create_last_sync_yaml()
    with open('./config/config_done.txt','w',encoding='utf-8') as f:
        f.write('')

def create_config_yaml():
    content = '''#注:yaml文件很注重缩进,请不要随意删减空格,不确定的情况下请直接通过复制粘贴来添加同步目录
#如果想要重置配置文件状态,直接删除"/config/config_done.txt"即可

#配置文件支持热重载,即当程序检测到配置文件更改后,会重新载入配置文件,使配置生效,若程序报错,请重启容器
#若更改配置文件后,并没有生效,则需要重新运行程序/重启容器才会生效

#全局设置
#全局设置中的开关为总开关,如果设为true,则开启所有目录的同步功能，如果设为false，则关闭所有目录的同步功能
#在sync_list中每个目录配置中还有小开关，比如只有全局开关和小开关都为true，才会开启对应的同步功能

#全同步状态:true为开启,false为关闭
#全同步指的是,对指定目录进行完整同步

#同步状态:true为开启,false为关闭
sync_enabled: false

#重启容器后是否进行全同步:true为开启,false为关闭
restart_sync_enabled: false

#定时同步状态:true为开启,false为关闭,为了确保云端和本地数据一致,建议在每天的空闲时间运行一次,比如早上2点半
sync_scheduled: false

#定时同步的时间间隔:单位为秒,支持乘法表达式,比如一天就是24*3600,意思是每隔指定的时间进行同步
#支持cron表达式,只支持5位的cron表达式,cron表达式支持在每天指定的时间进行同步,cron表达式的格式如下
#"30 12 * * *" => "30分 12时 每日 每月 周5"
#如果想每天早上2点30运行,就写为#"30 2 * * *" 时间是24小时制
#请参照上述的示例进行更改,不要通过在线生成工具生成cron表达式,程序可能无法识别
sync_time: "3600"

#实时监控文件夹:true为开启,false为关闭
observer_enabled: false

#同步线程数,并不是越大越好,可以自己根据实际情况测一下,选择最适合的线程数,推荐2-8之间
num_threads: 8

#同步后缀名,以;隔开
#如果sync_linst中配置了后缀名，则以sync_linst中配置的为准，如果没有配置，则以下面的为准
#软链接/strm文件指定后缀名
symlink_ext: ".mkv;.iso;.ts;.mp4;.avi;.rmvb;.wmv;.m2ts;.mpg;.flv;.rm;.mov"
#元数据指定后缀名
metadata_ext: ".nfo;.jpg;.png;.svg;.ass;.srt;.sup"

#选择程序运行的优先级,数字越小越靠前
func_order:
  SymlinkCreator: 1
  MetadataCopyer: 2
  SymlinkDirChecker: 3
  SymlinkChecker: 4

#全局设置结束

sync_list:
    # 需要添加多个目录同步,直接复制粘贴从"- cloud_path:... 到 metadata_ext:..."为止的内容进行修改即可
    #下面的三个路径填的是容器内的映射路径
    #注意：多个目录同步,symlink_dir不能相同,否则全同步时会误删文件

    #cloud_path是网盘文件夹的挂载路径,用以检测网盘文件夹的挂载状态,需要填具体的网盘挂载路径,如115网盘就填/volume1/CloudNAS/CloudDrive2/115
  - cloud_path: "/path/to/cloud_path"
    #网盘挂载文件夹
    media_dir: "/path/to/media_dir"
    #本地链接文件夹,程序会在此文件夹中创建软链接/strm文件
    symlink_dir: "/path/to/synlink_dir"

    #当前目录同步状态:true为开启,false为关闭
    sync_enabled: true

    #重启容器后是否进行全同步:true为开启,false为关闭
    restart_sync_enabled: true

    #实时监控文件夹:true为开启,false为关闭
    observer_enabled: true

    #监控模式:
    #"compatibility":兼容模式，目录同步性能降低且NAS不能休眠，但可以兼容挂载的远程共享目录如SMB
    #"fast":内部处理系统操作类型选择最优解,监控性能更灵敏
    #两种模式可以自己测试一下，选择适合自己的模式
    observer_mode: "compatibility"

    #本地链接模式
    #symlink:软链接模式,创建视频软链接,和windows中的快捷方式一样
    #strm:strm文件模式，创建包含网盘视频播放地址的文件,优点在于直接访问视频的原始地址,emby扫库会更快
    symlink_mode: "symlink"

    #下面是strm模式才需要填写的内容,如果不用strm模式可以不填
    #clouddrive2的挂载根目录
    #比如/volume1/CloudNAS/CloudDrive2/115对应的挂载根目录就是/volume1/CloudNAS/CloudDrive2
    clouddrive2_path: ""

    #alist的挂载路径
    alist_path: ""
    #不要加http,推荐写具体的ip:19798,如192.168.9.89:19798
    cloud_url: ""
    #填cd2/alist
    cloud_type: ""

    #开始同步的时候是否运行下面的程序,true为运行,false为不运行,如果不需要从网盘同步元数据到本地,则metadata_copyer设为false
    #清除无效文件夹
    symlink_dir_checker: true
    #清除无效软链接/strm文件
    symlink_checker: true
    #更新元数据
    metadata_copyer: true
    #更新软链接/strm文件
    symlink_creator: true

    #要同步的后缀名,可以单独设置,如果不设置,则默认为全局后缀名
    #软链接/strm文件指定后缀名
    symlink_ext: ".mkv;.iso;.ts;.mp4;.avi;.rmvb;.wmv;.m2ts;.mpg;.flv;.rm;.mov"
    #元数据指定后缀名
    metadata_ext: ".nfo;.jpg;.png;.svg;.ass;.srt;.sup"'''
    with open('./config/config.yaml','w',encoding='utf-8') as f:
        f.write(content)

def create_last_sync_yaml():
    content = '''last_sync_list:
  - "/path/to/cloud_path"'''
    with open('./config/last_sync.yaml','w',encoding='utf-8') as f:
        f.write(content)

if __name__ == '__main__':
    working_directory = os.path.dirname(os.path.abspath(__file__))
    os.chdir(working_directory)
    create_config()