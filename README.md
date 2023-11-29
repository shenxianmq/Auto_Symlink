# auto_symlink
适用于通过CloudDrive2/Alist挂载网盘到本地的情况，创建软链接方便Emby/Jellyfin等媒体服务器刮削与读取，避免频繁访问网盘

自动复制与更新元数据，创建与更新软链接，清空无效文件夹，清空无效软链接

使用方法：

在config.txt中配置好"媒体文件夹 => media_dir"和"软链接文件夹 => symlink_dir",然后"python auto_symlink.py"

Tips：在windows系统中使用时，需要"以管理员运行"
