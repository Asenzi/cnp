"""运行数据库迁移脚本"""
import sys
from alembic import command
from alembic.config import Config

def run_migration():
    # 创建Alembic配置对象
    alembic_cfg = Config("alembic.ini")

    try:
        # 运行升级到最新版本
        print("开始运行数据库迁移...")
        command.upgrade(alembic_cfg, "head")
        print("✓ 数据库迁移成功完成！")
        return 0
    except Exception as e:
        print(f"✗ 数据库迁移失败: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(run_migration())
