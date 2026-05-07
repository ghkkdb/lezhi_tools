# Ubuntu + Nginx + systemd + FastAPI + Vue 后台部署指南

这份文档按“小白照做”的方式写。目标是把本项目部署到一台 Ubuntu 云服务器上，让你可以：

- 访问网页后台。
- 客户端连接服务器做卡密验证。
- 客户端上报使用事件。
- 后台发布版本更新信息。
- 后续把更新包放到服务器供客户端下载。

以下示例假设：

- 你的服务器公网 IP 是 `47.98.249.200`。
- 你没有域名。
- 本地项目目录是 `D:\Desktop\lezhi_tools`。
- 后端使用 FastAPI，代码在本地 `server\`。
- 后台前端使用 Vue3 + Vite，代码在本地 `admin\`。
- 服务器部署目录统一使用 `/opt/lezhi_tools`。

如果你的服务器 IP 不一样，把文档里的 `47.98.249.200` 换成你的真实 IP。

## 0. 本地目录和服务器目录对应关系

先明确哪些东西要上传。

```text
本地 D:\Desktop\lezhi_tools\server\
上传到 /opt/lezhi_tools/backend/
用途：FastAPI 后端代码。
```

```text
本地 D:\Desktop\lezhi_tools\admin\dist\
上传到 /opt/lezhi_tools/admin/dist/
用途：网页后台静态文件。
```

```text
本地 D:\Desktop\lezhi_tools\updates\*.zip
上传到 /opt/lezhi_tools/updates/
用途：客户端更新包。
```

当前项目没有普通用户前台页面，所以不需要 `/opt/lezhi_tools/frontend/dist/`。

如果目前没有更新包，`updates/` 可以是空目录。

## 1. 本地先构建后台页面

在你的 Windows 电脑上打开 PowerShell。

进入后台前端目录：

```powershell
cd D:\Desktop\lezhi_tools\admin
```

安装 Node 依赖：

```powershell
npm install
```

构建后台页面：

```powershell
npm run build
```

成功后会出现：

```text
D:\Desktop\lezhi_tools\admin\dist\
```

如果提示 `npm` 不是命令，说明你本地还没安装 Node.js。先安装 Node.js LTS 版本，然后重新打开 PowerShell 再执行。

## 2. 修改客户端服务器地址

客户端请求地址写在：

```text
D:\Desktop\lezhi_tools\src\config\app_config.py
```

确认里面是你的服务器地址：

```python
API_BASE_URL = "http://47.98.249.200"
```

注意：如果你按本文档使用 Nginx 反向代理，客户端地址不要写 `:8000`，应该写：

```python
API_BASE_URL = "http://47.98.249.200"
```

这样客户端会访问：

```text
http://47.98.249.200/api/license/verify
http://47.98.249.200/api/events
```

如果你绕过 Nginx、直接让客户端访问 FastAPI，才使用：

```python
API_BASE_URL = "http://47.98.249.200:8000"
```

推荐使用 Nginx，所以本文后面都按不带 `:8000` 来部署。

## 3. 登录服务器

在 Windows PowerShell 里用 SSH 登录服务器。

把下面的 IP 换成你的服务器 IP：

```powershell
ssh root@47.98.249.200
```

第一次连接会问是否继续，输入：

```text
yes
```

然后输入服务器 root 密码。

后面的命令都在服务器终端里执行，不是在本地 PowerShell。

## 4. 安装服务器基础软件

更新软件源：

```bash
sudo apt update
```

安装 Python、Nginx、SQLite 和常用工具：

```bash
sudo apt install -y python3 python3-venv python3-pip nginx sqlite3 curl unzip rsync
```

检查是否安装成功：

```bash
python3 --version
nginx -v
sqlite3 --version
```

## 5. 创建部署目录和运行用户

创建一个专门运行服务的用户：

```bash
sudo useradd --system --create-home --shell /usr/sbin/nologin lezhi
```

如果提示用户已存在，可以忽略。

创建项目目录：

```bash
sudo mkdir -p /opt/lezhi_tools/backend
sudo mkdir -p /opt/lezhi_tools/admin/dist
sudo mkdir -p /opt/lezhi_tools/updates
sudo mkdir -p /opt/lezhi_tools/data
sudo mkdir -p /opt/lezhi_tools/logs
```

把目录权限交给 `lezhi` 用户：

```bash
sudo chown -R lezhi:lezhi /opt/lezhi_tools
```

## 6. 上传后端代码和后台 dist

这一步在你的 Windows 本地 PowerShell 执行，不是在服务器里执行。

先新开一个 PowerShell 窗口。

上传后端代码：

```powershell
scp -r D:\Desktop\lezhi_tools\server\* root@47.98.249.200:/opt/lezhi_tools/backend/
```

上传后台构建产物：

```powershell
scp -r D:\Desktop\lezhi_tools\admin\dist\* root@47.98.249.200:/opt/lezhi_tools/admin/dist/
```

如果你已经有更新包，比如：

```text
D:\Desktop\lezhi_tools\updates\lezhi_tools_1.0.1.zip
```

再上传更新包：

```powershell
scp D:\Desktop\lezhi_tools\updates\*.zip root@47.98.249.200:/opt/lezhi_tools/updates/
```

如果没有更新包，这一步跳过。

上传完成后，回到服务器 SSH 终端，修正权限：

```bash
sudo chown -R lezhi:lezhi /opt/lezhi_tools
```

检查文件是否存在：

```bash
ls -lah /opt/lezhi_tools/backend
ls -lah /opt/lezhi_tools/admin/dist
ls -lah /opt/lezhi_tools/updates
```

## 7. 创建后端 Python 虚拟环境

在服务器 SSH 终端执行。

进入部署目录：

```bash
cd /opt/lezhi_tools
```

创建虚拟环境：

```bash
sudo -u lezhi python3 -m venv .venv
```

升级 pip：

```bash
sudo -u lezhi /opt/lezhi_tools/.venv/bin/pip install --upgrade pip -i https://pypi.tuna.tsinghua.edu.cn/simple
```

安装后端依赖：

```bash
sudo -u lezhi /opt/lezhi_tools/.venv/bin/pip install -r /opt/lezhi_tools/backend/requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

