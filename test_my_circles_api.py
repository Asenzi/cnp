#!/usr/bin/env python3
"""测试我的圈子页面接口"""
import requests
import json

BASE_URL = "http://127.0.0.1:8000"
API_PREFIX = "/api/v1"

# 使用之前测试获取的token
TEST_PHONE = "13800138000"

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

def get_token():
    """获取登录token"""
    print_info("发送短信验证码...")
    response = requests.post(
        f"{BASE_URL}{API_PREFIX}/auth/sms-code",
        json={"phone": TEST_PHONE}
    )

    if response.status_code != 200:
        print_error("获取验证码失败")
        return None

    result = response.json()
    debug_code = result.get('data', {}).get('debug_code')

    if not debug_code:
        print_error("未获取到debug验证码")
        return None

    print_info(f"使用debug验证码: {debug_code}")

    response = requests.post(
        f"{BASE_URL}{API_PREFIX}/auth/login",
        json={
            "phone": TEST_PHONE,
            "code": debug_code
        }
    )

    if response.status_code != 200:
        print_error("登录失败")
        return None

    result = response.json()
    token = result.get('data', {}).get('access_token')

    if token:
        print_success("登录成功,获取到token")
        return token

    print_error("登录成功但未获取到token")
    return None

def test_get_my_circles(token, offset=0, limit=20, keyword=""):
    """测试获取我的圈子列表"""
    print_test(f"获取我的圈子列表 (offset={offset}, limit={limit}, keyword='{keyword}')")

    headers = {"Authorization": f"Bearer {token}"}

    params = {
        "offset": offset,
        "limit": limit
    }

    if keyword:
        params["keyword"] = keyword

    response = requests.get(
        f"{BASE_URL}{API_PREFIX}/circle/me",
        headers=headers,
        params=params
    )

    if response.status_code == 200:
        result = response.json()
        print_success("获取圈子列表成功!")
        data = result.get('data', {})

        print_info("\n圈子统计:")
        print(f"  总数: {data.get('total', 0)}")
        print(f"  当前页数量: {len(data.get('items', []))}")
        print(f"  偏移量: {data.get('offset', 0)}")
        print(f"  每页数量: {data.get('limit', 0)}")

        items = data.get('items', [])
        if items:
            print_info("\n圈子列表:")
            for idx, item in enumerate(items, 1):
                print(f"\n  {idx}. {item.get('name', '未命名')}")
                print(f"     圈子代码: {item.get('circle_code')}")
                print(f"     描述: {item.get('description', '无')}")
                print(f"     行业: {item.get('industry_label', '未设置')}")
                print(f"     成员数: {item.get('member_count', 0)}")
                print(f"     帖子数: {item.get('post_count', 0)}")
                print(f"     创建者: {item.get('owner_nickname', '未知')}")
                print(f"     创建者认证: {'是' if item.get('owner_is_verified') else '否'}")
                print(f"     我的角色: {item.get('my_role', '未知')}")
                print(f"     加入时间: {item.get('joined_at', '未知')}")
        else:
            print_info("  暂无圈子")

        return data
    else:
        print_error(f"获取圈子列表失败: {response.status_code}")
        print_json(response.json())
        return None

def test_search_my_circles(token, keyword):
    """测试搜索我的圈子"""
    print_test(f"搜索我的圈子 (关键词: '{keyword}')")

    headers = {"Authorization": f"Bearer {token}"}

    response = requests.get(
        f"{BASE_URL}{API_PREFIX}/circle/me",
        headers=headers,
        params={
            "offset": 0,
            "limit": 20,
            "keyword": keyword
        }
    )

    if response.status_code == 200:
        result = response.json()
        print_success("搜索成功!")
        data = result.get('data', {})

        print_info(f"\n搜索结果: 找到 {data.get('total', 0)} 个圈子")

        items = data.get('items', [])
        if items:
            for idx, item in enumerate(items, 1):
                print(f"  {idx}. {item.get('name')} (代码: {item.get('circle_code')})")
        else:
            print_info("  未找到匹配的圈子")

        return data
    else:
        print_error(f"搜索失败: {response.status_code}")
        print_json(response.json())
        return None

def test_pagination(token):
    """测试分页功能"""
    print_test("测试分页功能")

    # 第一页
    print_info("\n获取第一页 (offset=0, limit=5)...")
    page1 = test_get_my_circles(token, offset=0, limit=5, keyword="")

    if page1 and page1.get('total', 0) > 5:
        # 第二页
        print_info("\n获取第二页 (offset=5, limit=5)...")
        page2 = test_get_my_circles(token, offset=5, limit=5, keyword="")

        if page1 and page2:
            print_success("\n分页功能正常")
            return True
    else:
        print_info("\n圈子总数不足,无法测试分页")

    return False

def main():
    print(f"\n{Colors.BLUE}{'='*60}{Colors.END}")
    print(f"{Colors.BLUE}我的圈子页面接口测试{Colors.END}")
    print(f"{Colors.BLUE}{'='*60}{Colors.END}")
    print(f"API地址: {BASE_URL}{API_PREFIX}")

    # 1. 获取token
    token = get_token()
    if not token:
        print_error("\n无法获取Token,测试终止!")
        return

    # 2. 获取我的圈子列表
    circles_data = test_get_my_circles(token)

    # 3. 测试分页
    if circles_data and circles_data.get('total', 0) > 0:
        test_pagination(token)

    # 4. 测试搜索功能
    if circles_data and circles_data.get('items'):
        # 使用第一个圈子的名称进行搜索
        first_circle_name = circles_data['items'][0].get('name', '')
        if first_circle_name:
            test_search_my_circles(token, first_circle_name)

    # 总结
    print(f"\n{Colors.BLUE}{'='*60}{Colors.END}")
    print(f"{Colors.BLUE}测试总结{Colors.END}")
    print(f"{Colors.BLUE}{'='*60}{Colors.END}")

    tests = [
        ("获取Token", token is not None),
        ("获取圈子列表", circles_data is not None),
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
