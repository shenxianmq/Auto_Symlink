### 交流群
telegram: https://t.me/autosymlink_channel

### 文档
https://github.com/shenxianmq/Auto_Symlink/wiki

### Auto_Symlink

**小白牙整理**

### 项目简介
`Auto_Symlink` 是一个自动化工具，专门设计用于管理通过 CloudDrive2/Alist 挂载到本地的网盘。它能够创建软链接，使得像 Emby/Jellyfin/Plex 这样的媒体服务器能够更容易地刮削和读取内容，同时减少对网盘的频繁访问。

#### 主要特性:
- **实时监控**: 需要CloudDrive2的会员功能**文件通知**,监控指定目录，自动进行必要的更新和管理。
- **自动化处理**: 创建与更新软链接/strm文件，自动复制与更新元数据。
- **清理功能**: 清空无效文件夹和软链接，保持本地云端一致性。
- **转存监控**: 在**常用工具**中，自动监控指定文件夹，转移到目标文件夹，并删除源文件
- **媒体库通知**: 支持Emby/Plex通知，当检测到新视频的时候，会自动通知Emby/Plex扫描该视频，极大加块扫库速度
- **封面制作**: 自动生成精美的Emby媒体库封面
- **Web 界面操作**: 提供一个简洁易用的Web界面，用于查看日志、编辑配置和监控系统状态。这使得用户能够更方便地管理和调整 Auto_Symlink 的运行。
更多功能可以去**常用工具**中自行发掘.

---

### 安装和使用
1. **直接运行 Python 文件**:
   - 在首次运行后，`config` 文件夹中会生成 `config.yaml` 文件。根据文件中的注释进行配置。
   - 配置完成后，使用命令 `python auto_symlink.py` 运行。
   - 在 Windows 系统中，需要以管理员模式运行。

2. **Docker 运行**:
   使用以下命令运行 Docker 容器：
   ```bash
   docker run -d \
     --name auto_symlink \
     -e TZ=Asia/Shanghai \
     -v /volume1/CloudNAS:/volume1/CloudNAS:rslave \
     -v /volume2/Media:/Media \
     -v /volume1/docker/auto_symlink/config:/app/config \
     -p 8095:8095 \
     --user 0:0 \
     --restart unless-stopped \
     shenxianmq/auto_symlink:latest
   ```
   注意：映射网盘路径时必须使用绝对路径。

---

### Docker 运行指令详解
- `-v /your/cloud/path:/cloudpath:rslave`: 将你的云盘路径（`/your/cloud/path`）映射到容器内的路径（`/your/cloud/path`）。`rslave` 表示使用相对于宿主机的从属挂载模式。请确保左右路径保持一致，否则生成的软链接不是指向真实路径，导入emby中的时候会导致无法观看。**（简单的来说，这里需要填写你映射的云盘路径，且两边都填写一模一样的路径即可。）**
- `-v /your/media/path:/media`: 将你即将创建软连接的位置映射到容器内的 `/media` 目录。
- `-p 8095:8095`: 映射8095端口，可方便的查看日志以及管理服务。
- `-v /path/to/auto_symlink/config:/app/config`: 将 `auto_symlink` 的配置目录映射到容器内的 `/app/config`。这样可以使容器中的 `auto_symlink` 使用外部的配置文件。
- `--restart unless-stopped`: 设置容器在退出时自动重启。

#### 注意：
- 映射云盘路径时必须使用绝对路径（虽然此处是本工具的docker运行说明，但EMBY也应使用同样的绝对路径，否则软连接将指向错误的位置，从而导致无法播放），以确保软连接可以正确指向原始文件或目录。
- 根据你的实际路径和需求调整 `-v` 选项中的路径。
- 群晖请使用控制台创建docker，因为群晖的Docker GUI界面无法选择`rslave`模式
---
### Web 界面访问和账户信息

#### 账号密码
- 默认账号：`admin`
- 默认密码：`password`

在首次登录时，你可以使用这些凭据进行登录。为了安全起见，建议登录后立即更改密码。

#### Web界面说明
通过映射端口8095，用户可以方便地访问 `Auto_Symlink` 的Web界面。在任何支持的浏览器中输入 `http://[你的服务器地址]:8095` 即可访问。

---

## 常见问题解答 (FAQ)

#### Q: `auto_symlink` 在什么情况下特别有用？
**答**: 当你正在使用CloudDrive2/Alist等工具管理媒体，并使用EMBY/Jellyfin等工具来管理这些媒体时，本工具将大大降低媒体刮削时访问网盘的频率。

#### Q: EMBY显示当前没有兼容的流
**答**: 请确保你EMBY映射的也是绝对路径，需要与 `auto_symlink`设置的路径保持一致。

#### Q: 虽然我有元数据，但EMBY扫库还是很慢？
**答**: 因为我们映射了所有影片的软连接，所以可以尝试先禁用EMBY的FFmpeg进程，CloudDrive2可以在设置黑名单添加`/bin/ffprobe`，扫库完成后，再删除该黑名单即可。

#### Q: 我映射后为什么不能在windows下播放？
**答**: 映射的软连接仅支持绝对路径，windows下的绝对路径肯定与linux不一致，所以请在EMBY内验证。

#### Q: 为什么运行完毕后，只同步了文件夹？
**答**: 群晖`File Station`或部分工具不支持显示软连接，可以尝试用windows或者命令行查看。

#### Q: 群晖创建容器rslave报错
**答**: 在群晖的任务计划中添加开机任务： 

mount --make-shared /volume1/ 

mount --make-shared /volume2/ 

systemctl daemon-reload 
添加后手动运行一次，之后开机会自动运行

---
