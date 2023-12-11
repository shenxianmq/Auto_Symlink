# auto_symlink
适用于通过CloudDrive2/Alist挂载网盘到本地的情况，创建软链接方便Emby/Jellyfin等媒体服务器刮削与读取，避免频繁访问网盘

自动复制与更新元数据，创建与更新软链接，清空无效文件夹，清空无效软链接

使用方法：

1.直接运行py文件

**支持多目录自动同步，多目录同步时，软链接目录不可以是同一个目录，否则清除无效文件夹的时候，会误以为云端不存在对应的文件夹而清除**

第一次运行程序后会在config文件夹中生成config.yaml文件，然后打开config.yaml后根据注释进行自定义配置即可

配置好后'python auto_symlink.py'

Tips：在windows系统中使用时，需要"以管理员模式运行"

2.docker运行

docker run -d \
  --name auto_symlink \
  -e TZ=Asia/Shanghai \
  -v /volume1/CloudNAS:/volume1/CloudNAS:rslave \  #映射目录自己根据实际情况修改
  -v /volume2/Media:/Media \
  -v /volume1/docker/auto_symlink/config:/app/config \
  shenxianmq/auto_symlink:latest

  Tips：网盘路径映射进容器的时候，必须为绝对路径，否则软链接会找不到正确的路径