## 8. 配置后端环境变量

创建环境变量文件：

```bash
sudo tee /etc/lezhi_tools.env >/dev/null <<'EOF'
ADMIN_USERNAME=admin
ADMIN_PASSWORD=请改成一个强密码
LICENSE_SERVER_DB=/opt/lezhi_tools/data/server.sqlite3
EOF
```

把 `请改成一个强密码` 改成你自己的后台管理员密码。

例如：

```bash
sudo nano /etc/lezhi_tools.env
```

编辑完按：

```text
Ctrl + O 保存
Enter 确认
Ctrl + X 退出
```

注意：默认账号是 `admin`，密码就是这里的 `ADMIN_PASSWORD`。

## 9. 手动启动一次后端测试

先手动启动，确认后端没问题。

```bash
cd /opt/lezhi_tools/backend
sudo -u lezhi --preserve-env=ADMIN_USERNAME,ADMIN_PASSWORD,LICENSE_SERVER_DB \
  env $(cat /etc/lezhi_tools.env | xargs) \
  /opt/lezhi_tools/.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000
```

看到类似下面的信息，说明启动成功：

```text
Uvicorn running on http://127.0.0.1:8000
```

再新开一个服务器 SSH 窗口，测试接口：

```bash
curl http://127.0.0.1:8000/docs
```

如果能返回 HTML，说明后端可用。

回到刚才运行 Uvicorn 的窗口，按：

```text
Ctrl + C
```

停止手动运行。

如果这一步报错，先不要继续配置 Nginx，先看错误信息。

## 10. 创建 systemd 服务

systemd 用来让后端开机自启、崩溃自动重启。

创建服务文件：

```bash
sudo tee /etc/systemd/system/lezhi-tools.service >/dev/null <<'EOF'
[Unit]
Description=Lezhi Tools FastAPI Service
After=network.target

[Service]
Type=simple
User=lezhi
Group=lezhi
WorkingDirectory=/opt/lezhi_tools/backend
EnvironmentFile=/etc/lezhi_tools.env
ExecStart=/opt/lezhi_tools/.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF
```

启动服务：

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now lezhi-tools
```

查看状态：

```bash
sudo systemctl status lezhi-tools --no-pager
```

如果看到 `active (running)`，说明后端服务已经运行。

查看后端日志：

```bash
sudo journalctl -u lezhi-tools -n 100 --no-pager
```

持续看日志：

```bash
sudo journalctl -u lezhi-tools -f
```

## 11. 配置 Nginx

Nginx 做三件事：

- 访问 `http://47.98.249.200/` 显示后台页面。
- 访问 `http://47.98.249.200/api/...` 转发到 FastAPI。
- 访问 `http://47.98.249.200/updates/...` 下载更新包。

