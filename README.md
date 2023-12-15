# auto_symlink

适用于通过 CloudDrive2/Alist 挂载网盘到本地的情况，创建软链接方便 Emby/Jellyfin 等媒体服务器刮削与读取，避免频繁访问网盘

实时监控指定目录，自动复制与更新元数据，创建与更新软链接，清空无效文件夹，清空无效软链接

## 使用方法：

1. 直接运行 py 文件

   **支持多目录自动同步，多目录同步时，软链接目录不可以是同一个目录，否则清除无效文件夹的时候，会误以为云端不存在对应的文件夹而清除**

   第一次运行程序后会在 config 文件夹中生成 config.yaml 文件，然后打开 config.yaml 后根据注释进行自定义配置即可

   配置好后 'python auto_symlink.py'

   Tips：在 Windows 系统中使用时，需要 "以管理员模式运行"

2. docker 运行

   ```bash
   docker run -d \
     --name auto_symlink \
     -e TZ=Asia/Shanghai \
     -v /volume1/CloudNAS:/volume1/CloudNAS:rslave \  #网盘映射路径左右要一致
     -v /volume2/Media:/Media \
     -v /volume1/docker/auto_symlink/config:/app/config \
     --restart unless-stopped \
     --log-opt max-size=10m \
     --log-opt max-file=3 \
     shenxianmq/auto_symlink:latest
Tips：网盘路径映射进容器的时候，必须为绝对路径，否则软链接会找不到正确的路径

## 配置目录说明:
config.yaml: 以 yaml 格式的配置文件，主要配置都在里面，具体配置可以参考文件里的注释
last_sync.yaml：用以保存已经同步过的目标目录，如果重建容器，不希望重新全同步的话，可以自己把对应的目标目录填入
