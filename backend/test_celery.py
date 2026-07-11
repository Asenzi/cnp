"""Test Celery tasks execution."""

import sys
import time

# Fix Windows console encoding
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

from app.tasks.email import send_verification_email, send_welcome_email
from app.tasks.notification import send_push_notification, send_system_notification

print("=" * 60)
print("Testing Celery Tasks")
print("=" * 60)

# Test 1: Send verification email
print("\n[Test 1] Sending verification email...")
result1 = send_verification_email.delay("test@example.com", "123456")
print(f"Task ID: {result1.id}")
print(f"Task State: {result1.state}")

# Wait a moment
time.sleep(2)

# Check result
if result1.ready():
    print(f"Task Result: {result1.result}")
    print("[PASSED] Test 1")
else:
    print("[PENDING] Task still processing...")

# Test 2: Send welcome email
print("\n[Test 2] Sending welcome email...")
result2 = send_welcome_email.delay("newuser@example.com", "张三")
print(f"Task ID: {result2.id}")

time.sleep(2)

if result2.ready():
    print(f"Task Result: {result2.result}")
    print("[PASSED] Test 2")
else:
    print("[PENDING] Task still processing...")

# Test 3: Send push notification
print("\n[Test 3] Sending push notification...")
result3 = send_push_notification.delay(123, "测试通知", "这是一条测试消息")
print(f"Task ID: {result3.id}")

time.sleep(2)

if result3.ready():
    print(f"Task Result: {result3.result}")
    print("[PASSED] Test 3")
else:
    print("[PENDING] Task still processing...")

# Test 4: Batch notifications
print("\n[Test 4] Sending batch notifications...")
result4 = send_system_notification.delay([1, 2, 3, 4, 5], "系统公告", "这是一条系统公告")
print(f"Task ID: {result4.id}")

time.sleep(2)

if result4.ready():
    print(f"Task Result: {result4.result}")
    print("[PASSED] Test 4")
else:
    print("[PENDING] Task still processing...")

print("\n" + "=" * 60)
print("All tests completed!")
print("=" * 60)
