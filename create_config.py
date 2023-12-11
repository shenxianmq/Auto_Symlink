import os
from print_message import print_message

def create_config():
    print_message('开始初始化配置文件...')
    if not os.path.exists('./config/config_done.txt'):
        create_config_yaml()
        create_sync_temp_yaml()
    else:
        if not os.path.exists('./config/config.yaml'):
            create_config_yaml()
        if not os.path.exists('./config/sync_temp.yaml'):
            create_sync_temp_yaml()
    with open('./config/config_done.txt','w',encoding='utf-8') as f:
        f.write('')

def create_config_yaml():
    content = '''#注:yaml文件很注重缩进,请不要随意删减空格,不确定的情况下请直接通过复制粘贴来添加同步目录
#如果想要重置配置文件状态,直接删除"/config/config_done.txt"即可

#更改设置后,需要重新运行程序/重启容器才会生效

#同步状态:true为开启,false为关闭
sync_enabled: false
#定时同步状态:true为开启,false为关闭
sync_status: false
#定时同步的时间间隔:单位为秒,支持乘法表达式,比如一天就是24*3600
sync_time: "3600"

#上传元数据:true为开启,false为关闭
upload_enabled: false
#定时上传元数据:true为开启,false为关闭
upload_metadata: false
#定时上传元数据的时间间隔:单位为秒,支持乘法表达式,比如一天就是24*3600
upload_sync_time: "24*3600"

#同步线程数
num_threads: 8

#全局同步后缀名,以;隔开
symlink_ext: ".mkv;.iso;.ts;.mp4;.avi;.rmvb;.wmv;123.m2ts;.mpg;.flv;.rm;.mov"
metadata_ext: ".nfo;.jpg;.png;.svg;.ass;.srt;.sup"

#选择程序运行的优先级,数字越小越靠前
func_order:
  MetadataCopyer: 1
  SymlinkDirChecker: 2
  SymlinkChecker: 3
  SymlinkCreator: 4

#同步文件夹选项,cloud_path是挂载的网盘文件夹路径,用以检测网盘文件夹挂载状态
sync_list:
  - cloud_path: "/path/to/cloud_path"
    media_dir: "/path/to/media_dir"
    symlink_dir: "/path/to/synlink_dir"

    #当前目录同步状态:true为开启,false为关闭
    sync_enabled: true

    #开始同步的时候是否运行下面的程序,true为运行,false为不运行,如果不需要从网盘同步元数据到本地,则metadata_copyer设为false
    #清除无效文件夹
    symlink_dir_checker: true
    #清除无效软链接
    symlink_checker: true
    #更新元数据
    metadata_copyer: true
    #更新软链接
    symlink_creator: true

    #要同步的后缀名,可以单独设置,如果不设置,则默认为全局后缀名
    symlink_ext: ".mkv;.iso;.ts;.mp4;.avi;.rmvb;.wmv;123.m2ts;.mpg;.flv;.rm;.mov"
    metadata_ext: ".nfo;.jpg;.png;.svg;.ass;.srt;.sup"

  # 需要添加多个目录同步,直接复制粘贴即可

#要上传元数据的文件夹
upload_list:
#cloud_path是网盘挂载目录,如果是本地同步,就是target_dir的上层目录
  - source_dir: "/path/to/source_dir" #源目录
    target_dir: "/path/to/target_dir" #目的目录
    #同步状态,true为开启同步,false为关闭同步
    upload_enabled: true
    #要同步的后缀名,可以单独设置,如果不设置,则默认为全局后缀名
    metadata_ext: ".nfo;.jpg;.png;.svg;.ass;.srt;.sup"'''
    with open('./config/config.yaml','w',encoding='utf-8') as f:
        f.write(content)

def create_sync_temp_yaml():
    content = '''last_sync_list:
  - cloud_path: "/path/to/cloud_path"
    media_dir: "/path/to/media_dir"
    symlink_dir: "/path/to/synlink_dir"'''
    with open('./config/sync_temp.yaml','w',encoding='utf-8') as f:
        f.write(content)

if __name__ == '__main__':
    working_directory = os.path.dirname(os.path.abspath(__file__))
    os.chdir(working_directory)
    create_config()