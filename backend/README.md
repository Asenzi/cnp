# 圈脉链后端基础工程（FastAPI）

下一步可以直接把消息页接入真实接口（会话列表、未读数、好友申请、系统通知）并做分页/下拉刷新。
当前按钮行为先用 toast 占位，后续你要我可以直接接后端申请接口（同意/忽略/已发送列表/未读计数）。

体验层建议

会员订单页（你可以在会员中心加“购买记录”）
支付中断后可恢复（重新进入页面自动轮询 pending 订单）
开通成功后的权益引导弹层
如果你要，我可以下一步直接把第 1 条和第 2 条一次性补完（/payment/wechat/notify + 查单确认 + 幂等），这是最关键的生产级缺口。

本目录提供“圈脉链”小程序后端 MVP 的基础框架，当前阶段只包含基础设施与工程骨架，不包含具体业务实现。

配置腾讯地图 WebService Key（二选一）
UNI_APP_QQ_MAP_KEY=你的key 或 VUE_APP_QQ_MAP_KEY=你的key。
微信小程序后台“request 合法域名”加入
https://apis.map.qq.com。

## 技术栈

- Python 3.11
- FastAPI
- SQLAlchemy 2.x
- Alembic
- Pydantic v2 + pydantic-settings
- MySQL
- Redis
- Uvicorn
- python-dotenv
- loguru

## 目录说明

```text
backend/
  app/
    main.py
    core/
    api/
    models/
    schemas/
    services/
    crud/
    utils/
    middleware/
    tasks/
  alembic/
  alembic.ini
  .env.example
  requirements.txt
  README.md
```

## 快速启动

1. 创建并激活虚拟环境（Python 3.11）
2. 安装依赖

```bash
pip install -r requirements.txt
```

3. 配置环境变量

```bash
cp .env.example .env
```

4. 启动服务

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8001

python -m uvicorn app.main:app --app-dir F:\项目区\friends\backend --host 0.0.0.0 --port 8001 --reload
```

WECHAT_PAY_ENABLED=true
WECHAT_PAY_APP_ID=你的小程序appid
WECHAT_PAY_MCH_ID=微信商户号
WECHAT_PAY_API_V2_KEY=商户APIv2密钥
WECHAT_PAY_NOTIFY_URL=https://你的域名/api/v1/payment/wechat/notify

5. 访问地址

- OpenAPI: `http://127.0.0.1:8001/docs`
- ReDoc: `http://127.0.0.1:8001/redoc`
- 根路径: `http://127.0.0.1:8001/`
- 健康检查: `http://127.0.0.1:8001/api/v1/health`

## Alembic 使用

初始化迁移（当前项目已包含 Alembic 配置）：

```bash
alembic revision -m "init"
```

执行迁移：

```bash
alembic upgrade head
```

回滚一步：

```bash
alembic downgrade -1
```

## 当前已具备能力

- 环境变量配置读取
- MySQL 连接与 Session 依赖
- Redis 初始化与关闭钩子
- 全局日志配置（loguru）
- 统一响应结构
- 统一异常处理
- `/api/v1` 路由前缀
- 健康检查接口
- 业务模块路由占位（auth/user/circle/network/post/event/im/payment/admin）

.\.venv\Scripts\alembic.exe upgrade head
.\.venv\Scripts\alembic.exe current

## Network Recommendation Notes

- Runtime config key: `network.reco.impression_1d_hide_count`
- Current default value: `5`
- Meaning: the same candidate will be temporarily hidden for the same viewer only after `5` impressions within `1` day
- If `sys_config` exists, runtime value is read from DB first; otherwise the backend falls back to the code default

Example SQL:

```sql
SELECT config_key, config_value
FROM sys_config
WHERE config_key = 'network.reco.impression_1d_hide_count';

UPDATE sys_config
SET config_value = '5'
WHERE config_key = 'network.reco.impression_1d_hide_count';
```

## Admin Console

- Login API: `POST /api/v1/admin/auth/login`
- Profile API: `GET /api/v1/admin/auth/profile`
- Dashboard API: `GET /api/v1/admin/dashboard/overview`
- Static entry: `http://127.0.0.1:8001/admin-console`
- Static file path: `backend/static/admin`

Default admin bootstrap:

- Username: `admin`
- Password: `Admin@20260325`

Optional env vars:

```env
ADMIN_DEFAULT_USERNAME=admin
ADMIN_DEFAULT_PASSWORD=Admin@20260325
ADMIN_DEFAULT_DISPLAY_NAME=系统管理员
```
