#!/usr/bin/env python3
"""测试圈子成员列表接口"""
import requests
import json

BASE_URL = "http://127.0.0.1:8000"
API_PREFIX = "/api/v1"
TEST_PHONE = "13800138000"

def get_token():
    """获取登录token"""
    response = requests.post(
        f"{BASE_URL}{API_PREFIX}/auth/sms-code",
        json={"phone": TEST_PHONE}
    )

    if response.status_code != 200:
        return None

    debug_code = response.json().get('data', {}).get('debug_code')
    if not debug_code:
        return None

    response = requests.post(
        f"{BASE_URL}{API_PREFIX}/auth/login",
        json={"phone": TEST_PHONE, "code": debug_code}
    )

    if response.status_code == 200:
        return response.json().get('data', {}).get('access_token')

    return None

def test_get_circle_members(token, circle_code):
    """测试获取圈子成员列表"""
    print(f"\n{'='*60}")
    print(f"测试: 获取圈子成员列表 (圈子代码: {circle_code})")
    print(f"{'='*60}")

    headers = {"Authorization": f"Bearer {token}"}

    response = requests.get(
        f"{BASE_URL}{API_PREFIX}/circle/{circle_code}/members",
        headers=headers,
        params={"offset": 0, "limit": 50}
    )

    print(f"\n状态码: {response.status_code}")

    if response.status_code == 200:
        result = response.json()
        print(f"[OK] 成功获取成员列表")

        data = result.get('data', {})
        print(f"\n成员统计:")
        print(f"  总数: {data.get('total', 0)}")
        print(f"  当前页: {len(data.get('items', []))}")

        items = data.get('items', [])
        if items:
            print(f"\n成员列表:")
            for idx, member in enumerate(items, 1):
                print(f"\n  {idx}. {member.get('nickname', '未知')}")
                print(f"     用户ID: {member.get('user_id')}")
                print(f"     认证状态: {'已认证' if member.get('is_verified') else '未认证'}")
                print(f"     公司: {member.get('company_name') or '未填写'}")
                print(f"     职位: {member.get('job_title') or '未填写'}")
                print(f"     加入时间: {member.get('joined_at')}")
        else:
            print(f"  暂无成员")

        return True
    else:
        print(f"[ERROR] 获取失败")
        print(json.dumps(response.json(), indent=2, ensure_ascii=False))
        return False

def main():
    print(f"\n{'='*60}")
    print(f"圈子成员列表接口测试")
    print(f"{'='*60}")

    # 1. 获取token
    print("\n> 获取登录token...")
    token = get_token()
    if not token:
        print("[ERROR] 无法获取Token,测试终止!")
        return
    print("[OK] 登录成功")

    # 2. 先获取我的圈子列表
    print("\n> 获取我的圈子列表...")
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(
        f"{BASE_URL}{API_PREFIX}/circle/me",
        headers=headers,
        params={"offset": 0, "limit": 1}
    )

    if response.status_code != 200:
        print("[ERROR] 无法获取圈子列表")
        return

    circles = response.json().get('data', {}).get('items', [])
    if not circles:
        print("[ERROR] 没有加入任何圈子")
        return

    circle_code = circles[0].get('circle_code')
    circle_name = circles[0].get('name')
    print(f"[OK] 找到圈子: {circle_name} ({circle_code})")

    # 3. 测试获取成员列表
    success = test_get_circle_members(token, circle_code)

    # 总结
    print(f"\n{'='*60}")
    print(f"测试结果: {'通过' if success else '失败'}")
    print(f"{'='*60}\n")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n[ERROR] 测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
