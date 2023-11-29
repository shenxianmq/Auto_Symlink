# auto_symlink
适用于通过CloudDrive2/Alist挂载网盘到本地的情况，创建软链接方便Emby/Jellyfin等媒体服务器刮削与读取，避免频繁访问网盘

自动复制与更新元数据，创建与更新软链接，清空无效文件夹，清空无效软链接

使用方法：

支持多目录自动同步

在config文件夹中新建txt文件，文件名随意在文件中配置好如下两个变量（路径不要加引号）：

media_dir = /path/to/media/dir

symlink_dir = /path/to/symlink_dir

需要同步几个目录就新建几个txt文件，文件中配置好上面两个变量即可

然后"python auto_symlink.py"

Tips：在windows系统中使用时，需要"以管理员模式运行"
