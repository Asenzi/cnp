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
- Celery（异步任务队列）
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

**启动 FastAPI 服务器：**

```bash
# 在 backend 目录下执行
uvicorn app.main:app --reload --host 0.0.0.0 --port 8001

# 或从项目根目录执行

.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

如果项目目录移动过，旧的 `backend/.venv` 可能记录了原目录路径，建议删除后重建：

```powershell
cd backend
Remove-Item -Recurse -Force .venv
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

如果提示 `No suitable Python runtime found`，说明本机没有安装 Python 3.11。先查看已安装版本，再用已有版本创建虚拟环境：

```powershell
py -0p
py -3.13 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

**启动 Celery Worker（异步任务处理）：**

```bash
# 在新的终端窗口中运行
celery -A app.core.celery_app worker --loglevel=info

# Windows 需要添加 --pool=solo
celery -A app.core.celery_app worker --loglevel=info --pool=solo
```

**启动 Celery Beat（定时任务调度，可选）：**

```bash
# 在新的终端窗口中运行
celery -A app.core.celery_app beat --loglevel=info
```

**监控 Celery 任务（可选）：**

```bash
# 安装 flower
pip install flower

# 启动 flower
celery -A app.core.celery_app flower
# 访问 http://localhost:5555
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
- Celery 异步任务队列
- 全局日志配置（loguru）
- 统一响应结构
- 统一异常处理
- `/api/v1` 路由前缀
- 健康检查接口
- 业务模块路由占位（auth/user/circle/network/post/event/im/payment/admin）

## Celery 任务使用示例

### 在代码中调用异步任务

```python
from app.tasks.email import send_verification_email, send_welcome_email
from app.tasks.notification import send_push_notification

# 立即执行（异步）
send_verification_email.delay("user@example.com", "123456")

# 延迟 60 秒后执行
send_welcome_email.apply_async(
    args=["user@example.com", "张三"],
    countdown=60
)

# 指定时间执行
from datetime import datetime, timedelta
send_push_notification.apply_async(
    args=[123, "提醒", "您有新消息"],
    eta=datetime.now() + timedelta(hours=1)
)
```

### 创建新的异步任务

在 `app/tasks/` 目录下创建新文件，例如 `app/tasks/cleanup.py`：

```python
from app.core.celery_app import celery_app
from app.core.logger import logger

@celery_app.task(name="app.tasks.cleanup.cleanup_expired_sessions")
def cleanup_expired_sessions() -> dict[str, int]:
    """清理过期会话"""
    try:
        # 实现清理逻辑
        deleted_count = 0
        logger.info(f"Cleaned up {deleted_count} expired sessions")
        return {"deleted": deleted_count}
    except Exception as exc:
        logger.error(f"Failed to cleanup sessions: {exc}")
        raise
```

然后在 `app/core/celery_app.py` 的 `include` 列表中添加新模块：

```python
include=["app.tasks.email", "app.tasks.notification", "app.tasks.cleanup"]
```

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
