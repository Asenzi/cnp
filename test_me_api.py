#!/usr/bin/env python3
"""测试个人中心页面相关接口"""
import requests
import json
from datetime import datetime

BASE_URL = "http://127.0.0.1:8000"
API_PREFIX = "/api/v1"

# 测试用的手机号和验证码
TEST_PHONE = "13800138000"
TEST_CODE = "123456"  # 需要根据实际情况修改

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'

def print_test(name):
    print(f"\n{Colors.BLUE}{'='*60}{Colors.END}")
    print(f"{Colors.BLUE}测试: {name}{Colors.END}")
    print(f"{Colors.BLUE}{'='*60}{Colors.END}")

def print_success(msg):
    print(f"{Colors.GREEN}[OK] {msg}{Colors.END}")

def print_error(msg):
    print(f"{Colors.RED}[ERROR] {msg}{Colors.END}")

def print_info(msg):
    print(f"{Colors.YELLOW}> {msg}{Colors.END}")

def print_json(data, indent=2):
    print(json.dumps(data, indent=indent, ensure_ascii=False))

def test_login():
    """测试登录获取token"""
    print_test("登录获取Token")

    # 先发送验证码
    print_info("发送短信验证码...")
    response = requests.post(
        f"{BASE_URL}{API_PREFIX}/auth/sms-code",
        json={"phone": TEST_PHONE}
    )

    if response.status_code == 200:
        result = response.json()
        print_success(f"验证码发送成功: {result.get('message', '')}")
        data = result.get('data', {})
        print_json(data)

        # 获取debug验证码
        debug_code = data.get('debug_code')
        if debug_code:
            print_info(f"使用debug验证码: {debug_code}")
            actual_code = debug_code
        else:
            actual_code = TEST_CODE
    else:
        print_error(f"验证码发送失败: {response.status_code}")
        print_json(response.json())
        return None

    # 使用验证码登录
    print_info(f"\n使用验证码登录 (手机号: {TEST_PHONE}, 验证码: {actual_code})...")
    response = requests.post(
        f"{BASE_URL}{API_PREFIX}/auth/login",
        json={
            "phone": TEST_PHONE,
            "code": actual_code
        }
    )

    if response.status_code == 200:
        result = response.json()
        print_success("登录成功!")
        print_info("完整响应数据:")
        print_json(result)

        data = result.get('data', {})
        token = data.get('token') or data.get('access_token')
        user_info = data.get('user', {}) or data.get('user_info', {})

        print_info(f"\nToken: {token[:50]}..." if token else "\nToken: None")
        print_info(f"用户ID: {user_info.get('user_id')}")
        print_info(f"昵称: {user_info.get('nickname')}")
        print_info(f"手机号: {user_info.get('phone')}")

        return token
    else:
        print_error(f"登录失败: {response.status_code}")
        print_json(response.json())
        return None

def test_get_current_user_profile(token):
    """测试获取当前用户资料"""
    print_test("获取当前用户资料 (GET /api/v1/user/me)")

    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(
        f"{BASE_URL}{API_PREFIX}/user/me",
        headers=headers
    )

    if response.status_code == 200:
        result = response.json()
        print_success("获取用户资料成功!")
        data = result.get('data', {})

        print_info("\n基本信息:")
        print(f"  用户ID: {data.get('user_id')}")
        print(f"  昵称: {data.get('nickname')}")
        print(f"  手机号: {data.get('phone')}")
        print(f"  头像: {data.get('avatar_url')}")
        print(f"  认证状态: {'已认证' if data.get('is_verified') else '未认证'}")
        print(f"  实名认证: {'已认证' if data.get('real_name_verified') else '未认证'}")

        print_info("\n职业信息:")
        print(f"  公司: {data.get('company_name') or '未填写'}")
        print(f"  职位: {data.get('job_title') or '未填写'}")
        print(f"  行业: {data.get('industry_label') or '未填写'}")
        print(f"  城市: {data.get('city_name') or '未填写'}")

        print_info("\n统计数据:")
        print(f"  圈子数: {data.get('circle_count', 0)}")
        print(f"  人脉数: {data.get('network_count', 0)}")
        print(f"  余额: {data.get('balance', 0):.2f} 元")
        print(f"  积分: {data.get('points', 0)}")

        print_info("\n会员信息:")
        print(f"  会员状态: {data.get('member_status')}")
        print(f"  是否会员: {'是' if data.get('is_member') else '否'}")
        if data.get('member_expire_at'):
            print(f"  会员到期: {data.get('member_expire_at')}")

        print_info("\n联系方式:")
        print(f"  展示手机号: {data.get('display_phone') or '未设置'}")
        print(f"  展示微信号: {data.get('display_wechat') or '未设置'}")
        print(f"  邮箱: {data.get('email') or '未设置'}")

        print_info("\n人脉包信息:")
        print(f"  剩余查看次数: {data.get('contact_package_remaining_views', 0)}")
        print(f"  已使用次数: {data.get('contact_package_used_views', 0)}")
        print(f"  可查看他人联系方式: {'是' if data.get('can_view_others_contact') else '否'}")

        return data
    else:
        print_error(f"获取用户资料失败: {response.status_code}")
        print_json(response.json())
        return None

