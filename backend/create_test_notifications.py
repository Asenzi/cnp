# -*- coding: utf-8 -*-
"""
临时脚本:为当前用户创建测试通知数据
"""
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from datetime import datetime, UTC
from app.core.database import SessionLocal
from app.models.notification import Notification


def create_test_notifications():
    """创建测试通知数据"""
    db = SessionLocal()
    try:
        # 创建系统通知示例
        system_notifications = [
            Notification(
                user_pk=17,
                type="system",
                title="欢迎加入圈脉链",
                content="欢迎您使用圈脉链!在这里你可以扩展人脉、加入圈子、分享资源。",
                is_read=False,
            ),
            Notification(
                user_pk=17,
                type="system",
                title="完善个人资料",
                content="完善你的个人资料可以获得更多曝光机会,快去填写吧!",
                link_type="user",
                link_id="17",
                is_read=False,
            ),
            Notification(
                user_pk=17,
                type="system",
                title="系统维护通知",
                content="系统将于今晚23:00-24:00进行例行维护,届时部分功能可能暂时无法使用。",
                is_read=True,
                read_at=datetime.now(UTC),
            ),
        ]

        # 创建圈子通知示例
        circle_notifications = [
            Notification(
                user_pk=17,
                type="circle",
                title="新的圈子申请",
                content="张三申请加入你的圈子",
                link_type="circle",
                link_id="circle_001",
                is_read=False,
            ),
            Notification(
                user_pk=17,
                type="circle",
                title="圈子申请已通过",
                content="你的加入申请已通过",
                link_type="circle",
                link_id="circle_002",
                is_read=True,
                read_at=datetime.now(UTC),
            ),
        ]

        all_notifications = system_notifications + circle_notifications

        for notification in all_notifications:
            db.add(notification)

        db.commit()
        print(f"Success: Created {len(all_notifications)} test notifications")
    except Exception as e:
        db.rollback()
        print(f"Error: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    create_test_notifications()