创建 Nginx 配置：

```bash
sudo tee /etc/nginx/sites-available/lezhi-tools >/dev/null <<'EOF'
server {
    listen 80 default_server;
    listen [::]:80 default_server;
    server_name _;

    client_max_body_size 100m;

    root /opt/lezhi_tools/admin/dist;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    location /updates/ {
        alias /opt/lezhi_tools/updates/;
        autoindex off;
        add_header Cache-Control "public, max-age=300";
        try_files $uri =404;
    }

    location /api/ {
        proxy_pass http://127.0.0.1:8000/api/;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
EOF
```

启用这个站点：

```bash
sudo rm -f /etc/nginx/sites-enabled/default
sudo ln -sf /etc/nginx/sites-available/lezhi-tools /etc/nginx/sites-enabled/lezhi-tools
```

检查 Nginx 配置是否正确：

```bash
sudo nginx -t
```

如果显示 `syntax is ok` 和 `test is successful`，重载 Nginx：

```bash
sudo systemctl reload nginx
```

## 12. 放行防火墙和云服务器安全组

如果服务器启用了 UFW：

```bash
sudo ufw allow OpenSSH
sudo ufw allow 'Nginx Full'
sudo ufw status
```

如果 `ufw status` 显示 inactive，也没关系。

还需要去云服务器控制台安全组放行：

```text
TCP 22    SSH 登录
TCP 80    网页后台和客户端 API
```

暂时不需要开放 `8000`，因为 FastAPI 只监听本机 `127.0.0.1:8000`，外部通过 Nginx 访问。

## 13. 浏览器访问后台

在你的电脑浏览器打开：

```text
http://47.98.249.200/
```

登录账号：

```text
账号：admin
密码：你在 /etc/lezhi_tools.env 里设置的 ADMIN_PASSWORD
```

登录后能看到：

- 仪表盘
- 卡密管理
- 客户端绑定
- 版本发布
- 事件日志

## 14. 创建第一张卡密

进入后台的“卡密管理”页面。

填写：

```text
天数：30
最大客户端：1
备注：测试卡密
```

点击“生成卡密”。

复制生成出来的卡密，后面客户端里要输入它。

## 15. 客户端连接服务器

确认本地客户端配置：

```text
D:\Desktop\lezhi_tools\src\config\app_config.py
```

应为：

```python
API_BASE_URL = "http://47.98.249.200"
```

然后运行客户端：

```powershell
cd D:\Desktop\lezhi_tools
python main.py
```

打开客户端后：

1. 进入“基础设置”。
2. 输入后台生成的卡密。
3. 点击“验证卡密”。
4. 授权有效后，再去执行任务。

如果授权无效，主界面仍能打开，但任务启动会被拦截。

## 16. 检查使用数据是否上报

客户端启动或验证卡密后，回到网页后台。

打开：

```text
事件日志
```

你应该能看到类似事件：

```text
app_start
license_verify
license_activate
update_check
task_start
task_finish
task_error
```

如果看不到，先在服务器检查后端日志：

```bash
sudo journalctl -u lezhi-tools -n 100 --no-pager
```

再检查 Nginx 访问日志：

```bash
sudo tail -n 100 /var/log/nginx/access.log
```

## 17. 发布新版本更新信息

如果你还没有更新包，可以跳过本节。

假设你有一个更新包：

```text
D:\Desktop\lezhi_tools\updates\lezhi_tools_1.0.1.zip
```

上传到服务器：

```powershell
scp D:\Desktop\lezhi_tools\updates\lezhi_tools_1.0.1.zip root@47.98.249.200:/opt/lezhi_tools/updates/
```

服务器上修正权限：

```bash
sudo chown -R lezhi:lezhi /opt/lezhi_tools/updates
```

下载地址就是：

```text
http://47.98.249.200/updates/lezhi_tools_1.0.1.zip
```

进入后台“版本发布”页面，填写：

```text
版本号：1.0.1
下载地址：http://47.98.249.200/updates/lezhi_tools_1.0.1.zip
更新说明：写本次更新内容
```

发布后，客户端下次检查更新会提示新版本。