def test_get_privacy_settings(token):
    """测试获取隐私设置"""
    print_test("获取隐私设置 (GET /api/v1/user/me/privacy)")

    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(
        f"{BASE_URL}{API_PREFIX}/user/me/privacy",
        headers=headers
    )

    if response.status_code == 200:
        result = response.json()
        print_success("获取隐私设置成功!")
        data = result.get('data', {})

        print_info("\n隐私设置:")
        print(f"  联系方式对好友可见: {'是' if data.get('phone_visible_to_friends') else '否'}")
        print(f"  保护真实姓名: {'是' if data.get('protect_real_name') else '否'}")
        print(f"  允许通过邮箱查找: {'是' if data.get('allow_find_by_email') else '否'}")
        print(f"  好友请求范围: {data.get('friend_request_scope')}")
        print(f"  私信接收范围: {data.get('message_scope')}")
        print(f"  允许自动添加好友: {'是' if data.get('allow_auto_add_friend') else '否'}")
        print(f"  黑名单用户数: {data.get('blocked_count', 0)}")

        return data
    else:
        print_error(f"获取隐私设置失败: {response.status_code}")
        print_json(response.json())
        return None

def test_get_blocked_users(token):
    """测试获取黑名单列表"""
    print_test("获取黑名单列表 (GET /api/v1/user/me/blocked-users)")

    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(
        f"{BASE_URL}{API_PREFIX}/user/me/blocked-users?offset=0&limit=20",
        headers=headers
    )

    if response.status_code == 200:
        result = response.json()
        print_success("获取黑名单列表成功!")
        data = result.get('data', {})

        print_info(f"\n黑名单统计:")
        print(f"  总数: {data.get('total', 0)}")
        print(f"  当前页: {len(data.get('items', []))}")

        items = data.get('items', [])
        if items:
            print_info("\n黑名单用户:")
            for item in items:
                print(f"  - {item.get('nickname')} (ID: {item.get('user_id')})")
                print(f"    拉黑时间: {item.get('blocked_at')}")
        else:
            print_info("  黑名单为空")

        return data
    else:
        print_error(f"获取黑名单列表失败: {response.status_code}")
        print_json(response.json())
        return None

def test_update_profile(token):
    """测试更新用户资料"""
    print_test("更新用户资料 (PATCH /api/v1/user/me)")

    headers = {"Authorization": f"Bearer {token}"}

    # 只更新简介
    update_data = {
        "intro": f"这是测试更新的简介 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    }

    print_info(f"更新数据: {update_data}")

    response = requests.patch(
        f"{BASE_URL}{API_PREFIX}/user/me",
        headers=headers,
        json=update_data
    )

    if response.status_code == 200:
        result = response.json()
        print_success(f"更新用户资料成功! {result.get('message', '')}")
        data = result.get('data', {})

        print_info(f"\n更新后的简介: {data.get('intro')}")

        # 检查是否需要审核
        review = data.get('_review', {})
        if review.get('review_required'):
            print_info(f"需要审核: {review.get('review_reason')}")

        return data
    else:
        print_error(f"更新用户资料失败: {response.status_code}")
        print_json(response.json())
        return None

def test_token_validation(token):
    """测试Token有效性"""
    print_test("测试Token有效性")

    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(
        f"{BASE_URL}{API_PREFIX}/user/me",
        headers=headers
    )

    if response.status_code == 200:
        print_success("Token有效!")
        return True
    elif response.status_code == 401:
        print_error("Token无效或已过期!")
        return False
    else:
        print_error(f"Token验证失败: {response.status_code}")
        return False

def main():
    print(f"\n{Colors.BLUE}{'='*60}{Colors.END}")
    print(f"{Colors.BLUE}个人中心页面接口测试{Colors.END}")
    print(f"{Colors.BLUE}{'='*60}{Colors.END}")
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"API地址: {BASE_URL}{API_PREFIX}")

    # 1. 登录获取token
    token = test_login()
    if not token:
        print_error("\n无法获取Token,测试终止!")
        return

    # 2. 测试Token有效性
    if not test_token_validation(token):
        print_error("\nToken无效,测试终止!")
        return

    # 3. 获取当前用户资料
    user_profile = test_get_current_user_profile(token)

    # 4. 获取隐私设置
    privacy_settings = test_get_privacy_settings(token)

    # 5. 获取黑名单列表
    blocked_users = test_get_blocked_users(token)

    # 6. 更新用户资料
    updated_profile = test_update_profile(token)

    # 7. 再次获取用户资料验证更新
    print_test("验证更新结果")
    final_profile = test_get_current_user_profile(token)

    # 总结
    print(f"\n{Colors.BLUE}{'='*60}{Colors.END}")
    print(f"{Colors.BLUE}测试总结{Colors.END}")
    print(f"{Colors.BLUE}{'='*60}{Colors.END}")

    tests = [
        ("登录获取Token", token is not None),
        ("Token有效性验证", token is not None),
        ("获取用户资料", user_profile is not None),
        ("获取隐私设置", privacy_settings is not None),
        ("获取黑名单列表", blocked_users is not None),
        ("更新用户资料", updated_profile is not None),
        ("验证更新结果", final_profile is not None),
    ]

    passed = sum(1 for _, result in tests if result)
    total = len(tests)

    for name, result in tests:
        if result:
            print_success(f"{name}: 通过")
        else:
            print_error(f"{name}: 失败")

    print(f"\n{Colors.BLUE}测试结果: {passed}/{total} 通过{Colors.END}")

    if passed == total:
        print_success("\n所有测试通过!")
    else:
        print_error(f"\n有 {total - passed} 个测试失败!")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n{Colors.YELLOW}测试被用户中断{Colors.END}")
    except Exception as e:
        print(f"\n\n{Colors.RED}测试过程中发生错误: {e}{Colors.END}")
        import traceback
        traceback.print_exc()
