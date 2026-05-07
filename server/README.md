# Lezhi License Server

最小 FastAPI + SQLite 服务端，提供客户端授权、更新查询、事件写入，以及管理员登录、卡密、客户端、版本、事件和统计接口。

## 启动

```powershell
cd D:\Desktop\lezhi_tools\server
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

默认数据库：`server\data\server.sqlite3`。

默认管理员账号由首次启动时创建：

```powershell
$env:ADMIN_USERNAME="admin"
$env:ADMIN_PASSWORD="admin123"
```

生产环境必须改掉默认密码。也可以通过 `LICENSE_SERVER_DB` 指定数据库路径。

## 客户端接口

- `POST /api/license/activate`
  - 请求：`{"key":"LIC-xxx","machine_id":"pc-1","client_name":"A","app_version":"1.0.0"}`
  - 返回：`{"valid":true,"activation_token":"act_...","license":{...}}`
- `POST /api/license/verify`
  - 请求：`{"activation_token":"act_...","machine_id":"pc-1","app_version":"1.0.1"}`
  - 或：`{"key":"LIC-xxx","machine_id":"pc-1"}`
- `GET /api/update/latest?platform=windows`
- `POST /api/events`
  - 请求：`{"event_type":"client.start","activation_token":"act_...","machine_id":"pc-1","payload":{"x":1}}`

## 管理接口

登录后服务端会写入 HttpOnly Cookie：`admin_session`。也可以使用返回的 `token` 作为 `Authorization: Bearer <token>`。

- `POST /api/admin/login`
- `GET /api/admin/me`
- `POST /api/admin/logout`
- `GET /api/admin/licenses`
- `POST /api/admin/licenses`
- `PATCH /api/admin/licenses/{license_id}`
- `GET /api/admin/clients`
- `GET /api/admin/releases`
- `POST /api/admin/releases`
- `PATCH /api/admin/releases/{release_id}`
- `GET /api/admin/events`
- `GET /api/admin/stats`

交互式接口文档：启动后打开 `http://127.0.0.1:8000/docs`。

## 测试

```powershell
cd D:\Desktop\lezhi_tools\server
pytest -q
```