当前实现只提醒用户手动下载，不会自动替换安装。

## 18. 常用检查命令

检查后端服务：

```bash
sudo systemctl status lezhi-tools --no-pager
```

重启后端服务：

```bash
sudo systemctl restart lezhi-tools
```

查看后端日志：

```bash
sudo journalctl -u lezhi-tools -n 100 --no-pager
```

查看后端实时日志：

```bash
sudo journalctl -u lezhi-tools -f
```

检查 Nginx 配置：

```bash
sudo nginx -t
```

重载 Nginx：

```bash
sudo systemctl reload nginx
```

查看 Nginx 错误日志：

```bash
sudo tail -n 100 /var/log/nginx/error.log
```

检查端口：

```bash
ss -lntp | grep ':80\|:8000'
```

测试后端本机接口：

```bash
curl -i http://127.0.0.1:8000/docs
```

测试 Nginx 转发：

```bash
curl -i http://47.98.249.200/api/admin/stats
```

这个接口未登录时返回 `401` 是正常的，说明请求已经转发到 FastAPI。

测试后台页面：

```bash
curl -I http://47.98.249.200/
```

测试更新包目录：

```bash
curl -I http://47.98.249.200/updates/
```

如果目录为空，可能返回 `403`，这是正常的；具体文件存在时应该能下载。

## 19. 更新部署流程

以后你修改后端代码后：

1. 本地上传新的 `server\` 到服务器 `/opt/lezhi_tools/backend/`。
2. 服务器执行：

```bash
sudo chown -R lezhi:lezhi /opt/lezhi_tools/backend
sudo -u lezhi /opt/lezhi_tools/.venv/bin/pip install -r /opt/lezhi_tools/backend/requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
sudo systemctl restart lezhi-tools
```

以后你修改后台页面后：

1. 本地重新构建：

```powershell
cd D:\Desktop\lezhi_tools\admin
npm run build
```

2. 上传新的 `admin\dist\` 到服务器：

```powershell
scp -r D:\Desktop\lezhi_tools\admin\dist\* root@47.98.249.200:/opt/lezhi_tools/admin/dist/
```

3. 服务器修正权限并重载 Nginx：

```bash
sudo chown -R lezhi:lezhi /opt/lezhi_tools/admin/dist
sudo systemctl reload nginx
```

不要删除：

```text
/opt/lezhi_tools/data/
```

这里面有 SQLite 数据库，删了卡密、事件、版本记录都会丢。

## 20. 常见问题

### 打开后台是 403 或 404

检查后台 dist 是否上传成功：

```bash
ls -lah /opt/lezhi_tools/admin/dist
```

里面应该有：

```text
index.html
assets/
```

然后检查 Nginx：

```bash
sudo nginx -t
sudo systemctl reload nginx
```

### `/api` 返回 502

说明 Nginx 找不到后端。

检查后端是否运行：

```bash
sudo systemctl status lezhi-tools --no-pager
```

检查后端日志：

```bash
sudo journalctl -u lezhi-tools -n 100 --no-pager
```

### 客户端验证卡密失败

先确认客户端地址：

```python
API_BASE_URL = "http://47.98.249.200"
```

然后在服务器看日志：

```bash
sudo tail -n 100 /var/log/nginx/access.log
sudo journalctl -u lezhi-tools -n 100 --no-pager
```

如果没有任何请求记录，说明客户端没有连到服务器，检查 IP、安全组、防火墙。

### 后台登录失败

确认 `/etc/lezhi_tools.env` 中的账号密码：

```bash
sudo cat /etc/lezhi_tools.env
```

注意：默认管理员只在数据库第一次初始化时创建。如果你启动过一次后又改了 `ADMIN_PASSWORD`，旧数据库里的管理员密码不会自动变化。

小白处理方式：

如果是刚部署、没有重要数据，可以删除数据库重新初始化：

```bash
sudo systemctl stop lezhi-tools
sudo rm -f /opt/lezhi_tools/data/server.sqlite3
sudo systemctl start lezhi-tools
```

然后用新的 `ADMIN_PASSWORD` 登录。

如果已经有重要卡密和事件数据，不要删除数据库。

### 事件日志没有 IP

确认 Nginx 配置里有这几行：

```nginx
proxy_set_header X-Real-IP $remote_addr;
proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
```

然后重载 Nginx：

```bash
sudo nginx -t
sudo systemctl reload nginx
```

